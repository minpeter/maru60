# GPIO25 after +3V3 branch cleanup: bounded native-shape analysis

## Result

No PCB candidate was saved, no geometry was edited, and no open pair was closed. Source remains 9 native opens / 39 native warnings. The new space is real, but an unchanged-copper route and the specifically assessed 49-segment GPIO_ISOLATE B.Cu reroute scope do not connect the two B.Cu regions. This is a finite-grid planning blocker, not a global impossibility or a validated layout.

## Provenance

Current immutable source: selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype/pcb/maru60.kicad_pcb
SHA256: 88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e
Selected commit: fa96a7c8b334f0f496ab7cdb4de9b18cf9276966.
Old comparison source: continuation-c782/combined27fix2/pcb/maru60.kicad_pcb
SHA256: 9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed.
Candidate SHA256: not applicable. No candidate exists.

All native runs used installed KiCad 9.0.2+dfsg-1 via run-kicad.sh. No installation, remote action, saved-environment use, or credential action occurred.

## Complete endpoint components

The source corrected all-through-hole material graph identifies three separate EXT_GPIO25 components. Each consists of exactly one positive B.Cu pad island, with no attached track/via. They are U11.15 cff436d2-a051-486a-8eda-ad80c8687157 at (107.1,37.325), J3.6 bee40e5c-5047-43dd-8262-df42b4062ba6 at (93.5,39), and U13.11 a18e6e59-fb74-4513-a5f4-6a34d9223429 at (89.45,42.5). See qa/target-components.json. This avoids substituting DRC representative endpoints for whole material components.

## New versus old reachable regions

At 0.025 mm grid, 0.15 mm track width/clearance with conservative 0.205 mm clearance near drilled signals, the J3-derived F.Cu region has bbox (89.225,39.35)-(99.3,43.3). The previously found transition (98.15,40.6) still passes the conservative via-site screen. Its B.Cu region now reaches x106.2, versus the historical x101.425. It cannot reach U11.15.

An independently repeated comparison uses the same ordinary 0.15 mm clearance everywhere, finer 0.0125 mm grid and fixed boxes on both old and new boards:

- Old bridge B.Cu: 35,955 sites, bbox (95.5,39.5125)-(101.5125,42.15).
- New bridge B.Cu: 56,750 sites, bbox (95.5,37.25)-(106.2,42.15).
- Old and new U11 B.Cu pocket: identical 5,018 sites, bbox (106.275,37.1125)-(108.6625,38.9).
- Bridge/pocket grid intersection: zero on both.
- Ordinary-rule 0.50 mm through-via screening at every new U11 pocket site: zero clear sites. Thus this negative result is not merely caused by the extra conservative 0.205 mm reference margin. GPIO25_ISO F.Cu, GPIO_ISOLATE B.Cu and ROW1 F.Cu are principal barriers, alongside neighboring pads/vias. All per-site actual native-shape gap records are retained.

The closest grid points are (106.275,37.575) in the pocket and (106.125,37.85) in the bridge region, 0.3132491022 mm apart. A 0.15 mm connecting trace has only 0.127913 mm clearance to EXT_GPIO24 object 79e90551-63f2-4d3a-82a7-9d5d6259c3d6 and 0.114775 mm to EXT_GPIO26 object 9802007f-2fe7-4459-b27f-4f1f6eb27cb3. Both fail 0.15 mm. The closest seam is not GPIO_ISOLATE.

## Scoped GPIO_ISOLATE detour assessment

The 49 B.Cu segments of GPIO_ISOLATE lying wholly in x108.1..109.3, y35.05..41.5 were assessed in memory only. No PCB objects were removed or saved. As a deliberately optimistic *failure bound*, their obstacle entries alone were omitted. Even then the bridge reachable set remained exactly 12,958 sites with max x106.2 at the conservative 0.025 mm screen, and no path to U11.15 existed. Any restored version of that conductor can only restrict this region further. Therefore a complete direct B.Cu bridge route plus restored GPIO_ISOLATE path within this scope cannot be proposed by this screen. No missing conductor is included in a proposed solution; there is no proposed solution.

The unchanged-copper eastern bridge frontier (x >=105, fine ordinary-rule scan) has 857 outward grid edges, obstructed by EXT_GPIO24, EXT_GPIO10, EXT_GPIO27 and EXT_GPIO26. None is GPIO_ISOLATE. Moving only the assessed isolate segments does not remove these actual remaining barriers.

The source material graph records three positive retained-contact edges for the 49-segment scope: one at (108.1,35.05), and two at the lower end adjoining a retained short segment and the pad centered at (109.325,41.5). Their independently guarded overlap areas are 0.01779124922, 0.0185772304645 and 0.0800828929255 mm². A future actual reroute must preserve all three material contacts, not just assume two endpoint labels suffice. Exact UUIDs/coordinates are in qa/joint-scope.json and qa/retained-contact-details.json.

The rejected historical rightward x109.6 detour was not reused. No other conductor was rerouted. No optimistic clearance claim was made after deleting foreign material. The scoped analysis does not rule out a materially broader joint reroute, a different via topology enabled by such a reroute, or a route between grid samples; those are outside this bounded assessment.

## Validation boundaries

There was no saved candidate, so the candidate-native gate, fresh candidate material graph, ERC/parity rerun, full all-hole plane/reference/contact comparisons, and cold58 comparison were intentionally not run or claimed. The source graph is a verified existing input, not a newly exported candidate result. No plane loss, contour-row pass, SI result, or electrical stability improvement is claimed. Source51 guarded-contact diagnostics and inherited exact-no-loss failures remain separate and unresolved.

Native shape screening includes track/pad/via obstacles and physical copper-layer membership. It does not certify zone refill, all-hole physical material integrity, return-current quality, manufacturing, or SI. A future candidate must first pass native severity/category checks, semantic complete-component merger, and then all per-row area AND contour assertions and other required gates.

## Evidence

- scripts/: reproducible native shape screens and comparison scripts.
- qa/bridge25-attempts.json, bridge.log: reassessed second transition.
- new-rules/qa/SUMMARY.json, old-rules/qa/SUMMARY.json: matched ordinary-rule fine-grid results.
- new-rules/qa/via-blockers.json: every scanned U11 via site's blockers.
- qa/seam.json, bridge-frontier.json: concrete remaining obstacles.
- qa/joint-plan.json, joint.log: finite isolate-scope failure bound.
- qa/PROVENANCE.json: final source hash recheck and no candidate declaration.

## Follow-up: precise interface classification and positive next-scope diagnostic

The closest EXT_GPIO24 object 79e90551-63f2-4d3a-82a7-9d5d6259c3d6 is a **through-via** at (105.8,37.5), not a fixed U11 pad. EXT_GPIO26 object 9802007f-2fe7-4459-b27f-4f1f6eb27cb3 is the **fixed U11.14 pad** at (107.1,37.975). These are the only GPIO24/GPIO26 objects touching the sampled eastern bridge frontier. See qa/interface-objects.json.

A diagnostic that excludes only that via from obstacle queries (retains every pad and all tracks, including both GPIO24 attached tracks) finds this complete B.Cu geometric path at ordinary 0.15 mm clearance and 0.0125 mm grid:
(98.15,40.6) -> (101.025,40.05) -> (103.6875,38.075) -> (106.0625,37.775) -> (106.2875,37.5625) -> (106.4125,37.525) -> (107.1,37.325).

This is **not a candidate or a valid route**: the real via still exists on the immutable source, and the diagnostic has not restored its GPIO24 connection, drill, plane/reference geometry or return-current transition. It establishes a materially useful next design scope: jointly reposition/reconnect the GPIO24 transition while opening GPIO25's passage, without moving U11 pads or assuming GPIO26 must change. No larger design was saved.

The via currently belongs to the active material component joining J3.5 (8acfaaa0-99ff-425a-b370-70be0fbb3868) and U11.16 (3827e42c-c508-4185-8351-759c94512528). Its two positive source contact edges are:
- F.Cu track b9d330ac-1b1c-42cf-989e-7a81dbfe810a from (104.35,38.0) to (105.8,37.5), guarded contact area 0.019373619872 mm².
- B.Cu track 27d5bab5-97b2-409f-970d-ef67b5e0bc6a from (106.275,36.9) to (105.8,37.5), guarded contact area 0.019373332348 mm².

A future joint attempt must restore both active contacts and preserve the complete J3.5/U11.16 component, then meet all source-preservation, native DRC, exact reference, material and plane gates. A missing-via diagnostic alone does not authorize success. See qa/interface-traces-omitted.json (the omitted non-pad object is explicitly the via), qa/via24-contacts.json, and scripts/classify_interface.py.
