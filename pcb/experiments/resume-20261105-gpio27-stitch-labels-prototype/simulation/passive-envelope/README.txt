Current-nameplate-informed passive sensitivity, not an active stability test

The exact frozen PCB56d66f65 has four directly grounded capacitors on +4V_REG: C1004.7uF, C1201uF, C14022uF and C14122uF, nominal sum49.7uF. Native values and pad nets are recorded in RESULTS.json. The 44uF historical example omitted the first two parts. This new set uses all four nominal values as the basis of an explicitly synthetic lumped charge-balance bench.

Eighteen cases combine 100%,50%,20% effective-capacitance assumptions,10/50/100us fixed-regulator-current holds, and0.2A load application/release. Initial4V, aggregate20mohm ESR and10ns ramp are assumptions, not measured/extracted parameters. The fractions are illustrative sensitivities, NOT known physical bounds or probabilities.

All18 shared-ngspice runs completed with finite waveforms and exact requested end times; analytical finite-ramp endpoint checks differ by less than10uV. Under the50us/0.2A load example, output is3.794813V at the49.7uF nominal basis,3.593625V at50%, and2.990063V at20%. This illustrates why nominal capacitance alone is insufficient. It does not predict these voltages on the hardware. Unload cases are also deliberately unclamped, fixed-current envelopes, not buck-regulator predictions.

No pass/fail operating voltage is asserted. Missing active control/current limiting, effective C vs bias/temperature/aging, ESR/ESL, layout parasitics, eFuse states, and real loads prevent startup, fault, brownout, pulse, thermal or stability qualification. The official active-model compatibility gap remains. No CAD or part value was changed.

build_and_run.py, cases/,runs/ and RESULTS.json preserve reproducible inputs, outputs, analytic checks and source hashes. Existing ngspice shared library was used without installing anything. Runtime inventory confirmed no installed XSPICE .cm modules under /usr/lib; the prior missing-model result was not bypassed.
