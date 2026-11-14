# Routed-copper DC model

`results.json` is the corrected final-board result; `provenance.json` binds its
board, geometry and tool. At 60 °C the maximum modeled LED drop is 26.86 mV for
234 mA uniform loading and 28.55 mV for the recorded concentrated loading.
The U8→U18 path drops 123.89 mV at 0.5 A / 20 °C; U2→U1.49 drops 78.49 mV
at 0.15 A / 20 °C. These are assumed loads, not measured operating currents.

The earlier output in `rejected-results.json.gz` is **invalid evidence**: it
contained huge finite voltages at LED30 for 20 °C and inconsistent temperature
scaling. It is retained only to document the correction. The previous extractor
missed overlapping track end caps, overwrote alternative same-number pad sites,
and dropped colocated loads in a dictionary. A weak diagonal ground tie hid a
disconnected loaded graph component instead of reporting an error.

The corrected graph accepts positive same-net copper cap/land overlap, selects
alternative LED pads by position, sums each physical load and explicitly rejects
loaded components without a source path. Unloaded floating copper is excluded;
the solve checks finite values and its current residual. Tests cover those
cases, real gaps and the expected copper-temperature scaling.

Pads, overlapping contacts and filled islands are equipotential approximations;
via plating is assumed, and the return-plane resistance is not independently
solved. This is not a field-solved power-integrity model, active-regulator
transient analysis, thermal qualification or hardware bring-up result.
