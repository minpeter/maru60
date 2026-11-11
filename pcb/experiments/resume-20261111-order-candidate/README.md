# Order candidate (2026-11-11)

Derived from [`resume-20261109-relocated-expansion-zero-opens`](../resume-20261109-relocated-expansion-zero-opens/README.md)
(PCB `cb7b5b29`). This checkpoint fixes what stood between that board and an
order, and records the analyses run on the result. PCB SHA256:
`c24899aaf0356446aac753b649a9f7747ebf66a4df8dc9dae3937b8fcfbb162f`. The order
files exported from it are in [`pcb/order`](../../order/README.md).

**It is an order candidate for a first prototype, not a qualified design.**
Everything below is CAD checking, data-sheet reading, calculation and
simulation. Nothing has been measured on hardware.

## Checks on this board

| Check | Result | Evidence |
| --- | --- | --- |
| KiCad 9.0.2 DRC: opens / warnings / other errors | 0 / 0 / 0 | [`qa/native/RESULT.json`](qa/native/RESULT.json) |
| ERC, schematic parity, net identity, cold refill | 0, 0, pass, 67 files identical | same |
| Material (copper connectivity) graph | recomputed, pass | same |
| Netlist against the 0/0 prototype | only the intended differences: U2's pins, C142 and R163 removed, R115 added, values and footprint names | `qa/netlist.xml` |
| Firmware GPIO and matrix bindings on this netlist | 24 bindings match, negative controls rejected | [`qa/firmware-static/static.json`](qa/firmware-static/static.json) |
| Top-side parts under a switch housing (default build) | none | `pcb/tools/plan_topside_relocation.py` keep-out |
| Bottom-case fit, including the new bottom-side parts (`U2`, `C200`, `R115`, `LED75`) | 23 pass, USB-C pass, 7U stabilizer pass | [`qa/mechanical-fit/REPORT.md`](qa/mechanical-fit/REPORT.md) |
| Pin tables and land patterns against manufacturer data sheets | all pin tables match | [`qa/datasheet-review/`](qa/datasheet-review/) |
| DRC with JLCPCB's limits as rules | see the report | [`qa/dfm-jlcpcb/REPORT.md`](qa/dfm-jlcpcb/REPORT.md) |
| Power tree, ngspice | no change needed | [`qa/power-sim/REPORT.md`](qa/power-sim/REPORT.md) |
| Power-net copper: drop, current, heating | no change needed | [`qa/pdn/REPORT.md`](qa/pdn/REPORT.md) |
| Signal integrity | one change (R115) | [`qa/signal-integrity/REPORT.md`](qa/signal-integrity/REPORT.md) |
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
- Copper at least 0.2 mm from non-plated holes where the routing allowed it,
  one via moved away from a switch pin hole, silkscreen reference text enlarged
  to 1.0 mm / 0.15 mm where it fitted.
- `R115`, 100 Ω, in series at the source of the 276 mm underglow data hop.
- 25 of the 39 via holes that sat inside SMD pads moved out of the pad (an
  open via in a pad draws solder away from the joint); each pad keeps a short
  track to its via.

### 7. Placement file fitted to JLCPCB's footprints

`fit_jlcpcb_placement.py` fetches the footprint JLCPCB places from for each
LCSC part and solves the rotation and centre that put its pads on the board's
pads. 307 of 308 placements are fitted (the remaining one is a non-polar
resistor); SOIC, TSSOP and SOT-23 agree with the community correction tables,
and the USB-C connector needed a 1.3 mm centre shift.

## Findings that needed no change

- **USB:** the RP2350 PHY is full speed only; the high-speed eye of the earlier
  USB report does not apply. The routed pair is 95 Ω differential with 1.6 ps
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
- **Matrix read delay:** with all 15 keys of one row held and a worst-case pin,
  the last column settles 50 ns after QMK reads it. One line in the firmware
  `config.h` removes it; the firmware overlay is hash-pinned to its build
  evidence and was not touched. See the signal-integrity report.
- **Buck phase margin** is 38–44° in the model and **VBUS rings on hot-plug**;
  both are for the first bring-up, see the power-simulation report.
- **14 vias remain inside SMD pads** where no free position exists: the GND
  pads of `R140`–`R143`, `R145`, `R159`, `Y1` (two), `U12`, `U6`, `U7`, `C122`
  and the DIN pads of `LED70` and `LED71`. Expect less solder on those joints;
  inspect them on the first boards, or order the vias filled and capped if
  JLCPCB offers it for this stack.
- Track ends that stay 0.15–0.19 mm from a non-plated hole and 10 reference
  texts that stay at 0.8 mm, where the change would have broken another rule;
  the JLCPCB-rule report counts them.
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
