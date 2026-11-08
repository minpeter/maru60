# Independent review of C124 D adoption rationale

Disposition: a bounded conservative adoption rationale is supportable; electrical qualification or blanket superiority is not. This review makes no CAD changes, simulations, or selection.

## Exact TI boundary

TPS25947 Rev C (SLVSFC9C, revised May 2026), section 7.3.5.1, p30, recommends a 100 ohm series resistor for CdVdt greater than 10 nF. It is a recommendation, not a mandatory assertion for nominal 10 nF. The exact D C124 is YAGEO CC0402KRX7R9BB103, 10 nF ±10%, 50 V X7R. Initial tolerance alone spans 9–11 nF at its applicable measurement conditions, including values above 10 nF. This makes accommodating the upper tolerance side a defensible conservative motivation for R125=100 ohm, not proof that every capacitor exceeds 10 nF. Temperature, DC bias, aging and frequency-dependent behavior are not captured by that initial tolerance interval. Exact operating effective capacitance is not established.

TI's statement alone does not establish guaranteed stability, universal noise suppression, reset-pulse survival, startup timing, or functional equivalence of the added network. 100 ohm × 10 nF = 1 microsecond is only a nominal passive product, not rail rise/ready time.

## Selected baseline versus proposals

Selected c770 R121 is generic 0603, 156 kohm ±0.1%, with no exact MPN and an empty datasheet field (parent's verified selected-baseline finding). TNPW0603156KBEEA belonged to an unselected V4/C proposal. D actually uses KOA RN73R1ETTP1563B25, 0402, 156 kohm ±0.1%, ±25 ppm/K.

Consequently, the reviewed KOA/Vishay endurance and humidity differences are comparisons with that earlier proposal only. They do not establish degradation, improvement or stability equivalence against the selected c770 baseline, whose manufacturer-specific properties are unknown. Nominal 156 kohm and ±0.1% equality are established; baseline TCR equality is not. The sealed R121 review's phrase 'same ... TCR class' must retain its proposal-comparison context and must not be reused as a claim about selected c770. Different test conditions also prevent treating datasheet allowances as measured drift comparisons at actual circuit dissipation.

## Evidence and limits that adoption must retain

- The actual-D passive-binding packet establishes nominal connectivity and matching model class, not actual extracted parasitics or active TPS259470LRPW behavior.
- The old-versus-D passive calculation is not actual-board noise prediction. At its central assumed 1 MHz pin-side injection example, series 100 ohm increases modeled pickup versus direct 10 nF; there is no universal noise-improvement claim. Capacitor-side results are injection-path dependent.
- Active startup/inrush/rail-ready timing, brownout recovery, discharge and repeated-enable behavior remain unqualified. A passive AC replay cannot close them.
- R125 0402 reset/pulse energy, repetition and thermal limits remain unqualified. Nominal power or RC arithmetic cannot replace this.
- Divider drift, exact-value KOA humidity caveat, R120 MPN/TCR and thermal tracking, contamination leakage, and required voltage-coefficient bounds remain open. Low static resistor stress does not settle these.
- There is no approved VBUS_FUSED input-fault/transient maximum. The 5/5.25/5.5 V stress examples are examples, and the 23 V divider diagnostic is not an operating or fault-survival authorization.
- Actual footprint/land suitability, maximum-body/termination and placement envelopes, solder/paste/mask/process margins, contamination/ESD handling, rooted returns, support/contact dispositions, corrected physical-contact/reference/fill/DRC checks and manufacturing assembly review remain necessary. Nominal clearance alone is not assembly approval.
- No startup, brownout, reverse-input, ESD, EMC, production or measured-hardware qualification is created. Any selection must be separately authorized and described as a bounded design choice with these limits intact.

## Sources reviewed

- /workspace/scratch/edd9a5be63e7/v7-r121-0402-bom-review-20261104/REVIEW.md
- /workspace/scratch/edd9a5be63e7/v7-c124-d-passive-binding-20261104/REPORT.md
- /tmp/v7-r121-0402-review/TPS25947_revC.txt (note at line 2104)
- Parent's exact selected-baseline identity finding in task handoff; this review did not independently reopen selected c770 CAD.
