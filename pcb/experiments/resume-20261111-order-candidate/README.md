# Order candidate (2026-11-11)

Derived from [`resume-20261109-relocated-expansion-zero-opens`](../resume-20261109-relocated-expansion-zero-opens/README.md)
(PCB `cb7b5b29`). This checkpoint fixes what stood between that board and an
order, and records the analyses run on the result. PCB SHA256:
`8057453f75871b4df187fc1adfe50b0b870c53e2fcc7e5202948398253904107`. The order
files exported from it are in [`pcb/order`](../../order/README.md).

**It is an order candidate for a first prototype, not a qualified design.**
Everything below is CAD checking, data-sheet reading, calculation and
simulation. Nothing has been measured on hardware.

## Checks on this board

| Check | Result | Evidence |
| --- | --- | --- |
| KiCad 9.0.2 DRC: opens / warnings / other errors | 0 / 0 / 0 | [`qa/native/RESULT.json`](qa/native/RESULT.json) |
| ERC, schematic parity, net identity, cold refill | 0, 0, pass, 74 files identical | same |
| Material (copper connectivity) graph | recomputed, pass | same |
| Netlist against the 0/0 prototype | only the intended differences: U2's pins, C142 and R163 removed, R115–R119, R170–R188, C143 and C144 added, 23 LED DOUT pins on their own `_SRC` nets, `VBUS_SNUB`, values and footprint names | `qa/netlist.xml` |
| Firmware GPIO and matrix bindings on this netlist | 24 bindings match, negative controls rejected | [`qa/firmware-static/static.json`](qa/firmware-static/static.json) |
| Top-side parts under a switch housing (default build) | none | `pcb/tools/plan_topside_relocation.py` keep-out |
| Bottom-case fit, including the new and moved bottom-side parts (`U2`, `C200`, `C143`, `LED75`, `R159` and 17 series resistors) | 41 pass, USB-C pass, 7U stabilizer pass | [`qa/mechanical-fit/REPORT.md`](qa/mechanical-fit/REPORT.md) |
| Pin tables and land patterns against manufacturer data sheets | all pin tables match | [`qa/datasheet-review/`](qa/datasheet-review/) |
| DRC with JLCPCB's limits as rules, 30 rules | every minimum met; no silkscreen within 0.15 mm of a pad or hole; no via inside an SMD pad | [`qa/dfm-jlcpcb/REPORT.md`](qa/dfm-jlcpcb/REPORT.md) |
| Power tree, ngspice | two changes (C143; snubber R187 + C144) | [`qa/power-sim/REPORT.md`](qa/power-sim/REPORT.md) |
| Power-net copper: drop, current, heating | no change needed | [`qa/pdn/REPORT.md`](qa/pdn/REPORT.md) |
| Signal integrity | USB pair laid again (0.955 ns, 1 ns allowed), 23 series resistors on LED data hops, and the matrix read delay in the firmware | [`qa/signal-integrity/REPORT.md`](qa/signal-integrity/REPORT.md) |
| Firmware built with the matrix read delay, both layouts | exit 0; delay 120 cycles and LED qualification 0 in the macro dumps; 120 `nop` in the linked delay routine | [`qa/qmk-build/RESULT.json`](qa/qmk-build/RESULT.json) |
| Gerber and drill files read back with a second parser | 973 plated holes, every non-plated hole and every SMD pad match | [`qa/gerber-verify/result.json`](qa/gerber-verify/result.json) |

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

### 8. Second pass: the items that had been left

The operation lists are in [`qa/second-pass`](qa/second-pass/REPRODUCE.md).

- **USB pair laid again.** Connector to transceiver was 1.03–1.07 ns against
  the 1 ns USB 2.0 allows a device; it is now 0.915 ns to `R102`/`R103` and
  0.955 ns to the pins. `plan_pair_route.py` searched both outer layers
  for the shortest any-angle path of the pair as one ribbon with every other
  piece of copper left where it is: 156 mm became 138 mm
  in the same corridor (the staircase is gone), still with four vias per line.
  A route on the bottom layer alone would save the vias but is 15 mm longer;
  letting the pair cross other tracks would gain 3 mm at most. At the
  connector D+ lost its length-matching detour and D− changes layer ahead of
  `U10`, which now hangs on a 2 mm stub like D+'s. No other net moved.
- **No via is left inside an SMD pad** (39 at the start, 6 after the first
  pass). `R140` and `R143`: the GND via sits between the resistor's two pads.
  `LED71`: 0.37 mm beside the pad. `U12`: the +4V_LED track beside it moved
  0.6 mm and the via went between pad and track. `Y1`: the +3V3 track round
  the crystal moved 0.4 mm outward and the via went below the pad. `R159`
  (buck feedback): the resistor moved 0.6 mm and the via 0.15 mm, so that
  0.2 mm of solder mask lies between hole and pad; the feedback node gains
  0.7 mm of track.
- **Orientation marks.** `LED30`'s pin-1 dot is 0.11 mm further from the Caps
  Lock pin hole; `U11`'s pin-1 triangle is a dot beside pin 1
  (`Maru60:Texas_PW0020A_TSSOP-20_4.4x6.5mm_P0.65mm`).
- **Series resistors on every LED data hop that needed one.** With an LED
  output of 10 Ω and a 1 ns edge, the strongest in the sweep, 18 more hops
  rang back through the input threshold: nine underglow hops of 28–62 mm and
  nine key hops of 27–33 mm (39–52 mm with the stubs of second sites).
  `R170`–`R186` and `R188`, 100 Ω each, are at their sources. 23 of the 74
  LED-to-LED hops now have a series part; the longest of the other 51 is
  26.6 mm (`KEY_RGB_CHAIN_15`) and keeps 0.08 V at that output. Fourteen
  were placed by `plan_series_resistor.py`; `R181`, `R184`, `R186` and `R188`
  were planned by hand because the hop runs under housings without a via or
  because the LED has two sites and the resistor has to sit behind both.
  `COL0` moved 0.8 mm for `R188` and passes between its pads.
- **Snubber on the USB input.** `R187` (1 Ω, 0805) in series with `C144`
  (4.7 µF 50 V, 0805) across `C125`, on the top side beside `R120`. Plug-in
  overshoot at the eFuse input in the model: 7.5 V → 5.0 V from a 5 V source,
  31.3 V → 20.1 V from a faulty 20 V source (the eFuse input is rated 28 V).
- **`LED54` has a second site** in the row gap west of the right-Shift
  stabilizer, for a 2.75U right Shift on a PCB-mount stabilizer: its window
  site lies under the left stabilizer housing in that build. As with the Caps
  Lock LEDs, fit exactly one site; the chain order and the firmware LED map
  do not change. `R184` sits behind the point where the two sites join.

## Findings that needed no change

- **USB:** the RP2350 PHY is full speed only; the high-speed eye of the earlier
  USB report does not apply. The routed pair is 95 Ω differential and passes
  the full-speed crossover and edge limits in simulation.
- **LED supply at 4.0 V:** inside the SK6805-EC15-001's 3.7–5.5 V range; the
  furthest LED still has about 3.82 V at the limiter maximum.

## Left as it is

- **2U Backspace:** not supported; Backspace is split only. A 2U key needs a
  third switch position between the two 1U ones, and a hot-swap socket there
  overlaps both neighbours. The earlier study
  (`engineering/candidates.pretty`, Mill-Max 3305 receptacles for the three
  positions) changes the assembly to six solder-in receptacles; whether to do
  that is the owner's decision.
- **Right Shift, 2.75U:** with a plate-mount stabilizer nothing changes. With
  a PCB-mount stabilizer move `LED54` to its second site (section 8); this
  was planned from nominal stabilizer dimensions and not checked against a
  real part. `LED55` is about 0.1 mm from the right stabilizer housing if
  the housing is 7.75 mm wide (assumed); check that on the part.
- **`F1`:** the Bourns land pattern does not fit between its neighbours; the
  standard 1206 land stays. The fuse terminals are fully on the pads.
- **No fiducials or tooling holes on the board:** 23 parts are within 2.5 mm
  of an edge, so the order needs edge rails anyway, and JLCPCB puts both on
  the rails.
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
`*-plan.json`, `*-spec.json` and `*-ops.json` files in `qa/` and, for the
second pass, in `qa/second-pass/`. See
[`pcb/tools/README.md`](../../tools/README.md).
