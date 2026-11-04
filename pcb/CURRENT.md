# Current V7 recovery selection

Selected CAD: `experiments/v7-buck-feedback-cleanup/candidate/pcb/maru60.kicad_pcb`.
SHA256: `aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f`.

The degree-one BUCK_FB via and 2.85 mm unused arm are removed, preserving the 1.95 mm active feedback section and all three feedback pads. The previous 2c7 four-label/logo project remains unchanged.

Verified: 12 unchanged expansion-GPIO opens, zero critical source opens, 67 warnings (one removed, none added), zero other hard DRC errors, ERC zero and parity zero. Tracks 9,752; vias 918; footprints 382; summed track length 13,178.75473138763 mm. All 245 pad partitions, 731 plane contacts and 247 rooted GND pads remain exact.

The original strict zero-global-plane-loss check remains FAIL. Selection explicitly uses the independently reviewed candidate-specific bilateral 1 nm contour-precision criterion, with a proven 0.733693794 nm upper bound and unchanged critical reference/contact/root and normal clearance checks. It is not a generic epsilon waiver or electrical/manufacturing qualification. Full reasons, original failures, controls and final fresh native checks are preserved in this unit.

The J3 and C124 circuit trials remain unselected. No noise, pickup or loop-stability benefit is claimed.

## Corrected current physical evidence

`experiments/v7-material-contact-correction/` supersedes the old global contact/support-area measurements. The exact reviewed R2 implementation is active at `tools/export_material_graph.py`. Five fresh material rechecks and exact positive-interior certificates for all 22,531 accepted selected-board contacts preserve the current 245-net pad connectivity. Microscopic unproved contacts remain excluded. No CAD/firmware change, new experiment adoption or hardware qualification accompanies this correction. Original evidence and separate failed plane/reference gates remain intact.

## Active recovery firmware

The active development overlay remains `firmware/qmk/keyboards/maru60/rp2350`, with supporting files under `engineering`. It is unchanged and byte-identical to the reviewed LED startup recovery. Nineteen former fixed-overlay files were recovered exactly; three are newly tested implementations. LED qualification remains 0. No full pinned QMK/ARM build, flashing or hardware acceptance is claimed.

Verify exact package/active-file identity from repository root with `python3 pcb/experiments/led-startup-recovery/verify_package.py --active-root pcb`. The original lost Git history and full historical QA were not restored.
