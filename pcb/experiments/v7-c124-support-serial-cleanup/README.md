# Natural serial support-route cleanup

This is an experimental working selection, not an electrical or production release. Open `candidate/pcb/maru60.kicad_pro`. PCB SHA256: abdbf4c80e11cadc525389060d2215b73fc3cbcc85b2bff6ddb0e8d2581e052d. Its predecessor 7882 is preserved unchanged.

Exactly three existing main-track endpoints change. The GND, OVLO and UVLO source-support segments are retained and become genuine serial route/width-transition legs. No track is added or deleted, and no duplicate, zero-length or fake-loop object is used. All footprints, pads, drills, vias, rules and twelve saved zone records are unchanged. Circuit values and nominal topology remain unchanged.

Native DRC:64→61 warnings, exactly the three new support warnings removed and none added. The12 raw expansion-open records are identical. Other hard DRC/ERC/parity:0. Inventory:9,750 tracks,919 vias,383 footprints,13,184.45545001526mm summed track-object length. The reduction in summed length is mainly redundant overlap removal; it is not a demonstrated improvement in current-path length or impedance.

Independent raw-byte review, actual native endpoints, ordinary cold refill, complete guarded-edge/barrel component reconstruction and actual-native all-hole support/reference reconstruction pass. All383 material component sets,246 pad-net partitions,247 ground-pad roots,935 barrels and733 plane contacts are preserved. All14 strengthened source support patches and both new signal projections on both actual inner planes have zero missing area, with no tolerance waiver. Two old incident contacts disappear and eight incident witnesses change; unrelated material records remain exact. The original51 guard failures remain explicit and unjoined.

GND is ideal-capsule-equivalent but NOT native-polygon-identical: recorded union loss5.3943e-8mm² and gain2.814105e-7mm² remain nonzero. OVLO/UVLO have explicit small copper-shape changes. The saved planes and every drill are unchanged, so old reference-shadow results inherit exactly. No signal/analog stability improvement is claimed, and parasitics were not extracted.

All C124 adoption risks remain: undefined input-fault envelope, active startup/reset/brownout, repetitive pulse/discharge, capacitor bias/aging, resistor environmental tracking, physical SI/ESD/EMC, assembly and hardware checks. LED qualification stays OFF. Read the preceding unit's `electrical-adoption-risk/BRIEF.md`. No fabrication, flashing or push.

Frozen source and candidate reports retain their original UNSELECTED phase labels. This separate adoption receipt records only the later limited experimental selection. `frozen-trial` contains215 mapped artifacts; `independent-review` contains the independent receipts and scripts. Absolute original run paths are provenance rather than a relocated one-command replay promise. Earlier source/evidence files are unchanged.
