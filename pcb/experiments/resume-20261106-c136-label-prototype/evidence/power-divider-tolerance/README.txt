CURRENT-NOMINAL DIVIDER TOLERANCE SUPPLEMENT

This is a static arithmetic sensitivity, not a new active circuit simulation. Four present PCB values and both pad nets were freshly checked: R122 620k / R123 267k for UVLO and R120 590k / R121 156k for OVLO, each marked 0.1%. All sixteen independent resistor tolerance corners were calculated as exact rational numbers. Monotonic closed-form extrema independently confirm the corner bounds.

The upper/lower comparator thresholds are fixed at 1.200 V / 1.090 V, taken from the already saved idealized hysteresis deck. They are assumptions for this calculation, NOT measured or guaranteed TPS259470 thresholds. Under those assumptions only:
- UV enable: 3.980949 to 3.992095 V, nominal 3.986517 V.
- UV disable: 3.616029 to 3.626153 V, nominal 3.621086 V.
- OV disable: 5.729394 to 5.747548 V, nominal 5.738462 V.
- OV re-enable: 5.204199 to 5.220689 V, nominal 5.212436 V.

The resistor-only corners do not remove the model's headroom concern: every modeled UV enable value is below the synthetic 4 V regulated target, and the modeled UV disable values are lower still. This does not prove an actual brownout or specify a safe operating range. A buck rail's usable input headroom, U8 real threshold behavior and downstream reset/power policy must be evaluated together with supported active models and measurements. No threshold or component was changed to make the model look safer.

RESULT.json records the exact source PCB/deck hashes, parts, all corners and limitations. analyze.py reproduces the arithmetic using the installed native PCB reader. The delivered analyze.py resolves the checkpoint CAD and the copied original behavioral deck using relative paths. No install, vendor-model modification, active-loop qualification or hardware claim occurred.
