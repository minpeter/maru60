# Exact positive-interior contact witness helper

Standalone optional verifier, not installed into any active exporter. Files in this directory only were created. No board was loaded or exported.

## API and integration

```python
from positive_witness import prepare_polyset, find_positive_witness, require_positive_witness

# Cache exactly once per immutable physical component, before testing its edges.
prepared_a = prepare_polyset(physical_component_a)  # one outline + its holes
prepared_b = prepare_polyset(physical_component_b)

# Or select one component explicitly from a multi-outline SHAPE_POLY_SET:
prepared_zone = prepare_polyset(physical_zone, outline_index=component_index)

# A native intersection or inward-guarded intersection is merely a seed source.
# Do NOT pass inward-guarded source components as prepared_a/prepared_b unless
# deliberately proving against those instead of the original physical shapes.
result = find_positive_witness(prepared_a, prepared_b,
                               seed_polyset=native_guarded_overlap)
if not result.found:
    # Record unresolved/no witness and BLOCK the proposed contact. This is not
    # proof of disjointness and must not become an area waiver.
    raise RuntimeError((result.reason, result.candidates_checked))
edge_witness = result.witness.to_dict()

# Equivalent fail-closed convenience:
edge_witness = require_positive_witness(prepared_a, prepared_b,
                                       seed_polyset=native_guarded_overlap).to_dict()
```

`verify_positive_witness(a, b, point, clearance_nm=2)` accepts `ExactPoint`, integer coordinate pairs, or `Fraction` coordinate pairs. Floats are rejected. `verify_witness_record(a, b, dictionary)` independently rechecks a serialized certificate and verifies coordinate hashes. Guards below 2 nm are rejected. The threshold is inclusive: exactly 2 nm distance from every boundary segment is accepted, with strict polygon interior membership still required.

The certificate stores a common positive denominator and two integer numerators, a lower bound on clearance, and SHA-256 fingerprints of the prepared coordinate snapshots. Hashes preserve exact contour order, so reparsing a reordered but geometrically equal shape requires a fresh certificate. The certificates do not bind board UUID/layer: keep the existing material edge endpoints beside each certificate.

## What proves acceptance

Both physical components independently satisfy:

1. Exact horizontal-ray parity says the point is strictly in the selected outer contour and outside every hole. Hole orientation is irrelevant.
2. Exact point-to-segment distance is at least 2 nm for **every** outer/hole boundary segment. Rational points use scaled integers; squared distances use cross multiplication. No epsilon, square root, native inside classification, native area, or native Boolean topology decides acceptance.

A cached segment bounding-volume tree prunes by exact y range/rightmost x for ray tests, and by exact guard-square bounding boxes for distance tests. Seed means and sampled source y coordinates are also cached. All source rings must be straight, simple polygon boundaries with valid physical hole assignments; this helper does not reconstruct or independently validate the native Boolean-produced source topology. Native arcs are rejected until polygonized.

## Search limits and interpretation

Default search: 128 candidate proposals and up to 16 scanlines, deterministic order. Seeds include overlap bounding-box center, explicit seed points, native seed contour means/triangle centroids, cached source contour means/triangle centroids, and exact intersection centers of source material scanline intervals. Every seed passes the same final verifier. Search is incomplete and may fail for real contacts. `SearchResult.witness is None` means no certificate was obtained, not global false/disjointness. A failed search must not silently remove evidence or be called a completed proof of absence.

Bounded scanline search and BVH filtering avoid irrelevant segments, but the worst case remains linear in source boundary size per query. Native seed outlines are capped at eight; extracting one large native contour still costs its vertex count. Prepare/cache native source coordinates once, and use focused audits first.

## Verification performed

`/usr/bin/python3 -m unittest -v`: 12 tests passed under KiCad 9.0.2+dfsg-1. Tests include disjoint, boundary touching, 1 nm sliver rejection; robust overlap; ring-hole rejection; correct native component/hole selection; false native seed rejection; exact 4 nm strip threshold; diagonal segment distances; large/negative coordinates; orientation/closed endpoint; bounded-search failure; and 1,500 deterministic points against an independent direct `Fraction` oracle.

`benchmark_synthetic.py` uses only synthetic coordinate rings, not a board or native exports. This environment measured a 57,000-vertex cached zone in 0.298 s to prepare; 22,000 easy accepted small-shape contacts (256 vertices each, cached) in 0.832 s; and 731 easy accepted zone contacts in 0.028 s. These center-seed hits are a scale smoke test, not a production-board performance claim or a worst-case benchmark. See `benchmark-results.json` and `test-results.txt`.

## Selected-aead R2 audit completed

`audit_selected_aead.py` was subsequently authorized and run on the pinned selected-aead board after the separate R2 native exports finished. It uses the exact pinned checker prefix only through physical-object/barrel setup, reconstructs zone components without new neighbor discovery, checks all 14,687 node IDs/metadata/areas, object component assignments and barrel proofs, then verifies points against the original physical components.

Final corrected replay: **PASS, exit 0; 22,531 / 22,531 R2 accepted material edges have exact >=2 nm interior witnesses; 0 failures.** All pinned inputs were unchanged. The 51 pre-existing R2 guard-failing edges are excluded from this accepted-edge audit; no absence or material-graph equivalence claim is made about them here.

- Final full report: `selected-aead-exact-witnesses-order-replay.json`
- Final summary: `selected-aead-exact-witnesses-order-replay-summary.json`
- Final log: `selected-aead-order-replay.log`
- First report, preserved: `selected-aead-exact-witnesses.json`
- First log: `selected-aead-audit.log`

The first pass verified 22,463 points and hit 68 **audit-harness** area-equality exceptions before point search. R2 records zone-edge endpoints as `[zone, object]`, but computes the unguarded native intersection as `object intersection zone`. Native rounding made the reversed operand area's floating result differ for those 68 edges. The correction preserves R2's original native operand order. The final replay reconstructed the same source again, reverified all 22,463 saved points against their source-coordinate hashes, and obtained exact points for all 68 remaining edges. No material edge exception or waiver was made. The original failure records remain intact in the first report.

The report's compact witness rows are `[pinned graph edge index, x numerator, y numerator, common positive denominator]`. Use the pinned graph edge index to resolve both material node IDs and the report's `component_sha256` map for their exact coordinate hashes. Guard is 2 nm for every row. This proves positive interior for the accepted physical-component edges, not independent correctness of the native source topology itself.
