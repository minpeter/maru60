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


## Continued region-to-region planning: second and bounded third transition
The prior one-transition stage is preserved as STAGE2-REPORT.md and STAGE2-FINAL.json. Its stopping point is superseded by this continued planning result: **a second transition does escape the F.Cu pocket**. No route is complete and no candidate PCB has been saved.

Screened 1,701 positions inside the F pocket on a 0.1 mm grid, finite bounds x112.2–119.8/y82.4–89.2 mm. Of these, 228 passed actual all-layer copper and conservative retained-reference-envelope screens. Selected nine north-first spatially separated sites (minimum0.8mm separation between selected sites; cap12). All nine reach a distinct B region; eight survive the explicit native-hole and mutual-drill checks. The initial broader loop was interrupted before completion to impose this finite sample; its log is preserved.

Qualified read-only portal coordinates: (113.2,82.9), (113.6,83.6), (118.9,86.1), (117.0,86.7), (115.1,87.0), (117.7,87.1), (117.0,87.6), (115.4,87.8) mm. Geometry remains 0.5/0.25 mm vias, minimum copper and hole clearance0.15mm, trace width0.15mm, rule-derived inner/outer envelopes0.45/0.40mm. These are planning sites, not saved or finally qualified design changes. All evaluated inner-plane contour/area rows were asserted; prospective envelope subtraction leaves each inner GND layer with one positive contour. Actual refill may reveal further loss and remains mandatory before acceptance.

Rejected second-via position (112.6,83.7): its drill edge is only0.05mm from the first planned via drill, below the0.15mm rule. This mutually colliding proposal is explicitly excluded, despite passing copper-only and existing-conductor reference screens.

Strongest northward portal (113.2,82.9) reaches the B.Cu component bounded by x108.10830080976139–113.89169919023861, y81.54628239022381–85.86106193315423 mm. Its minimum existing-hole edge gap is0.7698039221446918mm and its first-via drill-edge gap is1.0029954387633122mm. It remains enclosed and does not connect to northern GPIO3. Other tested portals go east or south; some B regions meet the finite search boundary. Their negative destination results are explicitly bounded, not evidence against routes outside the region.

Following the clarified scope, assessed a third transition only along the northern edge of the strongest B region: x108.2–113.8/y81.6–82.3mm,0.1mm grid. Forty positions fall inside the actual reachable B component. None meets via copper clearance; none meets the stricter retained-reference envelope screen. Nearest blockers are LED_ENABLE at35 positions, +1V1 at2, +3V3 at2, and GND at1. Example (113.3,81.6) is only0.30mm from the copper edge of +3V3 B track543cfde6-c0cc-494d-bd0d-690025e63549 and +1V1 F track8ced2f34-575e-48f3-a500-8677f6d5ef41. A0.25mm-radius via leaves only0.05mm copper clearance, not the required0.15mm; its0.45mm inner antipad would also intersect retained-conductor reference. No barrier was removed to create a path.

Portal-to-region continuity uses actual native-shape polygons and all-hole-cut GND, not a straight unsupported segment assumption. Every trial has only its own declared transition allowance; mutually different trial sites are not unioned into an optimistic route. B target-via transition windows were not relaxed, so destination negatives are conservative. No precise end-to-end centerline has been constructed; region reachability is planning evidence only.

New evidence: qa/second-transition.json (all1701 sampled rows and9 B-region outcomes), qa/second-transition-audit.json (hole spacing and native plane contour assertions), qa/third-transition.json (all40 northern portals with blocking object UUIDs), corresponding logs and scripts/second_transition.py, second_audit.py, third_transition.py. Reachable region WKT files are preserved for each tested portal.

Current result: eight legal-looking second portals escape the first F pocket, but the finite northern third-portal sample is blocked. A different bounded region or a specifically assessed local reroute may still work. Source, source hash and inherited errors remain unchanged. No candidate hash, DRC/material/net/ERC/cold-refill acceptance or readiness claim exists.


## Final bounded extension: entire best B-region third-portal assessment
The previous northern-only sample is preserved in qa/third-north-only.json and scripts/third_north_only.py. It is superseded as the final stopping point by this whole-region assessment, which deliberately allows lateral progress.

Assessed the entire best B region on the0.1mm grid bounded by x108.2–113.8/y81.6–85.8mm, excluding the prior40 northern sample positions.570 new grid positions lie in that region.85 pass copper plus explicit hole exclusions,96 pass the conservative retained-reference envelope screen, and66 pass both. Selected five spatially distributed representatives using west-first farthest-point sampling with0.4mm minimum spacing and a cap16. No additional regions were recursively searched.

All five selected portals pass exact actual-hole shape spacing to every existing drill and BOTH previously proposed vias, and prospective native inner-plane contour checks. Native all-hole-cut GND remains one positive contour per inner layer after subtraction of all THREE declared envelopes; every area and contour row is asserted. This remains an analytical screen, not a native refill or final route validation.

Two actual F-region groups result:
1. Third portal (109.2,83.7) reaches a NEW western F region bounded x105.24976878864774–111.83155309380301/y75.200002–86.55346026830499mm. This is meaningful north/west routing progress beyond the original pocket, but the region is enclosed and contains no existing GPIO3 destination copper.
2. Third portals (113.6,83.3), (113.0,84.1), (113.6,84.0), (113.1,83.5) return to the original F pocket bounded x112.1892755612236–119.83416560646793/y82.350002–89.22914151002624mm. They do not advance into new routing space.

The strongest planning sequence is first transition(112.6,84.0), second transition(113.2,82.9), third transition(109.2,83.7). No complete centerline to the remote GPIO3 component has been established. Neither reached F region touches the finite search exterior or the destination. Stopped here exactly as requested, without expanding through successive regions or saving dangling CAD.

A provisional whole-region run incorrectly retained the narrower prior broad-phase box, omitting some western obstacles. It is explicitly rejected and preserved as qa/third-whole-region-INVALID-pruning.json/.log, not used as evidence. The corrected broad-phase box x107.5–114.5/y81–86.5mm encloses the entire portal scan plus all copper/antipad margins. Corrected results are the570/66/five counts above. This correction prevented optimistic western obstacles from masquerading as legal routes.

Final evidence: qa/third-whole-region.json (all sample rows/blockers and five reach outcomes), qa/third-whole-region-audit.json (exact drill gaps and asserted three-envelope native plane rows), qa/third-whole-summary.json (grouped regions and strongest sequence), scripts/third_whole_region.py and third_whole_audit.py. Earlier stage evidence is retained.

Final outcome: useful three-transition planning progress, zero completed pairs, zero saved PCB candidates. The immutable source hash remains9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed. Native candidate severity/material/net/ERC/cold-refill checks remain unrun because there is no complete candidate to test. Source remains at inherited9 opens/42 warnings, with separate inherited exact-no-loss and51 guarded-contact limitations. No readiness or SI claim.
