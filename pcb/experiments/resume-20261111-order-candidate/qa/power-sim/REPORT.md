# Power-tree simulation (ngspice, behavioural models)

Board as of the order candidate: AP2112K-3.3 LDO, buck output 2 × 22 µF 0603 +
22 µF 1206, buck input 2 × 10 µF, OVLO divider 590 k / 154 k, TPS259470A,
TPS2553 (constant current), feed-forward capacitor `C143` 22 pF across the
buck's top feedback resistor, snubber `R187` 1 Ω + `C144` 4.7 µF across the
input capacitor `C125`. **Two changes came out of this simulation: `C143`**
(the loop's phase margin was 38–44° without it) **and the snubber** (the
connector voltage rang to 1.5 × the source at plug-in without it). One thing
to know before bring-up is listed at the end.

Everything below is simulated with the models in
[`pcb/tools/power_sim/models.lib`](../../../../tools/power_sim/models.lib). None is a
vendor model; each parameter there is tagged `[DS …]` (read from the named
datasheet), `[AN …]` (TI SLUAAG4), `[CALC]` or `[ASSUMED]`. Capacitor values are
the effective values under DC bias from `qa/datasheet-review/followup-verification.md`.
Nothing is measured. Numbers: [`results.json`](results.json). Rerun:
`.venv/bin/python pcb/tools/power_sim/run_power_sim.py <out dir>`.

## Verdict

| Item | Result | Limit / reference | Basis |
| --- | --- | --- | --- |
| Start-up, 5.0 V / 5.5 V source | 3V3 in regulation 33.26 / 33.25 ms after plug-in; largest dip on the way up 33.22 mV; no overshoot (3.333 V, 4 V rail 4.0005 V) | monotonic enough for the RP2350 power-on reset | simulated |
| Plug-in current | 4.15 A for a few µs into `C125` (1 µF) and the snubber `R187` + `C144` (4.7 µF), 5.7 µF nominal ahead of the eFuse; after that the eFuse ramp limits the charge current to milliamps | USB allows a 10 µF hot-plug load | simulated; cable 1 µH assumed |
| Plug-in overshoot at the connector / at the eFuse input | 5.13 V / 5.00 V from a 5 V source (7.50 V / 7.47 V without the snubber) | 28 V eFuse input rating, 50 V capacitors | simulated; cable 1 µH assumed |
| Input current, worst steady state | 295.1 mA | 425 mA minimum eFuse limit, 500 mA USB | simulated |
| 3V3 load step 20 → 120 mA | 15.5 mV droop on 3V3 | ±5 % = 165 mV | simulated, switching model |
| LED rail enable | 93.2 mA input peak, 21.6 mV on +4V_REG (switching ripple included), 3V3 undisturbed | — | simulated, switching model |
| LED load step 0 → 150 mA | 43.6 mV on +4V_LED, 23.7 mV on +4V_REG | LED minimum 3.7 V | simulated |
| Buck loop, with `C143` 22 pF | crossover 27–49 kHz, phase margin 45.5–50.8°, gain margin ≥ 33 dB over load, capacitor tolerance and gain assumption (0.68–1.3 ×) | 45° is the usual target; without `C143` the same model gives 38–44° | simulated, model after TI SLUAAG4 |
| Source sagging to 4.2 V | +4V_REG 3.223 V (buck in dropout), 3V3 3.16 V | flash 2.7 V minimum | simulated at 120 mA + LEDs 150 mA |
| Source sagging to 3.9 V | 3V3 2.981 V | outside the USB range | simulated |
| Short on +4V_LED | limited to 0.201 A; +4V_REG dips to 3.488 V for microseconds, 3V3 stays at 3.3 V | 3V3 must hold | simulated |
| Short on +3V3 | LDO folds back, input 64 mA, recovers to 3.3 V | — | simulated |
| 6 V or 20 V source | eFuse output never rises (-0.0 V); nothing downstream sees the over-voltage. The eFuse input peaks at 6.00 V and 20.12 V (8.97 V and 31.28 V without the snubber) | OVLO 5.80 V nominal; eFuse input rated 28 V | simulated; capacitors at half value for the 20 V case |
| 6 V surge while running | eFuse opens at 5.775 V, the board resets and restarts (3.3 V after) | protective | simulated |

## Input current by state

| State | Input current |
| --- | --- |
| idle 20 mA on 3V3, LEDs off | 18.3 mA |
| typing 60 mA on 3V3, LEDs off | 54.0 mA |
| 60 mA on 3V3, LEDs at the firmware cap (38 mA static + 25 mA) | 111.1 mA |
| 120 mA on 3V3, LED rail at the 234 mA limiter maximum | 295.1 mA |

## Buck loop gain

| Case | Crossover | Phase margin | Gain margin |
| --- | --- | --- | --- |
| 0.1 A, nominal capacitors, kea 1 | 36.3 kHz | 48.7° | 39.2 dB |
| 0.3 A, nominal capacitors, kea 1 | 36.1 kHz | 48.9° | 39.3 dB |
| 0.3 A, capacitors at -20 % / -10 %, kea 1 | 40.7 kHz | 47.7° | 35.9 dB |
| 0.3 A, nominal capacitors, kea 0.68 | 27.1 kHz | 50.8° | 42.6 dB |
| 0.02 A, nominal capacitors, kea 1 | 36.1 kHz | 49.0° | 39.2 dB |
| 0.3 A, capacitors at -20 % / -10 %, kea 1.3 | 48.9 kHz | 45.5° | 33.6 dB |
| 0.3 A, nominal capacitors, kea 1, C143 not fitted | 35.7 kHz | 40.1° | 31.6 dB |
| 0.3 A, capacitors at -20 % / -10 %, kea 1, C143 not fitted | 40.1 kHz | 37.9° | 31.7 dB |
| 0.3 A, nominal capacitors, kea 0.68, C143 not fitted | 26.9 kHz | 44.1° | 34.9 dB |
| 0.3 A, nominal capacitors, kea 1, C143 47 pF | 37.9 kHz | 58.0° | 31.5 dB |
| 0.3 A, capacitors at -20 % / -10 %, kea 1.3, C143 47 pF | 52.9 kHz | 56.4° | 27.2 dB |

`C143` is the feed-forward capacitor the TPS6293x data sheet describes in
section 10.2.2.10 ("can be used across RFBT to improve the load transient
response or improve the loop phase margin"; TI's own example fits 10 pF on a
52.5 kΩ resistor and advises starting low). 22 pF on the 40 kΩ `R159` puts
every corner at or above 45° and leaves the crossover where it was. 47 pF
gives 56–58° in this model but moves the crossover up to 53 kHz in the
highest-gain corner; it is the value to try if the first board rings.

`kea` scales the error-amplifier / current-sense gain: 1 is the TPS62933 figure
from the application note, 0.68 is the value if TI scaled it with the smaller
switch of the TPS62932. Both are shown because the data sheet does not say.

## The new LDO against its data sheet

Diodes Incorporated AP2112, DS39724 Rev. 2-2:

| Item | Data sheet | Board |
| --- | --- | --- |
| SOT25 pins | 1 VIN, 2 GND, 3 EN, 4 NC, 5 VOUT (pin drawing p.2, pin table p.3) | same |
| Input voltage | 2.5 – 6.0 V operating, 6.5 V absolute maximum | 4.0 V; 5.8 V if the buck ever passed its input through |
| EN | high = on; the typical circuit ties it to VIN | tied to VIN |
| Capacitors | 1 µF X5R/X7R minimum at input and output | 22 µF at the input, 4.7 µF X7R plus the 3V3 decoupling at the output |
| Dropout | 125 mV typical, 200 mV maximum at 300 mA | 0.6 V available at the lowest buck tolerance |
| θJA, SOT25 | 184 °C/W | 0.105 W at 150 mA → +19 °C; 0.21 W at 300 mA → +39 °C |

## Hot-plug ringing and the snubber

A low-loss cable and the 1 µF ceramic at the connector form a resonant circuit:
without damping the connector voltage rings to about 1.5 × the source for
microseconds (7.5 V from 5 V, 31 V from a faulty 20 V source, which is above
the eFuse's 28 V input rating, before the eFuse has turned on). `R187` (1 Ω,
0805) in series with `C144` (4.7 µF 50 V X5R, 0805) across `C125` damps it:

| Source | Without the snubber: connector / eFuse input | With it |
| --- | --- | --- |
| 5 V | 7.50 V / 7.47 V | 5.13 V / 5.00 V |
| 6 V | 9.01 V / 8.97 V | 6.15 V / 6.00 V |
| 20 V (C125 and C144 at half value) | 31.34 V / 31.28 V | 21.35 V / 20.12 V |

1 Ω is near the optimum in this model (0.5 Ω and 2 Ω give 21.8 V and 21.4 V
at the eFuse input from 20 V). The peak plug-in current rises from 3.4 A to
4.2 A at 5 V; the charge stays below USB's 10 µF hot-plug allowance (5.7 µF
nominal). `R187` absorbs about 60 µJ per plug-in at 5 V and 1 mJ at 20 V.
There is still no TVS on VBUS: one that stands off 20 V would clamp above the
eFuse rating, and one that clamps a 5 V port would blow `F1` on a 20 V source
that the eFuse otherwise survives.

## Know before bring-up

1. **Phase margin 46–51° with `C143`, in a model.** The model is an
   approximation and TI does not publish the error-amplifier gain of the
   TPS62932. Check the +4V_REG load-step response with a scope on the first
   board; `C143` can be changed between 10 pF and 47 pF without touching the
   layout.
