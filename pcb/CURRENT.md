# Current baseline and development prototype

Machine-readable entrypoint: [`current.json`](current.json). It pins the primary
KiCad project, board and root schematic for each selection with repository-relative
paths and SHA256 hashes. Both selections are **not manufacturing-ready**.
Run `uv run tools/check_pcb_current.py` from the repository root to check file
identity and path containment. This read-only check does not replay DRC, cold
refill, electrical checks or qualification, and does not inventory every CAD
dependency. Diagnostic counts in the manifest are reported historical results.

| Selection | Primary project | Reported open pairs / warnings |
| --- | --- | --- |
| Strict geometry baseline | [Open project](experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pro) | 11 / 51 |
| Bounded development prototype | [Open project](experiments/resume-20261106-usb-pendant-prototype/pcb/maru60.kicad_pro) | 9 / 38 |

For the prototype's preserved decision and limits, see
[`README.txt`](experiments/resume-20261106-usb-pendant-prototype/README.txt) and
[`DECISION.json`](experiments/resume-20261106-usb-pendant-prototype/DECISION.json).
Return to the [PCB overview](README.md) or [project overview](../README.md).

Strict geometry baseline remains experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pro, commit bbf61e6 / PCB04be04e5: 11 open pairs and 51 warnings.

Latest bounded development prototype: experiments/resume-20261106-usb-pendant-prototype/pcb/maru60.kicad_pro, PCB41f82c80: 9 open pairs and 38 warnings. Exactly one unused 0.4375 mm USB_DM_CONN pendant is removed. Independent native, all-hole junction, full byte-scope and graph review pass. Every other serialized PCB object, hole and zone fill remains exact. Fresh final-copy material replay preserves all retained contact values, all pads and all nine physical open-component pairs. All 58 CAD files pass cold refill. See README.txt and DECISION.json.

Previous fa96a7c / PCB88fbac1d (9/39), 97d9eb7 / PCB2e532c1a (9/40), ef45f84 / PCB9d787421 (9/42), and c782123 / PCB56d66f65 (10/50) remain preserved. This is not strict baseline promotion or manufacturing release. Inherited exact-no-loss failure and 51 guarded-contact diagnostics remain unresolved. No USB SI/EMI, active-power, full firmware, thermal or hardware qualification. LED qualification stays OFF.

Remaining wiring: three header pairs and six MCU pairs. Three new GPIO25 candidates were rejected: two passed native 8/39 but lost exact remote inner-plane copper, and one introduced three clearance errors. All are preserved separately; none is selected. A different transition topology remains an untested hypothesis, not a proved solution.

The power audit checks 13 components and 32 pin assignments, with official-data conditional feedback and soft-start calculations. A self-contained arithmetic replay passes 519 assertions. Input nominal 5.8 uF versus typical 10 uF guidance is a review flag, not proven instability. Effective component parameters, actual source/load data, supported active models and measurements remain open.
