C136 REFERENCE-LABEL DEVELOPMENT CHECKPOINT

Selected PCB SHA256: 2e532c1a16e64a34eafafdfbd5b85c05d70bb12ad9e52924c5cbe024fdc9aa2c

Native KiCad9.0.2: 9 open connection pairs,40 warnings,0 other errors,ERC0 and schematic parity0. Relative to ef45f84, only the C136 Reference property changes. Its 0.80mm visible mirrored bottom silkscreen now clears the mask and minimum text-height checks. No warning is hidden, excluded or globally relaxed. The preview includes fabrication, courtyard and mask layers for context, and is not a photo of assembled hardware.

Complete byte reversal of the Reference form restores the previous PCB exactly. All57 companion files match. The full material graph was also freshly recomputed from this exact PCB and independently compared: every pad partition, direct/zone contact and all9 full physical open-component pairs are preserved. All58 CAD files remain byte-identical after a cold load, connectivity rebuild, zone refill and save.

Only the label improvement is selected here. Separate copper experiments and their failures are never part of this board. Strict baseline bbf61e6 and earlier qualified prototypes remain preserved. The inherited exact no-loss failure and51 conservative guarded-contact proof failures remain explicit. This is NOT promotion to strict geometric acceptance or a manufacturing release.

The new resistor-tolerance supplement includes16 exact-rational corner calculations using the current 0.1% resistor values and the saved model's fixed comparator thresholds. It cannot supply real U8 operating limits, active stability, transient or hardware qualification. Earlier passive capacitor sensitivities and their limitations remain in the ef45f84 checkpoint. No component value was changed.

Open pcb/maru60.kicad_pro. Run VERIFY_LABEL.py for the exact single-property reversal check and VERIFY.py --material with the installed KiCad9.0.2 Python runtime for fresh native, ERC, pin, cold-refill and full material checks. Original construction/geometry scripts and historical reports retain their source-bound paths; the two top-level verification commands are the portable entry points.

Read DECISION.json and WARNING_REGISTER.json. No SI/EMI, active-power, full ARM/QMK build or physical qualification is claimed. LED qualification remains OFF. No remote push, order or flashing occurred.
