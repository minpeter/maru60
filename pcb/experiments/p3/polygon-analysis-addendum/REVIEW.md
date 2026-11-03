# P3 polygon-analysis safety addendum

The AVDD study identified that calling Unfracture on a normalized BooleanAdd union can discard actual holes. That preliminary shadow result was rejected; no CAD was changed. Native direct GetFilledPolysList/UnitSet source witnesses do not use that transformation.

This addendum checked130 actual P3 per-zone lost/gained differences and exact retained-reference union→subtract pipelines across five completed stages. All difference results had zero holes before and after; the large hole-loss condition is not triggered here. Nonetheless Unfracture perturbed tiny slivers/outline counts, up to5.19668e-7mm². Therefore every affected retained-track comparison was rerun with the call removed, preserving normalized native outlines/holes and original oldContains/!newContains midpoint confirmation.

All five old reference results reproduce exactly: S1→S2(7,934 tracks),S2→rejectedS3(7,939),S2→C105(7,939),rejectedS3→repairedbridge(7,947),bridge→composition(7,958): zero new left/center/right reference-loss intervals. Per-zone area figures were recorded BEFORE Unfracture and remain authoritative. Old frozen payloads were not rewritten. Future helper copies omit this unsafe call entirely. Direct new-feed boundary/holes audits were unaffected and still preserve the separate0.509167mm VIN edge-only LX-keepout caveat.

Scope is exactly these hash-bound P3 inputs, not a blanket validation/invalidation of arbitrary historical scripts or physical return performance.
