# GPIO27 header closure: frozen development candidate

Status: complete evidence packet, unselected pending independent review. No further header edits are in progress. This is a nominal layout development candidate, not SI, EMI, fabrication, or hardware qualification.

## Exact files

- Candidate: `trial27/pcb/maru60.kicad_pcb`
- SHA256: `ad2fddcfa109ad2b21c27471eebc822408fd5a92a713cb393d523185e3c8a532`
- Complete 58-file PCB project: `trial27/pcb/`.
- Direct source: `/workspace/shared/maru60-resume/combined-trial/pcb/`, SHA256 `56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9`, prototype commit c782123.
- Neither that source nor the older strict checkpoint was modified. The source already has an explicit bounded-prototype decision; this candidate does not erase that decision or restore an exact identity claim.

## Verified result

Native KiCad 9.0.2+dfsg-1: 10→9 unconnected pairs, all50 pre-existing warnings exactly unchanged, zero other DRC errors, zero schematic parity violations, ERC0. Exactly one complete physical pad-component pair closes: EXT_GPIO27, from2 components to1 (J3.9 joins the existing U11.13/U13.8 component). The nine remaining complete open-component pairs are unchanged, even where native representative objects differ.

Raw/native net identity: all12,133 raw conductive object names agree with native Load/Build; all1,064 XML electrical node bindings agree. Names remain stable through cold Load/Build/refill/save. A separate cold copy returns all58 files byte-identical in3.0478 seconds. All57 companion project/schematic/library files remain identical to the source.

Metrics: 9,772 track segments,922 vias,383 footprints,13,210.809188057545mm summed track length. Delta: +14 tracks,+1 via,+7.831894240651mm. No component/footprint, net, rules, clearances, widths, copper layers, firmware, or release state changed; no new ground stitch was added.

## Explicit copper refactor

All new tracks are0.15mm wide. The new through via is0.50mm copper /0.25mm drill. No new inner-layer signal routing.

1. EXT_GPIO10 B.Cu original segment `fdd2376a-e263-51cf-8638-7d8989c5ffc8`, formerly (96,40.05)→(98.25,40.05), becomes an8-segment detour through (96.25,40.3),(96.25,40.55),(96.5,40.8),(97.35,40.8),(97.6,40.55),(97.6,40.3),(97.85,40.05), then the original endpoint. The original UUID is retained for the first segment;7 tracks are added. Net length increases0.914213562373mm.
2. Existing EXT_GPIO26 via `bd60c430-58d5-568a-b034-a604187f20ee` moves from(96.8,41.775) to(96.65,41.625), a0.212132mm translation. Its3 incident track ends are retargeted: `55e5d0cf-c179-4e88-925d-241a5a9d4416`, `df690eec-df6a-52bf-82fe-eace87245374`, and `76015e03-58a6-5c88-b481-9c628c5b1061`.
3. EXT_GPIO26 F.Cu joint (93,41.95) moves to(93,41.85), updating `28cd3c37-8361-5c39-8d60-61e9bfc427f4` and `df690eec-df6a-52bf-82fe-eace87245374`. Net26 length decreases0.482796212981mm.
4. J3.9 GPIO27 (96.5,39) B.Cu dogbone joins new via (96.925,40.175), then6 F.Cu segments through (97.2,41.675),(97.125,41.9),(96.925,42.1),(96.65,42.175),(93.5,42.2), to existing GPIO27 via(92.9,42.5). This adds7.400476891259mm to GPIO27.

Six old conductive objects are changed (5 tracks,1 via);15 new objects are added (14 tracks,1 via). `qa/raw-audit.json` records every field. Only declared start/end/position fields and regenerated zone fills differ. Restoring the six objects and original zone fills, then removing additions, reconstructs the source parsed board exactly. All undeclared source objects are exact.

## Material contacts and physical connectivity

The corrected material exporter was run on the exact frozen source and candidate. Direct guarded edges:21,785→21,801. Zone-contact edges:733→733, all exact. All247 GND pads retain their complete original partition, as do every other net's pad partitions except GPIO27. Guard failures, empty/multiple object-layer diagnostics and old barrel joins are inherited and identical. All undeclared object material nodes are exact; declared geometry changes are listed separately.

Three old direct UUID edges at the old EXT_GPIO10 far endpoint retire because its UUID now identifies only the first detour segment. The last new segment `b3bc6543-bd14-4b17-a59c-2b4bbc878cc5` reproduces all three old physical contact patches exactly:0.017792209043,0.002619127193 and0.007514899337mm². Missing area and gain are zero for each. These are remapped contacts, not severed endpoints.

Nine surviving direct-edge measurements change:8 on the explicitly retargeted GPIO26 geometry and1 at the changed EXT_GPIO10 start. All remain positive guarded contacts, with original pad topology intact. The changed GPIO10 start overlap grows from0.0177921599255 to0.018878311454mm². Its native1nm polygon Boolean old-minus-new result is nevertheless1.37825e-08mm² across26 tiny outlines. This raw difference remains explicitly reported; exact contact-patch identity is not claimed. This deliberately reshaped junction shares the same endpoint at(96,40.05), track widths0.15mm, with the preceding track from(94.8,41.25). It is not an unrelated unchanged junction. No broad numerical tolerance is applied.

## Full-board return-plane evidence

`qa/plane-review.json` compares the exact current source, not the older baseline. It unions all filled GND material on each inner plane, subtracts all native through-hole shapes, then scans every old conductive object against the full-board lost area. No cropped check substitutes for that scan.

Each plane remains one component. Per plane: lost area0.831212507706mm², gained area0.189959295388mm². Exactly zero loss lies outside radius0.455mm windows around newGPIO27(96.925,40.175), existingGPIO27(92.9,42.5), and movedGPIO26(96.65,41.625). The source GPIO27 window is included because the new signal lands there; it does not license unrelated losses.

Only four old object shadows change, all declared refactors:
- Retired GPIO10 straight-segment shadow:0.1296352742925mm² per plane. Its removed center section is replaced by a grounded detour; this is intentional retired copper, not a preserved old route.
- Three retargeted GPIO26 tracks:0.031764599479,0.017104230918 and0.017031531894mm² per plane, wholly inside the moved-via transition window.

No unrelated old object has any detected loss. Every newly added GPIO10 segment is fully referenced by the adjacent inner plane. Every added GPIO27 segment has zero uncovered area outside its own two signal-transition windows. Across all137 retained EXT_GPIO10/26 tracks, there is zero newly unsupported area outside the applicable moved-via window; no window is allowed for GPIO10. The shifted GPIO26 F.Cu joint passes this same check.

Verified existing GND through-via alternatives, with positive native contact to both planes and barrel proof:
- New GPIO27 via: nearest GND(94.5,40.7), distance2.481179155mm.
- Existing GPIO27 landing: nearest GND(91.425,43.043), distance1.571774157mm.
- Moved GPIO26 via: nearest GND(94.5,40.7), distance2.340539468mm, improved from2.538823546mm at its old location.

These distances establish nearby grounded transitions, not a measured loop inductance or a proof of acceptable fast-edge return behavior. No stitch is included in this trial; the separately reviewed stitch near GPIO24 is outside this candidate.

## Gates and recommendation

- Native electrical, clearance, parity, raw-scope, net-identity, cold-refill, component connectivity and declared-refactor nominal return gates: pass as documented.
- Strict unchanged old geometry / exact old contact-patch / exact old shadow identity: not satisfied, intentionally. GPIO10 is rerouted, GPIO26 is moved, and positive contact measurements change. This must not be presented as the old strict checkpoint.
- No unrelated old material-contact or return-shadow regression was detected by the full-board tests.
- Recommend independent review for a reversible development-prototype checkpoint. Do not promote to fabrication or claim SI/stability qualification. The remaining three header opens, six MCU opens,50 inherited warnings, active-power limits and hardware validation remain unfinished.

## Remaining opens

- EXT_GPIO24: U13.12 ↔ J3.5/U11.16 component.
- EXT_GPIO25: J3.6 ↔ U13.11; U11.15 ↔ J3.6 component.
- MCU_GPIO3: expansion-side component ↔ U1.5.
- MCU_GPIO10: expansion-side component ↔ U1.14.
- MCU_GPIO24: R132.1 component ↔ U1.36.
- MCU_GPIO25: R133.1 component ↔ U1.37.
- MCU_GPIO26: expansion-side component ↔ U1.40.
- MCU_GPIO27: R145.1 component ↔ U1.41.

Exact before/after native UUID pairs and complete physical pad components are in `qa/open-component-pairs.json` and `qa/drc-comparison.json`.

## Finite attempts and evidence map

Source GPIO27 escape was blocked by the GPIO10 horizontal segment. An explicit local detour opened the via pocket. Fixed-geometry routing and two smaller GPIO26 via-shift attempts failed; retargeting the via's incident ends was necessary, then the F.Cu corridor near x93 still failed. Raising that existing GPIO26 joint0.10mm opened the corridor. Only the final plan was saved as a PCB candidate. Earlier in-memory search results remain in `qa/plan27*.json` and their scripts; no speculative global router was added.

- `qa/BUILD.json`: exact plan, hashes, added/modified UUIDs.
- `qa/raw-audit.json`: full raw-object and58-file provenance.
- `qa/drc.json`, `erc.json`, `net-identity.json`, `cold-refill.json`: native checks.
- `qa/material-graph.json`, `material-comparison.json`, `material-declared-changes.json`: corrected material export and complete comparisons.
- `qa/retired-contact-patches.json`: all three remapped endpoint-patch proofs and explicit changed-start difference.
- `qa/plane-review.json`: full-board, not cropped, plane losses and all projected-object checks.
- `qa/transition-evidence.json`: nearest verified GND transitions and per-net metrics.
- `images/full-native.svg` and `.png`: native KiCad full-board F.Cu/B.Cu/Edge.Cuts export from the exact candidate.
- `images/detail-F.Cu.svg/png`, `detail-B.Cu.svg/png`: same-board native-shape local views, visually checked. Blue=GPIO27, green=GPIO26, purple=GPIO10, red=GPIO24, yellow=GPIO25. Light gray includes other signal nets, not only ground. Dark gray=GND.
- `images/detail-In1.Cu.svg`: conductive-object-only diagnostic, not a filled-plane/reference plot; do not infer ground coverage from it. Numerical full-plane evidence is authoritative.
- `FROZEN_EVIDENCE.json`: hashes of the completed packet. No further header edits until composition review.
