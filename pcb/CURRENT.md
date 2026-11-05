# Current baseline and development candidate

Strict geometry baseline remains experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pro, commit bbf61e6 / PCB04be04e5: 11 open pairs and 51 warnings.

Latest qualified development prototype: experiments/resume-20261106-3v3-branch-prototype/pcb/maru60.kicad_pro, PCB88fbac1d: 9 open pairs and 39 warnings. The complete unused +3V3 branch (nine tracks and one via) is removed. Independent fresh native/material and exact plane-boundary review passes. Every retained physical conductor remains exact; all GND plane changes are gains, with no loss exception. Complete pads/contacts/open pairs are preserved. See README.txt and DECISION.json.

Prior 97d9eb7 / PCB2e532c1a (9/40), ef45f84 / PCB9d787421 (9/42), and c782123 / PCB56d66f65 (10/50) remain preserved. This is not promotion to strict baseline or manufacturing release. The inherited earlier exact no-loss failure and 51 guarded-contact diagnostics remain. No active-power, SI/PDN, full firmware or hardware qualification. LED qualification stays OFF.

Remaining wiring: three header pairs and six MCU pairs. New finite GPIO3 and U13 GPIO24 planning did not produce a complete route. Unselected/held copper experiments remain separately labeled. A new 64-corner datasheet-based static power envelope is included, with explicit test-condition and dynamic limits.
