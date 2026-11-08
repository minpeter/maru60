+3V3 UNUSED-BRANCH DEVELOPMENT CHECKPOINT

PCB SHA256: 88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e

Native KiCad 9.0.2: 9 open connection pairs, 39 warnings, no other native errors, ERC 0 and parity 0. This checkpoint removes exactly nine unused 0.30 mm tracks and one through-via, totaling 8.503623449077 mm of track centerline. The complete branch has only one attachment to a retained supply/load track. Partial removals were not adopted.

All retained copper, pads, footprints and their physical material remain exactly unchanged. All pad partitions and the nine complete physical open pairs remain unchanged. All 11 zones have zero loss; both inner GND planes gain metal. Native zero-area/zero-contour results were independently strengthened with exact rational boundary, clearance-cycle and strip proofs. No tolerance or exception window excuses lost ground metal. All 58 CAD files survive a cold connectivity/refill/save unchanged.

Independent review passed this bounded change against 97d9eb7. Earlier construction reports say unselected because they predate this checkpoint decision; DECISION.json records the selected scope. All prior checkpoints and the strict baseline remain preserved. The inherited earlier exact no-loss failure and 51 conservative guarded-contact diagnostics remain explicit. This is not strict-baseline acceptance or a production release.

The before/after image is a native CAD overlay of F.Cu and B.Cu at identical coordinates and scale, not assembled hardware. Remaining warning records are all visible in WARNING_REGISTER.json.

Additional read-only GPIO3 and U13 GPIO24 routing screens did not close a pair or save new CAD. The GPIO3 work found a possible three-transition route into a more northern region, but no complete path. These planning records are isolated under evidence and are not part of the selected copper.

The new power supplement checks 64 static resistor/threshold/leakage corners against official datasheet tables. It expands the earlier resistor-only sensitivity while retaining test-condition, part-selection and dynamic limitations. No resistor value changed, and no active SPICE or hardware stability claim follows.

Open pcb/maru60.kicad_pro. With the installed KiCad 9.0.2 Python runtime, VERIFY.py reruns native DRC, ERC, net identity and cold refill; --material additionally regenerates the candidate graph and compares every contact and physical open component. Original construction and exact relative-boundary scripts retain their original source-bound paths; they and their inputs/results are preserved for review. Independent source material was hash-bound rather than freshly regenerated; the candidate graph was freshly generated twice.

No SI/EMI, PDN improvement, active-power, full ARM/QMK build, thermal or hardware qualification is claimed. LED qualification stays OFF. No external push, order or flashing occurred.
