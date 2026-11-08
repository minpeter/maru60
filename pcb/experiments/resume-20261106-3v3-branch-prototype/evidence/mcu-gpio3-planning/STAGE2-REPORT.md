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


## Continued assessment after clarified qualification scope
The initial result is preserved unchanged in INITIAL-REPORT.md and INITIAL-FINAL.json. The refined development scope specifies that a deliberately introduced signal-via drill and rule-derived antipad can be declared in advance as a local transition change for an isolated qualified-development prototype. This does not qualify the strict baseline, excuse remote plane loss, or permit retained-reference loss. The initial drill-area-only stopping reason is superseded.

Before further assessment, froze a new via at (112.6,84.0), copper diameter 0.5 mm, drill 0.25 mm. Actual local inner zone clearance is 0.20 mm, yielding a 0.45 mm inner transition radius. Actual outer zone clearance is 0.15 mm, yielding 0.40 mm outer transition radii. Native outside polygonization is 1 nm. No discretionary extra region is permitted; any future actual refill loss outside those declared regions would fail rather than silently enlarge them. The 0.45 mm survey radius does not authorize 0.45 mm changes on the outer layers.

No retained outer conductor intersects even the larger inner transition envelope. Native subtraction from all-hole-cut inner GND removes 0.6162069755805 mm² on each inner layer, in one enumerated 1299-vertex contour each. The global positive GND contour count remains 1 on both layers; all area/contour rows were asserted. This is prospective envelope geometry, NOT a zone-refill validation. The exact original source is unchanged.

A bounded, continuous polygon route assessment then searched F.Cu within x=99–121 mm, y=23–94 mm, including the entire existing GPIO3 copper destination. It uses actual native copper contours, all-hole-cut In1 GND, the declared new transition and existing GPIO3 via transition windows. Foreign-copper clearance includes 0.075 mm half-width + 0.150 mm clearance with a 0.000002 mm conservative numerical guard; reference is eroded by half-width with the same guard. There is no rectangular-obstacle cache or grid search.

The launch is in a 17.25682699281979 mm² connected free-center pocket, bounds x=112.1892755612236–119.83416560646793 mm, y=82.350002–89.22914151002624 mm. This pocket is strictly interior to the assessment region, so the negative result is not caused by a clipped search boundary. It intersects NONE of the existing GPIO3 destination copper. The preceding y≤86 mm assessment was boundary-clipped and is separately preserved as qualified-route-topology-y86.json; it was not used as final evidence. All 54 nearby foreign-copper boundary witnesses and their UUIDs/nets/positions are listed in qualified-route-topology.json.

No complete concrete route was plausible using this single new transition and F.Cu continuation. Stopped without creating another dangling launch. An additional layer transition or a separately assessed narrow reroute would be a different proposal; neither was silently introduced. This is a bounded single-layer topology result under the stated guarded geometry, not global impossibility or a native DRC result. The new via itself is NOT rejected solely for its drill area.

New evidence: qa/transition-freeze.json, qa/transition-plane-topology.json, qa/qualified-route-topology.json, qa/reachable-region.wkt, qa/qualified-assess.log, scripts/qualified_assess.py. No candidate hash exists; no native candidate DRC/material/net/ERC/cold-refill gates ran. No pair was closed. Existing limitations and inherited source counts remain unchanged.
