# Connector GND stitch: verified, unselected trial

Open `filled/pcb/maru60.kicad_pro` for the actual candidate. The selected recovery repository is unchanged at commit 094851aa91eb49e40182c9a88657a8ed6e6dcba8; this archive is not a selected-board or manufacturing release.

Source: c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a.
Candidate: aaafc033c6e9809afcb189290c3740157b7ab5596aaa0867e581f08d89807eca.

Exactly one ordinary GND through-via is added at (17.20, 9.90) mm, diameter 0.50 mm, drill 0.25 mm. The original connector stub, signal traces, all existing holes, components, schematics and settings are unchanged. All 12 serialized zone records are byte-identical. Actual physical ground loses only the exact new drill polygon, 0.049087681002 mm² per inner plane; outer zone material is unchanged. All 13,129 current and 11,905 historical non-GND shadows are protected, including the retired U10 D− segment.

Fresh corrected all-drill material graph and independent review preserve all 245 pad-net partitions, 247 original GND pad roots, every old material component and retained contact witness. The new plated barrel has one intact annulus on each copper layer and two positive guarded inner-plane contacts. Independent normal cold refill reproduces the candidate byte-for-byte. Native DRC: 66 unchanged warnings, 12 unchanged expansion opens, zero other hard errors, zero schematic parity issues. ERC: zero. Inventory: 9,750 tracks, 919 vias, 382 footprints, 13,176.816253756544 mm summed track length.

This passes the frozen bounded one-via geometry/nominal-connectivity contract. It does not restore the missing USB between-via ground neck. The left D+ via's nearest rooted GND via distance changes from 2.351197 to 1.597655 mm, which is geometry only. Added grounded copper can alter actual local fields and coupling. No parasitic extraction, post-change waveform, SI/ESD/EMC, physical stability, assembly or hardware qualification is claimed.

The full source, prefill and candidate project trees are separate. Their schematics are supplied so the actual project can be opened. QA serialization-only/intermediate boards are not the candidate. Existing firmware and prior recovery history are not changed or duplicated here; the selected full-repository backup remains separate. The original lost pre-recovery Git history/full historical QA are still missing.

## Evidence and execution history

The independent contract and actual review are preserved under `independent-contract` and `independent-actual`. The actual graph is `qa/material-graph.json`; its source is `qa/source-material-graph-R2.json`. `qa/comparison.json` and the independent result preserve exact source bindings. Historical run paths inside frozen reports/scripts are provenance, not a claim that every original script is a one-command relocated replay. `verify.py` checks the portable archive contents only.

The initial constructor attempted an unsupported UUID setter and stopped before saving a modified board. Its script/log are retained. The successful constructor emitted a SetWidth-without-layer API diagnostic; the serialized 0.50/0.25 geometry was independently reloaded and verified on all four layers. An initial edge-list comparison was order-sensitive; the corrected comparison uses complete-record multisets, preserving duplicates, and finds zero changed/lost old edges. The original diagnostic is retained. These corrections do not change geometric acceptance tolerances.

The independent review retains its interrupted slow-audit script/log. Its first cold-refill SyntaxError exists in the tool transcript and README summary, but that local error log was overwritten by the successful run; do not interpret its README phrase “Both diagnostics are retained” as preserving that original local log. The successful cold-refill receipt and frozen result hashes are intact.
