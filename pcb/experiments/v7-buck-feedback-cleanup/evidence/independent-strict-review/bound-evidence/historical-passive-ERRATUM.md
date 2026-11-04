# Correction to the earlier TPS62932 leakage description

The earlier power audit incorrectly described FB leakage as **“0.15 µA typical, no stated bound.”** In the official TPS62932-family datasheet SLUSEA4D, §8.5, page 6, **0.15 µA is in the MAX column**, at the specified VFB=0.8 V test condition. The visual column check is saved as `research/tps62932-page6.png`.

This correction supersedes that wording in:
- `v7-power-audit-20261104/audit.py` and `electrical-review.json`
- The copied `simulation/inputs/electrical-review.json`
- `v7-power-corrections-20261104/inputs/electrical-review.json`

Previously sealed artifacts have not been silently rewritten. Their intervals explicitly titled “reference plus resistors only” excluded FB leakage, so those particular calculations remain what their labels say. They must not be reinterpreted as total regulation bounds.

For Rtop=40.0 kΩ, a positive sink current of 0.15 µA into FB would require +6.000 mV output correction in an ideal slow regulating loop. At Rtop+0.1%, the term is +6.006 mV. The table does not specify a signed minimum; this is **not permission to invent a guaranteed ±0.15 µA interval**. It is also not a total output-accuracy, dropout, transient or startup qualification.

Source: [TI TPS62932 family datasheet](https://www.ti.com/lit/ds/symlink/tps62932.pdf), SHA256 `16ec2eac43c7374eb9e7edd7df7bdb24de6862f695e1582c68716ced4820e5f6`.

To avoid repeating the error, future parameter extraction should visually verify MIN/TYP/MAX column placement before classifying a numerical specification. This correction is also recorded in the new simulation summary and was sent to the coordinating review.
