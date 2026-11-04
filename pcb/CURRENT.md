# Current V7 recovery selection

Selected CAD:`experiments/v7-gnd-deadbranch-cleanup/candidate/pcb/maru60.kicad_pcb`.
SHA256:`c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a`.

Exactly two unused F.Cu GND tracks totaling1.938477631mm are removed. The existing boundary via, every one of1,269drills and all12serialized zone records are unchanged. No component/BOM, circuit, firmware, clearance or rule change.

Verified:12unchanged expansion-GPIO opens, zero critical source opens,66warnings(one removed,noneadded), zero other hard DRC errors,ERC0,parity0. Tracks9,750;vias918;footprints382;summed track length13,176.816253756544mm. Fresh correctedR2 and independent review preserve all245pad-net partitions,247original ground returns,934barrel proofs and every retained material/zone contact witness. All51existing guard failures remain explicit. Normal cold refill reproduces the exact board.

The current aead-to-c770 transition passes strict plane preservation with zero saved-zone difference and no tolerance exception. Historical BUCK predecessor aead and its original strict failure/candidate-specific1nm condition remain unchanged; this does not retroactively change that earlier result. All previous sources and evidence are preserved.

No HF-ground, noise,PDN,SI,EMC,thermal,stability,assembly or hardware improvement is inferred. F.Cu ground foil is intentionally reduced; only the bounded nominal topology/reference claims above are established. C128,+4Vstub,J3,C124 alternatives remain unselected. See the current unit's adoption receipt and complete92-warning history(26resolved,66remaining).

## Corrected current physical evidence

The exact reviewed material checker remains `tools/export_material_graph.py`. `experiments/v7-material-contact-correction/` preserves the original error correction, five source-bound rechecks and exact positive-interior certificates for the aead baseline. The new current unit independently verifies its two-track successor; no old contact-area shortcut is reinstated. This is bounded nominal connectivity evidence, not manufacturing or hardware qualification.

## Active recovery firmware

The active development overlay remains `firmware/qmk/keyboards/maru60/rp2350`, with supporting files under `engineering`. It is unchanged and byte-identical to the reviewed LED startup recovery. Nineteen former fixed-overlay files were recovered exactly; three are newly tested implementations. LED qualification remains 0. No full pinned QMK/ARM build, flashing or hardware acceptance is claimed.

Verify exact package/active-file identity from repository root with `python3 pcb/experiments/led-startup-recovery/verify_package.py --active-root pcb`. The original lost Git history and full historical QA were not restored.
