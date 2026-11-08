# GPIO24 joint local corridor: planning blocker, no candidate saved

The bounded joint GPIO10/COL13 planning attempt did not establish a complete path that preserves both existing routes. No PCB was edited or saved; no pair was closed. The exact immutable source remains SHA256 9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed. Candidate hash: none. Changed-object list: empty.

## What was checked

Native KiCad 9.0.2 shapes were inspected through the private-runtime wrapper. U13.12 is actually on B.Cu; PAD.GetLayer() alone reports an inappropriate F.Cu default, so local-geometry.json now explicitly lists actual layer membership. Source EXT_GPIO24 already joins J3.5 and U11.16 through existing vias at (92.35,37.75) and (105.8,37.5). U13.12 at (89.45,42) is the intended disconnected component.

The screen uses 0.15 mm traces, 0.15 mm ordinary clearance, 0.50/0.25 mm proposed through vias, four copper layers, and a conservative 0.205 mm non-GND signal-via screen. Filled-plane material and physical contact certification are not part of this preliminary screen and are not asserted.

In memory only, the previously specified four-object GPIO10 adjustment was considered, and diagonal COL13 a19f0dbf-babd-46e0-b269-9c02b78fb0f0 was removed as an optimistic diagnostic relaxation. The local U13 escape then reaches (88.85,42). This is NOT an acceptable saved board because COL13 has not been restored.

A direct F.Cu path from that location to existing GPIO24 via (92.35,37.75) fails the bounded 0.05 mm grid within x87..106, y36.8..45. Its 10,811-node reachable region stops at y39.05 near the target. The immediate northward step from (91.75,39.05) to (91.75,39.0) has 0.125 mm clearance to +4V_LED track 8c0879ff-0cc8-4c2e-9368-ae1ffae0255e, below 0.15 mm.

A second-transition screen from the actual J3 B.Cu component reaches 782 nodes. Of 160 overlapping F/B positions, none admits the screened through via. Importantly, 43 positions are obstructed only by the retained COL13 horizontal 393cd1e2-4007-43d0-803e-78162f1899a5. Therefore this is not presented as a proof that all GPIO24 routing is impossible.

The joint restoration screen explicitly considered (88.85,42) and (92.5,39.5) as hypothetical GPIO24 vias and sought a continuous original-width COL13 replacement between original-line anchors (87.65,43.5) and (93.5,39.05), within x86.8..94, y38.5..44. Same-net COL13 objects are not obstacles. With native 0.50 mm via geometry verified using the correct layer-first SetWidth overload, this search fails after 5,441 nodes. Reaching the second transition while restoring COL13 is the concrete local blocker for this proposed corridor. The screen is finite, not an exhaustive proof over alternate via locations or broader reroutes. No further series of alternate positions was attempted.

## API diagnostic correction

Two preliminary joint-screen logs are retained, not accepted: joint-col13-screen.log used the no-layer SetWidth overload that emitted an assertion warning; joint-col13-screen-corrected-api.log reversed the two-argument overload and therefore produced invalid tiny via widths and a false path. The actual binding is SetWidth(layer, width). The final script uses that order, and joint-col13-screen-native-final.log plus joint-col13-screen.json contain the valid failed result. No geometry from any of these runs was saved. The initial geometry-inspection no-layer GetWidth warning was likewise corrected in scripts/inspect.py; the final inspect.log is clean.

## Preserved status and validation limits

Source QA, not a new candidate measurement: 9 open pairs, 42 warnings (15 text height, 13 silk-over-copper, 10 silk overlap, 4 track dangling), zero native hard violations and zero schematic parity findings. Existing source ERC is zero. The C136-only selected checkpoint was not touched.

Candidate native DRC, net identity, ERC, cold58 refill, corrected material graph, complete pad partitions, contact proof, and all-row area/contour return-plane proof were NOT run because no concrete complete layout was saved. No contact/plane acceptance claim is made. No antipad or reference-loss exception was declared or applied. Inherited strict no-loss failure and 51 conservative guarded-contact diagnostics remain separate, unresolved prior facts, not native errors added by this screen.

No SI, active-power, manufacturing, hardware-readiness or stability claim. No installation, publication, order, manufacturing or flashing occurred.

## Evidence

- qa/RESULT.json: source and companion hashes, inherited native counts, no changed objects/no candidate.
- qa/local-geometry.json, qa/inspect.log: actual local source geometry and layers.
- qa/route24-refactor-plan.json, qa/optimistic-screen.log: optimistic U13 planning escape; J3 lower-pocket attempt is not the complete-component test.
- qa/complete-screen.json, qa/complete-screen.log: direct connection screen to the actual existing via.
- qa/frontier-obstacles.json: +4V_LED frontier measurements.
- qa/bridge-screen.json, qa/bridge-screen.log, qa/B-reach.json, qa/bridge-blockers.json: two-layer completion screen and every overlapping site's obstacles.
- qa/joint-col13-screen.json, qa/joint-col13-screen-native-final.log: final valid local COL13 restoration blocker.
- qa/reach-last.json: final COL13 reachable grid, NOT the earlier GPIO24 F.Cu grid.
- scripts/: repeatable bounded in-memory native geometry screens. Execute complete_screen.py before bridge_screen.py and bridge_blockers.py, because they intentionally consume its latest reachable grid; execute joint_col13_screen.py last.
