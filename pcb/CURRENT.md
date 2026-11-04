# Current V7 recovery selection

Selected CAD: `experiments/v7-four-reference-logo/candidate-four/pcb/maru60.kicad_pcb`.

SHA256: `2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373`.

This successor changes only four reference labels (C100, R140, R160, R134) and translates the complete LOGO1 artwork. All electrical geometry, rules, pads, nets, drills and saved planes are unchanged from the exact recovered 7c23 board. The previous selected source remains under `experiments/v7-reference-legibility`.

Verified: 12 expansion-GPIO opens, 0 critical source opens, 68 warnings (24 removed, none added), 0 other hard DRC errors, ERC 0 and parity 0. Tracks 9,752, vias 919, total track length 13,181.60473138763 mm. Exact source-bound native checks, independent ink/association review and complete warning lifecycle are under the new unit. This bounded metadata/artwork adoption does not claim a new cold-fill replay, active simulation or hardware/manufacturing/3D qualification.

The short C124/R121/R125 routing trial remains unselected. Read the root README for the original missing Git history and other recovery limits.

## Active recovery firmware

The active development overlay is `firmware/qmk/keyboards/maru60/rp2350`; supporting files are under `engineering`. It is byte-identical to the reviewed candidate under `experiments/led-startup-recovery/candidate`. Of the former fixed overlay, 19 files are exact recovery and three are new code. Qualification defaults to 0. Host tests and the fresh static V7 mapping pass; full QMK/ARM and hardware verification remain pending. No CAD byte changed in this firmware adoption.

Verify package and active identity with `python3 pcb/experiments/led-startup-recovery/verify_package.py --active-root pcb` from the repository root. Follow that package's README for a fresh complete host replay. This is development-source adoption only, not a build, flash or release.

The completed C124 circuit experiment and its independent reviews are archived at `experiments/v7-c124-short-local-review`. It remains explicitly unselected; this current-board pointer is unchanged.
