# Independent actual-board review: isolated V4

## Result and exact scope

**Bounded native geometry/contact/reference review passes for the preserved unselected trial, with one explicit DRC warning and a stale manifest field noted below. No qualification or adoption approval.**

Actual reviewed board: `/tmp/v7-c124-rebound-short/isolated-v4/filled/pcb/maru60.kicad_pcb`
Actual SHA-256: `8c45df3642599be269697ce9b225fe55ee6b886dce713b77f6ced533ea268fb6`.
Exact source SHA-256: `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1`.

This review reads actual native shapes, not merely the plan JSON. It is specific to the 7c23-based trial. The selected lineage's subsequent artwork-only 2c7 state and label carry remain outside this snapshot's acceptance. Any board change requires rebinding and appropriate rechecks.

No source/candidate editing, save, fill, or full-board graph was performed. Outputs are confined to this review directory. Source and candidate BOARDs were loaded in separate bounded processes, never simultaneously. KiCad pcbnew9.0.2, private XDG, 1 nm polygons were used.

## Actual inventory and geometry

An independent raw-object comparison reproduces:

- Exactly 31 old tracks removed and 21 added; no retained segment altered.
- 9,721 old segments and all 919 old vias unchanged: 10,640 retained track/via records total.
- 383 footprints; only old C124 and R121 footprint blocks changed, one R125 added, 380 old footprint blocks unchanged.
- 10,661 tracks/vias in the actual native board.
- All 12 complete zone records, including their saved filled geometry, byte-identical to the exact source.

All 21 added actual tracks match the reviewed endpoints, widths, nets and B.Cu layer with zero mismatches. All six actual pads match the full reviewed lands:

- R125 center(15.54,20.27): rectangular0.40×0.30 mm lands at(15.99,20.27)/(15.09,20.27), USB_DVDT/USB_DVDT_CAP.
- C124 center(15.38,19.17): rectangular0.35×0.50 mm lands at(15.005,19.17)/(15.755,19.17), USB_DVDT_CAP/GND.
- R121 center(13.68,18.65): rectangular1.00×0.90 mm lands at(13.68,19.45)/(13.68,17.85), OVLO/GND. The custom footprint is drawn vertically and has native footprint orientation0°, correctly matching the actual pad coordinates. It must not be blindly rotated90°.

Each pad has exactly B.Cu/B.Mask/B.Paste membership, native paste and mask shapes equal the intended land, effective paste margin(0,0), and mask expansion0. Native pad/paste/mask areas are0.120 mm² for each R125 land,0.175 mm² for each C124 land and0.900 mm² for each R121 land. No hidden mask/paste exception was found. Manufacturer, exact proposed MPN and UNSELECTED status fields are present. The changed/new references are0.8×0.8 mm text.

Actual source courtyard primitives, not cached erosion, exactly match the intended rectangles. Measured gaps: C124–R1250.050 mm, R121–C1240.150 mm, R121–R1250.210 mm, R125–U80.060 mm.

## Actual physical contacts and series topology

- All16 reviewed new-to-retained boundary contacts are physically positive using native drilled-annulus copper where applicable.
- All19 reviewed new-to-new contacts are physically positive.
- The two actual ground bridge tracks overlap by0.0603916194445 mm².
- Actual R121.2→retained GND spur overlap remains0.055103142777 mm². This is a deliberate changed contact, not complete preservation of old R121-pad support.
- Full old C124 support is preserved under the stronger direction: **outside old physical support minus inside actual bridge is exactly0 mm²** for both old support regions. The two outside old support areas are0.105708073089 mm² to old spur19181a2b and0.0091029973315 mm² to the drilled annulus763086b7.
- The actual USB_DVDT_CAP net contains only C124.1, R125.2 and the one new CAP track. The actual pin-side net contains R125.1, both physical U8.7 pads, the retained stub and three new input tracks.
- Input-side versus capacitor-side copper has **zero overlap and minimum0.500000 mm gap**. Thus no physical copper bypass of R125 was found. Whole-board/all-net partition acceptance is being checked separately by the parent and is not claimed here.

## Actual reference and terminal checks

The actual **outside-approximated union of22 new signal pads/tracks** was compared against each actual inner GND fill with all intersecting physical holes subtracted using outside drill envelopes. Both In1 and In2 have **zero uncovered area and zero uncovered outlines**. All three retained GND vias retain both physical annular plane roots, each0.147260768066 mm².

All12 complete saved zone records are byte-identical to source; all old holes are unchanged, and changed/new footprints are SMD without holes. Therefore this trial introduces no loss of the existing physical reference geometry, including under old route shadows. This is an exact source-to-snapshot preservation result, not a claim that all source reference geometry was itself ideal.

Critical process-envelope checks were reconstructed at actual part centers using conservative integer rounding:

- C124.1 envelope→actual OVLO0/1:0.170722 mm.
- C124.1 envelope→retained ILM via:0.179286 mm.
- R121.2 envelope→retained ILM via:0.167369 mm.
- R125.2 envelope→actual OVLO3:0.182902 mm.
- Actual R121.2 land→UVLO1:0.173672 mm.
- Actual ground bridge→nearest foreign copper:0.375000 mm to retained ILM track2aa1548e.

The prior documented maximum-terminal dimensions and ±0.05 mm XY/±2° placement plus0.05 mm solder assumptions remain assumptions. Actual geometry does not certify the assembler, current C124 approval, repetitive-reset/pulse behavior, or switch/socket/plate/keycap envelope.

## Explicit unresolved records

1. **DRC warning retained, not waived.** The saved filled DRC report lists track_dangling for GROUND_BRIDGE_B UUID`0dd51559-bc06-502f-8bb1-1b186fa751d0` at(15.5,17.85). It is the only entry involving a new track or changed/new part UUID in the reviewed DRC file. Native physical bridge overlap/support and rooted ground connectivity are positive, so the warning alone is not evidence of an open ground component. Nevertheless this review does not call the board DRC-clean, suppress the warning, or authorize waiving it. The report contains88 total violations and12 unconnected entries; whole-board baseline attribution is outside this bounded review.
2. **Manifest identity is stale.** BUILD_CONTRACT.json's candidate_prefill_sha256 still points to`db4f1277…`, the preserved invalid-net-order intermediate. Its UUID/dimension specification matches the actual candidate, but that field must not identify the final board. native-fill.json records4aa454eb…→8c45df36…; this review is bound directly to the exact8c45 hash above.
3. **No production acceptance.** Analog evaluation, pulse/thermal/reset behavior, common-return impedance, current C124 acceptance, mechanical/assembly envelope, later artwork carry and final selected-lineage integration remain pending.

## Evidence

- `raw_source_candidate_delta.json`: independently extracted raw object/fill comparison.
- `source_support_polygons.json`: exact-source native inside/outside physical support polygons.
- `actual_native_review.json` and `.log`: actual geometry, apertures, contacts, no-bypass, envelopes, references and roots.
- `actual_drc_scope.json`: preserved DRC warning and exact DRC-report hash.
- `extract_source.py`, `review_actual.py`: bounded read-only reproducible checks.
