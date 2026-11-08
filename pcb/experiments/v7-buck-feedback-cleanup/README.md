# Selected BUCK_FB dead-arm cleanup

Open `candidate/pcb/maru60.kicad_pro`. Exact selected PCB SHA256: aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f. This is bounded working-design adoption, not hardware or manufacturing qualification.

## Intentional edit and verified result

The degree-one BUCK_FB via and 2.85 mm unused arm are removed. The original 4.80 mm track is replaced by its exact 1.95 mm active section; deleting the entire track would have disconnected U18 and was rejected by a negative control. All three active feedback pads and contacts remain connected. All unrelated conductors, footprints, net definitions, stackup and rule settings remain unchanged. The removed via also removes its real drill.

Fresh final native checks and independent binding verify all 245 pad-net partitions, all 12 complete open-component pairs, all 731 plane-contact support areas and 247 rooted GND pads. Warnings fall from 68 to 67, solely by resolving the named dangling via. There are 12 inherited expansion-GPIO opens, zero other hard DRC errors, ERC zero and schematic parity zero. Inventory: 9,752 tracks, 918 vias, 382 footprints, total track length 13,178.75473138763 mm. This board is not DRC-clean.

## Explicit criterion change

The original strict zero-global-plane-loss check remains **FAIL**. Normal refill creates real remote sub-nanometre saved-contour differences. They are neither silently rounded away nor described as nonexistent.

For this exact source2c7-to-aead cleanup only, an explicit engineering decision applies a bilateral 1 nm opposite-material precision bound outside the exact recovered original via-hole polygon. An independent complete rational-cell proof establishes a constructive upper bound of 0.733693793701 nm for every remote gain and loss point. Exact remote loss and gain are approximately 3.36086505284e-7 and 8.06539005284e-7 mm² per inner layer; the intentional local recovered original hole is exactly 0.641253345104 mm² per layer. Earlier native integer-Boolean area estimates remain preserved alongside the refined exact areas.

The alternate criterion additionally requires unchanged remote obstacles/rules, exact zero loss at every old signal-reference shadow and retained contact support, unchanged all-net connectivity, proper copper/hole clearances and deterministic normal refills. These pass. Actual last-noncollision brackets remain at least 0.200499 mm to foreign copper and 0.150499 mm to holes. Source and candidate each refill byte-identically. A rejected exploratory probe incorrectly treated NPTH holes as copper and is preserved with its correction.

This is not a universal epsilon allowance, a future-candidate exemption, a J3 transition exemption, a manufacturing tolerance or evidence of improved electrical performance. The original strict report, separate precision proof and final independent eligibility receipt remain unchanged under `evidence/`. Their historical UNSELECTED captions describe their pre-install stage; this README and ADOPTION.json record the later selection.

## Preserved scope and limitations

No C124 alternative, J3 closure, model port or firmware change is included. Active firmware remains the previously reviewed recovery with LED qualification OFF. No noise, pickup, loop-stability, SI, EMC, hardware or manufacturing benefit is claimed. The prior feedback-width layout-guideline deviation and wider power/PDN uncertainties remain. No fabrication, flashing or push occurred.

The original lost Git history is not reconstructed. This unit preserves exact native input/output projects, scripts and source-bound reviews, not a generic validated harness or relocated one-command full historical replay. Execution paths inside evidence retain their original provenance. The complete 92-warning lifecycle is in `warning-review/`; 25 are resolved and 67 remain without suppression.
