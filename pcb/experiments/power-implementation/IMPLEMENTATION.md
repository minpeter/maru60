# MAX38902A bounded implementation study

2026-11-02 UTC. **Isolated, reversible, not adopted, not fabrication-ready.** This follows the [independent component review](../independent-review/max38902a-20261102/REVIEW.md). The accepted PCB and prior reviewed correction package remain unchanged. No orders, flashing, public pushes or supplier contacts occurred.

## Decision and useful closures

Specify the exact five-part LDO BOM and official land geometry. Keep every electrical pin/net endpoint identical to the reviewed correction. Use **10 nF C0G for C142 in this implementation candidate**, rather than treating the earlier 68 nF as a requirement. This is an explicit value/footprint revision, not a connectivity change. It follows ADI's electrical-table/EV-kit baseline and avoids an unnecessary 1206 bypass capacitor. It does **not** close preconfiguration inrush: the faster ramp increases capacitor-charge current. Keep the 68 nF alternative in the comparison below.

The public sources do not establish an all-corner effective-C/ESR/hot-leakage guarantee for the selected ceramic parts. Those precise missing guarantees are recorded below; no typical curve was promoted to a worst case. Automatic reverse protection and the ≥0.1 mA internal load floor remain the component-level remedies accepted by the reviewer, subject to these implementation conditions.

## Finite BOM

| Ref | Exact candidate MPN | Value/package | Implementation status |
|---|---|---|---|
| U2 | Analog Devices **MAX38902AATA+T** | 3.3 V selection, T822+3C, 2×2 mm TDFN8+EP | Pin mapping and official land dimensions implemented; assembly/thermal qualification pending |
| R163 | Vishay **TNPW060331K6BYEA** | 31.6 kΩ, 0.1%, 10 ppm/K, 0603 | Bounded total-error allocation below; do not substitute an ordinary 1%-initial resistor |
| C100 | Murata **GRM31CR71H475KA12L** | 4.7 µF, 50 V, X7R, ±10%, 1206 | Exact input candidate; effective-C/impedance under actual waveform remains unqualified |
| C101 | Same as C100 | 4.7 µF, 50 V, X7R, ±10%, 1206 | Local ≥2 µF and ESR <30 mΩ requirement retained, not proven by nominal value |
| C142 | Murata **GRM1885C1H103JA01D** | **10 nF**, 50 V, C0G, ±5%, 0603 | Official ADI EV-kit listed family; below-10 nA assembled leakage condition still requires applicable evidence |

Machine-readable BOM: `bom.json`. No stock, pricing or purchasing commitment is implied. The 50 V ceramic rating is chosen for a practical catalog/bias margin, **not** evidence of 21 V board-abuse survival.

### R163: initial tolerance is not total tolerance

The [Vishay TNPW e3 specification](https://www.vishay.com/docs/28758/tnpw_e3.pdf), Rev 10-Apr-2026, provides part-code decoding and explicit drift-test limits. The code selects 0.1% initial tolerance and 10 ppm/K. Use the proposed resistor-film envelope −40 to +125 °C; referenced to the specified 20 °C test, the largest excursion is 105 K, or 0.105% TCR error. This is a component analysis envelope, not a newly adopted whole-keyboard temperature/lifetime requirement.

The conservative **arithmetic allocation** is: initial 0.100%; TCR 0.105%; general-mode 225,000 h/70 °C drift 0.300158%; solder heat 0.020032%; damp heat 0.100032%; thermal cycling 0.100032%; cold 0.050032%; board bending 0.050032%. Sum **0.825316%**, leaving **0.174684%** within the existing ±1% total contract. At this sum, 3.20 V gives ≥100.437 µA; the 3.267–3.333 V static band gives 102.540–106.352 µA. Dissipation is approximately 0.36 mW, far below general-mode rated power.

These are sums of separately specified tests, **not a manufacturer guarantee for arbitrary combined stress or 225,000 hours at 125 °C**. Required implementation control: approved life/environment equivalent to or less severe than the allocated conditions; assembled resistance within the ±1% envelope over that declared life; no unbudgeted repeated rework, sulfur exposure, overstress, condensation or indefinitely accumulated drift. This actual precision part and explicit allocation replace the previous ambiguous “1% total” BOM. Combined environmental/lifetime qualification remains finite and named, not assumed.

### C100/C101: exact candidates, precise missing guarantee

The current [Murata GRM31CR71H475KA12 reference sheet](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31CR71H475KA12-01A.pdf) specifies 4.7 µF ±10% and X7R ±15% **without DC bias**. Therefore 4.7×0.90×0.85 = **3.5955 µF before bias/aging**. To retain 2 µF, the remaining combined bias/aging factor must be ≥**0.55625**. A deliberately hypothetical 0.90 aging ×0.70 bias screen gives 2.2652 µF, but neither factor is a published worst-case bound for this part. It is not a pass.

The sheet's DF ≤0.025 at 1 kHz/1 Vrms is not the requested ESR guarantee. Even converting that test at minimum initial C permits approximately **0.941 Ω**; it cannot prove <0.03 Ω at the LDO's relevant frequencies or corners. ADI's ESR statement does not itself specify the measurement frequency. Do not infer a universal 30 mΩ limit from a typical impedance plot or from “X7R.”

* **C101 release gate:** obtain a supplier-approved effective minimum ≥2 µF at local OUT, 0–3.40 V bias, declared temperature/life/AC excitation; obtain an applicable <0.03 Ω ESR bound with frequency conditions agreed with ADI; then verify assembled loop stability and load transients. No distributed board capacitance substitutes for the local part.
* **C100 correction:** ADI recommends a 4.7 µF ceramic maintaining capacitance under bias/temperature. It does **not** publish an identical 2 µF input minimum. The prior “input effective ≥2 µF” label is removed, not elevated into a manufacturer requirement. This exact 4.7 µF candidate must be checked at the proposed 3.65–4.10 V normal input envelope, actual buck/source impedance and startup/load waveform; obtain ADI confirmation if relying on an effective input capacitance substantially below its recommendation.

A 1206 part increases area compared with the earlier 0603 placeholders; it does not add nominal capacitance or steady current. Do not replace with a large film/polymer network merely to claim a paper guarantee: that changes area, startup charge and ESR behavior and needs a separate justified review. No further capacitor search is necessary to report the exact missing supplier guarantees.

## BYP is optional in value, not proven optional in existence

The [MAX38902 Rev 10 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX38902A-MAX38902D.pdf) specifies stable operation for **effective CBYP 1–100 nF** and describes a high-speed feedback role as well as noise filtering. No cited official source authorizes an open BYP pin. **Do not omit C142.** A nominal 1 nF with negative tolerance would also cross the supported lower limit.

There is no adopted ultra-low-noise audio/precision-analog requirement. A 10 nF C0G is the datasheet's default electrical-test value and appears explicitly in the [official EV-kit BOM](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX38902EVKIT.pdf). Its typical reference-noise corner is about 32 Hz; the headline 10.5 µVrms is tested with 47 nF, not a guaranteed 10 nF noise figure. Smaller CBYP gives less low-frequency filtering and faster startup/recovery; it does not remove COUT's stability requirement.

| CBYP nominal | Initial 3.3 V ramp, formula | Short-recovery approximation | Charge current for nominal 10.7 µF to ground |
|---|---:|---:|---:|
| 1.5 nF, comparison only | 0.099 ms | 49.5 ms | 356.7 mA |
| **10 nF, implementation candidate** | **0.660 ms** | **330 ms** | **53.5 mA** |
| 22 nF, comparison only | 1.452 ms | 726 ms | 24.3 mA |
| 47 nF, comparison only | 3.102 ms | 1.551 s | 11.4 mA |
| 68 nF, prior lower-inrush alternative | 4.488 ms | 2.244 s | 7.87 mA |

All figures derive from the published nominal slew formula/approximate ×500 factor; **none is a guaranteed timing/current limit**. Core/module charging and load are additional. At 10 nF, nominal capacitor charging consumes 53.5 mA of the earlier conditional 84.433 mA external-3V3 preconfiguration remainder, leaving only about **30.93 mA** before reset-state MCU/core/module loads, capacitor upper corners and slew variation. Holding MCU reset through charging is a useful architecture measure, not proof of this current budget. Neither 10 nor 68 nF is released for USB startup. The 68 nF alternative remains available if a qualified charge envelope requires it; hardware reset must then tolerate the longer recovery. No feature is removed to make either fit.

### Leakage/cleanliness contract

The [10 nF Murata reference sheet](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM1885C1H103JA01-01A.pdf) gives initial room-temperature IR >10 GΩ, post-damp-heat >500 MΩ, post-endurance >1 GΩ. At an assumed maximum 3.4 V BYP–OUT differential, simple V/R estimates are <0.34 nA, <6.8 nA and <3.4 nA respectively. These are **inferences**, not guaranteed low-voltage/hot-PCB leakage: the specified tests use rated voltage and measure at room temperature after recovery. Capacitance initial/temperature screen is about 9.472–10.561 nF, comfortably inside 1–100 nF; stress/life and bias conditions remain tied to the reference/approval sheet.

For comparison, the exact 68 nF C0G **GRM31C5C1H683JA01L** has IR limits 500 Ω·F initially and 25 Ω·F after damp heat. Using its 71.814 nF upper initial/temperature screen gives ~0.488 nA fresh and ~9.767 nA after damp stress at 3.4 V, before PCB leakage. This is a concrete reason not to lock that larger part merely for noise.

Proposed assembly target: cap-plus-PCB BYP leakage **<10 nA**, with ≤1 nA allocated to PCB residue/adjacent nets at the applicable differential (≥3.4 GΩ at 3.4 V). Route pin7 and C142 locally on a clean quiet surface, no connector/test-header exposure, no buck SW adjacency, no shared high-impedance contamination path; validate cleaning and humidity on the actual assembly. A shield/guard connected to OUT may reduce differential leakage but is not itself a guarantee. If worst-case BYP differential exceeds 3.4 V, recalculate the leakage allocation; do not reuse it blindly for input collapse/fault overshoot. Public data alone cannot close hot/humid assembled leakage; the exact remaining action is supplier approval plus board-level leakage evidence for the declared environment.

## Native footprint, placement and sensing contract

* `native-max38902a/MaruStudy.pretty/MAX_T822-3C_90-0065_2x2_P0.5_EP0.8x1.38.kicad_mod` transcribes **[ADI 90-0065 Rev E](https://pdfserv.maximintegrated.com/land_patterns/90-0065.PDF)**, including T822-3C: lead lands 0.70×0.30 mm, row centers ±0.99 mm, pitch 0.50 mm, **EP land 0.80×1.38 mm**. Source land tolerance is ±0.02 mm. The [21-0168 Rev M outline](https://mds.analog.com/api/public/content/tdfn-cu_21-0168.pdf) has a 2×2 mm body and 0.80×1.20 mm nominal package EP: land and package dimensions are deliberately distinguished.
* Top view: left pins1–4 top-to-bottom; right pins8–5 top-to-bottom. EP is native pad9/GND. Pin5 SELB has a physical solder land but **no electrical connection**. Pin4 SELA goes directly to GND. Pin6 OUTS remains distinct from pad8 even though both share +3V3 electrically.
* Proposed mask expansion 0.025 mm and two 0.60×0.55 mm EP paste windows give **59.78% paste coverage**. These are assembly-process choices, not copied manufacturer guarantees. Stencil thickness, pad registration, solder voiding and inspection require assembler agreement. No unfilled open via-in-pad is implied.
* The native 18×14 mm **placement-only** tile demonstrates five-part spacing, not final routed area or a thermally qualified island. It contains **no tracks, vias or copper planes**. DRC honestly reports 12 unrouted connections; there are no other reported geometry violations. Its outline is a study frame, not board geometry for adoption.
* Route C100 positive directly to IN1, with its return joining GND2/EP through a short low-inductance plane; EN3 ties to the same valid input. Route OUT8 by a wide power path to local C101 positive. Route **OUTS6 separately as a Kelvin sense trace to that same C101-positive / 3V3 distribution star**, not to a remote connector or the switcher's current path. The regulated point is the star; budget resistance from it to MCU VREG_AVDD/USB/flash separately. Do not put 300 mA through the sense trace.
* Connect C142 between BYP7 and the quiet OUT/star side, never GND. Keep its loop short and away from SW/inductor, with no load current in BYP or OUTS traces. Proposed placement allows a local route but routing still needs completion and review.
* EP must connect to a ground plane and thermal vias per ADI. Before adoption, implement a continuous top-ground heat path plus bottom copper using fabrication-qualified outside-pad vias or filled/capped via-in-pad, then verify copper area/voiding/temperature. No specific via count or θJA is claimed sufficient from this unrouted tile.

At the **proposed** 300 mA external-load ceiling, static 4.0865 V in /3.267 V out and the illustrative 600 µA no-load-IQ term give about **0.2484 W**. Applying ADI's four-layer θJA to an unknown two-layer board is not valid. For illustration, keeping TJ≤125 °C at TA=85 °C would require total θJA≤161 °C/W at that power; actual loaded IQ, load states and thermal implementation must establish the bound. Short/thermal-cycle behavior is a separate fault case; 500 mA silicon rating is not USB permission.

## Verification and finite stopping point

Run `bash reproduce.sh` using the existing pinned correction directory, KiCad 9 and repository `sexp.py` helper. Results: native netlist endpoints identical to reviewed correction, four unaffected child sheets byte-identical, all five MPN/footprint fields checked, **ERC 0**, official U2 land dimensions checked, accepted PCB SHA256 still `80681cd392d1ca83bd37e58faef07a0def301f2d93763102982eaf1c0148f831`. The prior correction manifest is unchanged. See `verification.json`, `implementation-calculations.json`, `reproduction.log` and `qa/`.

The exact remaining component actions are: supplier effective-C/ESR approval at named corners; applicable BYP leakage/cleanliness evidence; declared resistor life/environment acceptance; routed Kelvin/EP implementation and thermal verification. See `RESET-RECOVERY.md` for the independent hardware/firmware architecture gap. No prototype, impedance analyzer, thermal instrumentation or supplier-approved specification is available here. Those missing observations/guarantees are **not denied permissions**. This study is complete enough for independent review, not production release.

Normal working envelope remains **USB 4.4–5.5 V**. The proposed 21 V abuse-survival case is separate, not an explicit user requirement. Existing 150/140/350 mA screens remain proposals, not adopted feature limits. Whole-USB current, upstream buck/fuse headroom, LED retained-state/inrush and suspend gates remain open. Accepted translators remain **SN74LV1T125DBVR**; the other inherited V6 sheets are unadopted context, not a migration instruction.
