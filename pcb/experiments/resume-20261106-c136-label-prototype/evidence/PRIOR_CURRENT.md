# Current baseline and qualified development candidate

Strict geometry baseline remains `experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pro`, commit `bbf61e6`, PCB `04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99`: 11 open pairs and 51 warnings.

Latest frozen qualified development prototype: `experiments/resume-20261105-gpio27-stitch-labels-prototype/pcb/maru60.kicad_pro`, PCB `9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed`: 9 open pairs and 42 warnings. Read its README.txt and DECISION.json. GPIO27 header closure, a rooted GPIO24 GND stitch and four label repairs are included. An independently caught departure-reference exception was corrected without enlarging the allowed transition windows; every new and affected reference row now has an executable passing assertion.

The earlier c782123 / 56d66f65 prototype remains preserved with 10 open pairs and 50 warnings. Held b1e3 and rejected MCU experiments are not selected. The inherited strict exact-no-loss failure remains explicit; this is NOT promotion to the strict baseline or manufacturing release.

All prior designs are retained. No full current-board active-power, SI/EMI, full firmware-build or hardware qualification is claimed. LED qualification stays OFF.
