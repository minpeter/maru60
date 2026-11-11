# Order candidate (2026-11-11)

Derived from [`resume-20261109-relocated-expansion-zero-opens`](../resume-20261109-relocated-expansion-zero-opens/README.md)
(PCB `cb7b5b29`). This checkpoint fixes what stood between that board and an
order, and records the analyses run on the result. PCB SHA256:
`36700843ef6c11179ef8453efac2747133c23870c03e9ecf52e248d44c42779e`. The order
files exported from it are in [`pcb/order`](../../order/README.md).

**It is an order candidate for a first prototype, not a qualified design.**
Everything below is CAD checking, data-sheet reading, calculation and
simulation. Nothing has been measured on hardware.

## Checks on this board

| Check | Result | Evidence |
| --- | --- | --- |
| KiCad 9.0.2 DRC: opens / warnings / other errors | 0 / 0 / 0 | [`qa/native/RESULT.json`](qa/native/RESULT.json) |
| ERC, schematic parity, net identity, cold refill | 0, 0, pass, 72 files identical | same |
| Material (copper connectivity) graph | recomputed, pass | same |
| Netlist against the 0/0 prototype | only the intended differences: U2's pins, C142 and R163 removed, R115–R119 and C143 added, five LED DOUT pins on their own `_SRC` nets, values and footprint names | `qa/netlist.xml` |
| Firmware GPIO and matrix bindings on this netlist | 24 bindings match, negative controls rejected | [`qa/firmware-static/static.json`](qa/firmware-static/static.json) |
| Top-side parts under a switch housing (default build) | none | `pcb/tools/plan_topside_relocation.py` keep-out |
| Bottom-case fit, including the new bottom-side parts (`U2`, `C200`, `R115`–`R117`, `R119`, `C143`, `LED75`) | 27 pass, USB-C pass, 7U stabilizer pass | [`qa/mechanical-fit/REPORT.md`](qa/mechanical-fit/REPORT.md) |
| Pin tables and land patterns against manufacturer data sheets | all pin tables match | [`qa/datasheet-review/`](qa/datasheet-review/) |
| DRC with JLCPCB's limits as rules, 30 rules | every minimum met; two orientation marks are within 0.15 mm of a pad or hole | [`qa/dfm-jlcpcb/REPORT.md`](qa/dfm-jlcpcb/REPORT.md) |
| Power tree, ngspice | one change (C143) | [`qa/power-sim/REPORT.md`](qa/power-sim/REPORT.md) |
| Power-net copper: drop, current, heating | no change needed | [`qa/pdn/REPORT.md`](qa/pdn/REPORT.md) |
| Signal integrity | R115–R119, and the matrix read delay in the firmware | [`qa/signal-integrity/REPORT.md`](qa/signal-integrity/REPORT.md) |
| Firmware built with the matrix read delay, both layouts | exit 0; delay 120 cycles and LED qualification 0 in the macro dumps; 120 `nop` in the linked delay routine | [`qa/qmk-build/RESULT.json`](qa/qmk-build/RESULT.json) |
| Gerber and drill files read back with a second parser | 962 plated and 334 non-plated holes and every SMD pad match | [`qa/gerber-verify/result.json`](qa/gerber-verify/result.json) |

## Changes from the 0/0 prototype

### 1. Top-side parts moved out from under the switches

MX housings sit flush on the PCB and only the LED fits the housing's LED
opening. The prototype had each LED's 0402 bypass capacitor 4.0 mm beside the
LED, under the housing, and `R100` under the edge of the Esc switch.
`plan_topside_relocation.py` moved 64 parts into the gaps between housings
(courtyard at least 0.35 mm outside every 14 × 14 mm housing outline and every
stabilizer zone) and reconnected them on F.Cu, with a GND via into the planes
where no top-side ground was within 3 mm. `C200` (LED1, beside the USB
connector) had no top-side position and moved to B.Cu.

### 2. Caps Lock LEDs: two land sites each

`LED30` (normal Caps) and `LED75` (stepped Caps) are in series in the key chain,
so both must be fitted, but each lies under the other option's switch. `LED75`
is placed on the bottom side as a data relay (three vias, B.Cu routing) and
keeps its top pads in the stepped-Caps window; `LED30` keeps its window site and
gains a second top site in the row gap. Chain order and the firmware LED map are
unchanged. Every LED land site has a silkscreen dot at pin 1.

### 3. LDO: MAX38902A → AP2112K-3.3

JLCPCB does not stock the MAX38902AATA+T. `U2` is now an AP2112K-3.3TRG1 in
SOT-23-5 in the same place (`Maru60:SOT-23-5_TightCourtyard`: the stock KiCad
land with the courtyard drawn 0.04 mm outside the pads, because the pads sit
0.4 mm from `C100` and `C101`). The AP2112K has no bypass pin, no output sense
and no minimum load, so `C142`, `R163` and the In2 sense jumper with its two
vias were removed. Pinout, ratings and capacitor requirements are checked
against Diodes DS39724 in the power-simulation report.

### 4. Capacitors, from manufacturer DC-bias data

| Ref | Was | Now | Effective |
| --- | --- | --- | --- |
| `C100` (+4V_REG, 1206) | 4.7 µF 50 V | 22 µF 25 V X5R | 15.8 µF at 4 V |
| `C140`, `C141` (buck output, 0603) | 22 µF 10 V | unchanged | 8.7 µF each at 4 V |
| `C137` (buck input, 0603) | 4.7 µF 50 V | 10 µF 25 V X5R | 4.7 µF at 5 V |
| `C136` (at the buck VIN pin, 0603) | 100 nF | 10 µF 25 V X5R | 4.7 µF at 5 V |

Buck output about 33 µF effective (TI's minimum is 15 µF); buck input 9.4 µF
(TI's typical is 10 µF).

### 5. Parts that can be bought

`U8` TPS259470ARPWR (auto-retry; the latch-off part is not stocked), `U7`
TPS2553DBVR (constant current; FAULT is unchanged and the firmware latches the
fault itself), `R121` 154 k (OVLO 5.80 V instead of 5.74 V; 156 k is not
stocked). Every assembled part is in stock at JLCPCB on the snapshot date in
`pcb/order/parts.json`; the hot-swap sockets are not and are left for hand
soldering.

### 6. Corrections from the reviews and analyses

- `U13` TPD6E05U06: pads and paste follow TI land pattern 4221500/A.
- `L1`: pour keep-out between the pads of the RP2350 core-regulator inductor.
- `C102`: 0.18 mm further from `C103` (pad gap 0.24 → 0.42 mm).
- Switch pin holes 3.00 → 3.05 mm (Kailh KH-PS1607-10: 3.05 ± 0.05 mm).
- Copper at least 0.2 mm from every non-plated hole (JLCPCB's limit; the board
  rule was 0.15 mm): tracks follow the hole on a tangent polygon, the GND
  planes keep 0.25 mm, and the `LED30` and `LED75` window pads beside the Caps
  Lock pin holes are 0.03 mm narrower on the hole side. The rule is now in the
  board's own `maru60.kicad_dru`. Two vias moved away from switch holes.
- Silkscreen: every reference text is 1.0 mm high with a 0.15 mm stroke and
  at least 0.15 mm from every pad; the outline dashes of the 0402 capacitor
  and resistor footprints and the test-point circles, which sat 0.10–0.14 mm
  from their own pads, are removed. Those footprints and the USB connector's
  (GND lands 0.02 mm shorter beside the locating-peg holes) are now in the
  project's `Maru60` library; pads and courtyards are otherwise unchanged.
- `R115`–`R119`, 100 Ω each, in series at the source of the five LED data hops
  longer than 62 mm: underglow 274 mm (`LED68`) and 102 mm (`LED71`), key
  79 mm (`LED58`), 72 mm (`LED59`) and 63 mm (`LED48`). The LED data sheet
  does not give the output strength; with a strong, fast output an
  unterminated hop of this length rings back through the input threshold.
  With the resistors all five are clean for every output simulated
  (10 Ω–1 kΩ, 1–30 ns). `R118` is on the top side under the spacebar, outside
  the switch housing and stabilizer zones; the others are on the bottom.
- `C143`, 22 pF, across the buck's top feedback resistor `R159`: the
  feed-forward capacitor of TPS6293x data sheet section 10.2.2.10. In the
  loop model the phase margin goes from 38–44° to 46–51° with the crossover
  unchanged.
- 33 of the 39 via holes that sat inside SMD pads are out of the pad (an open
  via in a pad draws solder away from the joint): 25 moved up to 1.3 mm with
  their tracks, 8 rerouted to a position up to 3.3 mm away.

### 7. Placement file fitted to JLCPCB's footprints

`fit_jlcpcb_placement.py` fetches the footprint JLCPCB places from for each
LCSC part and solves the rotation and centre that put its pads on the board's
pads. 312 of 313 placements are fitted (the remaining one is a non-polar
resistor); SOIC, TSSOP and SOT-23 agree with the community correction tables,
and the USB-C connector needed a 1.3 mm centre shift.

## Findings that needed no change

- **USB:** the RP2350 PHY is full speed only; the high-speed eye of the earlier
  USB report does not apply. The routed pair is 95 Ω differential with 2 ps
  skew and passes the full-speed crossover and edge limits in simulation.
- **LED supply at 4.0 V:** inside the SK6805-EC15-001's 3.7–5.5 V range; the
  furthest LED still has about 3.82 V at the limiter maximum.

## Left as it is

- **Right Shift, 2.75U with a PCB-mount stabilizer:** `LED54` lies under the
  left stabilizer housing. No route to a second site was found on either
  layer. A plate-mount stabilizer, which is what the stock plate takes, hangs
  about 1.5 mm above the PCB by nominal dimensions and should clear the
  0.65 mm LED; this was not checked against a real part.
- **2U Backspace:** not supported; Backspace is split only.
- **`F1`:** the Bourns land pattern does not fit between its neighbours; the
  standard 1206 land stays. The fuse terminals are fully on the pads.
- **USB delay:** connector to transceiver is 1.03–1.07 ns; USB 2.0 allows a
  device 1 ns. The allowance is a share of the budget through five hubs; every
  full-speed waveform limit passes with margin. Meeting the number needs 13 mm
  less route. The pair is a 156 mm staircase between the switch holes (the
  shortest path with no obstacles would be 132 mm) and the excess is spread
  over the whole run, so it means laying the pair again from the connector to
  the MCU. Left as a recorded deviation.
- **LED hops of 62 mm and less** have no series resistor. The longest keeps
  0.40 V above the input threshold with a 20 Ω, 2 ns LED output and rings
  back under it only with 20 Ω and 1 ns, or 10 Ω and 2 ns. Look at `LED74`
  DIN with a scope at bring-up.
- **VBUS rings on hot-plug** (about 1.5 × the source for microseconds, into a
  50 V capacitor and a 28 V eFuse input): harmless from a 5 V port. There is
  no TVS on VBUS. See the power-simulation report.
- **Six vias remain inside SMD pads**: the GND pads of `R140`, `R143`, `Y1.2`
  and `U12`, the DIN pad of `LED71` (no free position with a route within
  6.5 mm) and the feedback pad of `R159` (kept on purpose: moving it adds
  2.4 mm to the buck's feedback node beside the switch node). Expect less
  solder on those joints; inspect them on the first boards.
- **Two orientation marks** are closer than 0.15 mm to a pad or hole: the
  pin-1 dot of `LED30`'s window site (0.088 mm from a switch pin hole) and the
  pin-1 triangle of `U11` (0.115 mm from a pad of `R130`). Kept, because they
  show orientation.
- Hardware qualification, license and USB ID are as in [`pcb/CURRENT.md`](../../CURRENT.md).

## Reproduce

```sh
docker build -f tools/kicad9.Dockerfile -t maru60-kicad:9.0.2 .
tools/run_kicad9.sh python3 tools/check_pcb_native.py \
  --checkpoint pcb/experiments/resume-20261111-order-candidate \
  --expected-opens 0 --output build/order-native-new --material
.venv/bin/python pcb/tools/export_order_package.py
```

The edits were made by the planners and appliers in `pcb/tools`, each step
followed by KiCad DRC; the plans and operation lists that were applied are the
`*-plan.json`, `*-spec.json` and `*-ops.json` files in `qa/`. See
[`pcb/tools/README.md`](../../tools/README.md).
