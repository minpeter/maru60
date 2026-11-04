# BUCK_FB dead-arm cleanup: hold unselected

Candidate `aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f` is based on selected `2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373`, not the J3 experiment.

## Bounded cleanup succeeds

The degree-one via d382de57 and original 4.80 mm track 2c0aa2c5 are retired. Replacement 6ffab701 is exactly .15 mm F.Cu, (181,85.75) to (182.95,85.75): the 1.95 mm active portion, with no copper outside the old track. All three declared active contacts and U18.8/R159.2/R160.1 remain connected. Independent full-track-deletion control isolates U18.8, confirming why retaining the active portion is necessary.

Every other raw conductor, footprint, net and zone setting is exact. All 54-file maps were checked again at sealing; all non-board files are unchanged. Track count stays 9,752, vias fall 919→918, pads stay 1,437 and actual holes fall 1,270→1,269. Centerline length falls exactly 2.85 mm, from 13,181.60473138763 to 13,178.75473138763 mm. This is removed branch length, not a shortened U18-to-divider active path.

All 245 observed physical pad-net partitions, all 247 J1.A1-rooted GND pads and all 731 zone-contact identities/support areas are exact. Independent native FB intersections corroborate the critical branch. The original 68 warnings become 67 by removal of exactly the named dangling-via record, with no added warning. Observed hard errors, ERC and schematic parity remain zero. Twelve open complete endpoint-component pairs remain exact; all 48 reported endpoint UUIDs, native positions and descriptions were validated. Four representatives change (MCU_GPIO10/24/25/26), not their complete component pairs.

## Strict global plane condition fails

Outer fills are unchanged. Native saved-fill subtraction reports remote inner losses of 0.000000142282 mm² on In1 and 0.000000140974 mm² on In2, alongside gains of 0.641253861231 / 0.641253859923 mm². No threshold discards these losses.

The raw serialized contour coordinates exactly match the native exported coordinates. Exact rational point-in-polygon witnesses against those original contours, without Boolean clipping or epsilon, establish real source-inside/candidate-outside regions in 10 of 17 reported In1 slivers and 9 of 16 In2 slivers. Self-subtraction and identical-reparse controls are zero on both layers (eight controls total). Thus the result cannot be dismissed as only a Boolean artifact. Every reported sliver fits an enclosing strip no wider than 0.811799 nm. This is a geometric bound, not an assumed manufacturing tolerance or acceptance waiver. The native Boolean total is not asserted to be an exact rational integral of all slivers.

No retained full-width old shadow is lost. The replacement's absolute inherited reference gap is unchanged at 0.068332661731 mm²; newly introduced gap is zero. Neither result substitutes for the global plane requirement. Loss regions intersect no retained inner-layer physical contact support and do not intersect the .50 mm-radius region around the removed via. All source-root supports remain intact. These are consequence checks, not permission to ignore the contour change.

## Decision and next condition

**Hold unselected.** The strict no-global-plane-loss condition is not met. Preserve this candidate. A separate successor must meet the unchanged condition, or a narrowly justified alternate serialization-geometry criterion must be explicitly reviewed before adoption. This review neither invents an epsilon nor authorizes a new rule. It does not show the board is physically unsafe, but the specified strict gate has failed.

No quantified noise, pickup, stability, thermal, manufacturing, hardware or SI improvement is established. The historical passive FB study is not an active regulator model and warns that reducing shunt capacitance alone can increase edge pickup.

## Evidence and methods

`FINAL_REVIEW.json` provides the machine-readable decision; `SOURCE_BINDINGS.json` pins the actual boards, build/DRC/ERC and inherited graph observations. Native source and candidate geometry was independently exported in separate one-board/private-XDG processes, with no save or fill. The complete native bbox inventory plus a full-board-width strip (x0–300, y85.2–86.4 mm) covers every demonstrated loss and every possible affected shadow. No loss is omitted merely for being remote or small. Full copied geometry/graph/open records and exact contour witnesses are retained.

The first local-window review failed because remote losses fell outside its bounds. A full-board export was then completed, but an initial comparison launched before its candidate export existed and failed. Final bounded proof uses fresh board-wide strip exports and verifies the loss bounds explicitly; unused duplicate 366 MB exports are hash-listed rather than duplicated in this portable packet. An initial exact-contour probe was interrupted for quadratic rotation-comparison cost; the final algorithm preserves exact semantics and completes with all controls passing. Preserved review-attempt files document these events, not CAD failures or acceptance evidence.

The graph/DRC/ERC observations were rechecked and component partitions independently reconstructed; they are not claimed as a new complete native graph/DRC run by this reviewer. No cold refill or active simulation is claimed. Scripts retain original execution paths; board-dependent replay requires the matching boards supplied in the builder's packet. Pure exported-geometry checks can run in this packet with the native KiCad Python module.
