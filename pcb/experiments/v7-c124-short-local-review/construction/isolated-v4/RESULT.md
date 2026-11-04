# Actual short C124 V4: passed bounded electrical geometry, unselected

Filled board: `filled/pcb/maru60.kicad_pcb`, SHA-256 `8c45df3642599be269697ce9b225fe55ee6b886dce713b77f6ced533ea268fb6`.
This immutable57-file tree is preserved by `FILLED_TREE_MANIFEST.json` (SHA `d55fc301a00a92b538af07b6a2e9f1f0e9556c1d8390551d0a3aeea88ad11c8c`). Its source is exact selected unit34/7c23. New selected metadata/artwork2c7 is not in this snapshot and must be carried separately. No selected repository or source CAD was modified.

## Actual results

- Native saved board:9,742 tracks,919 vias,383 footprints;13,186.830228728211 mm summed track length. Exactly31 old tracks retired,21 tracks andR125 added; no new/moved/removed drill. Only oldC124/R121 footprints changed. All10,640 retained old track/via blocks are byte-identical.
- All12 complete source zone records are byte-identical after actual native refill, including both inner planes and every saved fill polygon. Combined with unchanged drills, this proves zero source-reference copper loss and zero old-shadow loss, including obsolete DVDT/OVLO/UVLO shadows. No nominal-antipad or numerical epsilon exception was used.
- Native DRC:0 hard violations beyond the12 existing expansion opens,88 warnings,0 schematic parity issues. ERC0. The netlist gives USB_DVDT onlyU8.7/R125.1 and USB_DVDT_CAP onlyR125.2/C124.1. UVLO/OVLO divider values and logical memberships are unchanged.
- Fresh whole-board native neighbor graph, with every edge checked against positive physical copper after drill subtraction and zones split into actual physical islands: only the intended DVDT/CAP pad partitions change. All other net partitions are exact. GND is one247-pad component. All physical zone-component records are exact.
- The20 original native neighbor candidates without positive-area physical intersection remain exactly the same set. They are not new losses and do not add a disconnected pad component. This fresh conservative graph is not a restored historical checker.
- Native open count and affected nets/physical partitions are unchanged, but one EXT_GPIO26 ratsnest report endpoint changes from track76015e03 todf690eec. Both untouched tracks are proved in the sameU13.9/U11.14 physical component in both snapshots; J3.8 remains its separate existing component. Raw open-pair identity is therefore not claimed. See `qa/open-endpoint-disposition.json`.

## Independent actual review

`../r121-expanded-review/actual/REVIEW_ACTUAL.md` independently checks actual native shapes, not merely the analytical plan:
- All21 tracks and six pads/paste/mask openings/courts equal the plan.
- All16 new-to-retained and19 new-to-new required contacts are positive.
- Both complete outside-approximated oldC124 ground contact support regions are covered by the inside actual bridge, zero deficit.
- Both oldGND vias and the existingU8 return via independently contact both inner planes: six positive annular roots.
- Actual R125 input/output copper gap0.500000 mm; no resistor bypass.
- All22 outside-approximated new signal-track/pad projections have zero uncovered area on both drill-subtracted inner references.
- Minimum reviewed actual worst-terminal/placement/solder envelope gap0.167369 mm. Current Murata approval-sheet access and actual assembler bounds remain unresolved.

The independent power reviewer also matched actual board8c45, all31/21 changes, all10,640 retained tracks/vias, all351 footprint drills, six pads and XML resistor order. Its separate archive is `/workspace/scratch/edd9a5be63e7/v7-c124-local-actual-binding-20261104.zip`, SHA `e5f78cf2236e75aa99b127cf63ec458b9554f171304e85370e177c774bbb07b9`.

## Explicit remaining warning and limits

GROUND_BRIDGE_B `0dd51559-bc06-502f-8bb1-1b186fa751d0` has a native track_dangling warning at its free support tail (15.5,17.85). It physically overlaps bridgeA by0.0603916194445 mm² and retains the old supported/rooted ground component. The warning is retained, explained, not deleted or waived; this board is not called DRC-clean. Compared with7c23, five old warnings retire and this one is added. No new/changedR125/C124/R121 reference defect remains.

The original emitted prefill had a net-declaration ordering error, preserved asdb4f1277. The valid26102ec2 prefill, two-reference-anchor4aa454eb successor and8c45 saved fill are all separately recorded in `ACTUAL_LINEAGE.json`. The original BUILD_CONTRACT prefill hash refers to that obsolete diagnostic; use ACTUAL_LINEAGE and actual report hashes, not that field, for validation binding. The isolated Study library was also completed with the exactR125 symbol before the finalERC0 report. None of these implementation fixes changed the reviewed electrical geometry.

Pin-side track1.660404265 mm, after-resistor1.103279203 mm, capacitor return0.699231721 mm, zero new signal drills. This avoids the rejected20 mm/5-via alternative. UVLO chain grows0.894932120 mm and the OVLO arm1.410519448 mm, explicitly traded for usable placement/terminal margins. Nominal100Ω×10nF RC is1µs. These do not prove startup/noise/reset or EMI behavior. ProposedKOA0402 pulse/derating, proposedMurata bias/temperature/ageing, proposedVishay lands, and the changed high-impedance sense routing remain under analog/process review.

Actual socket/switch/plate/keycap envelope and height registration are not established. The former1.68 mm socket-strip interpretation remains withdrawn. No3D assembly, manufacturing, procurement, hardware or production qualification is implied. The experiment remains unselected.

## Key evidence

- `qa/filled-drc.json`, `qa/drc-warning-delta.json`, `qa/erc-with-library.json`, `qa/netlist.xml`, `qa/netlist-order.json`
- `qa/filled-raw-object-delta.json`, `qa/native-fill.json`, `qa/all-net-physical-partition-comparison.json`
- `qa/source-native-physical-graph.json`, `qa/actual-native-physical-graph.json`, `qa/open-endpoint-disposition.json`
- `qa/local-top-bottom-unselected.png`: actual saved local top/bottom geometry, explicitly unselected. Native footprint Fab/court lines are not a verified socket envelope.
- `../EXPANDED_V4_PLAN.md`, `../CONTACT_LEDGER.md`, `../PLAN_MANIFEST.json`: reviewed expanded scope,31 UUID retirements, full contact ledger and manufacturer assumptions.
