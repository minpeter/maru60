# MCU_GPIO3 bounded escape assessment

Result: no route closed, no candidate saved, source unchanged. Stopped at a concrete geometry blocker before any board edits. This is not a proof that all GPIO3 routing is impossible.

Source PCB: /workspace/shared/maru60-resume/continuation-c782/combined27fix2/pcb/maru60.kicad_pcb
SHA256: 9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed

## Useful result
U1 pad 5 (5a0545bd-febf-49dd-9baa-b129430d4f9c) is at (112.2,84.95) mm on B.Cu. Its existing remote component includes track 7610c2f0-d25f-5392-9c6d-51572f345960 at (104,33.325) to (104.95,33.0). Closing it requires a long connection, not a tiny representative-pair bridge.

A 0.15 mm B.Cu inward dogleg (112.2,84.95) → (112.2,84.25) → (112.6,84.0), followed by a standard 0.5/0.25 mm through-via, passes a local actual-object copper clearance screen. First segment minimum foreign B clearance is 0.21 mm; second is 0.346525101 mm. Proposed via minimum F clearance is 0.25 mm and other copper layers are at least 0.323411767 mm. Both segment shadows are fully supported by source In2 GND after subtraction of every actual through-drill.

But the new drill alone necessarily removes 0.049086866958 mm² of source GND on EACH of In1 and In2. These are positive native polygon intersections, not an artifact of rectangle caching or a tolerance. Each intersection is one explicitly enumerated contour; all area and contour rows were asserted. Antipad removal would only enlarge this lower bound. Therefore this proposed escape fails the required strict exact-no-real-GND-loss gate even before cold refill. No tolerance waiver or unrelated power-rail reroute was attempted.

Five simple escape variants are preserved in qa/escape-screen.json. Straight inward/south via placements hit the existing F.Cu +1V1 0.6 mm rail f6b3e19b-5c04-48f1-baf9-4cc5b9d4e682; others also violate B.Cu ROW2/+1V1 clearance. The dogleg avoids those copper obstacles but not the strict plane-loss blocker.

## Evidence and scope
- qa/source-net.json: full existing GPIO3 object inventory.
- qa/nearby-objects.json: source local inventory.
- qa/escape-screen.json and .log: five bounded analytic variants.
- qa/detour-screen.json and .log: native source GND polygons, all-hole cuts, exact drill-loss contours and actual-copper clearance screen.
- scripts/inventory.py, assess.py, assess_detour.py: reproducible scripts. Execute with run-kicad.sh /usr/bin/python3.
- FINAL.json: machine-readable status.

All-clearance distances use actual native shape contours converted to Shapely, not cached rectangular obstacles. A conservative broad-phase region contains the full proposed copper and clearance margin. GND support and mandatory drill-loss proof use native polygon booleans against actual filled zones, subtracting all physical through-holes. Zone refill and candidate DRC were not invoked because no candidate board was created; no candidate full-material, ERC, net-identity or cold-refill pass is claimed. Source remains at inherited 9 open pairs and 42 warnings. Existing strict exact-no-loss failure and 51 guarded-contact proof failures remain separate. No simulation, SI, active-power, hardware, or manufacturing readiness claim.
