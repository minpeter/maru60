# A22 hole-preserving positive source witness

The immutable A22 PCB remains unchanged. This addendum supersedes reliance on the optional annular verifier's two unnecessary `Unfracture()` calls. A separate exact B75/B70 sequence replay demonstrated hole loss in that implementation; it does **not** establish that A22's native/source gate was false.

## Positive result
Exact A22 `fdd9ce12580c1dc8a1fe14dfced60f0199b2911b2d7c87a818a2bf7affb5fa33`: all 13 scoped source groups, including padless conductor components, have source witnesses. GND 215/215, +3V3 28/28, +1V1 10/10, +5V 7/7, +5V_LED 160/160. Native protected opens/hard errors remain 0. Runtime 44.0 s.

## Why the faster proof is conservative
Native ERROR_INSIDE polygons are subsets of the actual conductor. Subtracting ERROR_OUTSIDE polygons of the physical drills leaves subsets of actual copper, both for conductors and filled islands. A positive overlap (or exact finite shared boundary) between these subsets is a real contact: no coordinate inflation or epsilon promotion is used. Polygonization error is 1000 nm (1 um), **not a PCB clearance relaxation**. A root-driven graph may stop once every scoped conductor component has a positive source path; additional island-only edges cannot invalidate these paths. It does not claim every isolated filled island was exhaustively classified.

A coarse negative is only unproved contact, requiring finer refinement before any standalone disconnection claim. The included negative control cuts one real C115 supply link: both C115.1 and U1.30 remain unproved by this conservative graph, and an independent native +3V3 open plus the original source helper separately reject it. Other source groups still pass. That rejected board has 137 missing-footprint-library warnings because its diagnostic copy omitted external libraries; it is not a qualified candidate.

## Reproduce read-only
Use KiCad 9.0.2 /usr/bin/python3 with pcbnew, numpy, and the existing repository `pcb/tools/sexp.py` dependency. No refill, SaveBoard, relabeling or main edits occur.

    /usr/bin/python3 annular_source_conservative_positive_4L.py A22.kicad_pcb NEW-positive.json --native-drc A22-native-drc.json --expected-sha256 fdd9ce12580c1dc8a1fe14dfced60f0199b2911b2d7c87a818a2bf7affb5fa33

The original 1 nm exhaustive/all-contact run and the 1 nm lazy full-frontier run were stopped without terminal results; neither is credited as passing. The included primitive-line boundary equivalence report is the B owner's 31-test control for the copied exact integer boundary predicate. Current A22 remains 22 opens/0 hard: this is connectivity evidence, not new routing closure or powered/SI/assembly/fabrication qualification.
