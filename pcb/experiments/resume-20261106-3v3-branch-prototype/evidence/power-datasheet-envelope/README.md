# Datasheet-bound static power supplement

The four current nominal divider values, 0.1% markings and their pin nets were checked against native PCB88fbac1d and the unchanged schematic netlist. U8 remains TPS259470LRPW. Neither CAD nor component choices changed.

The [TI TPS25947 Rev C electrical table, pp8–9](https://www.ti.com/lit/ds/symlink/tps25947.pdf) gives rising thresholds1.183–1.223V, falling1.076–1.116V and each input's leakage±0.1µA. Using those limits, independent0.1% resistor corners, and no other node leakage gives these STATIC conditional envelopes at the divider's input:

- UV enable3.862615–4.130673V.
- UV disable3.507647–3.774711V.
- OV disable5.589286–5.916768V.
- OV re-enable5.078415–5.404278V.

All64 exact-rational corners pass an independent Thevenin-equation check. The earlier16-corner calculation remains a correctly limited resistor-only result; it is not the full tolerance envelope. At these large resistance values, pin leakage alone contributes about±62mV or±59mV at the input. Threshold uncertainty cannot be inferred from resistor precision alone.

These are not guaranteed observed board thresholds: the table's stated test conditions, unadopted resistor MPN/TCR/aging and unknown board leakage remain limitations. Switching delay, ramp rate, current limit, actual load, supply loss and dynamics are excluded. No active SPICE solve is claimed.

The [TPS62932 datasheet, pp1,26](https://www.ti.com/lit/ds/symlink/tps62932.pdf) specifies a3.8V minimum recommended input and describes dropout with up to98% duty operation. Some calculated U8 shutdown corners are below that input range, so U8's static threshold alone is not a buck operating-range guarantee.

Do not equate loss of4V regulation with immediate3V3 failure: the [MAX38902 Rev10 datasheet, pp4–5](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX38902A-MAX38902D.pdf) lists100mV maximum dropout at500mA/3.6V input, with dropout defined at95% of nominal output. Actual3V3 behavior still requires the complete input/load trajectory and regulator/reset dynamics.

No resistor was changed to hide the concern. Next qualification remains supported active startup/brownout/fault models plus measured supply/load and effective capacitor/part data. Links above were freshly checked on2026-11-05. RESULT.json binds exact sources and all arithmetic; analyze.py reproduces it using relative paths to the delivered CAD and netlist. No SI, hardware, fabrication or stability approval follows.
