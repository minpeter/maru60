# P3 +3V3 source repair: terminal scoped reconstruction

**Coordinator review candidate, not adopted main/A25, powered-rail, manufacturing, current, PI/SI or assembly qualification.** The C105 two-track study is not included. No part, pad, old copper, zone definition or rule was changed.

## Immutable candidate
- PCB SHA256: `29a77ef306e78f3c6e25a5bdaca68aa22aef278acdabeed0cbb3db7d78a4a8e2`.
- Source: frozen rejected S3 `cacce2aa6872d3e060b9dbc37e6527b73f3e7a6c8d1e09921667d2d2d2fc39bf`; that source had a +3V3 regression despite improved +1V1 connectivity.
- Exactly 14 additive +3V3 objects: 11 tracks and three standard Ø0.50/0.25 mm through-vias. All 9,037 source copper objects, 340 footprints, 1,275 physical pads, 924 numbered pin identities, 13 zone definitions and project bytes are retained exactly. The exact UUID/S-expression ledger is included.
- Native all-severity/all-track: **79 unconnected items, 0 hard errors, 119 warnings, parity 0, ERC 0**. Warnings are 107 inherited dangling tracks, ten inherited dangling vias and two inherited silk-over-copper. No new neck/thermal violation.
- Every 10,339 intended semantic net name remains exact through load/build/refill/save/reload. Cold refill is byte-identical at the final hash. The initial fill cache changed serialization once, but native Boolean lost/gained area was zero on every layer; the second fill is the fixed point. All final gates were freshly rerun on the final hash, not reused from the first cache.

## Restored actual source paths
The actual U2.5 source reaches the new tap (20.7,30.4) through the existing U2/C101 component and its filled B +3V3 island. The shared F bridge restores **C102.1, U1.49, U1.30 and U1.38**, the four real endpoints lost by the rejected S3 radial feeds. All 13 source witnesses retain every S2 reached endpoint. Nine of ten +1V1 pads remain reached (TP5 open), LX remains reached, and all six S2 ground restorations remain; C105.2 is the sole ground-open endpoint. C199.2 shares a real filled F GND island with U1 EP plated pads.

The source-tap-to-U1.49 new positive copper centerline is **5.951352 mm**, with two via transitions. Tap-to-U1.38 is **11.534172 mm**, with two transitions. These exclude the prior U2-to-tap source pour and physical barrel lengths. They are not complete supply or return-loop lengths. Added copper totals: F 0.30 mm width, 4.854138 mm; F 0.25 mm width, 5.947566 mm; B 0.20 mm width, 2.133820 mm.

The 0.25 mm F spine uses the existing U1 EP plated-pad grid channel, between 0.60 mm pads at 1.20 mm pitch. Nominal track-to-pad clearance is 0.175 mm against the 0.150 mm project rule. The 0.025 mm rule margin alone neither proves nor disproves manufacturing capability. All original plated pads and source-ground paths remain. Current/thermal/decoupling qualification is still open.

The three new +3V3 vias and their nearest real source-reached GND transfers are:
- (20.7,30.4) → GND via (21.463,30.425): **0.763409 mm** center distance.
- (23.7,31.6) → PGND via (23.1,31.3): **0.670820 mm**.
- (22.825,34.4) → U1 EP plated pad (24.3,34.0): **1.528275 mm**.
Actual In1/In2 source-island membership is recorded, not inferred from net names. Distances are not return-loop impedance or waveform proof.

## Reference and fill results
All **7,947 retained outer tracks** have zero new centerline or parallel-edge GND-reference loss. All 27 simultaneous local control escapes remain exact and connected.

The new-route audit has one explicit bounded caveat: the B VIN arm from U1.49 (23.9,30.55) to (23.9,31.2), width 0.20 mm, has **0.509167 mm right-edge-only missing In2 reference** at x23.8/y30.55–31.059167. The cause is the unchanged intentional LX inner keepout, whose east edge is x23.85 and south edge y31.05. Its nominal intrusion into this track is at most 0.05 mm. All new-feed centerlines and left edges have zero missing reference outside categorized own-via neighborhoods. This is not a plane-wide signal split, but it remains a documented power-return/PI review caveat, not a blanket waiver or current qualification.

Exact Boolean fill losses/gains are in audit-final.json. Main losses versus rejected S3: F GND 6.878087859 mm²; In1 and In2 GND each 1.968690117 mm² from three positive-via antipads; B +1V1 0.105860714 mm². B +3V3 gains 0.098702778 mm²; numerical sub-nanometer-area changes are listed rather than hidden. All source/endpoints and retained-reference gates were checked after these changes.

An earlier outer F spine restored +3V3 but isolated C199 ground and was rejected. An intermediate EP-grid candidate had a 0.308951 mm edge-only deficit on the existing S3 +1V1 feed. One bounded via adjustment removed it while retaining all sources. Those variants remain separately recoverable; none was merged.

## Remaining scope and resumption
This repair restores the S3 source regression, not the complete P3 power architecture. +3V3 still has 11 unreached physical endpoints, +1V1 TP5 remains open, AVDD C104.1/U1.46 remains open, downstream +5V U7/C120/TP3 remains open, and C105 ground/other intentional interfaces remain. Buck input and FB connectivity do not establish an operational regulator while AVDD/source/current/startup gates remain open.

For subsequent AVDD work, the F source via is (20.7,30.4), the rise is x20.7/y30.4–31.9, the crossing is y31.9/x20.7–23.75, and the VIN branch runs to (23.7,31.6). This is an exact obstacle ledger, not a blanket reservation of the AVDD area. The EP-grid spine is x24.9/y31.9–34.6, then west at y34.6 to x23.7 and to the lower via. Parent owns composition and final gates. Rebuild from the frozen source plus exactly the 14 additions, clear stale fills, run intended-net guards and all current native/source/reference/cold checks. Do not merge earlier rejected versions or the separate C105 study blindly.
