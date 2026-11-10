# Candidate-only contact geometry correction

Recommended candidate: `width-260000/pcb/maru60.kicad_pcb`, SHA256 `194180467c8ae7ead7d6bc23fe23d6dbb737cbd0ca04a3c1513bd141fe6890d0`. It is not promoted. Original selected board SHA256 is `ddea15f7eb9188617f81af2e998ed49bf385cfcc473d68bd40beb66ec4ff6020`; a byte copy remains in `baseline-250um.kicad_pcb`.

Ten0.25mm outer-layer tracks terminate on0.25mm via drills. Their equal-radius capsule ends and drill contours yield67 extra microscopic positive polygons after native integer subtraction.48 of those isolated fragments participate in51 failed guarded contacts. Native geometry inspection is in `native-shapes.json`; all edited UUIDs are in `affected-uuids.txt`.

Variants0.251mm and0.260mm both reduce the affected objects from77 positive components to10. Both pass native9opens/26warnings/0othererrors/ERC0/parity0 and byte-identical cold refill of58 CAD files.0.260mm additionally passed a fresh complete material export and all contact/partition checks.0.251mm has no full material-export claim. Existing250um source is the negative: `negative.py` freshly reconstructs every51 source contact and reproduces its original positive raw overlap and zero guarded overlap.

Actual serialized0.260mm delta (`width-260000.patch`) is ten width changes and one generated F.Cu GND filled-contour line, not merely ten lines. No endpoint, net, layer, via, drilled hole, zone boundary, schematic or inner-layer copper changes. The generated F.Cu zone `abadb040-0e38-4dde-9ed2-fe817c008499`, component3, changes area94.432693940882 to94.432693921669mm². This small outer-layer refill delta is explicit scope, not hidden as an unchanged object. All other14637 nonedited material nodes retain identical metadata.

`comparison.json` verifies all22525 old admitted material contacts still exist after explicit viable-node remapping for the ten widened tracks; no contacts are lost. It verifies every named-pad partition and every barrel join equal. `component-mapping.json` enumerates all original and replacement per-object nodes, including the vanished isolated fragments. It does not conflate those old nodes or call them unchanged. `guard-identity.json` proves the2nm inward,1nm-error guard is unchanged; the new full graph contains zero guard failures. `open-pair-check.txt` verifies exact native open endpoint UUID pairs, not just open count.

Separate containment limits: the ideal analytic capsule with fixed segment endpoints and larger radius contains the original capsule, and subtracting identical holes preserves that mathematical inclusion. That is separate from native integer polygon inclusion. An attempted exact native old-minus-new containment assertion FAILED: five objects leave residual areas48,329,465,395.5,48nm² (total1285.5nm²; max465nm²). Every residual deflates to zero under2nm, but that is diagnostic information, not an exact-containment PASS or a guard waiver. `containment.json` records these residuals. Actual full native material contacts and partitions govern the result; no optional containment success is claimed.

## Reproduction and binary observables

Run from repository root using the unchanged native image and repository tools:

- `tools/run_kicad9.sh python3 .omo/evidence/pcb-routing-20261109/contact-geometry-fix/inspect_native_shapes.py` writes native shape metadata.
- `tools/run_kicad9.sh python3 .omo/evidence/pcb-routing-20261109/contact-geometry-fix/variants.py` creates both candidates; requires those candidate directories not already exist. `variants.log` records77→10 for both.
- `tools/run_kicad9.sh python3 tools/check_pcb_native.py --checkpoint .omo/evidence/pcb-routing-20261109/contact-geometry-fix/width-260000 --output .omo/evidence/pcb-routing-20261109/contact-geometry-fix/native-260000 --expected-opens 9 --material` exits0 and produces native RESULT.json/full material graph. Output directory must be new when repeating. Omit`--material` and use251000 paths to reproduce its recorded native scenario.
- `tools/run_kicad9.sh python3 .omo/evidence/pcb-routing-20261109/contact-geometry-fix/negative.py` exits0 iff all51 source failures reproduce exactly.
- `tools/run_kicad9.sh python3 .omo/evidence/pcb-routing-20261109/contact-geometry-fix/containment.py` records native difference diagnostics; its completion is not containment acceptance.
- `uv run .omo/evidence/pcb-routing-20261109/contact-geometry-fix/compare.py` exits0 iff serialized scope, source identities, all accepted contacts, partitions and barrels satisfy the recorded criteria. Output is comparison.json.
- Native open-pair comparison: extract sorted`[.unconnected_items[] | [.items[].uuid] | sort] | sort` from both drc.json files, then`cmp source-open-pairs.json candidate-open-pairs.json`; exit0 recorded in open-pair-check.txt.

Scripts each own one bounded evidence responsibility, are under120 lines, and change only candidate/evidence paths. No production code or tests were changed; real native scenarios are the validation. Original selected checkpoint remains unchanged. No hardware, SI, production readiness or physical qualification claim.

Preserved full58-file source CAD: baseline-250000/pcb/. Preserved source material graph: baseline-material-graph.json. Negative replay uses these preserved copies.
