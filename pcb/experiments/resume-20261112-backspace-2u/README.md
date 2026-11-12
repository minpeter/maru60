# Backspace 2U / split prototype candidate — 2026-11-12

**Status: CAD-validated alternative; mechanical parts fit still unqualified.**
This is a separate candidate, not a replacement for `pcb/order`. Do not order
this variant until the receptacle and stabilizer fit gates below are resolved.
The complete [KiCad project](pcb/maru60.kicad_pro), [board](pcb/maru60.kicad_pcb),
and [fabrication/assembly package](order/README.md) are preserved here.
Board SHA256: `c371018deed3ed99cf36f0ce974fb4153ebf05a1c8f8d35df3d4e4224f936129`.

## Design changes

- SW14/SW15 support a central 2U Backspace **or** two 1U switches. Six solder-in
  receptacle lands replace the two Kailh sockets: four lands belong to SW14,
  two to SW15. Center and left switch use ROW0/COL13; right uses ROW0/COL14.
- Split switches rotate 90 degrees in opposite directions. The center 2U
  switch uses the conventional orientation. Never populate center and split
  switches together. The center is at board XY (266.3225, 9.19875) mm.
- LED14 and LED15 each have two alternative sites. R189–R191 (100 Ω, 0402)
  damp the three affected key-LED links. C213/C214 and local matrix, LED,
  power and ground routes move to clear the new holes. D14 uses a cathode dot.
- U1.61's nine 0.25 mm holes are thermal barrels, not component insertion
  holes. The DFM deck now checks them separately: nine GND barrels inside the
  exposed pad, all copper layers, 0.20–0.30 mm drills and minimum annulus.
  Existing 0.60 mm lands give 0.175 mm annuli; no hole enlargement is needed.
- The [dedicated 2U HHKB plate](../../../models/maru60-hhkb-plate-7u-plate-mount-2u-backspace.dxf)
  preserves the original plate-mount 7U cutout and adds center-switch retention
  edges and PCB-mount **2U Backspace** stabilizer relief. It is
  **not** a universal split/2U plate. Use the split plate with split switches.

## Saved checks

| Check | Result and boundary |
| --- | --- |
| KiCad 9.0.2 native checks | DRC/open pairs/warnings, ERC and schematic parity: 0. Cold refill preserved CAD bytes. Material connectivity graph regenerated. |
| JLCPCB DFM | All 32 rule checks: 0 violations; no via drill holes in SMD lands. |
| Changed LED links | All 54 cases passed pulse-width, threshold recrossing and noise-margin checks. Four hops, all population pairs, six assumed driver corners at 4 V. |
| Case clearance | Three resistors and ten hardware envelopes pass. Swept hardware volumes include full 0.8 mm gasket travel and 0.5 mm side/bottom margin. A missed ray through an opening is checked by solid intersection, not ignored. |
| Gerber readback | All 24 checks pass using gerbonara, including drill sizes/locations and SMD copper/mask/paste. |
| LED rail resistance model | At 60 °C: 26.77 mV maximum drop for uniform 234 mA loading; 32.62 mV for the tested concentrated loading. This is a DC copper model, not regulator/thermal qualification. |
| Package | 410 footprints; 334 automated placements (136 top, 198 bottom), 54 LCSC parts. 333 placements fitted to supplier footprints; R123 retains the baseline nonpolarised convention. |

Reports are in [qa](qa). `MANIFEST.json` binds the delivered CAD, reports,
package, tools and plate files. Reports with historical `build/` paths refer
to the identical board hash above. Compressed geometry and material graph
retain the actual analysis inputs/outputs. `design-operations` records selected
edits for review; it is not a complete sequential replay recipe.

[Geometry delta](qa/geometry-delta.json) identifies every changed track/via/pad
net. USB, crystal and flash signal geometry is unchanged. The original full-board
SI report remains evidence for the **original** board, not a new global SI pass:
ground/LED-plane geometry changed and return-current/EMI effects were not
requalified. The dielectric sweep stored with the original candidate is a
sensitivity study, not guaranteed supplier corners or an increase in USB speed.

## Fit gates before fabrication

**Selected spacebar hardware:** [Designer Studio Stabilizer (For Plate)](https://geonworks.kr/article/assemble-guild/5/2140/), **7U** wire
(user selection). The selected plate now restores the original INKC plate-mount
7U cutout, including its exact arc vertices, and removes the additional
PCB-mount clearance holes from this variant. PCB NPTH stabilizer holes remain
unused; they do not need to pass through the plate. The prior
`maru60-hhkb-plate-pcb-mount-2u-backspace` files are an **unselected PCB-mount
alternative**, not the selected product's plate.

The supplied GEONWORKS guide confirms the product and plate-mount assembly
method, but contains no dimensioned mechanical drawing. Its component image
confirms the 6.25U/7U wire selection. [Source evidence](qa/designer-studio/source.json)
records the checked instructions and images. Original-cutout preservation is
verified, but product-specific clip retention, wire/housing
clearance to PCB components, case fit and supported plate thickness are **not**.
Use the nominal case-stack plate thickness of 1.5 mm only after confirming the
product's clip range; a 1.6 mm FR4 option is not automatically equivalent.
Do not fabricate the selected variant until these checks are resolved. This
7U selection does not specify the separate 2U Backspace stabilizer.

1. Select an exact Mill-Max 3305 receptacle variant and verify its manufacturer
   drawing against the **1.70 mm finished holes / 2.50 mm lands**. Test a coupon
   with the actual switch pins, soldering process, seating height and retention.
   These dimensions are inherited study geometry, not a verified 3305 land pattern.
2. Fit the chosen PCB-mount 2U stabilizer, screws/washers, switch and keycap to
   the board/plate. The model assumes hardware protrudes at most 2 mm below
   the PCB; the plate assumes a 7.75 × 14 mm upper housing with 0.25 mm allowance.
   Actual parts and machining tolerances must meet these envelopes. The plate
   has only 1.1378 mm minimum outer-edge margin near this opening.
3. Check both switch/LED population configurations. Fit exactly one LED per
   reference and ensure no switch body obstructs it. Inspect solder clearance
   and full 0.8 mm gasket travel. No physical test has been performed.

## Reproduce

Run from repository root; use the existing project Python environment, KiCad
wrapper and ngspice image described in `pcb/tools/signal_integrity/README.md`.
Use a fresh native-output directory. These commands do not promote the candidate.

```sh
tools/run_kicad9.sh python3 tools/check_pcb_native.py --checkpoint pcb/experiments/resume-20261112-backspace-2u --expected-opens 0 --output build/backspace-native --material
tools/run_kicad9.sh python3 pcb/tools/dump_board_geometry.py pcb/experiments/resume-20261112-backspace-2u/pcb/maru60.kicad_pcb build/backspace-geometry.json
.venv/bin/python pcb/tools/check_backspace_fit.py pcb/experiments/resume-20261112-backspace-2u/pcb/maru60.kicad_pcb build/backspace-fit.json
.venv/bin/python pcb/tools/run_dfm_jlcpcb_drc.py pcb/experiments/resume-20261112-backspace-2u/pcb pcb/experiments/resume-20261112-backspace-2u/qa/jlcpcb.kicad_dru build/backspace-dfm.json
.venv/bin/python pcb/tools/check_dfm_jlcpcb.py build/backspace-geometry.json build/backspace-dfm-geometry.json
.venv/bin/python pcb/tools/signal_integrity/check_backspace_leds.py build/backspace-geometry.json pcb/experiments/resume-20261112-backspace-2u/pcb/maru60.kicad_pcb build/backspace-led/results.json --lines pcb/experiments/resume-20261112-backspace-2u/qa/lines.json
.venv/bin/python pcb/tools/analyze_pdn.py build/backspace-geometry.json build/backspace-pdn
```

## Plate-mount 7U update

Generate the selected plate with `.venv/bin/python pcb/tools/build_plate_backspace_2u.py`.
Use `--seven-u-mount pcb` only for the unselected PCB-mount alternative.
The new [DXF](../../../models/maru60-hhkb-plate-7u-plate-mount-2u-backspace.dxf),
[Gerbers](../../../models/maru60-hhkb-plate-7u-plate-mount-2u-backspace-gerbers.zip)
and [report](../../../models/maru60-hhkb-plate-7u-plate-mount-2u-backspace.json)
are separately named to avoid confusing mount types. The report deliberately
keeps `product_fit_verified: false` until supplier dimensions or an actual
fit check establish retention and clearance. Assemble as the guide specifies:
insert the wire below the plate at an angle first, then press the housing into
place; inspect the housing-to-PCB gap and free wire travel. No PCB screw or
insert should be fitted to the unused 7U stabilizer holes.

Three regression tests confirm that only the split Backspace openings change,
that PCB-mount 7U relief is absent from the selected variant, and that the
exported DXF retains the original 7U arc vertices. PCB copper, the 2U Backspace
opening, outer case outline and previous electrical checks are unchanged.
