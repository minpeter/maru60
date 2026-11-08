MARU60 prototype candidate: 10 open pairs, 50 warnings

Open pcb/maru60.kicad_pro with KiCad 9. Candidate PCB SHA256:
56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9

This is a frozen, reversible development candidate, NOT strict acceptance or fabrication approval. The stricter accepted geometry baseline remains bbf61e6 / 04be04e5 with 11 open pairs and 51 warnings. No old baseline is overwritten.

Since the original recovered design, GPIO26 header wiring and GPIO24 J3-to-U11 wiring have been added. GPIO24's U13 side and all six MCU-side pairs remain unfinished. GPIO24 required moving one existing EXT_GPIO3 via by 0.10 mm. One redundant single-layer VBUS via was removed; an existing overlapping track was serialized without reducing the VBUS track copper union.

Fresh native checks on this exact candidate: 10 open pairs, 50 warnings, no other DRC errors, ERC 0, parity 0, raw/native net identity and all 1,064 electrical pin bindings pass. All 58 CAD files are byte-identical after a separate cold refill. Material checks preserve required physical components. Native ratsnest representatives change on five remaining pairs, but all complete physical endpoint-component pairs are proved unchanged after the VBUS increment.

STRICT EXACT NO-LOSS DIAGNOSTIC: FAIL. Do not describe it as an exact geometric pass. A real serialized +4V_LED reference-shadow loss of 2.7676778318142192e-08 mm2 per plane is independently proved. Full remote boundary movement from GPIO24 is bounded below 0.767898 nm, consistent with, but not proven caused by, integer refill/fracture rounding. VBUS remote movement is below 0.733 nm. Its apparent GND contact shrink is separately disproved by exact annulus coverage. All raw differences and failed gates remain in the evidence. The independent reviews support only an explicitly qualified prototype interpretation, not SI or manufacturing qualification.

Simulation: all 14 saved passive/behavioral decks reproduce, but none is a full current-board model. Thirteen are sensitivities; one is a simulator control. Fresh schematic/PCB checking of 29 components found directly connected nominal totals of 49.7 uF on +4V_REG and 5.8 uF on the protected input; old selected-capacitor examples omit other connected capacitors. These totals are NOT effective capacitance. Active startup wrappers produce no waveform because XSPICE models are unavailable; historical module-enabled runs also had semantics/regulation failures. See simulation/APPLICABILITY.md.

Next finite work: review the four remaining short header pairs and six MCU pairs; test a grounded stitch near the U11-side GPIO24 transition; resolve 50 warnings; bind real part, input/load and stackup assumptions; validate active power models, full firmware builds, mechanical fit and hardware. No power stability or production readiness is established. LED qualification remains OFF.

DECISION.json and WARNING_REGISTER.csv give the concise disposition. evidence/ holds source-bound native, material, exact-boundary and composition reports. simulation/ contains fresh replay and current-source applicability evidence. images/ contains a native full-board copper view and local GPIO24 views.
