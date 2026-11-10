# Relocated GPIO expansion block and zero-open RP2350A routing

Selected development board SHA256:
`cb7b5b2941bc0e1c4d0a1d10c6dd694f8cf35c4f35665c342dfb747492e10a5d`.
**Zero open pairs remain (`open_pairs: 0`, `warnings: 0`, `other_errors: 0`).**
The checkpoint is a bounded development prototype and is **not manufacturing-ready**.

Relative to the preserved seven-open [header25/U13 checkpoint](../resume-20261109-header25-u13-contact-repair/README.md) (`df21164e`), the 19-footprint GPIO expansion/isolation block (`J3`, `U11`, `U13`, `U12`, `R128`, `C128`, `C129`, `R130..R135`, `R140..R145`) is relocated on `B.Cu` next to `U1` below the spacebar row (`x = 71..97 mm`, `y = 77..92 mm`), except the 10-pin JST SH side-entry connector `J3` and its ESD array `U13`, which sit further west at `(44.25, 75.0) mm` and `(47.1, 79.5) mm` so the plug has a clear 3.5 mm insertion corridor under the board (`y = 68.2..71.7 mm`, no bottom-side courtyard or pin; 3.3 mm free height to the bottom case at full gasket travel); silkscreen-only `LOGO1` moves into the vacated upper area. All other 363 footprints remain electrically identical, and all seven formerly open nets are routed on `F.Cu`/`B.Cu`.

Design rules are unchanged from the source checkpoint (minimum connection width 0.15 mm). Warnings were cleared by fixing their causes, not by suppression: dangling stubs were removed, a `UG_LED_7` junction track was widened, the `SWDIO` corner at (103.8, 79.1) mm was rerouted to widen a 0.146 mm `+3V3` pour neck, the `C125` reference text was raised to 1.0 mm, and the `R122`, `R123`, `C125`, `U8` and `R159` references were moved to legible positions clear of pads and other silkscreen. No reference designator is hidden.

Fresh `qa/native/RESULT.json` (KiCad `9.0.2+dfsg-1`) records **0 opens, 0 warnings, 0 other DRC errors, ERC 0, schematic parity 0 and 58 byte-identical cold-refilled CAD files**. `qa/material-comparison.json` records identical pad inventory, zero source pad-component splits, every formerly open net merged into one component, 17,701 unaffected direct contacts preserved and zero guard failures. `qa/audit-summary.json` records both inner `GND` planes as single islands (`In1.Cu` 23450.8724 -> 23494.2804 mm², `In2.Cu` 23501.3927 -> 23521.9331 mm²). `qa/geos-audit.json` and `qa/geos-rational-witnesses.json` hold the independent GEOS 3.13.1 and exact rational replay of the inner planes.

Reproduce from repository root, using fresh output directories:

```sh
tools/run_kicad9.sh python3 tools/check_pcb_native.py --checkpoint pcb/experiments/resume-20261109-relocated-expansion-zero-opens --expected-opens 0 --output .omo/evidence/relocated0-native-new --material
uv run tools/check_pcb_portable.py --output .omo/evidence/relocated0-portable-new
```

`qa/netlist.xml` is the unchanged source export pinned by the portable wrapper; `qa/native/netlist.xml` is the fresh export checked against this board. Every schematic and firmware file is unchanged (`MARU60_LED_POWER_QUALIFIED=0`). Physical bottom-case clearance for the relocated parts, active power, USB SI/EMI, thermal and hardware qualification remain open.
