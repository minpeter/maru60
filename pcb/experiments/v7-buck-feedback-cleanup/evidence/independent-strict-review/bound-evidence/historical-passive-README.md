# BUCK_FB warning: topology, noise sensitivity and correction options

Read-only review of accepted PCB SHA256 `8a4ff6a646396a3faa11dda0f756c89e82c20eec18f37fe531cf730789106eea`, 2026-11-04. No PCB, schematic, BOM, firmware or qualification flag was changed.

## Decision

The warned via is an electrically redundant dead-end object in the native feedback graph. **That does not prove the converter is unstable.** The smallest object change is removal of that via alone, but it leaves a bare-ended copper arm and may replace the via warning with a track-dangling warning. A more complete, still narrow candidate would also trim the **2.85 mm dead arm**, while retaining the **1.95 mm active portion** of the same track. Neither candidate has been implemented or accepted by this study.

**Do not delete the whole 4.80 mm track.** Its middle is the active feedback junction; removing the whole object disconnects U18 from both divider resistors. Do not add a capacitor or claim improved stability merely to silence the warning.

## Actual source topology

- U18: TPS62932DRLR, B.Cu, FB pin 8 at (180.0, 83.51).
- R159: 40.0 kΩ, 0.1%; upper divider, +4V_REG to BUCK_FB.
- R160: 10.0 kΩ, 0.1%; lower divider, BUCK_FB to GND.
- The three populated FB pads are connected in native KiCad connectivity. No discrete feedforward capacitor or test-point footprint is connected to FB.
- Via `d382de57-3476-43c4-ac26-0a72b21acf7c`, at (178.15, 85.75), has exactly one native contact: F.Cu track `2c0aa2c5-bec8-4dff-bff7-2e823d3e36fa`.
- That track runs from (178.15, 85.75) to (182.95, 85.75), width 0.15 mm, length 4.80 mm. The U18-side route joins at **(181.0, 85.75)** through track `3c804add-ee74-5104-b471-73062ffcaeb9`.
- Thus **2.85 mm extends toward the warned via**, while **1.95 mm continues toward the divider**. The designated U18-to-R159 centerline witness is approximately **5.518 mm**, excluding via barrels and pad/contact spreading. This is not an impedance or unique-current-path extraction.

`inputs/layout.json` and `extract_layout.py` reproduce the objects, exact contacts, branch split and graph controls. Removing only the degree-one via from the native graph preserves all three populated FB pads; deleting the full horizontal track leaves only the U18 pad reachable from U18. These are graph controls, not post-edit CAD/DRC validation. The source board hash was checked before and after reading.

The board has no explicit FB test-point footprint, but undocumented probe intent cannot be ruled out. Ground-plane shielding, shared ground impedance and coupling to SW/BST were **not** extracted. A two-dimensional copper projection cannot establish their electrical effects.

## Device guidance and a separate layout observation

[TI TPS62932-family datasheet, §12.1, page 40](https://www.ti.com/lit/ds/symlink/tps62932.pdf) recommends close divider placement, a separate output-sense connection, separation from switching copper and ground shielding. It also gives a device-specific **>10 mil feedback-trace recommendation for heat dissipation**. Existing FB copper is **0.15 mm, about 5.91 mil**. This is a layout-guideline deviation, not proof of thermal failure or instability. A wider, shorter or relocated route would require its own clearance, return-reference, parasitic and thermal review.

The same datasheet's feedforward discussion (§10.2.2.10, page 33) flags large upper-divider resistances, particularly above 100 kΩ, as susceptible to parasitic FB-pole effects. This board's 40 kΩ is below that cited region, but that is not a blanket stability guarantee. No numerical allowable FB-via-stub length or maximum parasitic capacitance was found.

## Conditional passive calculations and native simulations

The divider has **β=0.2**, **8 kΩ Thevenin resistance**, and **80 µA nominal divider current at 4 V**. These facts make the node more sensitive to injected current and capacitive pickup than a low-impedance power node. They do not quantify actual board noise.

The model contains only the two resistors and assumed capacitors. VOUT and GND are ideal stiff small-signal references. There is **no controller, inductor/output plant, nonlinear input clamp, extracted ground impedance, parasitic field model or actual SW waveform**. Consequently it cannot calculate full-loop crossover, phase margin, real output ripple, startup or hardware acceptance.

### FB shunt capacitance

For assumed total shunt capacitance Cp, the passive sense transfer is:

`H(s) = 0.2 / [1 + s × 8000 × Cp]`

| Assumed Cp | Passive pole | Passive phase at illustrative 50 kHz |
|---|---:|---:|
| 1 pF | 19.894 MHz | −0.144° |
| 5 pF | 3.979 MHz | −0.720° |
| 10 pF | 1.989 MHz | −1.440° |
| 20 pF | 0.995 MHz | −2.878° |
| 50 pF | 0.398 MHz | −7.162° |

These are total-capacitance scenarios, **not values assigned to this via or branch**. 50 kHz is not an established converter crossover; 500 kHz is the nominal switching selection, not the loop crossover. Passive phase shifts are not phase margins.

### Capacitive pickup can change in either direction

For coupling Cc from an aggressor and other shunt capacitance Cp:

`Hpickup(s) = s Cc / [1/8000 + s(Cp+Cc)]`

The native simulations use a smooth **1 V** aggressor transition with **10 ns 10–90% edges**, not a measured SW waveform. Results are normalized per volt and must not be extrapolated through large-signal clamps or controller response.

| Hypothetical change | Cp | Cc | Peak FB pickup per 1 V edge |
|---|---:|---:|---:|
| Reference example | 10 pF | 0.10 pF | 8.687 mV |
| Reduce shunt C only | 9.5 pF | 0.10 pF | 9.091 mV |
| Reduce shunt C and halve pickup | 9.5 pF | 0.05 pF | 4.567 mV |
| Halve shunt C only | 5 pF | 0.10 pF | 15.686 mV |

**Removing capacitance to ground alone can increase edge pickup.** Removing an unused branch may also reduce aggressor coupling, but neither reduction is known here. The table illustrates why geometry cleanup must not be advertised as a quantified noise improvement without extraction or measurement. These changes are not fitted predictions of either proposed CAD candidate.

### Feedforward is not FB-to-ground filtering

CFF belongs across R159, the upper resistor. The separate plot compares hypothetical 10 pF and 100 pF feedforward networks with an FB-to-ground capacitor. Their transfer functions differ materially. No value is selected: copying an example or adding shunt capacitance to quiet a warning could change the active loop. [TI feedforward optimization guidance](https://www.ti.com/lit/an/slva289/slva289.pdf) starts with the working converter's no-CFF loop behavior, which has not been established here.

## Proposed experiments, without CAD changes

1. **Via-only cleanup:** remove only d382de57. It removes the warning's degree-one object and associated pad/drill, while the 2.85 mm dead arm remains. A track-dangling warning may then appear, so warning-count improvement is not established. Refill and rerun full native connectivity, DRC/ERC, schematic parity, reference-shadow and unrelated-net regression checks. A clean result supports geometric cleanup only.
2. **Trim the dead arm and via:** replace only the 4.80 mm segment with a 0.15 mm F.Cu segment from **(181.0, 85.75) to (182.95, 85.75)**, remove the warned via, and preserve its existing right-side contacts. This is the smallest proposed branch-removal geometry, not an accepted edit. Apply the same full checks and examine any intended probe use.
3. **Separate feedback-layout experiment:** investigate a shorter/wider quiet connection, divider placement, VOUT sense origin and bottom-resistor ground reference. This changes active routing and is broader than warning cleanup. Do not silently combine it with the minimal candidate.
4. **Electrical verification:** identify biased capacitor models, source/load conditions and parasitics; use a validated compatible controller model or measured loop response and load transients. The earlier TPS62932 vendor model failed basic regulation controls in the available ngspice runtime, so it is not a valid closed-loop reference.

## Numerical checks and scope

- **13 native ngspice AC cases** are checked against closed-form passive transfer functions.
- **4 smooth pickup transient cases**, each repeated at 50 ps and 12.5 ps maximum timestep, agree in peak value within **0.00814 µV**.
- A separate KCL/RC differential-equation implementation, without importing the simulation code, matches all four waveforms within **0.0137 µV** at 10 ps input resolution. This is an independent algorithm, **not a second reviewer or validation of the physical model**.
- Source research was independently performed, including visual verification of the datasheet table. A separate full numerical review worker could not be started because the thread limit was reached; this limitation is disclosed rather than described as a completed independent review.

## Important correction to the earlier audit

The TPS62932 **0.15 µA FB leakage value is MAX, not typical**. `ERRATUM.md` records the affected earlier artifacts and corrected interpretation. Its positive leakage term corresponds to 6.000 mV output correction with nominal 40 kΩ Rtop, or 6.006 mV at Rtop+0.1%, under the specified VFB=0.8 V condition. No signed minimum is specified; no guaranteed symmetric leakage interval is invented. Earlier reference-and-resistor-only intervals excluded leakage and remain labelled as such. Old sealed artifacts were not silently modified.

## Reproduce and files

Requirements: Python 3, NumPy, SciPy, Matplotlib, ngspice shared library; KiCad pcbnew for layout extraction. Tested with ngspice 44.2. Public publisher documents are linked rather than redistributed in the compact packet.

```
XDG_CONFIG_HOME=/tmp/buckfb-config MPLCONFIGDIR=/tmp/buckfb-mpl python3 extract_layout.py /path/to/8a4ff6a6/maru60.kicad_pcb
MPLCONFIGDIR=/tmp/buckfb-mpl python3 simulate_feedback.py
python3 check_passive_ode.py
python3 research/recompute_passive.py
```

The packet includes four plots, source-object extraction, hypothetical candidate plans, native netlists/logs and primary waveforms, passive equations/results, official-source research notes and the erratum. Fine-step waveforms can be regenerated. No result is a whole-board electrical simulation or hardware/manufacturing qualification; keep qualification OFF.
