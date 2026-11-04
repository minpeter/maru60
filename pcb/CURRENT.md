# Current V7 experimental working selection

Open `experiments/v7-connector-ground-stitch/candidate/pcb/maru60.kicad_pro`.
PCB SHA256: aaafc033c6e9809afcb189290c3740157b7ab5596aaa0867e581f08d89807eca.

One ordinary GND via was added to the preserved c770 source. All prior records and saved fills are byte-identical. Only its actual drill removes ground, 0.049087681002 mm² per inner plane, outside every protected current and historical signal shadow. The native/independent material and cold-refill checks pass; no current precision or endpoint waiver was used.

9,750 tracks; 919 vias; 382 footprints; 13,176.816253756544 mm. DRC: 66 unchanged warnings, 12 unchanged expansion opens, zero other hard errors. ERC and schematic parity: zero. All 245 pad-net partitions, 247 original GND-pad roots and old contacts are preserved.

The existing USB neck and connector stub remain. Added copper may alter fields/coupling; there is no post-change extraction or SI/ESD/EMC/hardware gain claim. This remains an unfinished experimental design, not a manufacturing release. C124 and J3 alternatives are not selected here. Historical BUCK-only 1 nm acceptance remains confined to that earlier transition; its original strict failure is unchanged.

Active firmware remains `firmware/qmk/keyboards/maru60/rp2350`, with the reviewed recovery overlay unchanged and LED qualification 0. No full pinned QMK/ARM build or flashing. Run `python3 pcb/experiments/led-startup-recovery/verify_package.py --active-root pcb` from the repository root to check its identity. The original lost history/full historical QA are not restored.
