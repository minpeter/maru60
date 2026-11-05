## Latest qualified development prototype

Unused +3V3 branch cleanup: 9 open connection pairs and 39 warnings. Independent exact geometry and fresh contact validation pass, with all retained conductor material unchanged and zero new GND-plane loss. All prior checkpoints and inherited limitations remain. See pcb/CURRENT.md and the selected prototype README. No manufacturing or active stability approval is implied.

## Latest qualified development prototype

C136 reference correction: 9 open connection pairs and40 warnings, with copper/fills exactly unchanged from ef45f84. All prior checkpoints preserved. Fresh physical-connection and cold-refill validation pass, but inherited limits and incomplete electrical work remain. See pcb/CURRENT.md and the selected prototype README. Unselected routing and power-branch experiments are explicitly separated in evidence.

## Latest qualified development prototype, 2026-11-05

The frozen GPIO27 + GND stitch + reference-label candidate has 9 open connection pairs and 42 warnings. Its independently caught GPIO26 departure-reference defect was corrected and all affected reference checks were rerun with explicit assertions. It is not strict geometric or fabrication acceptance: inherited exact no-loss differences and remaining electrical/model limits stay documented. Earlier strict and prototype checkpoints are preserved. See `pcb/CURRENT.md` and the candidate README.

## Latest development prototype, 2026-11-05

The frozen GPIO24 + VBUS candidate has 10 open pairs and 50 warnings, with source-bound checks and a new simulation applicability crosswalk. It is NOT strict acceptance: exact plane inclusion fails by explicit sub-nanometre boundary changes. The independently checked 11-open/51-warning GPIO26 baseline remains preserved. See `pcb/CURRENT.md` and `pcb/experiments/resume-20261105-gpio24-vbus-prototype/README.txt`.

# Latest resumed checkpoint

The latest experimental selection is now `pcb/experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pro`, with **11 open pairs and 51 unchanged warnings**. PCB SHA256: `04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99`. Read `pcb/CURRENT.md`. This supersedes only the prior current-selection pointer below; all historical units remain unchanged. It is not production-ready.

# MARU60 V7 recovery workbench

This isolated recovery repository preserves the exact selected PCB after the execution workspace was replaced. It does not invent or restore the lost Git history.

Open `pcb/experiments/v7-c139-reference-legibility/candidate/pcb/maru60.kicad_pro`.

- Current experimental PCB SHA256: `2b5787cc27e7fea92dff2ad483185fccfab1d2d27bf07662395de26f7ab14d69`.
- Prior U18/L2 label PCB 4765 is retained unchanged.
- Prior serial-support PCB abdb is retained unchanged.
- Prior C124-plus-GND PCB7882 is retained unchanged.
- Prior connector GND-only PCB aaaf is retained unchanged.
- Prior two-track GND cleanup c770 is retained unchanged.
- Prior BUCK cleanup PCB: `aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f`, retained unchanged.
- Prior four-reference/logo PCB: `2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373`, retained unchanged.
- Exact recovered original selected PCB: `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1`, retained in the prior unit.
- Original selection commit: `b42351518b0007177a85fa3ce44f8d41967c9af9`.
- Last known original evidence-only HEAD: `3bed855f70875e1466f3a0a253d549ae581baaf4`.
- Original working branch: `feat/maru60-v7-protection-layout`.
- This repository starts a separate recovery history. The original Git objects and full historical QA suites are missing, not recreated from summaries.

## Current experimental C139 legibility correction

C139 is now directly above its own component column, with separately verified raw nominal/drawn-stroke courtyard gaps of 0.279524/0.254524 mm. Only this Reference field changes; all electrical source, fills and companions match 4765. Independent exact raw reversal, native checks, visual inspection and separate cold refill pass. Warnings 55→51, same 12 opens, other hard DRC/parity 0; prior ERC and material results inherit from identical inputs. The full warning history has 44 resolved and 51 remaining. R159/C136 are retained because nearby examined free positions would confuse ownership. All prior qualification limits remain. See `pcb/experiments/v7-c139-reference-legibility/README.md`.

## Preserved experimental U18/L2 legibility correction

Two Reference fields are clearer, with actual nominal/stroked courtyard gaps above 0.20 mm and independent native/pixel/refill verification. The blocked first trial and its corrected boundary interpretation are preserved. Electrical data is byte-identical to abdb, so the completed material/support/reference results inherit without claiming new electrical simulations. Warnings 61→55, same 12 opens, other hard DRC/parity 0; prior ERC 0 inherits from identical circuit sources. Inventory remains9,750 tracks / 919 vias / 383 footprints / 13,184.45545001526 mm. All hardware, startup, pulse, environmental and signal-quality limits remain. See `pcb/experiments/v7-two-reference-legibility/README.md`.

## Preserved experimental source-support cleanup

Three main endpoints now use their retained support segments as real serial legs. Independent native/contact/reference checks and cold refill pass without relaxing any rule. Warnings64→61, same 12 opens, other hard DRC/ERC/parity0. Inventory:9,750 tracks,919 vias,383 footprints,13,184.45545001526mm. Actual small copper-shape changes are recorded; no impedance or stability gain is inferred. All prior C124/GND and hardware limits remain. Read `pcb/experiments/v7-c124-support-serial-cleanup/README.md`.

## Preserved experimental C124 correction and connector ground stitch

The reviewed local 100 Ω dV/dt series resistor, explicit 10 nF capacitor and same-value RN73R R121 package change are combined with the separately committed GND via. Exact circuit/part/geometry, strengthened old support and reference checks pass; independent combined review passes 45 checks with byte-identical cold refill. Counts: 9,750 tracks, 919 vias, 383 footprints, 13,185.28691027245 mm. The same 12 expansion opens remain; other hard DRC, ERC and parity are zero. There are 64 warnings: five old label warnings removed and THREE new source-support endpoint warnings explicitly retained, not waived.

This is an experimental working selection only. The electrical-risk memo recommends it as a next-prototype candidate, not a qualified replacement. Active startup/reset/brownout, repetitive pulse, input-fault envelope, environmental drift, assembly/mechanical and actual signal quality remain unverified. The unknown selected R121 specification is not equated with the earlier unselected TNPW proposal. LED qualification stays OFF. Read `pcb/experiments/v7-c124-series-with-connector-ground/README.md` and its electrical decision brief. Do not fabricate or claim electrical/production readiness from this selection.

## Preserved connector ground stitch

That preceding working selection added one ordinary GND via, with strict physical loss limited to its exact drill and all prior signal shadows protected. Fresh corrected material checks, native DRC/ERC/parity and independent cold refill pass. Counts are 9,750 tracks, 919 vias, 382 footprints and 13,176.816253756544 mm. The same 66 warnings and 12 expansion opens remain. All 245 pad-net partitions and 247 original GND roots are preserved. No SI/ESD, active startup, assembly or hardware qualification is implied. See `pcb/experiments/v7-connector-ground-stitch/`.

## Preserved two-track GND cleanup

That preceding selection removed only the proved two-track dead-end GND branch, preserving its existing via, every drill and all12serialized zone records exactly. Independent fresh corrected-material checks preserve all245net partitions and247original ground-return paths. Native DRC has66warnings/12inheritedopens/zeroothererrors, ERC 0 andparity0. Inventory:9,750tracks/918vias/382footprints/13,176.816253756544mm. Normal cold refill is byte-identical. No current-transition tolerance or warning waiver is used, and no high-frequency ground or hardware improvement is inferred. See `pcb/experiments/v7-gnd-deadbranch-cleanup/` for the frozen evidence, adoption receipt and full92-warning history(26resolved,66remaining).

## Physical-contact checker correction

That evidence-only milestone left the then-selected aead board and firmware unchanged. A corrected material checker and five fresh source-bound rechecks are preserved in `pcb/experiments/v7-material-contact-correction/`. It resolves via-wrapper, neighboring-drill and disconnected-material shortcuts in the earlier global exporter. Original physical contact/support-area claims are superseded by the explicit erratum; original receipts remain unchanged. That aead snapshot retains all245pad-net partitions, and all22,531accepted material edges have exact positive-interior witnesses. Its12opens/67warnings and separate plane/reference limits were unchanged. The later two-track removal is checked separately above. The active checker is `pcb/tools/export_material_graph.py`. This is bounded nominal connectivity evidence, not manufacturing or hardware qualification.

## Preserved bounded BUCK_FB predecessor

The preceding working selection removed the degree-one feedback via and 2.85 mm dead arm while preserving the 1.95 mm active path. Fresh full physical connectivity, DRC/parity/ERC and independent review pass the explicit candidate-specific 1 nm coordinate-precision criterion. The original strict global zero-loss result remains FAIL and is preserved separately; exact remote contour changes are bounded by 0.733693794 nm, with critical shadows/contacts/roots and normal clearance rules retained. This criterion does not apply to other candidates.

At that predecessor:9,752 tracks, 918 vias, 382 footprints and 13,178.75473138763 mm track length. The same 12 expansion-GPIO opens remain; warnings are 67, with precisely one removed and none added. There are zero other hard DRC errors, zero ERC violations and zero parity findings. No noise, loop-stability, hardware or manufacturing improvement is inferred. Read `pcb/experiments/v7-buck-feedback-cleanup/README.md` and its unchanged strict, precision and final eligibility evidence. Earlier J3/C124 alternatives remain unselected; the later experimental D-based selection is described above, and firmware is unchanged.

## Preserved metadata/artwork predecessor

The preceding selected successor changed four reference labels and moved the intact LOGO1 artwork. Independent native ink/association review and exact raw restoration establish unchanged electrical geometry and saved fills. Warnings fall from 92 to 68, with 24 exact removals and none added; the same 12 GPIO open-component pairs remain. Native counts remain 9,752 tracks, 919 vias and 13,181.60473138763 mm. Fresh candidate ERC and parity are zero. All 92 original warning records have an explicit current disposition in the new unit. This is bounded label/artwork adoption, not electrical, 3D or manufacturing qualification.

## Exact recovery baseline and fresh checks

All six complete board hashes, from integration baseline through U10, C128, width repair and typography, match their historical targets exactly. The independent review verifies raw deltas and unchanged saved fill bytes. This is full-byte recovery, not approximate geometry recreation.

The earlier 53-file CAD bundle was recovered from the saved tscircuit archive and verified against all 53 input hashes and all 235 delivery hashes. The selected board replaced only its earlier PCB. The expansion schematic received the same two test-point value corrections (+4V TEST and +4V_LED TEST). The complete later 54-file historical manifest is unavailable, so exact recovery is claimed for the board and the individually proven companion files, not for that missing full project map.

Fresh KiCad 9.0.2 DRC, schematic parity, ERC and netlist export completed without source changes: 12 expansion-GPIO opens, zero critical power/USB source opens, 92 warnings, zero other DRC errors, zero parity issues and zero ERC violations. Fresh native counts are 9,752 tracks, 919 vias, 382 footprints and 13,181.60473138763 mm summed track length.

Fresh recovery receipts are under the original recovered unit's `qa/recovery-native`. Their execution paths identify the isolated recovery staging directory where the exact same bytes were checked. Historical full physical-graph/frozen replay is not claimed to have been rerun or recovered. Source-bound simulation archives remain separate saved artifacts; full hardware, PDN, SI, ESD, EMC, mechanical and manufacturing qualification remain false.

## Missing work and safe continuation

A reviewed, newly tested LED startup-guard recovery implementation is now active at `pcb/firmware`, with exact copies of its supporting engineering files at `pcb/engineering`. Nineteen of the 22 former fixed overlay files were recovered exactly; three guard source files are explicitly new implementations. The immutable baseline, reviewed candidate, fresh host tests and static V7 mapping are preserved under `pcb/experiments/led-startup-recovery`. Qualification remains OFF. Full pinned QMK/ARM builds and hardware acceptance have not been performed; do not flash or enable qualification. Original C124 rejected-trial packets and later unselected label/C124 studies are also not fully restored. The reviewed four-label/logo predecessor remains preserved; the earlier C124 trials remain unselected; the later D-based experimental selection is described above.

Continue new experiments from the exact selected board in isolated directories, with new source-bound checks and independent review before adoption. Do not weaken clearance, old conductor/reference preservation or qualification gates. Do not push or fabricate from this baseline.

`recovery/` contains reconstruction inputs, scripts, source manifests, explicit historical limitations, independent review and the exact selected-board preview. Reconstruction scripts preserve their original execution layout; they are provenance artifacts, not a relocated one-command replay promise. The saved board can be opened directly without reconstruction.

## Completed unselected C124 circuit experiment

`pcb/experiments/v7-c124-short-local-review` preserves the independently reviewed short-local 100 ohm series-resistor trial. Its latest experimental PCB is ec48735f21b813f84873a4dfcd8a984a395f59a6d48d30e5bcfff19aaefe52a7, with accepted four-reference/logo artwork retained. Earlier scoped geometry/positive-contact/reference and carry reviews reported passes: 31 bounded old tracks retired, 21 new tracks, no drill changes, all retained copper and saved zones exact, and unrelated physical net partitions unchanged. Native hard DRC/ERC/parity are zero; 12 expansion opens and 64 warnings remain, including one explicit rooted support-tail warning.

This was evidence integration, not selection of the C124 circuit. The prior 2c7e100a board remains unchanged; the current entrypoint selects the later D-based combination described above. Passive models and independently checked component alternatives are included, but active startup/reset/pulse behavior, actual parasitics/coupling, assembly/3D and hardware qualification remain open. See the experiment README for exact source bindings and limitations. At that earlier checkpoint, no smaller-capacitor alternative or proposed procurement part had been adopted. Later source-bound actual-C review distinguishes positive connectivity from full original-support preservation and finds four inherited signal-support deficits, alongside the manufacturer occupied-envelope conflict; That actual-C trial remains unselected. The independently repaired D successor is separately selected for experimental development above.
