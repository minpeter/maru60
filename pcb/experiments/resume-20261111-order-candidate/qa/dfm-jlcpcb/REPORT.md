# JLCPCB manufacturability check

Board: `pcb/experiments/resume-20261111-order-candidate/pcb/maru60.kicad_pcb`,
SHA256 `36700843ef6c11179ef8453efac2747133c23870c03e9ecf52e248d44c42779e`.

**Result: nothing here stops the order.** Every JLCPCB minimum is met. Two
silkscreen marks sit closer than 0.15 mm to a pad or hole and six vias remain
inside SMD pads; both are listed under "What remains".

The limits are the figures on JLCPCB's capability pages as read on 2026-11-11;
each is in [`results.json`](results.json) with the page it came from. Nothing
here is a statement from JLCPCB about this board: their own review runs when
the order is placed.

## How it was checked

1. **KiCad 9.0.2 DRC with JLCPCB's limits as rules**
   ([`maru60-jlcpcb.kicad_dru`](maru60-jlcpcb.kicad_dru), 30 rules). Each rule
   is run alone on a copy of the project by `pcb/tools/run_dfm_jlcpcb_drc.py`,
   with KiCad's cap of 199 reported findings per type switched off;
   per-rule results with every finding are in
   [`drc-per-rule.json`](drc-per-rule.json).
2. **Geometry checks that DRC rules cannot express**
   (`pcb/tools/check_dfm_jlcpcb.py`): vias in SMD pads, solder-mask web, stencil
   area ratio, distance of parts to the board edge, fiducials and tooling
   holes. Results in [`results.json`](results.json).
3. **The board's own rule file** (`pcb/maru60.kicad_dru`) now holds the
   non-plated-hole clearance, so the normal KiCad DRC keeps it from regressing.

## DRC against JLCPCB's limits

| Limit | JLCPCB | Findings | Closest on the board |
| --- | --- | --- | --- |
| Track width | 0.09 mm | 0 | 0.15 mm |
| Copper to copper | 0.09 mm | 0 | 0.15 mm |
| Pad to track | 0.10 mm | 0 | 0.15 mm |
| SMD pad to pad, different nets | 0.15 mm | 0 | |
| Copper neck | 0.09 mm | 0 | |
| Via diameter / drill | 0.25 / 0.15 mm | 0 | 0.5 / 0.25 mm |
| Via diameter with no surcharge | 0.45 mm | 0 | 0.5 mm |
| Via annular ring, minimum / preferred | 0.05 / 0.075 mm | 0 | 0.125 mm |
| Plated-hole annular ring, minimum / recommended | 0.15 / 0.20 mm | 0 | 0.20 mm (`J1` shell slots); the `U1` thermal vias have 0.175 mm |
| Non-plated hole size, slot width | 0.5 mm, 1.0 mm | 0 | |
| Plated slot width, minimum / recommended | 0.35 / 0.5 mm | 0 | |
| Via hole to other copper | 0.20 mm | 0 | |
| Plated hole to other copper, outer / inner / recommended | 0.28 / 0.30 / 0.35 mm | 0 | |
| Non-plated hole to copper | 0.20 mm | 0 | 0.2008 mm |
| Via hole to via hole | 0.20 mm | 0 | |
| Component hole to any hole | 0.45 mm | 0 | |
| Copper to routed edge, minimum / recommended | 0.20 / 0.30 mm | 0 | 0.5 mm |
| Silkscreen text height | 1.0 mm | 0 | 1.0 mm |
| Silkscreen text stroke | 0.15 mm | 0 | 0.15 mm |
| **Silkscreen to pad** | 0.15 mm | **2** | 0.088 mm, see below |
| Recommended plated component hole | 0.5 mm | 9 (not a defect) | 0.25 mm: the nine thermal vias under `U1` are drawn as pads; JLCPCB's via minimum applies to them |

## Geometry checks

| Check | Limit | Result |
| --- | --- | --- |
| Solder-mask web between pads of fine-pitch parts | 0.10 mm | pass; smallest 0.17 mm (`U1`, 0.4 mm pitch) |
| Stencil area ratio, 0.10 mm foil | 0.66 | pass; lowest 0.74 (`U13`, 0.2 × 0.5 mm) |
| Stencil area ratio, 0.12 mm foil | 0.66 | `U13` 0.61, below the guideline; all others pass |
| Open vias inside SMD pads | none wanted | 6 remain, listed below |
| Assembled parts within 2.5 mm of the board edge | rails needed | 23 parts, `J1` at the edge |
| Fiducials, 1.152 mm tooling holes | needed for assembly | none on the board |

- **Stencil:** JLCPCB chooses the foil. With a 0.12 mm foil `U13`'s fourteen
  0.2 × 0.5 mm apertures are at 0.61. It is an ESD array with pads on 0.5 mm
  pitch; look at its joints on the first boards.
- **Rails and fiducials:** choose "edge rails added by JLCPCB" in the order;
  they add the fiducials and tooling holes on the rails. This is in
  [`pcb/order/README.md`](../../../../order/README.md).

## Fixed by these checks

Found on earlier revisions of this board and now clear:

| Finding | Was | Now | How |
| --- | --- | --- | --- |
| Tracks beside non-plated holes (switch pin and post holes), 15 hole/net pairs | 0.150–0.199 mm | ≥ 0.2008 mm | `plan_npth_clearance.py`: the track follows the hole on a tangent polygon; 41 segments replaced by 157. `USB_OVLO` was moved outward to make room for `USB_UVLO`. No track changed width. |
| GND planes on In1/In2 round every non-plated hole | 0.15 mm | 0.25 mm | rule `npth_to_zone_0.25` in the board's rule file, zones refilled |
| `LED30` and `LED75` window pads beside the Caps Lock pin holes | 0.179 mm | ≥ 0.20 mm | the two pads next to the hole are 0.52 mm wide instead of 0.55 mm, trimmed on the hole side |
| `J1` GND lands beside the connector's locating-peg holes | 0.194 mm | 0.21 mm | the two GND lands are 1.13 mm long instead of 1.15 mm, shortened at the peg end; the footprint is now `Maru60:USB_C_Receptacle_GCT_USB4105-…` |
| `+4V_REG` via beside the `SW59` post hole (hole to hole) | 0.429 mm | ≥ 0.45 mm | via moved 0.095 mm |
| Ten reference texts 0.8 mm high with 0.10 mm stroke | 0.8 / 0.10 mm | 1.0 / 0.15 mm | enlarged and moved to free positions |
| Outline dashes of the stock 0402 capacitor and resistor footprints, test-point circles | 0.10–0.14 mm from their own pads (277 places) | removed | the footprints are now `Maru60:C_0402_1005Metric`, `Maru60:R_0402_1005Metric`, `Maru60:TestPoint_Pad_D1.0mm`; pads and courtyards are unchanged |
| Reference texts 0.06–0.149 mm from a pad, 13 texts | < 0.15 mm | ≥ 0.15 mm | moved |
| Open vias inside SMD pads | 14 | 6 | `plan_via_relocate.py`: eight vias taken out of the pad and rerouted |

The first report of this board counted 199 silkscreen findings. That figure was
KiCad's reporting cap, not the total; the resistor dashes and the texts were
found once the cap was switched off.

Operation lists: [`../npth-clearance-ops.json`](../npth-clearance-ops.json),
[`../silk-text-ops.json`](../silk-text-ops.json),
[`../silk-clearance-ops.json`](../silk-clearance-ops.json),
[`../via-relocate-ops.json`](../via-relocate-ops.json).

## What remains

1. **Two silkscreen marks closer than 0.15 mm to a pad or hole.** The pin-1 dot
   of `LED30`'s window site is 0.088 mm from a Caps Lock switch pin hole, and
   the pin-1 triangle of `U11` is 0.115 mm from a pad of `R130`. Neither
   overlaps a mask opening. Both are orientation marks and were kept.
2. **Six open vias inside SMD pads**: the GND pads of `R140`, `R143`, `Y1.2`
   and `U12`, the DIN pad of `LED71`, and the feedback pad of `R159`. For the
   first five no free via position with a route exists within 6.5 mm (and
   removing the GND ones disconnects the pad). `R159`'s via is left on purpose:
   it is the buck's feedback node, and moving it out adds 2.4 mm of track to a
   high-impedance net beside the switch node. Solder can wick into the via and
   leave a lean joint: inspect these six on the first boards, or order filled
   and capped vias if JLCPCB offers it for this stack-up.

## Reproduce

```sh
.venv/bin/python pcb/tools/run_dfm_jlcpcb_drc.py \
  pcb/experiments/resume-20261111-order-candidate/pcb \
  pcb/experiments/resume-20261111-order-candidate/qa/dfm-jlcpcb/maru60-jlcpcb.kicad_dru \
  build/drc-per-rule.json
tools/run_kicad9.sh python3 pcb/tools/dump_board_geometry.py \
  pcb/experiments/resume-20261111-order-candidate/pcb/maru60.kicad_pcb build/board.json
.venv/bin/python pcb/tools/check_dfm_jlcpcb.py build/board.json build/dfm-results.json
```
