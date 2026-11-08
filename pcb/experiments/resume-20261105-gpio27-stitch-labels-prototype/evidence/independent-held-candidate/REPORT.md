# Independent combined27 review

Candidate SHA256: b1e3b41f868bebc2915264d1136e356a67b3b8896de3650068bd1c438aa62913.

## Recommendation

HOLD checkpoint selection pending correction or explicitly reviewed disposition of the newly verified GPIO26 adjacent-reference exception. The earlier provisional recommendation in this report is superseded. No unrelated raw-object or material-contact regression was found, but the claimed zero newly unsupported coverage across all 137 retained GPIO10/26 tracks is false. This is not fabrication-ready or a demonstrated stable/SI-qualified board.

The c782123 source is itself a qualified prototype, not the strict baseline. Its earlier exact no-loss failure from a tiny remote +4V_LED boundary difference remains inherited. The preserved bbf61e6 strict baseline must remain distinct. Header GPIO10 rerouting and GPIO26 movement intentionally do not preserve exact prior geometry or all old contact patches.

## Independently completed checks

- Verified exact candidate, source, and intermediate hashes.
- Parsed source→header scope: exactly 15 added conductors and six changed old conductors. Only declared coordinate fields and zone fills change; restoring them reconstructs the parsed source exactly.
- Parsed header→combined scope: exactly the authorized GND stitch and four Reference fields. The four whole footprints exactly match the label intermediate. All other parsed objects, including raw zone-fill polygons, are exact. Restoring the four footprints and removing the stitch reconstructs the header board exactly.
- All 57 companion project files remain byte-identical to the source.
- Independently compared the complete supplied material exports against their board hashes. Header→combined preserves all direct contact measurements, all old object-material nodes, pad partitions, guarded-contact diagnostics and old barrel joins. Two stitch-to-inner-plane contacts are added, each 0.147260768066 mm². This statement intentionally does not assert unchanged zone-material-node areas: the new drill removes 0.049087681002 mm² from each inner-plane material node.
- Fresh native KiCad DRC: nine unconnected pairs, 42 warnings, zero parity violations and no other DRC errors. All warning records exactly match the main validation. One native open representative differs, but both representatives map to the same complete material component; all nine canonical open pairs match exactly.
- Fresh native GPIO10 contact-patch recheck on combined: all three retired far-end UUID contacts are reproduced exactly by the new last segment, with zero loss/gain. The same-endpoint start contact grows from 0.0177921599255 to 0.018878311454 mm², but old-minus-new remains 1.37825e-8 mm² across 26 contours. This is explicitly declared rerouted copper, not an unchanged contact or a zero-loss result.
- Visually inspected header F.Cu and B.Cu native-shape detail images. These are conductor diagrams, not independent filled-plane, impedance, or fabrication-quality proofs. Combined raw conductor geometry there is identical to header.

## Plane and return-path review

Fresh full-board plane recomputation completed successfully, but found a failed affected-route coverage result. It exactly reproduces a nonzero record already present in header/qa/plane-review.json; header/REPORT27.md's assertion of zero across all 137 retained affected tracks overstates its own JSON evidence.

- GPIO26 F.Cu track 55e5d0cf-c179-4e88-925d-241a5a9d4416 has 0.0003496908615 mm² of newly unsupported current copper outside the declared moved-via window, in one outline.
- Bounds: x95.199320–95.453085 mm, y40.187554–40.422605 mm. Exact integer vertices are in exception-geometry.json.
- It lies near the unchanged GPIO26 via 075334c3-e6fd-4cf3-8599-1a58cef3db7f at (95.075,40.175), not the moved-via window at (96.65,41.625).
- Exact intersection diagnosis: all 0.0003496908615 mm² lies on current copper; zero lies on old copper or on either old/current reference plane. It is added departure copper over an existing source-via void, not newly lost plane.
- The track starts at that unchanged via. Its far endpoint changed from (96.8,41.775) to (96.65,41.625), rotating its approach at the unchanged start.
- The exception is derived from CURRENT track material minus CURRENT adjacent In1.Cu GND material, subtracting the old unsupported footprint and then the declared moved-via window. It is real current unsupported geometry under this stated gate, not merely a retired old-copper shadow. Do not widen the transition exception to conceal it.

The other full-board results pass their limited geometric predicates: each inner plane remains one component; source→combined loss is 0.880300188708 mm² and gain 0.189959295388 mm² per plane; zero loss lies outside the three previously declared transition windows plus the actual new stitch drill. Exactly four old signal projections change, all declared refactors. All newly added GPIO10/27 track coverage tests have zero outside-window loss. These findings do not erase the one affected retained-track failure above.

The initial independent drill recomputation was checked still running and interrupted (exit130) because it unnecessarily performed thousands of full-hole Booleans before rejecting disjoint conductors. Its log remains native-geometry-incomplete.log. A conservative bounding-box rejection version then completed: every old object is tested against the tiny loss bounding box before exact material intersection, preserving full-board scope. It confirms header→combined inner-plane loss is exactly the new stitch drill, 0.049087681002 mm² per plane, with no old-signal shadow loss from that drill. The planes remain one component and the separate GPIO10 contact-patch measurements reproduce exactly.

No transition window, tolerance, or acceptance gate was expanded. No SI/EMI/loop-inductance or stability improvement follows from these nominal geometry results.

## Explicit remaining risks and limits

- Nine physical open pairs remain: three header and six MCU. The board is not electrically complete.
- 42 DRC warnings remain: 15 text-height, 13 silk-over-copper, 10 silk-overlap, four dangling tracks.
- 51 inherited guarded-contact proof failures remain. Unchanged failures are not positive proofs of all contacts.
- New header signal-transition nearest verified GND-via distances are about 2.481 mm and 1.572 mm; the moved GPIO26 transition is about 2.341 mm from its nearest verified GND via. Proximity is not a demonstrated low-inductance return.
- Via barrels use nominal geometry/material graph assumptions, not manufacturing or assembled-board measurements.
- Active regulator behavior, effective capacitor values, extracted parasitics, edge-rate/loading variation, SI/EMI and hardware validation remain unqualified. The reviewed synthetic power sensitivity applies to unchanged nameplate capacitor values only; it is not current-board active-regulator simulation.
- Main cold refill, ERC, raw/native net identity and reference-courtyard results were not independently rerun here. Review their completed exact-candidate evidence before checkpoint selection.
- No PCB edits, installs, pushes, fabrication or publication performed by this reviewer.

## Evidence

- audit.py / audit.json: independent composition and supplied material-graph comparison.
- audit_header_scope.py / header-scope.json: source→header declared raw scope.
- drc.json / drc.log; check_open_pairs.py / drc-comparison.json: fresh DRC and complete component normalization.
- check_contacts.py / retired-contact-patches.json: fresh native contact Booleans, using reviewed header contact method against combined.
- native_geometry_bounded.py / native-geometry.json / native-geometry.log: completed conservative full-board drill/material computation. Original unoptimized run logged separately as incomplete.
- full_plane_sweep.py / full-plane-review.json / full-plane.log: completed full-board method against combined; explicit retained-track coverage failure.
- inspect_exception.py / exception-geometry.json: exact current unsupported polygon and location diagnosis.
