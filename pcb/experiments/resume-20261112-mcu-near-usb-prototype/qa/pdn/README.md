# PDN analysis evidence

`results.json` and `report.log` contain the copper-resistance model for the 25-open checkpoint.

- VBUS from U8 to U18: **250.34 mΩ at 20 °C**, or 125.17 mV at 0.5 A. The original 2U candidate's same path was 234.67 mΩ, so the limited-In2 route has similar DC resistance rather than an order-of-magnitude regression.
- Both inner GND pours remain single islands after the 34 In2 segments.
- The 60 °C LED-rail maximum drop is 28.26 mV at the 234 mA limiter maximum, comparable to the source candidate.

Several +3V3 paths and one LED-rail branch are still open, so these are not final power-integrity or thermal results. The report is a DC copper model only: regulator stability, transient response, component heating, and hardware qualification remain separate. Recompute after the final route.
