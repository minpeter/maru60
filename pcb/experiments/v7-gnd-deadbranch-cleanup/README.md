# Selected two-track GND dead-branch cleanup

Open `candidate/pcb/maru60.kicad_pro`. Selected PCB SHA256:c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a. This is bounded working-design adoption, not physical/hardware qualification.

Exactly two dead-end F.Cu GND tracks,68f95f8e and577f36c1, totaling1.938477631 mm, are removed. Existing via277a8b55 remains with its intact barrel and two unchanged inner GND contacts. No drill, component, schematic, BOM, rule, firmware or unrelated conductor changes.

All12 saved zone records and all1,269 physical drills are byte/shape-identical to predecessor aead. Current source-to-candidate strict plane preservation passes outright, without an epsilon or endpoint exception. This does not rewrite the historical2c7-to-aead BUCK transition or its candidate-specific1 nm condition; that record remains unchanged.

Fresh corrected R2 plus independent review preserve14,685 retained material nodes/382components, all245pad-net partitions,247original ground-return paths,934barrel proofs and every retained material/zone contact witness. Existing51guard-failing contacts stay explicit and excluded. Normal independent cold refill reproduces the candidate byte-for-byte. All53 non-PCB project companions are exact to the predecessor.

Current inventory:9,750 tracks,918vias,382footprints,13,176.816253756544 mm summed track length. Native DRC has66warnings and12unchanged expansion opens, zero other hard errors, ERC0 and parity0. Only the named0.10 mm dangling-track warning is resolved, with no new warning. The complete92-warning history records26resolved/66open, without suppression.

Frozen verification under `evidence/` describes the pre-adoption stage. This README and ADOPTION.json record subsequent selection after durable preservation. No high-frequency ground, noise, PDN, SI, EMC, thermal, active stability, assembly or hardware benefit is inferred from removing this nominal leaf. The F.Cu ground foil is intentionally reduced, while saved inner reference material and retained nominal returns stay exact. The board still has12opens and66warnings and is not fabrication-ready.

C128 stub removal, +4V unused-branch removal and J3/C124 alternatives remain unselected; their independent failures are not waived. Firmware remains unchanged with LED qualificationOFF. No full ARM/QMK build, flashing, manufacture or push is claimed. Original lost Git and full historical QA remain missing; this unit is a source-bound frozen experiment, not a universal replay harness.
