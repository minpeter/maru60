# Current baseline and prototype candidate

The strict accepted geometry baseline remains `experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pro`, PCB `04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99`, commit `bbf61e6`: 11 open pairs and 51 warnings.

Latest frozen development candidate: `experiments/resume-20261105-gpio24-vbus-prototype/pcb/maru60.kicad_pro`, PCB `56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9`: 10 open pairs and 50 warnings. Read its README.txt and DECISION.json before use. Its strict exact-no-loss diagnostic FAILS with explicit, independently bounded sub-nanometre plane-boundary changes. This is a reversible prototype candidate, not promotion to strict acceptance or manufacturing release.

All prior designs are retained. No full current-board active simulation, SI/EMI, full firmware build or physical qualification is claimed. LED qualification stays OFF.
