# V7 four-reference and whole-LOGO1 correction trial

## Current result

The actual candidate is `candidate-four/pcb/maru60.kicad_pcb`, SHA-256 `2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373`. It is an isolated, unselected trial from the restored selected board `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1`, recovery commit `49ce079404c79d18c85a7f80742f8d1778c47062`.

Fresh actual checks give **92 → 68 warnings**, with **24 exact warning records removed and none added**. The existing **12 expansion-GPIO open-component pairs** remain unchanged. There are no other hard native DRC errors. Fresh ERC and schematic parity are both zero. Complete XML netlists match after normalizing only the export source/date and the absolute URIs of three byte-identical copied project symbol libraries.

The independent final screen finds this exact candidate adoption-eligible within its bounded raw-byte, native-ink, association and electrical non-regression scope. See the separately sealed `v7-four-label-independent-screen-20261104/FINAL_REVIEW.json`, SHA-256 `02ad6343fd6f0d6287187d3efab68cd8ec4ededce864af2cdc63d9eee82e786f`. Selection remains the parent's decision. The generic checker is not certified for arbitrary future edits. This packet does not claim a new full acceptance replay, physical-plane graph, electrical simulation, manufacturing qualification or actual assembled/3D visibility qualification.

## Exact edit scope

All four references retain their text, UUID, visibility, B.Silkscreen layer, mirroring, 0.10 mm stroke and every other style property. Their square sizes change from 0.75 to 0.80 mm.

| Reference | Source anchor, mm | Candidate anchor, mm | Native angle |
|---|---|---|---|
| C100 | (143.60, 75.00) | (146.80, 75.00) | 90° unchanged |
| R140 | (111.07, 32.00) | (114.87, 31.80) | 90° → 180° |
| R160 | (183.07, 85.00) | (185.95, 85.00) | 90° unchanged |
| R134 | (107.50, 43.07) | (106.90, 45.87) | 0° unchanged |

R160's new anchor was inspected and measured afresh on the restored source. Its original text overlaps R159's body and pads; the proposed anchor sits immediately outside R160's own body, without an intervening component.

LOGO1 moves as a complete non-electrical footprint from (193.413393, 83.125000) to **(85.326786, 82.100000) mm**, retaining its 180° orientation and backside artwork. Both polygons retain their exact local vertices, width, fill, layer, UUIDs and relative geometry. The footprint has no pads or zones.

Restoring only the four reference `at`/font-size fields and the LOGO1 footprint anchor reproduces the complete source board structure exactly. Every other raw object and property, including copper, pad geometry, holes, net assignments, saved filled planes, electrical component placement, source C128/USB/power geometry and project rules, is unchanged. All 382 native reference fields are compared, allowing only the four declared edits and the global translation of LOGO1's own reference with its footprint.

The accepted 15 reference fields remain fixed. C124, R121, U8 and R131 remain fixed. The temporary C124/R125 review region is unchanged.

## Same-snapshot native electrical results

- Tracks: **9,752**; vias: **919**; pads: **1,437**; footprints: **382**.
- Track-length sum: **13,181.60473138763 mm**, unchanged.
- Native contact edges: **21,922**, unchanged.
- All **508** complete native conductor partitions are freshly derived from every native edge and match source-to-candidate.
- All 12 DRC open pairs are checked by complete endpoint-component membership and actual UUID, description and position. Five raw representative records changed within the same existing components; this is not a net-name/count-only equivalence.

This is fresh native electrical non-regression evidence, backed by exact full raw electrical/saved-plane geometry. No new physical source-root/plane graph or electrical simulation is represented as having run, and lost historical QA packets are not represented as restored.

## Actual-ink clearance

The rebuilt native checker includes every actual mask-aperture source on this board: **1,759 side-specific objects**, comprising 737 F.Mask pads, 1,014 B.Mask pads and eight U1 B.Mask graphics. There are no mask/silk zones, mask-only pads lacking corresponding copper, untented-via apertures or exposed track/arc apertures in this source. Unsupported encountered categories fail closed. All existing silk, board edges, native courtyards, closed Fab contours and remaining Fab ink are included.

The four new references meet at least 0.15 mm ink-to-mask, ink-to-silk, courtyard and Fab-proxy clearance and at least 0.25 mm edge clearance. Native brackets are last verified noncollision / first collision:

| Item group | Mask, mm | Silk, mm | Courtyard, mm | Closed Fab, mm |
|---|---|---|---|---|
| Four references, minimum | 0.409895–0.409896 | 0.302395–0.302396 | 0.159895–0.159896 | 0.472395–0.472396 |
| Complete LOGO1, minimum | 2.831699–2.831700 | 3.398932–3.398933 | 2.863468–2.863469 | 3.698412–3.698413 |

The four references' minimum edge bracket is 8.134524–8.134525 mm. LOGO1's edge bracket is 6.475000–6.475001 mm; its remaining-Fab-ink bracket is 4.753890–4.753891 mm. Full ink containment passes. The accepted 15 are also freshly rechecked for mask/silk/edge margins and no courtyard/Fab intersections after the new placements.

Fab evidence consists of 390 closed contours, 220 open line components and four other shapes. These are two-dimensional drawing proxies. They do not establish actual assembled body visibility or 3D fit. The project’s 0.0 mm silk-clearance and 0.08 mm stroke rules are unchanged and do not constitute supplier qualification.

## Deliberately excluded R131 and native-created metadata

A five-field prototype is preserved in `candidate/pcb`, board SHA `8a92cd8710e821d91e8b06c3f3b9d2a90cfd30f9ad76949f78c02672cc58ed3e`. A fresh native read of that actual prototype confirms that resized R131 intersects the unmoved U12 reference, UUID `e07bb8f5-f971-42b4-a464-7c90e816f6a3`, with zero gap. R131 was dropped rather than moving another label or inheriting clearance from the rejected nineteen-label bundle.

The first construction stopped at its strict 53-file gate because native SaveBoard created `maru60.kicad_prl`. The failure log and original builder are preserved. The recovered source remains an exact **53-file** tree. The revised candidate contract explicitly permits only that one **2,057-byte native-created local-preference file**, SHA `8c0a828ce6c58ebd31b8835a9bd58efb04385897813f3e5d51b961410868af58`, making the candidate tree **54 files**. Its known historical hash match is recorded, but is not a circuit change or proof that a full lost historical packet was recovered. All 52 non-board recovered source files remain byte-identical.

## Remaining work and review limits

The 68 remaining warnings are 24 text-height, 21 silk-over-copper, 16 silk-overlap, five dangling-track and two dangling-via records. The 12 GPIO opens are still unfinished. No reference or artwork is hidden, deleted or scaled down, and no rule is relaxed.

The earlier nineteen-label exploration was rejected because several labels crossed other components or misleadingly appeared to identify a neighbor. Its favorable warning count does not authorize adoption. The current four-label packet was constructed and remeasured from the actual restored source with newly rebuilt code. Historical checker/evidence bytes are not claimed restored.

## Main deliverables

- `PLAN-four.json`: exact source/candidate hashes, native intended fields, raw field records and complete candidate file map.
- `qa/SCREEN_COMPARISON.json`: exact 24 removed warning records, complete 12 open-pair ledger, native equality and all scope/margin checks.
- `qa/source-ink.json` and `qa/candidate-four-ink.json`: actual native measurements, all 382 fields and complete mask/silk/edge inventories.
- `qa/source-native.json` and `qa/candidate-four-native.json`: full electrical geometry, contacts, components and diagnostic endpoints.
- `qa/SCHEMATIC_CHECKS.json` and `qa/SCHEMATIC_PATH_BINDING.json`: fresh ERC and exact XML/library binding.
- `qa/ATTEMPT_HISTORY.json` and `qa/prototype-five-R131.json`: preserved failed metadata gate and measured R131 dependency.
- `qa/preview/candidate-four-preview.png`: five native detail panels.
- `qa/fullboard-preview/candidate-four-fullboard.png`: full front/back copper, mask and silk with same-snapshot tracks, vias, length and DRC/ERC/parity results.

Both preview directories contain native SVGs, execution records and hash bindings. Existing unrelated overlaps remain visible. No CAD object is removed or altered for visualization.
