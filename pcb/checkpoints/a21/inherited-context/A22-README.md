# Canonical isolated A22 — actual remote FAULT closure

PCB `maru60.kicad_pcb` SHA256 **fdd9ce12580c1dc8a1fe14dfced60f0199b2911b2d7c87a818a2bf7affb5fa33**. Independent exact-final **22 opens / 0 hard / 59 warnings / parity 0 / ERC 0**, all13 original source witnesses plus explicit XIN/XOUT/XTAL/UG/FAULT source checks,924 numbered pins/1275 physical pads/340 footprints, cold byte identity.

Actual **U1.35/R113.2→U7.4/TP9.1** four-pad fault function joins two populated components into one. The local MCU-to-pullup connection was already complete; this is the real remote switch fault connection, not another escape tail. Other populated net partitions remain identical. U7 default-off/current-limit/fault topology and parts are unchanged.

Exactly39 additive FAULT tracks(**106.552019mm**),two standard0.50/0.25 signal vias,and two GND stitches. All existing copper and footprints are preserved; every positive-rail fill is coordinate-identical. Two source-filled ground stitches at(45.7,15.8)/(111.8,74.6) yield nearest return centers0.848527/0.750mm; actual annuli after subtracting drills share the inner islands contacted by U1.61 thermal pads. These center distances are NOT full return-loop lengths. R113 endpoint is reinforced into its actual pad, with no connection-width warning.

All9,633 retained outer tracks have zero new continuous center/edge reference loss. All39 added FAULT tracks have zero center/edge gap outside declared own-via0.55mm launch disks. This is not a claim of impedance, EMC, fault waveform or physical qualification. Existing USB, SWCLK and LED29 launch/edge exceptions remain inherited and explicit.

Full unfinished board11,992.555877mm/881vias/9,886segments. The long added route connects an actual remote load/control function and is NOT a completed-board length saving. Remaining22:17 MCU matrix trunks,one padless ROW0 stub,and four control/service connections(SWDIO,RUN,KEY_RGB,LED_ENABLE). No padless stub is counted as a completed function.

Actual AP2112,ABM8-272-T3,LV1T125 and all current functions remain. Shared-rail current/PI,oscillator load/startup/drive,actual switch/passive/whole assembly/process and SI remain unqualified; unchanged LV1T asynchronous reset/trip/collapse is a logical release blocker. This is a conditional routing checkpoint,not accepted-main adoption or powered/prototype approval.

Root MANIFEST binds this complete current payload. Worker/inherited manifests describe separately preserved full historical packets,not selected subtrees here. Current authoritative independent reports are in coordinator-evidence/hash-bound-gates and rootSUMMARY. Native project/schema/libraries are complete. Reproduce only in a NEW writable copy; scripts retain original absolute paths and require destination updates. Preserve matching project hashes and one-board same-path load/refill/save plus intended-net guard at native boundaries. No public push,order,flash or accepted-main change. Main remains80681cd…f831.
