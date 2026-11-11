# Power-tree simulation (ngspice, behavioural models)

Board as of the order candidate: AP2112K-3.3 LDO, buck output 2 × 22 µF 0603 +
22 µF 1206, buck input 2 × 10 µF, OVLO divider 590 k / 154 k, TPS259470A,
TPS2553 (constant current). **No result calls for a design change.** Two things
to know before bring-up are listed at the end.

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
| Start-up, 5.0 V / 5.5 V source | 3V3 in regulation 33.26 / 33.25 ms after plug-in; largest dip on the way up 32.07 mV; no overshoot (3.332 V, 4 V rail 4.0005 V) | monotonic enough for the RP2350 power-on reset | simulated |
| Plug-in current | 3.3839 A for a few µs into C125 (1 µF, ahead of the eFuse); after that the eFuse ramp limits the charge current to milliamps | USB allows a 10 µF hot-plug load | simulated; cable 1 µH assumed |
| Input current, worst steady state | 295.1 mA | 425 mA minimum eFuse limit, 500 mA USB | simulated |
| 3V3 load step 20 → 120 mA | 15.5 mV droop on 3V3 | ±5 % = 165 mV | simulated, switching model |
| LED rail enable | 98.0 mA input peak, 11.7 mV on +4V_REG, 3V3 undisturbed | — | simulated, switching model |
| LED load step 0 → 150 mA | 37.9 mV on +4V_LED, 12.3 mV on +4V_REG | LED minimum 3.7 V | simulated |
| Buck loop | crossover 27–40 kHz, phase margin 38–44°, gain margin ≥ 31 dB over load, capacitor tolerance and gain assumption | stable; 45° is the usual target | simulated, model after TI SLUAAG4 |
| Source sagging to 4.2 V | +4V_REG 3.223 V (buck in dropout), 3V3 3.16 V | flash 2.7 V minimum | simulated at 120 mA + LEDs 150 mA |
| Source sagging to 3.9 V | 3V3 2.981 V | outside the USB range | simulated |
| Short on +4V_LED | limited to 0.201 A; +4V_REG dips to 3.488 V for microseconds, 3V3 stays at 3.3 V | 3V3 must hold | simulated |
| Short on +3V3 | LDO folds back, input 64 mA, recovers to 3.3 V | — | simulated |
| 6 V or 20 V source | eFuse output never rises (-0.0 V); nothing downstream sees the over-voltage | OVLO 5.80 V nominal | simulated |
| 6 V surge while running | eFuse opens at 5.776 V, the board resets and restarts (3.3 V after) | protective | simulated |

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
| 0.1 A, nominal capacitors, kea 1 | 35.8 kHz | 39.9° | 31.5 dB |
| 0.3 A, nominal capacitors, kea 1 | 35.7 kHz | 40.1° | 31.6 dB |
| 0.3 A, capacitors at -20 % / -10 %, kea 1 | 40.1 kHz | 37.9° | 31.7 dB |
| 0.3 A, nominal capacitors, kea 0.68 | 26.9 kHz | 44.1° | 34.9 dB |
| 0.02 A, nominal capacitors, kea 1 | 35.6 kHz | 40.2° | 31.5 dB |

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

## Know before bring-up

1. **Hot-plug ringing on VBUS.** With a low-loss cable the 1 µF at the connector
   rings: about 1.5 × the source voltage for microseconds in this
   model (9.0 V from a 6 V source, 31.34 V from 20 V). From a 5 V port that is
   about 7.5 V on a 50 V capacitor and a 28 V-rated eFuse input, before the
   eFuse has turned on: harmless. From a faulty 20 V source it would exceed the
   eFuse rating; a compliant USB-C source never gives more than 5 V to this
   board because it only presents Rd. There is no TVS on VBUS.
2. **Phase margin near 40°.** Stable in every corner simulated, but below the
   45° most designs aim for, and the model is an approximation. Check the
   +4V_REG load-step response with a scope on the first board.
