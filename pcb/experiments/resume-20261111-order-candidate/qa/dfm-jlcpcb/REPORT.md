# JLCPCB manufacturability check

Board: `pcb/experiments/resume-20261111-order-candidate/pcb/maru60.kicad_pcb`,
SHA256 `abd978a43c723d4d7358becb6a7f15646fdec8d6cd6b16dbe50d1d8da96b35ee`.

**Result: nothing here stops the order.** Every JLCPCB minimum for copper,
holes, vias and the board edge is met. Four kinds of finding remain; three are
silkscreen and one is the USB connector's own land pattern. They are listed
under "What remains".

The limits are the figures on JLCPCB's capability pages as read on 2026-11-11;
each is in [`results.json`](results.json) with the page it came from. Nothing
here is a statement from JLCPCB about this board: their own review runs when
the order is placed.

## How it was checked

1. **KiCad 9.0.2 DRC with JLCPCB's limits as rules**
   ([`maru60-jlcpcb.kicad_dru`](maru60-jlcpcb.kicad_dru), 30 rules). Each rule
   is run alone on a copy of the project by `pcb/tools/run_dfm_jlcpcb_drc.py`;
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
| **Non-plated hole to copper** | 0.20 mm | **4** | 0.194 mm, `J1` (see below) |
| Via hole to via hole | 0.20 mm | 0 | |
| Component hole to any hole | 0.45 mm | 0 | |
| Copper to routed edge, minimum / recommended | 0.20 / 0.30 mm | 0 | 0.5 mm |
| **Silkscreen text height** | 1.0 mm | **10** | 0.8 mm |
| Silkscreen text stroke | 0.15 mm | 0 | 0.15 mm |
| **Silkscreen to pad** | 0.15 mm | **199** | see below |
| Recommended plated component hole | 0.5 mm | 9 (not a defect) | 0.25 mm: the nine thermal vias under `U1` are drawn as pads; JLCPCB's via minimum applies to them |

## Geometry checks

| Check | Limit | Result |
| --- | --- | --- |
| Solder-mask web between pads of fine-pitch parts | 0.10 mm | pass; smallest 0.17 mm (`U1`, 0.4 mm pitch) |
| Stencil area ratio, 0.10 mm foil | 0.66 | pass; lowest 0.74 (`U13`, 0.2 × 0.5 mm) |
| Stencil area ratio, 0.12 mm foil | 0.66 | `U13` 0.61, below the guideline; all others pass |
| Open vias inside SMD pads | none wanted | 14 remain, listed below |
| Assembled parts within 2.5 mm of the board edge | rails needed | 23 parts, `J1` at the edge |
| Fiducials, 1.152 mm tooling holes | needed for assembly | none on the board |

- **Stencil:** JLCPCB chooses the foil. With a 0.12 mm foil `U13`'s fourteen
  0.2 × 0.5 mm apertures are at 0.61. It is an ESD array with pads on 0.5 mm
  pitch; look at its joints on the first boards.
- **Rails and fiducials:** choose "edge rails added by JLCPCB" in the order;
  they add the fiducials and tooling holes on the rails. This is in
  [`pcb/order/README.md`](../../../../order/README.md).

## Fixed in this pass

Found by the same checks on the board before this pass and now clear:

| Finding | Was | Now | How |
| --- | --- | --- | --- |
| Tracks beside non-plated holes (switch pin and post holes), 15 hole/net pairs | 0.150–0.199 mm | ≥ 0.2008 mm | `plan_npth_clearance.py`: the track follows the hole on a tangent polygon; 41 segments replaced by 157. `USB_OVLO` was moved outward to make room for `USB_UVLO`. No track changed width. |
| GND planes on In1/In2 round every non-plated hole | 0.15 mm | 0.25 mm | rule `npth_to_zone_0.25` in the board's rule file, zones refilled |
| `LED30` and `LED75` window pads beside the Caps Lock pin holes | 0.179 mm | ≥ 0.20 mm | the two pads next to the hole are 0.52 mm wide instead of 0.55 mm, trimmed on the hole side |
| `+4V_REG` via beside the `SW59` post hole (hole to hole) | 0.429 mm | ≥ 0.45 mm | via moved 0.095 mm |
| Ten reference texts with 0.10 mm stroke | 0.10 mm | 0.15 mm | stroke only; `R159`'s text moved 0.2 mm off a mask opening |

Operation lists: [`../npth-clearance-ops.json`](../npth-clearance-ops.json),
[`../silk-text-ops.json`](../silk-text-ops.json).

## What remains

1. **`J1`, four GND pads 0.194 mm from the connector's own locating-peg holes**
   (limit 0.20 mm). This is the manufacturer's land pattern for the GCT
   USB4105 as shipped in KiCad's library; the pads are GND and the peg is
   plastic. Changing it would move the connector's shell pads off the data
   sheet. Left as it is; the board rule exempts `J1` against itself and
   nothing else.
2. **Ten reference texts are 0.8 mm high** (JLCPCB asks for 1.0 mm): `C136`,
   `C137`, `R121`, `R122`, `R123`, `R126`, `R134`, `R159`, `U13`, `U8`. At
   1.0 mm they overlap pads or each other. They may print less sharply.
   Assembly uses the placement file, not these labels.
3. **Silkscreen closer than 0.15 mm to a pad, 199 places.** 197 are the two
   short outline dashes of KiCad's stock 0402 capacitor footprint, 0.10 mm from
   its own pads; two are the `TP5` circle. Fabricators remove silkscreen that
   falls on a mask opening, so the expected effect is a shortened dash. No
   effect on soldering.
4. **14 open vias inside SMD pads**, where no free position exists: the GND
   pads of `R140`–`R143`, `R145`, `R159`, `Y1` (two), `U12`, `U6`, `U7`, `C122`
   and the DIN pads of `LED70` and `LED71`. Solder can wick into the via and
   leave a lean joint. Inspect these on the first boards, or order filled and
   capped vias if JLCPCB offers it for this stack-up.

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
