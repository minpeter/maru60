# Bounded MCU GPIO27 escape repair: both variants rejected

No MCU pair was closed. No partial escape is selected. The two-variant repair set is complete and paused; no continuation search ran because neither variant passed both prerequisite gates. The frozen 9-open/42-warning checkpoint and previous rejected C remain unchanged.

## Exact source and candidates

- Source: `source/pcb/maru60.kicad_pcb`, SHA256 `9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed`. All 58 files match the original `continuation-c782/combined27fix2/pcb`.
- Rejected D: `repair-D/pcb/maru60.kicad_pcb`, SHA256 `dc152488552f56ce44641108be78be7928083bf04849242b7e6ba25eed0ca091`.
- Rejected E: `repair-E/pcb/maru60.kicad_pcb`, SHA256 `f0f604149199b14945edb481b1a8330ddb4c5f7eb12fc3153419d06dba3de865`.

Each saved variant received a complete native DRC severity/category gate before any deeper checks. An initial assembly failed in memory on a read-only UUID property before saving; `assembly-not-saved/` is only an exact source copy, explicitly labeled. Its baseline DRC is not counted as a candidate result.

## D: native clearance passes, adjacent reference fails

The power rail remains 0.60 mm wide with original endpoint vias at (111.4,75.7) and (111.4,79.3505). Its upper jog runs from (111.4,75.7) to (111.28,76.22); the middle remains at x111.28, with the lower endpoint leg unchanged from the prior experimental design. This avoids the four clearance errors caused by C's much earlier full 0.12 mm left shift.

Native DRC: **9 open pairs, 43 warnings, 0 other hard errors, parity 0**. The warnings are 15 text-height, 13 silk-over-copper, 10 silk-overlap, 4 dangling-track and 1 dangling-via. All 42 source warnings are exactly preserved; the one added warning belongs to the incomplete MCU_GPIO27 launch. Fresh ERC is 0. Fresh raw/native net identity and all 1,064 schematic pin bindings pass. The nine physical open-component pairs exactly match the source, despite a changed native representative on GPIO27.

**D is rejected:** upper-jog track `db39d882-6ecf-4006-b107-6b00b1abd04a` has **0.000004713901 mm²** of actual In1-adjacent-reference deficit outside the unchanged own-via transition envelope. The deficit is bounded by x111.594518–111.600970 / y76.163287–76.167096. Its seven exact polygon vertices are saved in `qa/repair-D-failure-geometry.json`. No tolerance waiver or enlarged transition envelope is applied.

D's deeper checks, which started only after its native gate passed:

- Cold load, connectivity build, fill and save: all 58 files byte-identical; refill approximately 3.00 seconds.
- Corrected all-hole material graph: complete named pad inventory/partitions unchanged; no unmodified object changes, old root splits, unrelated accepted-edge changes or unrelated witness changes. All 247 GND pads remain on the J1 root. All ten +1V1 pad bindings remain on one root. The 51 inherited guarded-contact diagnostic failures remain 51, separate from native warnings.
- Both actual drilled inner planes remain globally connected, but retain real local web changes. In1 loss/gain: 0.4863510432655 / 0.130372431028 mm². In2: 0.733131710302 / 0.129225117366 mm². Loss outside the two unchanged nominal 0.455 mm transition windows remains 0.038611251318 and 0.0370067392085 mm². Both include a remote 0.00000004586 mm² difference, retained in the report. A small In2 clipping region loses a shortcut; larger clips remain connected. This does not establish an acceptable return path.
- All 12,876 source signal-layer shadows were checked using F.Cu→In1 and B.Cu→In2. No retained, unmodified source conductor loses its nearest reference. All new/modified track tests pass except the upper power jog described above. The short modified COL5 In1 track is evaluated against In2. No new In2 signal track exists.
- +1V1 path length changes from 3.6505 to 3.713872190050 mm (+0.063372190050). Power-copper union removes 0.382629144355 mm² and adds 0.418672234995 mm². Both endpoint vias keep their geometry and net. Polygonized old-minus-new endpoint-contact diagnostics retain 0.000000097437 and 0.000000056933 mm² differences; exact unchanged-contact-area acceptance is not claimed.
- Existing-metal corridor requalification and an independent review were not run, because D already failed its own adjacent-reference gate. Earlier C corridor results are not silently transferred to this new source.

## E: stopped at native clearance gate

E changes only the upper-jog completion from y76.22 to y76.17, keeping x111.28, 0.60 mm width and both original endpoint vias. It is a final finite attempt to move the rail away from D's measured reference deficit.

Native DRC: **9 open pairs, 43 warnings, 2 additional hard clearance errors, parity 0**. Both measured clearances are **0.1445 mm**, below the **0.1500 mm** rule. The upper power jog conflicts with LED_FAULT_N tracks:

- `b995c2c7-f443-497b-bb80-da0d3312d10d`, from (110.8,75.45) to (110.8,75.95).
- `f6f5406e-c528-4d4f-a9d3-6a7ddc1ae774`, from (110.8,75.95) to (110.7,76.05).

The new errors were reported immediately. No deeper E material, plane, cold-refill, ERC or continuation tests ran. In-memory net identities were guarded during build/fill before saving, but that is not substituted for those unrun tests. In particular, E is not claimed to have repaired the reference deficit.

## Other declared escape geometry and remaining work

Both variants retain the same explicitly experimental COL5/MCU_GPIO27 changes: move the COL5 0.50/0.25 mm via from (112.35,76.8) to (112.175,76.3), adjust its three incident tracks, add a 0.175 mm In1 link and one B.Cu link, and add a 0.15 mm B.Cu GPIO27 launch from U1 pad41 (112.2,78.05) to a new 0.50/0.25 mm via at (112.16,77.0). There is no F.Cu continuation. No component placement or schematic, rule, width, endpoint-via or decoupler branch is changed.

D has 9,778 tracks, 924 vias and 383 footprints; summed length 13,212.334463650453 mm. Relative to source: +5 tracks, +1 via, no footprints and +1.525263957208 mm summed length. Five existing conductive objects change, all declared in `qa/repair-D-build.json`; every other source object is exact apart from recomputed zone fills.

All six MCU pairs remain open: GPIO3, GPIO10, GPIO24, GPIO25, GPIO26 and GPIO27. Three header pairs remain: one EXT_GPIO24 and two EXT_GPIO25. No MCU routing success is counted.

The measured conflict is between the shaped 0.60 mm power rail, the actual In1 boundary near (111.60,76.165), and the two LED_FAULT_N tracks near (110.8,75.95). These two tested straight upper jogs do not meet both gates. This is not proof that every shaped rail or bounded LED_FAULT_N refactor is impossible. A later experiment could use a more locally shaped rail or move that short LED_FAULT_N junction enough to recover at least the observed 0.0055 mm clearance deficit plus margin, then recheck all affected endpoint contacts, adjacent reference and nearby copper. Neither redesign was attempted here. The previously missed south-boundary continuation remains untested on this source and must wait for a passing escape.

## Evidence and limitations

`FINAL.json` provides explicit statuses, source-bound hashes, counts, unrun tests and the remaining-open net list. `qa/repair-{D,E}-native-gate.json` and `-drc.json` preserve native severity/category results. D's `-native-checks.json`, `-net-identity.json`, `-erc.json`, `-material-graph.json`, `-material-comparison.json`, `-return.json`, `-failure-geometry.json`, `-local-neck.json` and `-power-geometry.json` preserve its completed checks. `scripts/` retains the executed implementations.

No accepted candidate, SI/EMI result, active power stability, manufacturing, hardware or production claim is made. No other reviewer branch, baseline, current checkpoint, public repository or firmware was modified. No install, credential operation, push, purchase, fabrication or flashing occurred.
