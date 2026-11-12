# Backspace 2U / split candidate fabrication package

**Hold for the [mechanical fit gates](../README.md#fit-gates-before-fabrication).**
This package is generated and CAD-checked, but the receptacle variant and
stabilizer fit are not qualified. `PROVENANCE.json`'s `ORDER_CANDIDATE` means
export checks passed, not release approval or a physical fit guarantee.
Do not mix these files with `pcb/order`.

- `maru60-gerbers.zip`: four-layer PCB, 285 × 94.6 mm, 1.6 mm thick.
- `bom-jlcpcb.csv` and `cpl-jlcpcb.csv`: 334 placements, 54 part numbers.
- `bom-full.csv`: all 410 footprints and exclusions.
- `parts.json`: selection rules; stock is the 2026-11-11 snapshot, not live stock.
- `PROVENANCE.json`: board identity, export checks, file hashes and assembly caveats.

Use the original package's [fabrication options and assembly review](../../../order/README.md)
for unchanged circuitry: JLC04161H-7628, ENIG, 1 oz outer / 0.5 oz inner copper,
0.25/0.50 mm tented vias, RP2350 A4 stepping. Check the supplier assembly preview
for all polarised parts and the recorded land-pattern differences. The original
package's **Backspace population, socket counts and BOM/CPL do not apply here**.

## Backspace assembly

SW14/SW15 take six solder-in receptacles total, not Kailh sockets. SW14 represents
four receptacles (center and left); SW15 represents two (right). The exact
Mill-Max 3305 variant and 1.70 mm finished-hole fit remain to be confirmed.
Other populated switch positions retain their existing Kailh sockets.

LED14 and LED15 are deliberately omitted from the automated BOM/CPL. Hand-fit
two SK6805 LEDs total, choosing the following **board-coordinate** sites:

| Population | LED14 center XY (mm) | LED15 center XY (mm) |
| --- | --- | --- |
| Two split 1U switches | 251.7175, 9.19875 | 280.9275, 9.19875 |
| One central 2U switch | 266.3225, 4.11875 | 269.0000, 19.8000 (relay) |

Match the pin-1 dots; leave the alternate site of each reference empty.
Both LEDs are required to preserve the daisy chain. Do not populate all four
sites: duplicated outputs would drive one another. Use the selected [7U plate-mount / 2U Backspace plate](../../../../models/maru60-hhkb-plate-7u-plate-mount-2u-backspace.dxf)
for center population and the original plate-mount split plate for split population.
The Design Studio 7U product's exact clip dimensions and supported plate
thickness still need verification; restored stock geometry is not product
qualification. The former `plate-pcb-mount-2u-backspace` plate is unselected. Never fit the
center and split switches simultaneously.

The center switch is electrically SW14, matrix row 0 / column 13 (zero based).
Existing WKL firmware already maps it to Backspace. With `via_hhkb`, use VIA to
map row 0 / column 13 to Backspace and row 1 / column 13 to backslash; row 0 /
column 14 is unused in 2U population. Inspect Fn-layer assignments as desired.
The VIA drawing and firmware LED positions still describe split Backspace;
no new firmware build or physical firmware qualification is claimed.

## Regenerate after an approved CAD change

First dump fresh geometry as described in the candidate README. Then:

```sh
.venv/bin/python pcb/tools/fit_jlcpcb_placement.py build/backspace-geometry.json pcb/experiments/resume-20261112-backspace-2u/order/parts.json pcb/experiments/resume-20261112-backspace-2u/order/jlcpcb-placement.json
.venv/bin/python pcb/tools/export_order_package.py --checkpoint pcb/experiments/resume-20261112-backspace-2u --out pcb/experiments/resume-20261112-backspace-2u/order --parts pcb/experiments/resume-20261112-backspace-2u/order/parts.json
build/gerber-venv/bin/python pcb/tools/verify_gerbers.py build/backspace-geometry.json pcb/experiments/resume-20261112-backspace-2u/order/gerbers build/backspace-gerbers.json
```

Rerun the affected checks and update the candidate manifest after any edit.
