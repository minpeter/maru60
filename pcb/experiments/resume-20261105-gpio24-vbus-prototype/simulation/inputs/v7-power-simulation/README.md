# V7 power simulation experiments

2026-11-04. These experiments identify voltage and timing risks in the current power architecture. They do not qualify the complete board, establish a safe USB current budget, or authorize enabling the LED qualification gate.

**The strongest result is the brownout mismatch:** the eFuse can remain on after the buck input has fallen below its specified operating range. The low-voltage/load sensitivity also leaves little regulation headroom. The plots make the assumptions visible rather than treating an ideal supply or a numerical result as a hardware pass.

## Source and reproducibility

Source PCB: `pcb/integration/v7-label-candidate/pcb/maru60.kicad_pcb`, from the V7 protection-layout work at commit `0cd022a`.

SHA-256: `3663aac96fb305eb4925fff938dd2db5862b880c6c262b2fa82707567a6e98f7`.

The source was read-only and its hash was checked before and after the runs. The frozen input audit is `inputs/electrical-review.json`. Later routing or circuit candidates need a new input comparison; these results do not silently transfer to a different board. No source CAD, BOM or firmware was edited by this simulation work.

Environment: Python 3, NumPy 2.2.4, Matplotlib 3.10.1, ngspice 44.2 shared library (`libngspice.so.0`). The runner invokes the shared-library API through ctypes; it does not require the ngspice executable. Each circuit runs in a fresh process. Failed runs cannot reuse stale waveforms.

To rerun with the exact PCB available:

`python3 run_simulations.py --board /path/to/maru60.kicad_pcb`

To reproduce the frozen numerical experiments without CAD:

`python3 run_simulations.py --frozen-inputs`

The second command explicitly skips a fresh CAD check and reports that in `summary.json`. It does not establish that a different board has the same circuit. Run from an extracted copy because the script regenerates outputs in its own folder.

Outputs include 14 netlists, their ngspice logs and raw waveforms, five PNG/SVG plots, CSV sweeps, and `summary.json`. The fixed-input scripts and netlists are inspectable and editable. There is no hidden simulation service.

## What actually ran

| Analysis | Method | Cases | Interpretation |
|---|---|---:|---|
| RC positive control | Native SPICE R and C | 1 | Confirms the runner against an analytic response |
| UVLO and OVLO hysteresis | Native SPICE switches and actual dividers | 1 | Explicit behavioral comparator model, not the eFuse macro-model |
| Load and unload charge deficit | Native SPICE current sources, ESR and capacitor | 6 | Passive sensitivity before any regulator correction |
| Abrupt input recovery | Native SPICE RLC network | 6 | Sensitivity to assumed line inductance and an abrupt input edge |
| Startup sequence envelope | Datasheet equations | 5,001 time samples | Ideal timing envelope, not coupled startup simulation |
| DC headroom and input power | Numerical constant-power solution | Three maps and 27 CSV examples | Simplified loss and efficiency assumptions |
| Ideal CCM ripple and LC frequency | Numerical equations | 54 corners | Not closed-loop stability, PFM or measured ripple |

The RC control's maximum absolute error is 3.04 microvolts versus its analytic response. The four behavioral protection transitions match the intended divider thresholds within 2 mV. Charge-deficit endpoints match the analytic capacitor relation within 1 mV. These checks test the implemented models, not their completeness as representations of the board.

## 1 Protection and brownout

Figure: `plots/01_protection_hysteresis.png`.

Actual divider values are 620 kΩ / 267 kΩ for UVLO and 590 kΩ / 156 kΩ for OVLO. A 0 to 6.5 to 0 V ramp, nominal comparator thresholds and a 33 Ω test load produce these transitions:

- UVLO turn-on: approximately 3.987 V.
- OVLO turn-off: approximately 5.739 V.
- OVLO recovery: approximately 5.212 V.
- UVLO turn-off: approximately 3.621 V.

Independent threshold, 0.1% resistor and leakage corners from the source audit widen UVLO turn-on to 3.863–4.131 V and turn-off to 3.508–3.775 V. These are voltages at VBUS_FUSED. The downstream buck input is lower after losses. U18's specified input floor is 3.8 V, and a lossless 98% duty approximation requires 4.082 V to produce 4 V. Thus the protection threshold is not a regulation guarantee.

The behavioral circuit intentionally excludes eFuse slew control, delay, current limit, reverse blocking, thermal behavior and shutdown state. Its two ideal switches reproduce static hysteresis only. Comparator data and slew equation: [TI TPS25947 datasheet](https://www.ti.com/lit/ds/symlink/tps25947.pdf). Buck input, duty and soft-start data: [TI TPS62932 datasheet](https://www.ti.com/lit/ds/symlink/tps62932.pdf).

**Next decision:** specify allowable local rail minima and startup input conditions, then coordinate undervoltage shutdown, reset and load shedding. Changing the UVLO divider alone trades off startup availability and cannot be selected from this plot alone.

## 2 Output capacitance and transient sensitivity

Figure: `plots/02_capacitor_transient_envelope.png`.

A ±200 mA load step is applied while regulator current is deliberately held unchanged for 50 microseconds. ESR is assumed to be 20 mΩ. Effective capacitance is swept through 8 microfarads as a stress case, 24 microfarads as the existing unqualified effective-capacitance target, and 44 microfarads as the printed nominal total of C140/C141.

The simulated 50-microsecond voltage changes are approximately ±1.254 V, ±0.421 V and ±0.231 V respectively. The relation is ΔV = ΔI × Δt / C + ΔI × ESR. The load step is an experiment, not a measured keyboard load waveform.

**These are not predictions of the actual buck's overshoot or droop.** The real control loop responds during the event. The curves show why exact capacitor selection, DC-bias derating and transient response must be resolved. They do not prove that 24 microfarads is insufficient or 44 microfarads is sufficient. The 3.7 V line is the selected LED revision's supply minimum, not a complete regulator acceptance criterion. [Manufacturer-authored SK6805-EC15-001 A/1 datasheet hosted by LCSC](https://atta.szlcsc.com/upload/public/pdf/source/20260416/5D0010F4880A3599CA8BBF773AF1A095.pdf).

## 3 Abrupt recovery and input inductance

Figure: `plots/03_input_recovery_sensitivity.png`.

The experiment applies a 5 V transition in 100 ns to a passive network. Series resistance is 0.3583 Ω: 0.132 Ω fuse, 0.0283 Ω eFuse and 0.1980 Ω modeled protected-feed copper. Input capacitance is 2 or 4.7 microfarads, ESR is assumed 20 mΩ, and unextracted line inductance is swept over 0.1, 0.5 and 1 microhenry. A 33 Ω resistor represents the test load; it is not a constant-power buck input.

At 2 microfarads, peaks are 4.981, 6.287 and 6.948 V. At 4.7 microfarads, they are 4.946, 5.470 and 6.128 V.

**These peaks are hypothetical sensitivity results, not predicted PCB voltages or ESD results.** Normal eFuse startup is slew limited and is not represented by this fast edge. Neither line inductance nor ESR was extracted or measured. The fuse's published 0.132 Ω is typical at 25°C and low test current, with ±25% tolerance; this experiment uses the nominal value, not a worst-case bound. [Bourns SF-1206F datasheet](https://www.bourns.com/docs/product-datasheets/sf-1206f.pdf).

**Next measurement:** capture the actual buck-pin input during allowed supply disturbances and disconnect/reconnect conditions, using a short ground connection and appropriate probe bandwidth. Replace the assumed RLC values with measured or extracted values before using this experiment to size damping.

## 4 Startup envelope and LED readiness

Figure: `plots/04_startup_timing_envelope.png`.

For the selected 10 nF eFuse slew capacitor, the typical equation gives 0.2 V/ms and a 25 ms rise to 5 V. With a nominal 3.6 V internal buck startup threshold and a 100 nF soft-start capacitor, the illustrative buck ramp starts at 18 ms and has a 14.55 ms soft-start interval. Its ideal 4 V endpoint is 32.55 ms after the input first becomes valid.

The plotted 3.3 V trace is only `min(3.3 V, max(0, V4V − 0.1 V))`, an assumed headroom ceiling. It is **not** the LDO's simulated startup waveform. Turn-on delays, load charging, current limit, loop dynamics, MCU boot load and reset timing are excluded. [MAX38902A family datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX38902A-MAX38902D.pdf).

U7's LED rail is separate from this startup envelope. Its official TPS2553-1 model did not execute in the current simulator. The board has 12.5 microfarads nominal on that rail and no direct rail-ready sensor. The datasheet's 3 ms maximum turn-on time refers to 90% with 1 microfarad and 100 Ω, so it cannot establish readiness of this rail. At 4 V, 90% is only 3.6 V. [TI TPS2553-1 datasheet](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf).

The separate firmware experiment must retain qualification OFF. A measured settling-time contract can guard startup; it cannot detect arbitrary analog collapse. Measure the farthest LED supply and first data edge during cold start, brownout, residual-charge restart, fault and USB suspend/deconfiguration.

## 5 DC headroom and current conversion

Figure: `plots/05_dc_headroom_map.png`. Examples: `dc_sweep.csv`.

The maps sweep upstream supply voltage from 4.0 to 5.5 V, total 4 V-domain current from 50 to 600 mA, and assumed cable/source resistance of 0, 0.5 and 1 Ω. The downstream current includes LED, LDO input and other 4 V loads. The sweep intentionally includes overstress cases; they are not permitted loads.

Assumptions: 90% conversion efficiency; 98% duty; 76 mΩ high-side switch resistance; 44.1 mΩ inductor DCR; nominal fuse/eFuse/feed losses above. The efficiency, duty and switch resistance do not constitute worst-case guarantees. Copper return, vias, connector contacts, temperature and dynamic losses remain unbounded.

The input current solves `Iin × (Vs − Iin × R) × efficiency = 4 V × Iout`. Dropout headroom is approximated as `0.98 × VIN_local − Iout × (RHS + RL) − 4 V`. This approximation does not model actual dropout control. Positive headroom is not a pass, especially if current limit or UVLO is exceeded.

At 4.4 V upstream, 300 mA output and 0.5 Ω cable/source resistance, the solution is 323.4 mA input, 4.122 V local buck input and only +3.9 mV modeled headroom. Without the added 0.5 Ω, the same case has +166.8 mV. Component tolerances can dominate this difference.

Purple and red contours mark nominal-setting eFuse current-limit extrema of 0.425 and 0.575 A. They are not a USB negotiation or compliance model. **Do not subtract a 4 V LED current directly from a 5 V USB current allowance.** Convert power and include all other loads.

## 6 Ripple and stability coverage

`ripple_corners.csv` contains 54 ideal CCM combinations of input voltage, ±20% inductance, a 450–550 kHz frequency sweep and 24/44 microfarads output capacitance. Inductor ripple spans 0.117–0.645 A peak-to-peak; ideal capacitive voltage ripple spans 0.606–7.462 mV peak-to-peak. The natural LC frequency spans 10.1–16.8 kHz.

These are equation-based sensitivities. They exclude capacitor ESR/ESL, light-load PFM, spread spectrum, control-loop response, current-limit interaction and layout. LC natural frequency is **not** crossover frequency, phase margin or evidence of stability. No Bode plot or closed-loop stability claim is made.

## Official model availability and failures

Original vendor ZIPs and extracted libraries are retained unchanged with hashes in `vendor/model-status.json`.

- [TI TPS62932 SLUM808](https://www.ti.com/lit/zip/SLUM808): unencrypted PSpice 17.4 model. The attempted netlist is `tps62932_startup.cir`; `startup_original/ngspice.log` records failure because the installed ngspice lacks the needed XSPICE switch model. No vendor-model waveform was produced.
- [TI TPS2553-1 SLVM426A](https://www.ti.com/lit/zip/SLVM426): unencrypted PSpice 16.2 model. `tps2553_startup.cir` and `led_vendor_original/ngspice.log` record the same compatibility failure. No waveform was produced.
- [TI TPS25947 SLVMDJ6](https://www.ti.com/lit/zip/SLVMDJ6): encrypted PSpice library. It was not decrypted, altered or executed in ngspice.
- [ADI MAX38902A product page](https://www.analog.com/en/products/MAX38902A.html): lists a MAX38902B LTspice model. The different variant was not silently substituted for the selected A part.

A supported vendor simulator or a separately validated model port is needed before claiming coupled controller simulations. Even successful vendor models require comparison to hardware and their own documented limitations.

## Remaining coverage and acceptance work

1. Close and revalidate the source-bound C128 ground and U10 DP routing opens before a hardware release. The audit's counts apply to the cited candidate, not a later routing experiment.
2. Freeze exact capacitor MPNs and effective capacitance versus voltage, tolerance and temperature. Measure or extract supply/return impedance and cable resistance.
3. Run the exact regulator, eFuse and LED-switch models in a supported simulator, including cold start, slow ramps, brownout recovery, short circuit, overload and load release. Keep model provenance and failure logs.
4. Measure local input, 4 V, farthest LED rail, 3.3 V, EN, /FAULT, isolation and data timing together. Establish acceptance limits from every receiver's selected datasheet and the intended USB power contract.
5. Test transient load profiles representing actual firmware, brightness limits, MCU activity and external loads. Confirm reset/isolation behavior through supply collapse rather than relying on the LED fault signal as power good.
6. Perform thermal and component-rating checks using real copper, assembly, ambient and measured losses. This packet does not calculate junction temperatures or certify fuse/current-limit coordination.
7. USB signal integrity, ESD/TVS clamping, MCU pin electrical behavior, flash timing, oscillator startup, EMI, EMC and manufacturing tests are outside this power packet. An ideal power plot does not establish any of them.

All qualification and manufacturing release gates remain unchanged. The packet is an engineering experiment with reproducible evidence and explicitly incomplete coverage.
