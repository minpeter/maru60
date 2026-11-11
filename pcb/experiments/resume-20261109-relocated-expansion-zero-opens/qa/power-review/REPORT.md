# Maru60 power review — analysis only

**Status: ANALYSIS_ONLY. No stability, thermal, USB-compliance, EMC or hardware qualification.**
Board: `pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb`
(SHA256 `cb7b5b29…e10a5d`). Netlist: `qa/native/netlist.xml`
(SHA256 `dbc70642…8fd7c0`). Numbers: `power-review.json`; arithmetic:
`pcb/tools/analyze_power.py`.

This review closes the *arithmetic* gaps. It does not close the *physical* gaps.
Every number below is conditional on the stated assumption. Unknowns are marked
unknown.

## Bottom line

| Question | Answer |
|---|---|
| 5.8 µF vs TI 10 µF typical | **Below guidance, not a proven failure.** 5.8 µF nominal; 5.336 µF effective at 5 V under the stated 0.92 derating (58% / 53% of 10 µF). Add a **5.6 µF/50 V X7R** (or 6.8 µF) to reach ≥10 µF effective, or measure first. |
| Inrush | **1.16 mA** capacitor-only at 0.2 V/ms (C124 = 10 nF), **72.5 µJ**, 25 ms to 5 V. Far below the 425 mA eFuse minimum and the 500 mA USB descriptor. Inrush is not the limiting issue. |
| LED current | R112 = 133 kΩ 1% sets **173.657 / 201.513 / 233.901 mA** (min/nom/max). 76 SK6805 at the stated **5 mA/channel** full-white assumption draw **1.14 A** — **4.87–6.56× the limiter**. The TPS2553-1 latches off. Full white is not supported. |
| UVLO / OVLO | UVLO rising **3.987 V** nominal (3.863–4.131 V with leakage); OVLO rising **5.738 V** nominal (5.589–5.917 V with leakage). UVLO is below the 4 V buck's no-foldback input; OVLO min is only ~89 mV above the 5.5 V USB maximum. |
| Soft-start | C139 = 100 nF, 8 corners: **11.077–19.556 ms**, nominal **14.545 ms** (datasheet ISS 4.5/5.5/6.5 µA). Existing conservative screen: 10.860–19.955 ms recomputed (original `calculations.json`: 10.855–19.947 ms). This is the SS reference ramp, not measured board startup. |
| Sequencing | VBUS → FUSED → PROTECTED → 4V → 3V3 → LED rail. The eFuse 25 ms ramp and the buck 14.5 ms SS overlap; the 4 V rail may not be monotonic. LED rail is last and held off by R109 until firmware drives GPIO22. |

## 1. Input capacitance: 5.8 µF vs 10 µF

The protected rail `VBUS_PROTECTED_RAW` has C126 1 µF + C136 100 nF + C137
4.7 µF = **5.8 µF nominal**. TI's TPS62932 guidance is **10 µF typical** plus
0.1 µF.

The exact C126/C136/C137 MPNs and dielectrics are not recorded, so the DC-bias
derating is an **assumption**, not a manufacturer guarantee. The stated curve is
1.00 at 0 V, **0.92 at 5 V**, 0.85 at 10 V, 0.75 at 16 V, 0.60 at 25 V, 0.35 at
50 V. At 5 V:

- effective C = 5.8 × 0.92 = **5.336 µF** (53.4% of 10 µF);
- additional effective needed = 4.664 µF;
- additional nominal at 0.92 = **5.070 µF** → nearest standard **5.6 µF**
  gives 10.488 µF total effective; 6.8 µF gives 11.592 µF.

A 4.7 µF addition gives only 9.66 µF effective and does **not** reach 10 µF
under the same assumption. A 10 µF/25 V X7R part would have a different
(probably worse) derating at 5 V; it is not automatically better.

**Verdict:** below TI's typical guidance. This is a review flag, not a measured
failure and not a stability result. The 10 µF figure is a typical
recommendation, not a datasheet minimum. Adding the cap is a margin
improvement; it does not prove loop stability.

## 2. Inrush

C124 = 10 nF on the TPS259470 dVdt pin. TPS25947 Eq. 4 gives
`SR[V/ms] = 2 / C_dVdt[nF]` = **0.2 V/ms = 200 V/s**. Into the 5.8 µF protected
rail:

- `I = C·dV/dt` = 5.8 µF × 200 V/s = **1.16 mA**;
- `E = ½CV²` = **72.5 µJ** at 5 V;
- time to 5 V = **25 ms**.

The eFuse ILIM table for R124 = 6.65 kΩ is **425 / 500 / 575 mA**
(min/nom/max). The capacitor-only inrush is 0.27% of the 425 mA minimum and
0.23% of the 500 mA USB descriptor. The eFuse's 400 µs current-limit response
and 500 ns fast-trip are not expected to act on this ramp. Active buck and LED
load current is additional and is not included.

Adding 5.6 µF raises the capacitor-only inrush to **2.28 mA** and the energy to
**142.5 µJ** — still negligible. Inrush is not the reason to avoid the cap.

**Caveat:** the 1.16 mA is the *capacitor* current, not total board startup
current. The buck's output-capacitor charge and the LED rail turn-on are
separate. The LED rail has ~7.9 µF of local 100 nF bypass capacitors; U7's
current limit (174–234 mA) bounds that charge, but the latch-off behavior must
be checked.

## 3. UVLO / OVLO margins (R120–R123)

TPS259470 EN/UVLO and OVLO rising/falling references are 1.183/1.200/1.223 V
and 1.076/1.090/1.116 V. R120 = 590 kΩ, R121 = 156 kΩ (OVLO divider);
R122 = 620 kΩ, R123 = 267 kΩ (UVLO divider); all 0.1%.

| Threshold | Min (R+Vref) | Nom | Max (R+Vref) | With ±0.1 µA leakage |
|---|---:|---:|---:|---:|
| UVLO rising | 3.925 V | **3.987 V** | 4.069 V | 3.863–4.131 V |
| UVLO falling | 3.570 V | 3.621 V | 3.713 V | 3.508–3.775 V |
| OVLO rising | 5.648 V | **5.738 V** | 5.858 V | 5.589–5.917 V |
| OVLO falling | 5.137 V | 5.212 V | 5.345 V | 5.078–5.404 V |

Margins (nominal / min / max; negative means the threshold is below the
reference):

| Comparison | Nominal | Min | Max | With leakage |
|---|---:|---:|---:|---:|
| UVLO rising vs 4.301 V no-foldback ideal | −0.315 V | −0.377 V | −0.232 V | −0.439…−0.170 V |
| UVLO rising vs 4.082 V 98%-duty ideal | −0.095 V | −0.157 V | −0.013 V | −0.219…+0.049 V |
| UVLO rising vs 3.8 V buck recommended min | +0.187 V | +0.125 V | +0.269 V | +0.063…+0.331 V |
| UVLO falling vs 3.4 V assumed LDO min | +0.221 V | +0.170 V | +0.313 V | +0.108…+0.375 V |
| OVLO rising vs 5.5 V USB max | +0.238 V | +0.148 V | +0.358 V | +0.089…+0.417 V |

**Verdict:** the UVLO release is above the buck's 3.8 V recommended minimum but
below the 4.30 V no-foldback ideal and at/below the 4.08 V 98%-duty ideal at the
nominal and min corners. The 4 V rail may rely on frequency foldback at startup.
The OVLO min corner is only ~89 mV above the 5.5 V USB maximum. Both are review
flags, not measured failures. The 4.301 V is the existing 93%-duty design
screen; 4.082 V is the ideal 98%-duty screen. Neither is a guaranteed minimum
input voltage.

## 4. Soft-start (C139 = 100 nF)

TPS62932: `t_SS = C_SS·VREF/ISS`, VREF = 0.8 V, ISS = 4.5/5.5/6.5 µA. C139 is
100 nF ±10% (90/100/110 nF). The eight non-nominal corners span
**11.077–19.556 ms**; nominal is **14.545 ms**. The existing
`calculations.json` used a slightly wider ISS screen (4.41/6.63 µA); its
recorded range is **10.855–19.947 ms**, and recomputing with 4.41/6.63 µA gives
**10.860–19.955 ms**. Both are analysis screens.

This is the SS *reference* ramp. It excludes capacitor derating, the eFuse
ramp, the buck's actual startup dynamics and load. It is not the observed board
startup time.

## 5. LED limiter (U7 TPS2553-1, R112 = 133 kΩ 1%)

TPS2553 datasheet equations (mA, R in kΩ):
`Imax = 22980/R^0.94`, `Inom = 23950/R^0.977`, `Imin = 25230/R^1.016`.
Using R112 = 133 kΩ ±1% and the worst resistor for each corner:

| Corner | R_ILIM | Current |
|---|---:|---:|
| Min | 134.33 kΩ | **173.657 mA** |
| Nom | 133.00 kΩ | **201.513 mA** |
| Max | 131.67 kΩ | **233.901 mA** |

The board has **76** SK6805 LEDs on `+4V_LED`, 3 channels each. No SK6805
datasheet is in this repository, so the per-channel current is an explicit
assumption. At **5 mA/channel** (15 mA/LED), full white is **1.14 A** —
**6.56× / 5.66× / 4.87×** the min/nom/max limiter. Sensitivity:

| Per channel | Total (76 LEDs) | vs min limit |
|---|---:|---:|
| 0.5 mA | 114 mA | 0.66× |
| 1 mA | 228 mA | 1.31× |
| 2 mA | 456 mA | 2.63× |
| 5 mA | 1.14 A | 6.56× |
| 12 mA | 2.736 A | 15.76× |

The maximum per-channel current that fits the **min** limiter is
**0.762 mA/channel** (1.026 mA/channel at the max limiter). The TPS2553-1 is a
**latch-off** part: an overcurrent attempt is expected to latch the LED rail
off, not merely dim it. Even if U7 were bypassed, the eFuse 500 mA nominal is
below 1.14 A.

**Verdict:** full-white capability is not supported by this power tree. Either
enforce a firmware brightness cap of ≤0.76 mA/channel at the min corner, or
change the LED rail current limit and the USB power source. The 5 mA assumption
must be replaced with the exact LED datasheet before the full-white number is
treated as a specification.

## 6. Sequencing

Netlist order: **VBUS → F1 → VBUS_FUSED → U8 eFuse → VBUS_PROTECTED_RAW →
U18 buck → +4V_REG → U2 LDO → +3V3; U7 switch → +4V_LED**.

- eFuse ramp: 0.2 V/ms, 25 ms to 5 V; UVLO release at ~19.9 ms.
- Buck SS: 14.5 ms nominal, starting at UVLO release; 4 V ready ~34.5 ms after
  VBUS in the ideal case.
- The eFuse ramp and buck SS overlap: the buck starts while the input is still
  ramping. The 4 V rail may not be monotonic.
- The 3V3 LDO follows the 4 V rail; its startup is **unknown** here.
- The LED rail is last. R109 100 kΩ pulls U7 EN low at reset; firmware drives
  GPIO22 high after boot. LED_FAULT_N is pulled up to 3V3 via R113 10 kΩ.

## What is proven

- The netlist connectivity and component values used above (script assertions).
- The nominal input capacitance is 5.8 µF; the effective value under the stated
  derating is 5.336 µF.
- The capacitor-only inrush is 1.16 mA / 72.5 µJ at 0.2 V/ms.
- The UVLO/OVLO divider arithmetic and the stated margins.
- The soft-start arithmetic and the 8-corner range.
- The TPS2553 current-limit table and the full-white arithmetic for the stated
  per-LED assumption.
- The rail order and the enable/fault pull resistors.

## Review flags

1. **PWR-01** — 5.8 µF nominal / 5.336 µF effective vs TI 10 µF typical.
2. **PWR-02** — UVLO release below the 4 V buck's no-foldback input; possible
   frequency-foldback startup.
3. **PWR-03** — OVLO min corner only ~89 mV above the 5.5 V USB maximum.
4. **PWR-04** — LED limiter 174–234 mA vs 1.14 A full white; TPS2553-1 latches
   off.
5. **PWR-05** — eFuse ILIM min 425 mA is below the 500 mA USB descriptor; the
   board cannot guarantee 500 mA.
6. **PWR-06** — eFuse ramp and buck SS overlap; 4 V rail may not be monotonic.

## Must be measured on the bench

1. VBUS, VBUS_FUSED, VBUS_PROTECTED_RAW, +4V_REG, +3V3 and +4V_LED startup at
   5.0 V and 5.5 V, hot and cold, with the actual cable.
2. Input ripple at U18 VIN at no load, MCU load and a full-white LED attempt.
3. UVLO/OVLO trip points by sweeping VBUS up and down on the assembled board.
4. LED rail current and U7 FAULT/latch behavior at full white and at the
   intended firmware brightness cap.
5. 3V3 load step and LDO thermal at the actual load.
6. Buck load step and, if stability is to be claimed, loop gain/phase across
   the application corners.
7. eFuse current limit and thermal at 425/500/575 mA.
8. Soft-start time and monotonicity of the 4 V rail.

## Recommendation

**Primary: add cap.** Add a **5.6 µF/50 V X7R** (or 6.8 µF) on
`VBUS_PROTECTED_RAW` to reach ≥10 µF effective at 5 V under the stated 0.92
derating. This is a margin improvement, not a stability proof. The exact MPN,
package and land pattern still need selection; 5.6 µF/50 V is not a common 0603
value, so the added part may need a larger land. If board space is tight,
measure the existing 5.8 µF first; the analysis does not show that 5.8 µF fails.

**LED:** do not claim full-white capability. Enforce a firmware cap of
≤0.76 mA/channel at the min limiter corner, or change the LED rail current
limit and the USB power source.

**UVLO:** if the 4 V rail must be regulated at startup, raise the UVLO rising
threshold above ~4.3 V (e.g. 4.5 V) by changing R122/R123, and re-check the
OVLO margin.

**Measure first** for the actual startup, input ripple, UVLO/OVLO trip points
and LED rail current. The analysis identifies margins; it does not prove a
failure.

## Unknowns

- Exact C126/C136/C137 MPNs, dielectrics and DC-bias curves; the 0.92 derating
  is an assumption.
- Actual VBUS source/cable impedance and input ramp/dip waveform.
- Actual SK6805 per-channel current; 5 mA is an assumption, not a datasheet
  fact in this repo.
- Actual MCU, flash, logic and LED load currents and their simultaneity.
- TPS62932 loop stability, phase margin, load-step response and
  frequency-foldback behavior on this board.
- TPS259470 thermal/current-limit behavior and actual trip point.
- MAX38902 dropout, startup and thermal behavior at the actual 3V3 load.
- Firmware LED brightness cap, fault handling and latch-off recovery.
- Whether the 4 V rail is monotonic through the eFuse/buck overlap.

## Sources read

- TI TPS25947, SLVSFC9C (revised May 2026): UVLO/OVLO references, ILIM table,
  dVdt equation, current-limit/fast-trip response.
- TI TPS2553, SLVS841G (revised October 2026): ILIM equations, latch-off
  behavior, response time.
- TI TPS62932, SLUSEA4D (revised August 2022): 10 µF input-cap guidance, SS
  equation and ISS limits, 98% maximum duty and frequency foldback.
- Analog Devices MAX38902A/MAX38902D: 3.3 V LDO input range and 500 mA rating.
- Existing `qa/portable/power/calculations.json` and
  `calculation-replay-result.json`: feedback/SS arithmetic and the 5.8 µF
  nominal sum.
- `pcb/experiments/resume-20261106-usb-pendant-prototype/evidence/power-audit/DELIVERY_REPORT.md`
  and `pcb/experiments/v7-c124-short-local-review/analysis/v7-c124-capacitance-independent-review-20261104/REVIEW.md`:
  prior 5.8 µF vs 10 µF flag and C124 dVdt context.
- `pcb/engineering/electrical-architecture.md` and `pcb/CURRENT.md`: architecture
  and current-baseline status.
- No SK6805 datasheet is present in this repository; the 5 mA/channel figure is
  an explicit assumption, not a cited fact.

## Reproduction

```bash
.venv/bin/python pcb/tools/analyze_power.py
```

The script reads `qa/native/netlist.xml`, asserts the power-tree connectivity
and values, and writes `qa/power-review/power-review.json`. It uses only the
Python standard library. It does not run SPICE, does not qualify effective
capacitance, and does not prove stability.
