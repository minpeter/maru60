# C124 selected-versus-D adoption risk

**Recommendation:** retain D as the preferred, explicitly unqualified candidate for the next prototype comparison. It adds TI's recommended 100 Ω series value as a conservative response to the 10 nF ±10% tolerance range, and gives the changed parts documented identities. Do not treat it as an electrically qualified replacement or silently promote it from passive-model/DRC success. A prototype choice and production/electrical acceptance are separate decisions.

## 1. What is actually being compared

Selected **c770** has direct C124, 10 nF ±10%, 50 V, generic 0603, and R121, 156 kΩ ±0.1%, generic 0603. Fresh native inspection confirms that **neither has an exact manufacturer/MPN; R120 also has none**. Their datasheet fields are empty. No baseline power, TCR, dielectric, humidity, pulse or lifetime guarantee can be invented from footprint size.

Unselected **D f987** changes C124 to YAGEO CC0402KRX7R9BB103 0402 X7R, adds KOA RK73H1ETTP1000F 100 Ω ±1% in series, and uses KOA RN73R1ETTP1563B25 0402 for the same 156 kΩ ±0.1% R121. The latter has a documented ±25 ppm/K class. **TNPW0603156KBEEA was only an earlier unselected V4/C proposal**, not a qualified selected-board part. Therefore RN73R-versus-TNPW specification differences are a proposal comparison, not a proven downgrade or equivalence to c770.

## 2. Electrical reason and unchanged quantities

[TI TPS25947 Rev C, section 7.3.5.1, p30](https://www.ti.com/lit/ds/symlink/tps25947.pdf) recommends a series 100 Ω resistor when actual CdVdt is **greater than 10 nF**. Nominal 10 nF alone does not mandate it. Its ±10% initial tolerance spans 9–11 nF, so some conforming capacitors can cross the boundary. D is a conservative, recommendation-aligned solution to that specific issue. It does not establish the actual effective capacitance under bias, temperature or aging, nor a guaranteed active startup result.

The OVLO divider remains 590 kΩ/156 kΩ, each ±0.1%. Consequently selected and D have **zero nominal DC loading or threshold change** from this divider substitution:

| Quantity | Selected and D, identically |
|---|---:|
| OVLO divider current at 5 / 5.25 / 5.5 V | 6.7024 / 7.0375 / 7.3727 µA |
| 5 V divider current, resistor tolerance only | 6.6957–6.7091 µA |
| Nominal OVLO rising / falling threshold | 5.73846 / 5.21244 V |
| Rising threshold, resistor tolerance only | 5.72939–5.74755 V |
| Divider Thevenin resistance | 123.378 kΩ |

Including the previously bounded IC reference and ±0.1 µA leakage terms gives the same 5.58929–5.91677 V rising interval for both, before environmental drift and layout effects. UVLO's 620 kΩ/267 kΩ divider is also unchanged. These 5–5.5 V examples are not an accepted input contract.

The series RC branch adds no ideal steady DC path through the capacitor. Its tolerance-only RC product is 0.891–1.111 µs, **not the eFuse output ramp or rail-ready time**. Actual charging, reset and leakage behavior remain outside that arithmetic.

## 3. Remaining risks and honest comparison

- **Brownout/startup:** D does not change UVLO thresholds, buck headroom, reset thresholds or load shedding. It therefore does not resolve the earlier brownout mismatch. The eFuse vendor model remains encrypted/unexecuted; the passive checks cannot test slew control, inrush, restart from residual charge, fault recovery or startup thermal stress.
- **Noise:** the matched hypothetical passive models still show increased pin-side pickup when series resistance is added. At 1 MHz in one chosen example, 0.009991 mV becomes 0.063887 mV per hypothetical 1 V aggressor; capacitor-side pickup is almost unchanged. These are not measured or extracted board-noise values. D's new route and support-copper geometry cannot be converted into coupling/impedance without further evidence.
- **R125 reset/pulse:** the [KOA RK73H](https://www.koaspeer.com/catimages/Products/RK73H/RK73H.pdf) 0402 part has a 0.1 W rating, giving approximately 3.162 V nominal continuous rated voltage at 100 Ω before derating. Its short overload test and unassured pulse curves do not qualify repeated dVdt resets. Actual capacitor voltage, discharge current, repetition and resistor temperature must be established; USB voltage is not automatically the resistor voltage.
- **R121 precision/lifetime:** [RN73R](https://www.koaspeer.com/pdfs/RN73R.pdf) standard 1000-hour endurance allows ±(0.1%R+0.05 Ω) at 85°C. The unselected [TNPW0603 proposal](https://www.vishay.com/docs/28758/tnpw_e3.pdf) general-mode limit is ±(0.05%R+0.01 Ω) at 70°C. Holding everything else fixed, those respective test allowances correspond to roughly ±4.54 mV and ±2.27 mV movement of the nominal rising threshold. Different conditions prevent a prediction of actual comparative drift. No selected-baseline lifetime bound exists.
- **Humidity/temperature:** RN73R's generic moisture allowance is 0.25% plus a fixed term and has an exact-value caveat; the TNPW proposal's cited humidity limit is 0.1% under different bias. Do not assume the generic KOA bound is confirmed at 156 kΩ or reuse TNPW's longer-life specifications. R120's unknown TCR/identity prevents a complete divider-tracking bound. No guaranteed numerical DC voltage coefficient was found. Low static dissipation does not remove these precision risks.
- **Abnormal input and assembly:** no accepted VBUS_FUSED operating/fault/transient maximum exists. The earlier 23 V resistor-only calculation is outside the IC's recommended OVLO pin range and is not a survival result. Exact part identities, smaller pads, derived courtyards and passing native checks do not establish assembly-process, mechanical-envelope or production qualification.

## 4. Decision and measurement gates

**For an engineering prototype choice:** first finish the separate actual D geometry/contact/reference/assembly-envelope review, and explicitly accept that D remains unqualified. Specify the allowed input/rail/load envelope and protection-threshold drift budget, including an actual R120 choice; do not approve a fictitious “equivalent TNPW replacement.” The generic selected baseline is also insufficiently specified, so retaining it is not proof of lower risk.

**Before electrical/production acceptance:** resolve exact-value environmental allowances and component/process requirements; then measure cold/hot start, residual-charge restart, input ramps/brownouts, disconnect/reconnect and fault/reset cycles at bounded loads. Observe U8 input/output and DVDT, buck input/4 V, 3.3 V, far LED rail and enable/reset/fault timing. Bound R125 peak/repetitive discharge stress and threshold movement over the intended conditions. A measured rail-ready contract is still required where firmware relies on settling.

This memo makes no CAD/BOM edits, new active simulation or adoption claim. The existing 36-case passive replay verifies equations, not these release conditions.

## Exact evidence

- Selected PCB: `c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a`.
- D PCB: `f987edb49e7eb99e6db711ea428a5efb66a36653fe9dce77b02aae12f281441b`.
- D construction contract: `15835e0f49534e7250626669db5645dccc80034a3cefd88651578731627d62bd`.
- D netlist: `05b0032974c95e00e7b563cd8ffadadbb6d72d51e266706f813609c08ca01b6d`.
- Sealed nominal/passive packet: `d763ad67082493ef71399513d1665029f8e2ecbe3421b951d056426674005cb5`.
- Sealed R121 catalog/stress review: `10707d6de860893463a6c474e3eb701a35e95b531daddb14a562651d39bf78d6`.

The included `calculate_deltas.py` reproduces the small static and published-drift-limit calculations. Independent rationale review is included separately. No baseline ratings were inferred from either unselected proposal.
