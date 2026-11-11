# Order candidate (2026-11-11)

Derived from [`resume-20261109-relocated-expansion-zero-opens`](../resume-20261109-relocated-expansion-zero-opens/README.md)
(PCB `cb7b5b29`). This checkpoint fixes what stood between that board and an
order. PCB SHA256: `5b71591a4a068c7e51b45e12f7938a0b41a9ce99a85ec2fc03e842c7d056575f`.
The order files generated from it are in [`pcb/order`](../../order/README.md).

**It is an order candidate for a first prototype, not a qualified design.**
Nothing here has been measured on hardware.

## Result

| Check | Result | Evidence |
| --- | --- | --- |
| KiCad 9.0.2 DRC: opens / warnings / other errors | 0 / 0 / 0 | [`qa/native/RESULT.json`](qa/native/RESULT.json) |
| ERC, schematic parity | 0, 0 | same |
| Net identity, cold refill | pass, 61 files identical | same |
| Top-side parts under a switch housing (default build) | 0 fitted (C200 moved to B.Cu) | `pcb/tools/plan_topside_relocation.py` keep-out |
| Bottom-case fit incl. LED75 relay | 20 pass, USB-C pass, 7U stabilizer pass | [`qa/mechanical-fit/REPORT.md`](qa/mechanical-fit/REPORT.md) |
| Pin tables and land patterns vs manufacturer datasheets | all pin tables match, no blocker | [`qa/datasheet-review/`](qa/datasheet-review/) |

## Changes

### 1. Top-side parts moved out from under the switches

MX housings sit flush on the PCB. Only the LED fits the housing's LED opening
(about 2.7 × 2.3 mm on Cherry MX RGB). The prototype had each LED's 0402 bypass
capacitor 4.0 mm beside the LED, under the housing, plus `R100` under the edge
of the Esc switch: 65 parts that would have kept switches from seating.

`pcb/tools/plan_topside_relocation.py` moved 64 of them into the gaps between
housings (courtyard at least 0.35 mm outside every 14 × 14 mm housing outline
and every stabilizer zone) and reconnected them on F.Cu only. Where no top-side
ground was within 3 mm it added a GND via into the inner planes (53 vias; same
net, so the planes are not cut). Median distance from LED to its capacitor is
4.6 mm, maximum 8.5 mm. Plan: [`qa/topside-relocation-plan.json`](qa/topside-relocation-plan.json).

`C200` (LED1 bypass) moved to B.Cu beside the +4V_LED via and is populated
again; the bottom side has room where the top side did not.

### 2. Caps Lock LEDs: two land sites each

`LED30` (normal Caps) and `LED75` (stepped Caps) are in series in the key chain,
so both must be fitted, but each lies under the other option's switch. A
single-layer route to a spare site for LED75 does not exist (its data-in and
data-out enclose each other), so:

- `LED75` is now placed on the **bottom** side at (12.0, 56.0) as a data relay,
  joined by three vias and B.Cu tracks. Its top pads in the stepped-Caps window
  remain for stepped builds.
- `LED30` keeps its window site and gains a second top site at (19.99, 38.22).

Chain order and the firmware LED map are unchanged. Spec:
[`qa/led-alt-sites-spec.json`](qa/led-alt-sites-spec.json). The two extended
footprints are saved in `pcb/engineering/candidates.pretty`.

The same conflict exists for `LED54` with a 2.75U right Shift stabilizer; no
route was found and that option is documented as unsupported.

### 3. Corrections from the datasheet review

- `U13` TPD6E05U06: pads and paste now follow TI land pattern 4221500/A
  (0.20 × 0.50 mm; they were 0.30 × 0.65 mm with twice the paste).
- `L1`: pour keep-out on B.Cu between the pads; a +3V3 finger ran under the
  RP2350 core-regulator inductor against datasheet §6.3.8.1.
- `C102`: 0.18 mm further from `C103`; the +3V3 / +1V1 pad gap goes from 0.24 to
  0.42 mm. (The full 0.23 mm to the reference position would break clearance to
  a +1V1 track.)

### 4. Values

| Ref | Was | Now | Why |
| --- | --- | --- | --- |
| `U2` | MAX38902AATA+T (TDFN-8) | AP2112K-3.3TRG1 (SOT-23-5) | The TDFN part has no JLCPCB stock. The replacement needs no BYP capacitor, output sense or minimum load, so `C142`, `R163` and the In2 sense jumper go with it. EN is tied to VIN. |
| `C137` | 4.7 µF 50 V | 10 µF 25 V X5R | Only C137 and C136 sit at the buck input; TI asks for 10 µF typical. Effective 4.7 µF at 5 V. |
| `C136` | 4.7 µF 50 V | 10 µF 25 V X5R | Second buck input capacitor at the VIN pin: 9.4 µF effective with C137 at 5 V. |
| `C100` | 4.7 µF 50 V X7R | 22 µF 25 V X5R | Buck output rail. `C140`/`C141` alone are 17.4 µF effective at 4 V (13.9 µF at −20%), under TI's 15 µF minimum; C100 adds 15.8 µF. |
| `U8` | TPS259470LRPW | TPS259470ARPWR | Latch-off part not stocked; auto-retry is pin-identical. |
| `U7` | TPS2553DBVR-1 | TPS2553DBVR | Same pinout and limit; constant current instead of latch-off. FAULT is unchanged. |
| `R121` | 156 k | 154 k 0.1% | 156 k is not stocked. OVLO rises from 5.74 V to 5.80 V nominal. |

### 5. Socket holes, C200 and LED pin-1 dots

- Kailh specifies 3.05 ± 0.05 mm pin holes, so all 61 switch pin holes grow from
  3.00 to 3.05 mm; 61 track ends move 0.05 mm to keep their hole clearance.
- `C200` returns on B.Cu beside the +4V_LED via instead of the under-switch top
  site.
- Every SK6805 land site gets a silkscreen dot at pin 1 (DIN). The top-row
  orientation is the pad toward the front-left of the board.

### 6. Findings that needed no change

- **USB:** the RP2350 PHY is full speed (12 Mbit/s) only. The high-speed eye in
  the earlier USB SI report does not apply; the 171 mm route is about 0.89 ns
  against the 1 ns device allocation, and impedance and skew are irrelevant at
  full-speed edge rates. No impedance control is ordered.
- **LDO thermal:** U2 dissipates 0.21 W from the 4.0 V rail at 300 mA; the 5 V
  input case in the thermal report cannot occur while the buck regulates.

### 7. Follow-up checks against manufacturer data

[`qa/datasheet-review/followup-verification.md`](qa/datasheet-review/followup-verification.md)
closes the four points the datasheet review left open: buck output capacitance
under DC bias (led to the `C100` change above), the LED current version (5 mA),
the Kailh socket land pattern, and the LED supply at 4.0 V.

## Not done

- No JLCPCB rotation corrections are applied to the placement file.
- Hardware qualification, license and USB ID are as in [`pcb/CURRENT.md`](../../CURRENT.md).

## Reproduce

```sh
docker build -f tools/kicad9.Dockerfile -t maru60-kicad:9.0.2 .
tools/run_kicad9.sh python3 tools/check_pcb_native.py \
  --checkpoint pcb/experiments/resume-20261111-order-candidate \
  --expected-opens 0 --output build/order-native-new
.venv/bin/python pcb/tools/export_order_package.py
```

The first-stage edit sequence from the 0/0 prototype, each step followed by
DRC: `plan_topside_relocation.py` → `apply_topside_relocation.py
--dnp C200` → `prune_dangling_tracks.py` (repeat until clean) →
`plan_led_alt_sites.py` → `apply_led_alt_sites.py` →
`save_board_footprint_to_lib.py` → `apply_review_fixes.py` →
`set_component_values.py`. The later revisions (AP2112K LDO swap, 3.05 mm socket
holes, `C200` back on B.Cu, LED pin-1 dots, second buck input capacitor) are
recorded in `qa/ldo-swap-ops.json`, `qa/socket-holes-ops.json`,
`qa/led-pin1-dots-ops.json` and `qa/value-changes-*.json`.
See [`pcb/tools/README.md`](../../tools/README.md).
