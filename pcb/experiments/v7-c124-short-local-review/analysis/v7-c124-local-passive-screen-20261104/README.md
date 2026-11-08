# Local C124/V4 passive sensitivity screen

**Unreviewed and unselected.** This is a new linear passive calculation bound to exact selected PCB 7c23 and the expanded V4 plan manifest. V4 was not constructed when these calculations were made. No CAD or BOM is modified. Circuit-controller behavior, routing parasitics and actual noise are not established by this model.

## What was calculated

Three explicitly hypothetical parasitic sets compare direct 10 nF, 100 Ω + 10 nF, and direct 8.2 nF. The 8.2 nF option changes nominal capacitance only: it uses the same assumed ESR/ESL as the other cases and does not model NP0 dielectric, bias, temperature or aging behavior. A two-node network includes pin-to-ground capacitance, link resistance/inductance and capacitor ESR/ESL. A coupled aggressor is applied separately at the pin-side or capacitor-side node. The same assumed parasitics are used for all three options, so differences isolate this abstract topology, not the actual old/new layout.

There are 18 AC cases and 10,818 points over 100 Hz–100 MHz. Each closed-form complex response is independently checked with a numerical two-node matrix solve and KCL residual. An additional 18 UVLO/OVLO RC sensitivity cases use the actual divider resistor values but assumed ground/coupling capacitances. No transient waveform, active vendor model or extracted field simulation is claimed.

## Interpretation

In the central hypothetical case, at 1 MHz, pin-side pickup from a 1 V aggressor gives approximately 0.00999 mV with direct 10 nF, 0.06389 mV with 100 Ω + 10 nF, and 0.01218 mV with direct 8.2 nF. At the capacitor-side injection, the two 10 nF options are both approximately 0.01000 mV. **These are not predicted board noise amplitudes or old/new placement ratios.** They show why a series resistor cannot be advertised as blanket noise reduction and why the sensitive pin-side route deserves attention. The resistor's manufacturer-recommended active-controller purpose is outside this passive model.

Actual USB_UVLO is 620 kΩ/267 kΩ and USB_OVLO is 590 kΩ/156 kΩ. Their topology is unchanged by V4, but the proposed sense routes are longer. The divider calculation assumes an ideal AC-grounded upstream supply and ideal ground return; supply noise, source impedance and shared ground are absent. The calculation does not turn those lengths into a capacitance or coupling claim. Increasing assumed shunt capacitance reduces the high-frequency coupling ratio but lengthens the RC decay time. Actual pin filtering, thresholds, clamps, transient susceptibility and source/return impedance remain unmodeled.

`results.json` specifies every hypothetical parasitic and numerical crosscheck. `ac-sweep.csv` contains the complete AC output; `passive-comparison.png` is an illustrative central-case plot. `calculate.py` reproduces it using installed NumPy/Matplotlib, without a SPICE installation. The label 'low/central/high' names three chosen scenarios, not physical minimum, typical or worst-case bounds.

Do not use this report to adopt V4. Actual constructed-board topology, contacts, clearance, all-net/reference preservation, independent review and an appropriately bounded circuit/assembly assessment remain required. Physical startup, UVLO/OVLO response, SI/PDN/EMC and production qualification remain false.
