# Mechanical-fit fixes — relocated expansion checkpoint

Board: `pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb`
(SHA256 `cb7b5b29…e10a5d`). Baseline: `fit-before.json`. After: `fit.json`.
All numbers are CAD, not physical measurements.

## Summary

| Item | Before | After | Delta | New artifact |
| --- | ---: | ---: | ---: | --- |
| 7U stabilizer insert clearance | -1.71 mm (fail) | 0.40 mm (pass) | +2.11 mm | `models/rule60-v3-hhkb-gas-plate-pcb-mount.dxf` |
| USB-C 12.35 mm plug side clearance | -0.67 mm (stock 12.8) | 1.20 mm (J1-centred 14.75) | +1.87 mm | `models/maru60-hhkb-topcase-right-usb-14p75-j1centred.3mf` |
| J3 clearance | 0.33 mm (tight) | 0.85 mm (pass) | +0.52 mm | `models/maru60-hhkb-bottomcase-j3-relief-{left,right}.3mf` |
| Overall minimum | -1.71 mm | 0.40 mm | — | — |

## 1. 7U PCB-mount plate variant

The PCB footprint `Maru60_Candidates:MX-Hotswap-7U-4L-NPTH-StabRot180` is
**PCB-mount** (four NPTH holes at plate `[85.8, 8.684]`, `[85.8, 23.924]`,
`[200.1, 8.684]`, `[200.1, 23.924]`). The original plate
`models/rule60-v3-hhkb-gas-plate.dxf` is **plate-mount**; its 7U cutout
`7D` bbox `[81.5551, 8.669, 204.5051, 23.6395]` does not clear the NPTH
holes (insert -1.71 mm, screw -0.07 mm).

Fix: `pcb/tools/build_plate_pcb_mount.py` generates a new variant
`models/rule60-v3-hhkb-gas-plate-pcb-mount.dxf` (and the matching FR4 Gerber
zip) with the 7U cutout enlarged to clear all four NPTH holes with a
0.30 mm minimum margin. The 62 switch cutouts, the 2.25u stabilizer
cutouts, the outline and the 1.0 mm router-bit reachability are preserved.
The original plate is unchanged and remains valid for plate-mount
stabilizers.

Result: worst insert clearance **0.40 mm** (threshold 0.30 mm), screw
**0.40 mm**. The 3.0 mm switch hole at `[145.49, 20.749]` is 0.42 mm to the
14 × 14 mm switch cutout (pass).

## 2. USB-C J1-centred 14.75 mm notch

J1 is at board `(18, 3.8)` -> plate X `18.4525`. The stock 12.8 mm notch is
centred at plate X `19.35`, so a 12.35 mm plug overhangs it by 0.67 mm on the
left. The default printed 14.75 mm notch is centred at `18.65` and passes
with 1.00 mm.

Fix: `pcb/tools/build_topcase_usb14p75.py` generates
`models/maru60-hhkb-topcase-right-usb-14p75-j1centred.3mf` with the 14.75 mm
notch centred on J1 (`18.4525`), giving **1.20 mm** minimum side clearance.
The left half is unchanged. The stock-compatible top case still needs a
narrower plug or this variant.

## 3. J3 local relief

J3 is a JST SH `SM10B-SRSS-TB` (2.95 mm body) at board `(44.25, 75.0)`. The
stock cavity floor is Z `18.20`, giving 0.33 mm at full gasket travel.

Fix: `pcb/tools/build_bottomcase_j3_relief.py` adds a local 0.5 mm deep
pocket (0.5 mm margin, R0.5) under J3, raising the floor to Z `18.70` and the
clearance to **0.85 mm**. The remaining floor slab is 1.31 mm. The pocket is
local to J3; the rest of the cavity is unchanged. Both left and right halves
are regenerated.

## What remains physical-only

- Actual J3/U13/U11/U12/0603 body heights (datasheet/package nominals used).
- USB-C plug overmold height/width and insertion test.
- 7U stabilizer type (PCB-mount vs plate-mount) and housing dimensions.
- Printed floor Z/flatness, gasket compression, solder/paste thickness.
- Test-fit the PCB-mount plate variant and the J3 relief bottom case.

## Reproduction

```sh
.venv/bin/python pcb/tools/build_plate_pcb_mount.py
.venv/bin/python pcb/tools/build_topcase_usb14p75.py
.venv/bin/python pcb/tools/build_bottomcase_j3_relief.py
.venv/bin/python pcb/tools/check_mechanical_fit.py
```
