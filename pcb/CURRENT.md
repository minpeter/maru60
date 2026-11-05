# Current baseline and development candidate

Strict geometry baseline remains experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pro, commit bbf61e6, PCB04be04e5: 11 open pairs and51 warnings.

Latest qualified development prototype: experiments/resume-20261106-c136-label-prototype/pcb/maru60.kicad_pro, PCB2e532c1a: 9 open pairs and40 warnings. Only the C136 Reference field differs from ef45f84. Full raw reversal, fresh native/ERC/net/material and cold-refill validation pass. All copper, fill, masks, holes and component placements are exactly unchanged.

Prior prototypes ef45f84/9d787421 (9/42) and c782123/56d66f65 (10/50) remain preserved. This remains a qualified development checkpoint, NOT strict acceptance or manufacturing release. Inherited exact no-loss failure and51 guarded-contact proof failures are explicit. No active-power, SI/EMI, full firmware or hardware qualification. LED qualification stays OFF.

Latest unselected experiments: header25 refactor and MCU D/E rejected; complete +4V_REG branch removal held for exact remote GND boundary loss despite native41 warnings; MCU F is an incomplete launch with additional intentional warning and disclosed plane changes. None is present in the selected CAD.
