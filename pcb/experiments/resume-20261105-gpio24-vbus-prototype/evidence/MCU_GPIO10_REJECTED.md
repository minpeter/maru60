# Plane-aware GPIO10 escape: finite blocker, paused

No new routed candidate is selected. The selected26b source is unchanged, and the earlier rejected wide10b evidence is preserved.

## Exact source

Complete source copy: `source/pcb/`.
Source PCB SHA256: `04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99`.
Upstream source: `../header-routing/frozen26b/pcb/`.
The selected source retains 11 expansion open pairs. No firmware, project rule, component position, original conductor or release status was edited by this experiment.

## Bounded local route and refactor screens

The GPIO10 screen covered x103–110 / y84–89 on a 0.025 mm grid. Track width was 0.15 mm with unchanged native 0.15 mm clearance. New via candidates used a 0.456 mm source-shadow exclusion radius: the actual 0.20 mm inner-plane clearance, 0.25 mm via radius, 0.005 mm observed polygon extent, and 0.001 mm screening margin. Existing through-drills were removed from the reference-plane polygons. No Unfracture was used.

A route from U1 pad14 (108.6,84.95) to local B.Cu waypoint (103.05,84.65) exists if new-reference coverage is not required. With actual nearest-plane coverage required, the finite search explored 16,240 vertices and found no route. It encountered 334 reachable legal sampled via sites, so the issue is not simply an absence of via space. This is bounded search evidence, not proof of general routing impossibility.

The obstructing In1 reference gap is associated with the local COL6 route between its existing vias at (107.25,86.75) and (104.45,88.6). A proposed transfer of its five 0.15 mm In1 segments to B.Cu was screened before making any edit. Direct transfer crosses KEY_RGB track `9bd9d9fb-9f33-4e31-82f9-aec90d2a8051` and ROW2 track `7997dc47-4bb3-438c-822a-6104e7424fff`. A B-only detour search in x103.75–108 / y85.25–89, with In2 reference coverage outside the existing terminal-via envelopes, explored 962 vertices without a connection. Therefore no COL6 refactor board was produced, and all source copper remains unchanged.

## Native refill probes

Each isolated probe adds only one disconnected MCU_GPIO10 through-via, diameter 0.50 mm and drill 0.25 mm. They are geometric test articles, not routed or selectable candidates.

### Entry site: rejected

Position: (107.95,86.60).
File: `probe-entry/pcb/maru60.kicad_pcb`.
SHA256: `a95aad550b5879e8730f16626710673943b5984c26f9c199cfc44c47b75cb8ff`.

Actual normal refill removes 1.636641335072 mm² of In1 GND, including 1.1168600358625 mm² outside the nominal 0.455 mm antipad envelope. In2 loses 0.529062326909 mm², including 0.0098462848185 mm² outside the envelope. Both planes still report one connected physical component, but old source shadows lose support. For example, COL0 F.Cu loses 0.0686301839445 mm² of In1 reference and KEY_RGB B.Cu has 0.07061535 mm² of In1 projection loss. COL4 and COL6 shadows also have recorded losses. Not every listed cross-plane projection is the nearest reference; the COL0 F.Cu→In1 loss alone is sufficient to reject the site.

This is a plane-neck/island removal effect that survives the larger circle exclusion screen. Actual filled-plane subtraction, rather than copper clearance or component count, detects it.

### Exit site: passes only the bounded plane-loss screen

Position: (104.25,85.95).
File: `probe-exit/pcb/maru60.kicad_pcb`.
SHA256: `3c4c08dff37f30dbb6191942d6b21951cc5f6847892441d2bdb0e09035431c16`.

Each plane loses 0.641253319277 mm², wholly within the 0.455 mm envelope, with no overlap against the screened old signal shadows. Each plane remains one physical component. Tiny gained area of 0.0000000933455 mm² per plane is recorded, not discarded.

This does not accept a route or qualify a return transition. A full material-contact export, nearby GND transition audit, cold refill and independent review were not run for this disconnected probe.

## Checks and limits

For both probes, native DRC reports 12 open pairs and 52 warnings: one intentional extra open and one added dangling-via warning relative to source26b. There are no other hard errors and schematic parity is zero. All 1,064 schematic XML pin bindings and all raw/native LoadBoard/BuildConnectivity net identities match. Native fill also preserved all in-memory object net names.

Plane checks use actual saved fills minus every physical through-drill. Source signal shadows were checked in x102–111 / y83–90, with global loss outside the declared via envelope checked separately. Entry has global outside-envelope loss and is rejected; exit has none. These are nominal geometry checks, not SI, EMC, PDN or hardware qualification.

No new routed-candidate ERC, full material graph, independent review or hardware tests are claimed. Original circuit files are unchanged. Source26b is not replaced by either probe.

## Next constraint, not another broad search

Do not reuse the entry site merely because a clearance or circle mask permits it. The entry transition must avoid the refill-sensitive In1 neck near the COL6 crossing. The exit site is a useful bounded geometric witness for later work. Any resumed local redesign needs to resolve the COL6/KEY_RGB/ROW2 crossing or find a different referenced entry pocket, then test real refill and original contact/reference preservation before constructing a whole GPIO route.

Further GPIO10 search is paused as requested by the parent.

## Evidence

- `qa/local-screen.json` and local images: plane-aware and permissive search comparison.
- `qa/col6-screen.json`: finite B.Cu refactor screen.
- `qa/native-via-probes.json`: exact source/probe hashes and physical plane-loss witnesses.
- `qa/probe-entry-drc.json`, `qa/probe-exit-drc.json`: native diagnostics.
- `qa/probe-entry-net-identity.json`, `qa/probe-exit-net-identity.json`: independent identity checks.
- `scripts/`: executed source-bound screen/probe implementations.
