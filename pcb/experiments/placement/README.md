# Maru60 placement experiment — 2026-11-02

## Updated acceptance target: actual whole-board copper, not placement proxy

The user clarified that the objective is **all PCB wiring concatenated into one total**. Accordingly, the placement-screen result below is only a search heuristic, **not a demonstrated actual wire-length reduction**.

The frozen 15-open checkpoint measures **11,478.665 mm actual XY copper centerline**, including every power/GND/signal trace across all copper layers (F.Cu 6,948.777; B.Cu 4,529.889). It has 7,668 trace items and 683 through-vias; the separate nominal via-barrel estimate is 1,092.8 mm. Filled-plane areas are separate, not converted arbitrarily into wire length. The primary agent's later 7-open main measures 12,209.485 mm: more complete can correctly mean longer. Neither incomplete board is a completed-efficiency benchmark.

`ten-experiments.json` and `experiments/` now track ten distinct native design/router experiments. At most two router subprocesses run concurrently, not ten agent sessions. The route-preserving batch budgets four passes/1,200 s/768 MiB per router; a pre-existing full-rip-up probe occupies one slot until terminal. **Only native 0-unconnected / 0-geometric-findings candidates with matching netlist and hard constraints may enter the actual-length ranking.** A budget-exhausted or shorter incomplete board cannot win. `actual_length.py` implements the whole-board meter, `import_probe.py` enforces native post-import checks, and `run_ten.py` records real states/results.

Freerouting's DSN counts are explicitly not native counts: the unchanged frozen control imports as 580 router-unconnected and 106 fixed-item findings despite 15 native opens and no native geometric findings. Its plane/fixed-copper abstraction differs. Native post-import results, not router counters, govern acceptance.

## Placement-screen result (not actual routed optimization)

The closest MCU-to-USB placement is **not** the minimum-total-wiring placement in this search. The best screened board has U1 at **(118, 82) mm, −90°**, with support components repacked and local diode/bypass placements refined. Its pad-net Euclidean minimum-spanning-tree (MST) sum is **8,633.98 mm vs 9,237.53 mm (−6.53%)** for the frozen baseline.

**This is a placement estimate, not routed copper length or a global-optimum proof.** The candidate is deliberately unrouted. It is not a replacement for the separately progressing, 15-open frozen main routing checkpoint, and is not fabrication-ready.

| Placement | U1 mm | Total net MST mm | Change | USB nets mm | Matrix nets mm |
|---|---:|---:|---:|---:|---:|
| Frozen current | 111, 81.5 | 9,237.53 | — | 265.78 | 4,032.59 |
| USB-near, refined | 26, 36 | 8,882.26 | −3.85% | 65.47 | 4,466.56 |
| Intermediate, refined | 80, 84 | 8,864.52 | −4.04% | 197.07 | 4,164.60 |
| Original MCU anchor, support/local refinement | 111, 81.5 | 8,742.40 | −5.36% | 263.15 | 4,016.76 |
| Best screened, refined | 118, 82 | **8,633.98** | **−6.53%** | 248.11 | 3,874.03 |

Moving toward USB cuts USB wiring dramatically, but extends the matrix fanout. Rotation and support-part packing matter: the best MCU is physically slightly farther from USB (126.95 mm center-to-center vs 121.19 mm), yet its USB pad-net metric improves 6.65% and matrix metric improves 3.93%.

The final comparison image uses **actual native KiCad footprint geometry**. Blue/gray lines are MST estimates, **not tracks**. Native KiCad SVG exports are included separately.

## Search coverage and reproducibility

- Frozen board: SHA-256 in `verified-summary.json`; copied from main at commit `2078066` with 15 native unconnected items. The experiment did not edit main.
- KiCad 9.0.2; native `/usr/bin/python3` / `pcbnew`.
- **328 footprints, 1,263 pad/reference/net entries** independently re-extracted and compared.
- **139 hard-fixed footprints**: USB J1, mechanical/switch/stabilizer and LED sites. Every fixed footprint's position, orientation, side and library identity is unchanged.
- **All 189 remaining movable footprints** entered either the group or local search. Best moves 186 of them; no netlist or MCU pin assignment changes.
- **89,376** anchor/rotation screening evaluations: complete rigid controller+flash, protected core without flash, MCU-only diagnostic, and multi-cluster assumptions. A 2 mm anchor grid and 0/90/180/270° relative rotations were used.
- **425,100** support-placement proposals across **13 complete controller layouts**, seeded from **20261102 through 20261111**. Includes broad controller positions from x=26 to x=204 mm, rather than only USB/current choices.
- **313,992** local part-position/rotation proposals across seven complete refinement passes. Each covers 62 diodes, 76 LED bypass capacitors, and four USB-entry components.
- Total: **828,468 evaluation/proposal operations**. Positions can repeat under different cluster assumptions; this is not a count of unique complete-board permutations. An earlier courtyard-only pilot and its rejected results are excluded from this total.
- Files `*-grid.json`, `core-ranking.json`, `broad-search.json`, per-candidate JSON and `*-refinement.json` record anchors, seeds, counts and choices. `local-refinement.json` is the initial central-refinement record.

**Important search limits:** fixed optical components never move; small passives are locally searched rather than globally permuted. MCU/crystal/buck/decoupling geometry is protected as a rigid group. This controlled heuristic search is not exhaustive, and a future re-packing of the critical core itself or alternative package choice could find other solutions.

## Objective and electrical constraints

Metric: for every non-GND, non-NC net, calculate a Euclidean MST over native pad-center coordinates, then sum. Power nets are included and separately reported. GND is excluded because the candidate uses continuous reference planes. This metric does not model obstacles, vias, track width, impedance, return-current paths, Steiner junction savings, trace coupling, or fabrication costs; it is neither actual routed length nor a rigorous lower bound on every possible routed topology.

The 22-part protected core retains relative MCU/crystal/buck/decoupling/USB-series-resistor geometry. Flash and its bypass/pull-up/boot resistor move together; flash anchor remains within 20 mm of MCU. LDO and its capacitors, LED load switch and its support, and level-shifter/bypass groups preserve their local relationships. Reset/debug/boot/series/pulldown components can re-pack separately. LED bypass-to-own-LED center distance cannot increase. Local diode and LED-cap offsets are ±2 mm per axis; USB-entry offsets are ±0.5 mm per axis. Rotations are four quarter-turns.

Best clock-net MST remains **17.481 mm**, identical to baseline. QSPI metric changes from **73.921 to 76.497 mm**; it is not silently claimed improved. USB ESD/fuse/CC movements are bounded local changes, not a USB electrical signoff.

## Geometric and mechanical validation

- Best, USB-near, intermediate and original-anchor refined native boards: **0 native placement DRC findings** with the original 0.15 mm process rules. No DRC exclusions added.
- Every candidate preserves **4 copper layers, 1.6 mm board thickness**, fixed footprint identities and pin/net multisets. Board outline and mechanical holes are unchanged. Existing compact core zone outlines and buck inner-copper exclusion translate/rotate with the core; global ground plane definitions remain.
- Actual pad copper, both sides for through-hole parts, drills, B-side courtyards and board bounds were screened. Native DRC caught and eliminated an early debug-header/front-LED collision and C118/MCU-pad overlap missed by the first courtyard-only pilot.
- Final best required relocating only the non-electrical front board-label text to remove a silk-over-mask warning. No copper or net rule was relaxed.
- Unrouted candidate reports hit KiCad's **499 displayed-unconnected-item cap**. That is not a true 499-connection total and does not establish routing completion.
- Frozen routed baseline DRC has 15 unconnected items, 85 dangling-track warnings and 25 dangling-via warnings. These existing routing warnings are not erased or treated as a production pass by this placement study.

**Not proven:** physical switch-housing/socket body solids, plate/stabilizer assembly envelope, case underside height, connector mouth/insertion fit, mounting bosses, thermal/EMI/USB impedance and return continuity. Native courtyard/drill clearance is only PCB-level screening. No exact case/socket/plate solid model was available here; no mechanical fit certification or fabrication approval is given.

## Congestion proxy

A 10×10 mm grid samples ROW/COL/USB MST segments. This is an uncapacitated geometric concentration proxy, not a router congestion map. P95 segment-length density (mm per 100 mm² tile): baseline **40.71**, USB-near **52.23**, intermediate **48.62**, best **39.85**. Peak densities are 133.90, 117.30, 95.33 and 114.09 respectively. USB-near spreads more wiring into congested matrix corridors despite its very short USB connection. The intermediate choice reduces the single highest peak but has worse overall net length.

## Routing experiment status

The first full-rip-up automatic probe on `best-route-input.kicad_pcb` is now terminal and **rejected**. Four passes took 32.1 minutes; router opens fell 681→115→59→41→35 with zero router-reported violations. Native KiCad post-import instead reports **46 opens and 15 geometric findings** (six oval-slot copper-edge-clearance errors and nine 0.12 mm tracks below the 0.15 mm minimum). Its whole-board actual copper is **8,896.52 mm / 523 vias**, but it cannot enter the efficiency ranking. About **4,793.8 mm** also landed on the intended inner GND-reference layers, violating the stackup role contract. This failed result is retained at `full-reroute-result/`, not promoted to main.

The 10-design batch is stopped after systemic fidelity preflight failure; it is not still running. Corrected inputs apply inactive inner signal layers, disabled automatic neckdown, and explicit oval-NPTH keepouts. Earlier failed controls remain recorded under their actual settings.

The router is local-only. The router is network-denied by seccomp. The native CLI binary failed with a serialization feature error; the bundled Java runtime was used instead. An initial bulk-fanout probe on an earlier central candidate was stopped without an output after remaining in fanout; the best-candidate retry disables bulk fanout and optimizer and uses a four-autorouter-pass budget. It starts with 681 router-reported unrouted items (not directly comparable with KiCad's display count).

**No completed routed-best, routability, actual efficiency win or DRC-complete claim is made.** The failed terminal result is evidence that the placement proxy alone was insufficient. The validated main connectivity work remains separate.

## Useful files

- `placement-comparison-final.png`: final before/after comparison.
- `best_placement.kicad_pcb` / `.kicad_pro`: best placement-only native candidate.
- `usb_near_local_refined.kicad_pcb`, `intermediate_local_refined.kicad_pcb`: actual comparison candidates.
- `frozen.kicad_pcb`: exact routed source checkpoint, unchanged by this study.
- `verified-summary.json`: independently re-extracted native metrics and invariants.
- `*-drc.json`: native KiCad reports, including incomplete connectivity.
- `screen.py`, `optimize.py`, `pack.py`, `batch.py`, `local_pass.py`, `materialize.py`, `verify_all.py`, `visualize.py`: experiment scripts.

## Final status of this bounded routing-comparison attempt

**Comparison blocked; no accepted actual-wire-length winner.** Ten distinct native designs were materialized. Seven cases entered the router: the unchanged control exhausted its 1,200 s budget with no session, four attempts were rejected by an adapter ordering error (subsequently repaired), and two were stopped once systemic input-fidelity disagreements were established. Three further cases remain held, not falsely counted as routed designs. The additional full-rip-up probe completed four passes but was rejected by native geometry, connectivity and layer-role checks.

The focused repair/preflight is complete: existing tracks were locked, inner routing disabled, neckdown disabled, and the oval-slot keepout added in valid DSN declaration order. A DRC-only check of the unchanged control still produced 544 router-unconnected report records (173 disconnected-net reports plus 371 isolated-island records; not a native-open count) against a native baseline with 15 opens, 66 hole-clearance and 40 copper-clearance disagreements. For example, 0.25 mm drills with centers 0.60 mm apart have a 0.35 mm drill gap; the router reports approximately 0.0001 mm for a pair of 0.60 mm copper vias. Native geometry was not modified to hide this discrepancy.

`fidelity-preflight/result.json` and `router-drc.json` preserve this evidence. This establishes a routing-adapter limitation, not that every tested placement is unroutable. A native-equivalent routing backend or a separately validated DSN adapter is needed before the remaining comparative budgets are meaningful. The separately advancing main native board remains the authoritative implementation.


## Focused root-cause follow-up — terminal

Five small DRC-only runs confirm that a drill-metadata-only export repair is insufficient. See `unit-counterexamples/terminal-result.json`, native reports, DSNs and regression assertions. The heavy queue was not restarted.

| Native test geometry | Native opens / geometric errors | Freerouting result |
|---|---:|---|
| Same-net vias, 0.60 mm copper / 0.25 mm drill / 0.60 mm pitch | 0 / 0 | Four false copper-gap errors labeled `holeClearance` |
| Identical exported vias, `attach on` instead of off | Same native geometry | Same four errors |
| Two pads connected through an inner GND plane, center-ended stubs | 0 / 0 | Connected, no findings |
| Same plane circuit, one stub ends 0.20 mm off pad center but within pad | 0 / 0 | Disconnected-net report, dangling trace |
| Same plane circuit, one stub ends 0.10 mm off via center but within annulus copper | 0 / 0 | Disconnected-net report, dangling trace/via |

The via test retains two native one-layer-via warnings; these are not hidden. The three plane tests have no native findings. All native process rules are copied from the frozen project (0.15 mm clearance, 0.25 mm minimum drill); temporary default-project setup errors were corrected before the recorded final regression results.

### Why the metadata hypothesis fails

The official [Padstack source](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/core/library/Padstack.java) infers actual drill radius from the `600:250` name. But the [Via obstacle predicate](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/board/model/items/Via.java) treats another same-net via as an obstacle regardless of attachment setting. Generic [Item clearance checking](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/board/model/items/Item.java) compares the full copper shapes. [DRC report classification](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/drc/DesignRulesChecker.java) calls every via/pin clearance a hole clearance, including SMT pins. The reported 0.0001 mm is therefore not evidence of a missing 0.25 mm drill. No pad was shrunk and no native rule was relaxed.

### Why valid plane-connected native routes appear disconnected

[DrillItem contacts](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/board/model/items/DrillItem.java) require exact trace-endpoint equality with the pin/via center; KiCad accepts physical copper overlap. [ConductionArea contacts](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/board/model/items/ConductionArea.java) do recognize vias centered inside a plane. The center-ended control proves the simple plane itself survives export. The two off-center tests isolate contact-graph loss around the plane, not universal plane deletion. The native exporter also carries zone outlines rather than a certified identical filled-polygon representation; exact plane equivalence on the full PCB remains unproven. The 544 report records must not be presented as 544 native missing connections.

### Safe next implementation route

Use the native KiCad board as the geometry and connectivity authority. Start from a completed native checkpoint, retain approved inner bridges/planes, and optimize small outer-layer track deltas or local movable clusters. Refill zones, run native DRC, validate the inner-layer policy and fixed-footprint/pin-net invariants after each candidate. Rank only candidates retaining zero opens and the same acceptance rules, by summed whole-board copper centerline length; report vias/barrel estimate and zone area separately. Prioritize measured long nets such as +5V_LED and matrix rows rather than USB alone.

A possible future adapter would need copper-overlap-aware contact normalization plus independently tested same-net via/keepout semantics; center-stub normalization alone cannot fix the confirmed annulus discrepancy. That is a separate backend-development task, not a reason to burn the remaining ten-design routing budgets now.

## Opening this private experiment
Open each same-named `.kicad_pro` in KiCad 9.0.2. Custom footprints are included. Official KiCad 9 libraries remain required for library checking. The source references a missing `MX-Hotswap-Socket.step`; do not interpret a partial 3D viewer as mechanical fit evidence. Native board footprints/pad nets are embedded and editable. Placement candidates contain zero tracks on purpose; `frozen` retains the source routed checkpoint. No schematic edits are included, because pin/net identity is unchanged.
