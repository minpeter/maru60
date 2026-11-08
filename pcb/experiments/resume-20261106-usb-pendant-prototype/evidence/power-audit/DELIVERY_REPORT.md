# Maru60 U18 power audit

## Finding

No definite U18 pin/value incompatibility was established. This audit supports **no part replacement and no active stability pass**. It changes no CAD or component values.

The checked PCB is SHA256 `88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e`, supplied checkpoint `fa96a7c8b334f0f496ab7cdb4de9b18cf9276966`. Using installed KiCad/pcbnew 9.0.2, all 13 inspected component values and 32 pin nets matched a newly exported schematic netlist. This verifies CAD assignments, not physical assembly or electrical behavior.

## Board findings

- **U18 TPS62932DRLR:** RT and EN are intentionally floating. That configuration is permitted and selects nominal 500-kHz operation. VIN/GND/SW/BST/SS/FB assignments match the official pinout.
- **Soft-start C139:** 100 nF ±10%, SS-to-GND. It **passes the stated nominal minimum**: even 90 nF exceeds 6.8 nF. Effective capacitance remains unqualified. C138 is nominally 100 nF/16 V, correctly connected BST-to-SW; dielectric qualification remains open.
- **Feedback:** R159/R160 are 40.0 kΩ/10.0 kΩ, each labeled ±0.1%. Their divider sets nominal **4.000 V**.
- **Input capacitors:** C126+C136+C137 total **5.8 µF nominal**. Relative to TI's **10-µF typical decoupling guidance**, this is a review flag, not a mandatory-minimum breach or proof of instability.
- **Output capacitors:** C100+C120+C140+C141 total **49.7 µF nominal**. C140/C141 labels “effective>=12uF TBD” are requirements awaiting evidence, not verified effective values. Downstream switched LED capacitance is excluded from this direct sum.
- **Candidate MPN evidence exists:** L2 already names Coilcraft **XAL4030-472MEC**, 4.7 µH ±20%, in the PCB and schematic values. C100's schematic BOM fields identify Murata **GRM31CR71H475KA12L** with an isolated-study status; its PCB value is a generic 4.7-µF specification. Neither candidate is thereby procurement/thermal qualified. The existing C100 isolated-study evidence is acknowledged; this audit does not claim that all earlier effective-capacitance studies are absent or overwrite their conclusions. It has not established a qualified full-bank effective-capacitance bound for this board. Do not infer missing MPNs solely from PCB fields. Other inspected capacitor and feedback-resistor fields do not establish qualified manufacturer parts.

## Conditional calculations, not measurements

The included script preserves exact-rational calculations and their assumptions.

| Calculation | Result | Boundary |
|---|---:|---|
| Nominal feedback target | 4.000 V | Ideal regulated operation |
| Full-temperature reference + initial resistor tolerance | 3.913734–4.086535 V | No resistor TCR/aging, PCB leakage, ripple or distribution drop |
| Same, with explicitly assumed symmetric leakage magnitude ≤0.15 µA | 3.907740–4.092541 V | Conservative signed assumption; TI prints a positive MAX, not a signed interval |
| Nominal soft-start reference ramp | 14.545 ms | Equation result, not board startup time |
| Conditional soft-start reference-ramp range | 10.855–19.947 ms | Nameplate C tolerance, reference and charge-current limits; excludes capacitor derating |

A single nominal CCM calculation at **5 V at U18 VIN**, 4-V output, 4.7 µH and 500 kHz gives 0.340426-A inductor ripple. At the IC's 2-A rating, not an asserted board load, peak current is 2.170213 A. Treating the full 49.7-µF nominal output capacitance as effective gives 1.712402-mV capacitive ripple. **That is not an upper ripple bound**: ESR/ESL, bias/temperature effects, PFM, frequency variation and layout spikes are omitted.

The ideal no-frequency-foldback screen is 4.301075 V input, not a dropout threshold. Foldback can preserve regulation below it. The 3.8-V recommended input minimum does not guarantee a 4-V output; conversely, loss of 4-V regulation alone does not prove immediate 3V3 failure.

## Required to close stability review

1. Qualified capacitor effective-value/ESR data, resistor temperature/aging data and L2 inductance/current/temperature behavior.
2. Actual source/cable impedance, input ramp/dip range, eFuse settings and rail loads/LED sequencing.
3. Defined load-step magnitude/slew and allowable rail droop, overshoot and recovery time.
4. A supported complete vendor nominal simulation bench reproduced successfully before board substitution, and/or board measurements of startup/prebias, brownout/replug, load steps, fault recovery and loop gain/phase across application conditions.

The existing failed active-model wrappers and passive charge tests are not active-regulation evidence. No startup, brownout, load/fault or loop-stability approval follows from this audit.

## Sources and reproducibility

- [TI TPS6293x datasheet](https://www.ti.com/lit/ds/symlink/tps62932.pdf), SLUSEA4D, Rev D, August 2022: printed pp. 3–8, 19–25, 29–33; pinout, electrical limits, operating modes and component selection. Reviewed PDF SHA256: `16ec2eac43c7374eb9e7edd7df7bdb24de6862f695e1582c68716ced4820e5f6`.
- [Coilcraft XAL40xx datasheet](https://www.coilcraft.com/getmedia/6adcb47d-8b55-416c-976e-1e22e0d2848c/xal4000.pdf), Document 806, revised February 25, 2026, p. 1 specifications and notes. Reviewed PDF SHA256: `b26cf975bd56a807173b05665bddd49ed49323400330eb8f6fa63e24ff6d7d15`.

Included: `audit.py`, `calculations.json`, `components-audit.json`, `source-hashes.json`, source-derived `netlist.xml`, plus `replay_calculations.py` and `calculation-replay-result.json`. Manufacturer PDFs/text/screenshots remain local research and are not included.

Reproduction caveat: `audit.py` is unchanged from the research audit and expects the original native CAD location, included netlist, and locally held manufacturer PDFs for hashing. It runs through the existing `run-kicad.sh` with `/usr/bin/python3` and pcbnew. A recipient must supply those original inputs, retrieving the official PDFs and checking the hashes; the limited delivery bundle is **not a self-contained executable CAD/model package**. Source hashes include original local paths for provenance, not downloadable links.

### Portable calculation-only check

Run `python3 replay_calculations.py` beside `calculations.json`. This uses only Python's standard library and those two files; no pcbnew, wrapper, absolute CAD paths or manufacturer PDFs are needed. It independently evaluates the divider from nodal arithmetic, enumerates 48 feedback corners and 8 soft-start corners, and recomputes all nominal design formulas. It asserts exact rational and numeric agreement with the recorded calculations.

**Result: 519 checks passed.** The same result was reproduced in an isolated temporary directory containing only those two files. `calculation-replay-result.json` records the input/script hashes, named assumptions and each checked field. This closes arithmetic reproducibility only. It does not authenticate datasheet inputs, qualify their applicability, recheck CAD, establish effective component parameters, or validate an active model or stability. The original `audit.py` remains unchanged and retains the separate native-source requirements above.
