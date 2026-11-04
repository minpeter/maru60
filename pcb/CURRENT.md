# Current V7 recovery selection

Selected CAD: `experiments/v7-reference-legibility/candidate/pcb/maru60.kicad_pcb`.

SHA256 `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1` is exactly equal to the original selected unit34 board. No new circuit or layout change is selected by this recovery commit.

Fresh recovery checks: 12 opens (all incomplete expansion GPIO), 0 critical source opens, 92 warnings, other DRC errors0, ERC0, schematic parity0. Tracks9752, vias919. The older 14-open a9ff board is retained only in its saved source archive and is not this selection.

Read the root README for the unrecovered Git history, historical QA, full later project manifest and firmware limitations. The 100-ohm C124 long-route trial remains rejected. The short C124/R121 alternative and the safe label/logo subset remain unselected.
