# Current V7 recovery selection

Selected CAD: `experiments/v7-reference-legibility/candidate/pcb/maru60.kicad_pcb`.

SHA256 `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1` is exactly equal to the original selected unit34 board. No new circuit or layout change is selected by this recovery commit.

Fresh recovery checks: 12 opens (all incomplete expansion GPIO), 0 critical source opens, 92 warnings, other DRC errors0, ERC0, schematic parity0. Tracks9752, vias919. The older 14-open a9ff board is retained only in its saved source archive and is not this selection.

Read the root README for the unrecovered Git history, historical QA, full later project manifest and firmware limitations. The 100-ohm C124 long-route trial remains rejected. The short C124/R121 alternative and the safe label/logo subset remain unselected.

## Active recovery firmware

The active development overlay is `firmware/qmk/keyboards/maru60/rp2350`; supporting files are under `engineering`. It is byte-identical to the reviewed candidate under `experiments/led-startup-recovery/candidate`. Of the former fixed overlay, 19 files are exact recovery and three are new code. Qualification defaults to 0. Host tests and the fresh static V7 mapping pass; full QMK/ARM and hardware verification remain pending. No CAD byte changed in this firmware adoption.

Verify package and active identity with `python3 pcb/experiments/led-startup-recovery/verify_package.py --active-root pcb` from the repository root. Follow that package's README for a fresh complete host replay. This is development-source adoption only, not a build, flash or release.
