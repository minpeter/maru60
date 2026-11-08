# C124 official-manufacturer fact audit

Checked 2026-11-04. Read-only source audit; no study, CAD, or BOM edits.

## Findings

1. **TI citation correction:** The linked current TPS25947 data sheet is SLVSFC9C, revised May 2026. Slew-rate control appears in **section 7.3.5.1**, printed pages 29–30, not section 9.3.3. Equation 4 on printed page 30 gives C_dVdt[pF] = 2000 / SR[V/ms], equivalently SR[V/ms] = 2 / C_dVdt[nF]. The same page recommends a 100-ohm resistor in series with the dVdt capacitor for C_dVdt > 10 nF. This is a recommendation, not a stated absolute-maximum capacitance or a categorical prohibition at 10 nF.
   - Source: https://www.ti.com/lit/ds/symlink/tps25947.pdf
   - Section 6.5, printed page 11, lists dVdt charging current min/typ/max = 0.81 / 2.21 / 3.82 microamps. Listed default conditions include -40°C <= Tj <= 125°C and Vin = 12 V. Do not silently substitute these pin-current limits into Equation 4 as guaranteed output-slew limits: the equation's coefficient and tabulated typical current are different, and a verified transfer relationship is needed.

2. **YAGEO CC0402JRX7R9BB822:** The manufacturer part sheet confirms 8,200 pF (8.2 nF), 5% tolerance, 50 VDC, X7R, 0402 / 1005, and -55°C to +125°C. Body L/W/T are 1.00/0.50/0.50 mm, respectively, each ±0.05 mm. Thus describing this exact part as ±10% would be an error. Terminal dimension B is 0.25 ±0.10 mm. The sheet's simulation graphs are expressly non-specification material; they do not establish guaranteed bounds.
   - Source: https://yageogroup.com/download/specsheet/CC0402JRX7R9BB822
   - Verified fields are on its first page; simulation caveats are on its last page.

3. **TDK C1005X7R1H682K050BA:** The manufacturer page confirms 6.8 nF ±10%, 50 VDC, X7R (±15%), EIA 0402, -55°C to +125°C, and body L/W/T 1.00/0.50/0.50 mm, respectively, each ±0.05 mm. It is commercial grade, not AEC-Q200, and its official lifecycle status is **Production (NRND)**. Treat it as an analytical candidate, not an unqualified new-design recommendation. Matching body dimensions do not prove identical terminations or land-pattern compatibility. The product page provides distinct terminal and recommended-land-pattern values.
   - Source: https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1005X7R1H682K050BA

4. **Qualification of the 10.373 nF calculation:** 8.2 × 1.10 × 1.15 = 10.373 nF is correct arithmetic for the assumed +10% initial tolerance and +15% thermal-change corner. Call it a **conditional tolerance/temperature screening envelope** or sensitivity case, not a manufacturer-guaranteed all-condition effective-capacitance bound. Under appropriate shared specification/test conditions, combining applicable guaranteed initial and thermal limits can yield a valid conditional envelope; therefore avoid implying that multiplying such limits is inherently invalid. The missing step is showing applicability to the exact part and actual operating conditions.
   - For the named ±5% YAGEO part, the analogous simplified calculation is 8.2 × 1.05 × 1.15 = 9.9015 nF.
   - For the ±10% TDK part, it is 6.8 × 1.10 × 1.15 = 8.602 nF.
   - These calculations alone neither guarantee compliance with TI's guidance in the real circuit nor establish actual startup time. Applicable measurement conditions, bias dependence, aging/reflow history, other component variation, and circuit behavior require qualification.

5. **Manufacturer evidence for qualification:** TDK's specification, linked from that exact product page, defines Class-2 temperature-capacitance change relative to the reference-temperature measurement with no applied voltage. X7R's reference temperature is 25°C, with ±15% change over -55°C to +125°C. It also discusses capacitance aging and the need to evaluate Class-2 capacitors in timing applications. These are condition-specific specifications, not a blanket promise that effective capacitance is always nominal × tolerance × thermal factor.
   - Source: https://product.tdk.com/system/files/dam/doc/product/capacitor/ceramic/mlcc/specification/mlccspec_commercial_general_midvoltage_en.pdf
   - Printed pages 5 and 7: temperature/reference/test conditions. Printed page 30: capacitance-aging caution.

## Audit limits

This audit did not verify stock, procurement suitability, the actual C124 footprint/pads, dVdt operating bias, assembled-board behavior, or the circuit's timing/current margins. All conclusions above are source facts or explicitly identified analytical qualifications.
