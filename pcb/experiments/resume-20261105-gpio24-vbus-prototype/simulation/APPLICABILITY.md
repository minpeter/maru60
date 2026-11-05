# Applicability to current selected PCB

## Verification performed

Fresh schematic netlist export with installed KiCad 9.0.2, and independent read-only native pcbnew inspection, both against selected frozen26b. Exact hashes of PCB and all selected schematic sheets, exported netlist hash, 29 components' values and pin nets are recorded in current-source-crosscheck.json. All 29 checked schematic/native-board values and connected pin-net assignments agree. This verifies electrical net assignment, not physical copper continuity, impedance, or a populated BOM. No PCB/schematic save occurred. The initial native read emitted read-only home configuration-directory warnings; the follow-up used task-local XDG directories and completed without those warnings.

## Finite parameter/topology crosswalk

Status vocabulary: unchanged = present nominal/topology match; changed/omitted = simulation abstraction differs from current circuit; assumed = stimulus or idealization not sourced from CAD; missing = needed physical evidence unavailable.

1. eFuse divider: R122 620k from VBUS_FUSED to USB_UVLO, R123 267k USB_UVLO to GND, R120 590k VBUS_FUSED to USB_OVLO, R121 156k USB_OVLO to GND. All unchanged versus deck; current values specify 0.1%, which the deck omits. U8 pins 1/2/5/6 match UVLO/OVLO/input/protected output respectively.
2. eFuse behavior: U8 TPS259470LRPW is unchanged in current source, but deck substitutes two ideal switches plus a behavioral sign inversion. Threshold midpoint 1.145 V/hysteresis 55 mV, total on resistance 28.3 mΩ, off resistance 1 GΩ are model assumptions, not CAD values or validated active behavior. 0→6.5→0 V over 2 s and 33 Ω load are synthetic. U8 dVdt R125 100 Ω + C124 10 nF, current-limit R124 6.65k, fault output, AUXOFF/ITIMER behavior, actual load branches and other caps are omitted. R125/C124/R124 nominal values and their current pin nets were checked.
3. Output capacitor selection: C140 and C141 each remain 22 µF, 10 V, effective≥12 µF TBD, both +4V_REG to GND. Thus 44 µF is their nominal sum; 24 µF is their unqualified effective-capacitance target, not an adopted/verified minimum; 8 µF is synthetic stress. Exact MPN/bias/temperature/aging/ESR evidence is missing. 20 mΩ common ESR is assumed.
4. Output topology changed/omitted: C100 4.7 µF and C120 1 µF also connect +4V_REG to GND, verified in both sources. The six charge-deficit decks omit those capacitors and downstream dynamics. Full directly connected nameplate sum of these four capacitors is 49.7 µF, not 44 µF. This arithmetic is not effective capacitance and does not warrant silently changing the saved decks. U2 MAX38902AATA+T and U7 TPS2553DBVR-1 branches are omitted.
5. Output source/load: initial 4 V is a synthetic rail condition consistent with +4V_REG naming and unchanged R159 40k/R160 10k divider topology (output→BUCK_FB→GND), not guaranteed actual voltage. Ideal constant regulator currents 0.1/0.3 A, ±0.2 A load step, 5 µs step onset, 10 ns edge and fixed regulator response for 50 µs are assumed. Actual loop, inductor L2 4.7 µH, supply and load response are omitted. Deck out maps only conceptually to +4V_REG; cnode is artificial.
6. Input capacitor selection: C137 remains 4.7 µF 50 V effective≥2 µF TBD from VBUS_PROTECTED_RAW to GND. Thus 4.7 µF is its nominal value and 2 µF only a TBD target, not proven effective value. Missing part/bias/aging/ESR information prevents treating either as actual capacitance.
7. Input topology changed/omitted: C126 1 µF and C136 100 nF are also directly across VBUS_PROTECTED_RAW/GND. The six recovery decks omit these; total directly connected nameplate capacitance is 5.8 µF, not 4.7 µF. D100 reverse-discharge path to +4V_REG and active U18 loading are omitted; deck 33 Ω is synthetic. C125 1 µF is on the other side of U8, VBUS_FUSED, and is not simply added to protected output capacitance.
8. Input feed: 0.1/0.5/1 µH feed inductances, common 20 mΩ ESR, 5 V/100 ns edge are assumed, not layout-derived. The historical 0.3582870323 Ω series aggregate is not a current discrete component or fresh extraction; unchanged applicability is unproven. Do not represent it as current board parasitic resistance. No fab/stackup or cable dimensions were invented.
9. RC control: anonymous 1k/1µF network and 1 V pulse are purely analytic simulator control, with no component-reference mapping or hardware applicability.

## All fourteen decks: classification

- rc_control: no direct hardware applicability; simulator positive control only.
- efuse_hysteresis: current-source-bound nominal divider/static behavioral sensitivity only. All four divider values/topology directly apply; the complete deck does not model actual U8 protection.
- capacitor_8u_load, capacitor_8u_unload: synthetic stress sensitivity only, no current capacitor value match.
- capacitor_24u_load, capacitor_24u_unload: C140/C141 TBD effective-capacitance target sensitivity only, not measured or specified populated value.
- capacitor_44u_load, capacitor_44u_unload: source-bound C140+C141 nominal-only sensitivity, omits additional rail capacitors and active dynamics.
- input_recovery_C2u_L0p1u, input_recovery_C2u_L0p5u, input_recovery_C2u_L1p0u: C137 TBD effective-capacitance target plus assumed feed sensitivity only.
- input_recovery_C4p7u_L0p1u, input_recovery_C4p7u_L0p5u, input_recovery_C4p7u_L1p0u: C137 nominal-only plus assumed feed sensitivity, omits other input caps and active circuits.

No complete deck is a direct current-board simulation. Thirteen remain useful explicitly limited sensitivities with the above current-source associations; one is simulator-only control. No changed nominal value was detected for the selected R120–R123/C137/C140/C141 values; the major discrepancy is model omission and assumptions, not a demonstrated recent CAD regression. The historical complete board is not available in this work packet to prove all topology was unchanged over time.

No additional synthetic solve was necessary: the verified 49.7/5.8 µF nameplate sums would still require arbitrary shared ESR/load/feed assumptions and would not resolve stability. Existing ±200 mA sensitivity remains reproducible and properly scoped. Active startup, faults, brownout, pulse-load response, off-state injection, loop phase margin and production qualification remain unverified.

## Complete directly connected capacitor inventory

All capacitor references on these five nets were enumerated from the fresh schematic export and checked against native PCB values and both pad nets. This is exhaustive by capacitor reference for these nets, not a current-path or effective-capacitance extraction. A capacitor on two listed non-ground nets would appear twice and must not be double-counted.

### VBUS_FUSED
- C125: 1uF 50V effective TBD; grounded; pin 2 → GND, pin 1 → VBUS_FUSED.

### VBUS_PROTECTED_RAW
- C126: 1uF 50V; grounded; pin 2 → GND, pin 1 → VBUS_PROTECTED_RAW.
- C136: 100nF 50V; grounded; pin 2 → GND, pin 1 → VBUS_PROTECTED_RAW.
- C137: 4.7uF 50V effective>=2uF TBD; grounded; pin 2 → GND, pin 1 → VBUS_PROTECTED_RAW.

### +4V_REG
- C100: 4.7uF 50V X7R 10%; grounded; pin 1 → +4V_REG, pin 2 → GND.
- C120: 1u; grounded; pin 1 → +4V_REG, pin 2 → GND.
- C140: 22uF 10V effective>=12uF TBD; grounded; pin 1 → +4V_REG, pin 2 → GND.
- C141: 22uF 10V effective>=12uF TBD; grounded; pin 1 → +4V_REG, pin 2 → GND.

### +4V_LED
- C121: 4.7u; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C122: 100n; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C123: 100n; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C200: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C201: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C202: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C203: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C204: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C205: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C206: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C207: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C208: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C209: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C210: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C211: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C212: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C213: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C214: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C215: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C216: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C217: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C218: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C219: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C220: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C221: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C222: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C223: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C224: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C225: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C226: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C227: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C228: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C229: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C230: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C231: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C232: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C233: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C234: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C235: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C236: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C237: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C238: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C239: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C240: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C241: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C242: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C243: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C244: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C245: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C246: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C247: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C248: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C249: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C250: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C251: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C252: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C253: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C254: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C255: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C256: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C257: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C258: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C259: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C260: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C261: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C262: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C263: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C264: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C265: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C266: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C267: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C268: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C269: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C270: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C271: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C272: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C273: 100nF; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C274: 100nF 10V X7R candidate; grounded; pin 1 → +4V_LED, pin 2 → GND.
- C275: 100nF 10V X7R candidate; grounded; pin 1 → +4V_LED, pin 2 → GND.

### +3V3
- C101: 4.7uF 50V X7R 10%; grounded; pin 1 → +3V3, pin 2 → GND.
- C102: 4.7u 6.3V; grounded; pin 1 → +3V3, pin 2 → GND.
- C105: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
- C111: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
- C112: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
- C113: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
- C114: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
- C115: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
- C116: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
- C117: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
- C118: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
- C128: 100nF 16V; grounded; pin 1 → +3V3, pin 2 → GND.
- C129: 100nF 16V; grounded; pin 1 → +3V3, pin 2 → GND.
- C142: 10nF 50V C0G 5%; between_non_ground_nets; pin 1 → +3V3, pin 2 → LDO_BYP.
- C199: 100n; grounded; pin 1 → +3V3, pin 2 → GND.
