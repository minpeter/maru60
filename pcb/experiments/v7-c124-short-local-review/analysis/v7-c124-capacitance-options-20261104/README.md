# C124 capacitance alternatives: analytical screen, not a BOM change

Source: exact selected V7 board `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1`, recovered independently. The calculation also binds the freshly exported netlist by SHA-256. No CAD, BOM or selected source was changed.

## Finding

A smaller capacitor is a genuine alternative worth testing, but **8.2 nF ±10% is not a robust way to stay below 10 nF**. Combining its initial tolerance with an X7R +15% temperature corner gives 10.373 nF. A tighter 8.2 nF ±5% part reaches 9.9015 nF under those two factors, leaving only 98.5 pF of margin. A 6.8 nF ±10% part reaches 8.602 nF, with more margin but a faster startup ramp. These are not combined all-condition manufacturer bounds: bias, aging, measurement and reflow conditions remain to be established.

The selected C124 is recorded only as `10nF 10% 50V`, with no exact MPN or dielectric. Treating its temperature behavior as X7R is an explicit sensitivity assumption, not an established BOM fact.

## Compared options

| Option | Initial + assumed X7R range, nF | Nominal 5 V ramp, ms | Nominal cap-only inrush into 5.8 µF, mA | Change versus 10 nF |
|---|---:|---:|---:|---:|
| Existing 10 nF ±10%, direct | 7.650–12.650 | 25.0 | 1.160 | baseline |
| Same 10 nF plus 100 Ω | 7.650–12.650 | 25.0 | 1.160 | same first-order ramp |
| 8.2 nF ±10%, counterexample | 6.273–10.373 | 20.5 | 1.415 | +21.95% slew/inrush |
| YAGEO CC0402JRX7R9BB822, 8.2 nF ±5% | 6.6215–9.9015 | 20.5 | 1.415 | +21.95% slew/inrush |
| TDK C1005X7R1H682K050BA, 6.8 nF ±10% | 5.202–8.602 | 17.0 | 1.706 | +47.06% slew/inrush |

Calculated from the manufacturer's design approximation, SR[V/ms] = 2/C[nF], with Icap[mA] = Cload[µF] × SR. This is not a guaranteed output timing model. The 100 Ω case deliberately uses the same first-order approximation; it does not simulate the active controller or prove equal actual waveforms.

For 100 Ω ±1% and the assumed 12.65 nF upper corner, RC is at most 1.27765 µs. At the specified maximum 3.82 µA dVdt pin charging current, the resistor drop is 0.38582 mV. Neither value is the output startup delay. The separately tabulated C/I pin-charge times likewise cannot be substituted for the controller's output-slew relationship.

## Source circuit and what the simple load excludes

Fresh netlist assertions confirm USB_DVDT contains only U8.7 and C124.1. VBUS_PROTECTED_RAW directly connects C126 1 µF, C136 100 nF, and C137 4.7 µF (`effective>=2uF TBD`), totaling 5.8 µF nominal. That sum is neither guaranteed effective capacitance nor total dynamic load. U18 VIN is on this rail and its EN is intentionally floating; the active buck, downstream startup, source resistance, current limiting and thermal behavior are not included. Therefore the milliamperes above must not be presented as total board startup current or USB compliance.

The 1,200-row sensitivity table varies initial tolerance, ±15% temperature factors, hypothetical remaining-capacitance factors 1/0.90/0.75/0.50, five constant capacitive loads and three supply voltages. The extra remaining-capacitance factors are **assumed sensitivity cases**, not manufacturer-guaranteed bounds. All rows are crosschecked using a separate SI-unit formulation.

## Actual proposed components

The selected C124 uses a **0603 footprint**, whereas both initially screened parts below are **0402**. Neither is a drop-in selection. A same-size 0603 C0G alternative is being investigated separately; do not assume the existing pads suit a different case size.

- [YAGEO CC0402JRX7R9BB822](https://yageogroup.com/download/specsheet/CC0402JRX7R9BB822): 8.2 nF ±5%, 50 V, X7R, 0402. Nominal body 1.00 ×0.50 ×0.50 mm, each ±0.05 mm; termination B 0.25 ±0.10 mm. The spec sheet's simulation curves are typical, not guaranteed maxima. Selection and assembly compatibility have not been approved.
- [TDK C1005X7R1H682K050BA](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1005X7R1H682K050BA): 6.8 nF ±10%, 50 V, X7R, 0402; nominal body 1.00 ×0.50 ×0.50 mm, each ±0.05 mm. Consult its [series specification](https://product.tdk.com/system/files/dam/doc/product/capacitor/ceramic/mlcc/specification/mlccspec_commercial_general_midvoltage_en.pdf) and exact operating/measurement conditions before assigning effective bounds. The current product page marks this exact part Production (NRND); it is not recommended here for a new BOM. Recommended land dimensions and the actual existing footprint require a separate physical comparison.

## Manufacturer guidance and decision

[TI TPS25947 Rev C](https://www.ti.com/lit/ds/symlink/tps25947.pdf), §7.3.5.1, printed page 30, Eq. 4, recommends a 100 Ω series resistor for dVdt capacitance above 10 nF. Its design procedure uses the ramp and capacitive-inrush relationships. The data sheet gives dVdt charging current minimum/typical/maximum 0.81/2.21/3.82 µA; those limits alone do not bound actual output ramp with arbitrary parasitics and loads.

No option is selected. The resistor retains the nominal 10 nF ramp but requires a separately reviewed local routing/BOM change. Smaller capacitance may preserve the existing direct topology and avoid that routing disruption, but changes ramp/inrush and needs effective-capacitance and startup-contract validation. Neither option fixes the existing UVLO/buck headroom gap. Continue the short local resistor trial and the component/ramp investigation as distinct candidates; do not replace the BOM on this analytical screen alone.

Reproduce: `python3 calculate.py`. The source paths are relative to this study's sibling recovery repo. Results are numerical sensitivity, not active vendor SPICE, extracted PCB parasitics, bench verification, or production qualification.
