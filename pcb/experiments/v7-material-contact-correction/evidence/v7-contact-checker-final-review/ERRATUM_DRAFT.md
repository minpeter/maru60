# Physical-contact evidence correction

Status: selected-board correction verified; J3 and C124 family rechecks are still running. This document is not a new CAD acceptance or selection record.

## What was wrong

The recovered global exporter `export_native_physical_graph.py` with SHA256 `f53420eea14c81281a0f103951f25880ae9afe72631ac7370d299d98374fb6a9` treated some native via-neighbor wrappers as tracks, so its type-dependent hole subtraction could be skipped and the resulting disk cached. It also subtracted third-party physical drills only from zones, not from every copper object. Compound pad polygons were not consistently unioned before measuring material, and object UUID identity could conflate disconnected fragments. Thus original positive contact lists and support areas must not be presented as accurate drill-subtracted material evidence merely because before/after pad partitions matched.

The reachable BUCK, J3, current C128-retirement and C124 recovery exports use this exact helper. The pre-loss U10/C128/width/typography acceptance helper and complete original suites were not recovered. Their affected/unaffected status cannot be inferred from this lineage check. Native DRC reports, raw CAD deltas and separate local canonical-object proofs are distinct evidence; this correction does not replace them.

## Correction and actual selected result

Wrapper-only R1 is retained as an intermediate, incomplete repair. R2 (`57987368b095de525fc729a0d4b729b14cfc207afd07b4bd214ee5463a7719b9`) canonicalizes UUIDs, unions native primitives, subtracts all actual through drills from every object and zone, separates material islands per layer, and permits plated interlayer joins only after source-specific enclosure and intact-annulus checks. It fails closed outside its checked KiCad 9.0.2+dfsg-1/four-copper-layer/through-hole assumptions. NPTH does not receive an electrical barrel join. Native connectivity supplies candidate pairs, not proof of material contact.

For selected board `aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f`, predecessor `2c7e100a…` and unselected C128 `cafa9213…`:

- All 1,082 net-bearing pad identities and pad partitions on all 245 nets remain unchanged under R2. Material roots were independently reconstructed from its accepted edges and proved barrel joins.
- Each corrected graph drops 105 originally reported direct object pairs. Surviving support values also change; the new values supersede the old physical-area claims. They remain native polygon measurements, not exact rational area certificates.
- Each graph retains 51 explicit microscopic material-edge guard failures outside the connectivity graph. No zone edge fails the guard. The 56 NPTH approximation fragments have no accepted or guard-failed edge, barrel join, or named-pad-root participation.
- Both transitions preserve every retained material contact, measured support, and material partition after excluding exactly the declared retired and newly added objects. BUCK's replacement-track support is reported separately from retained-old-object equality. C128/C129 supply/return and attachment paths remain continuously connected through material nodes.
- A separate exact rational verifier certifies every one of the selected board's 22,531 accepted material contacts with a point at least 2 nm inside both reconstructed physical components. It checks exact polygon membership and distance to all boundary segments. Native intersections provide candidate points only. The 51 rejected edges are not waived. The first audit's 68 operand-order area-check mismatches are preserved; corrected replay reverifies all prior points and resolves those records without exemptions.

## Limits and preserved failures

The exact point certificates prove robust overlap of the reconstructed native polygons; they are not a wholly independent exact reconstruction of all CAD material or every possible physical contact. Barrel proofs, native candidate-pair discovery and polygonized geometry remain explicit source-specific model assumptions. No generic shape, manufacturing, SI, noise, active-loop stability or hardware qualification is claimed.

The R2 serial runners isolate four standard XDG homes but set nonstandard `XDG_RUNTIME_HOME`, not `XDG_RUNTIME_DIR`. Five-standard-home isolation is not claimed for those runs. The exact selected-board interior replay explicitly isolates all five standard variables. Original CAD and all old evidence remain unchanged.

C128 retirement still fails the original strict global plane-preservation rule: exact saved contours lose 30,756 nm² per inner plane. Its strict result is not waived by the BUCK-only precision criterion or by corrected connectivity. J3's prior new-transition reference failure also remains separate. These investigations do not select either experiment.
