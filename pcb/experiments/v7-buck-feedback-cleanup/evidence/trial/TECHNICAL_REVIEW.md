# UNSELECTED BUCK_FB dead-arm cleanup: strict plane-preservation FAIL

## Decision
Retain this trial **UNSELECTED**. The bounded cleanup passes native DRC/ERC/parity, exact declared conductor scope, FB-pad connectivity, unrelated-net/root preservation and old-reference-shadow checks. **The strict global no-plane-loss gate FAILS:** normal refill changes remote serialized inner-plane boundaries, with independently proven nonzero source-inside/candidate-outside regions. Their subnanometre widths do not grant an epsilon waiver. No stability, noise, pickup, hardware or manufacturing improvement is claimed.

Any coordinate-precision criterion is a separately investigated proposal, not an adopted condition. Old-shadow preservation is not substituted for global plane preservation.

## Source and narrow modification
Selected source remains `2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373`; neither the unselected J3 nor C124 trial was used as the source.
Prefill: `f3b45ed754bbbb8d0c1d4cac091062f0296bae7d6b8a184b27f4631da3b23c1c`.
Normal-filled unselected trial: **`aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f`**.

Retired only:
- Degree-one BUCK_FB via `d382de57-3476-43c4-ac26-0a72b21acf7c`, center (178.15,85.75), 0.50/0.25 mm copper/drill.
- BUCK_FB F.Cu track `2c0aa2c5-bec8-4dff-bff7-2e823d3e36fa`, 0.15 mm wide, (178.15,85.75)→(182.95,85.75), 4.80 mm centerline.

Added only:
- Replacement `6ffab701-7688-4850-9aad-8ab86bd0f04a`, BUCK_FB F.Cu, 0.15 mm wide, (181.0,85.75)→(182.95,85.75), **1.95 mm active centerline**.

Exactly 2.85 mm of dead-arm centerline is removed. The active tap at (181.0,85.75), all three FB pads and all remaining FB routing are retained. Deleting the entire 4.80 mm track without this replacement would isolate U18.8; that was tested only as a read-only graph control, not constructed.

The selected board and partial/rejected J3 diagnostics remain unchanged. No via-only cleanup candidate was constructed. No trace widening, resistor/capacitor change, FB rerouting, plane-rule change or manual fill patch occurred.

## Geometry, active contacts and inherited reference
The replacement is an exact subset of the source track and exactly matches the declared 1.95 mm segment. **Added physical BUCK_FB copper is zero on all four layers.**

Removed physical BUCK_FB copper, accounting for real drills:
- F.Cu: 0.527789761808 mm².
- In1.Cu, In2.Cu and B.Cu: 0.147262362220 mm² each.

The exact declared replacement contact set is retained:
- `3c804add-ee74-5104-b471-73062ffcaeb9`, U18-side vertical tap.
- `d20e66e3-44fb-4535-81e2-9bc53c5f6519`, right-side short track.
- `37c51a69-ea1f-42e2-b356-72426fc3b1b2`, active divider-side via.

The tap's overlap with the replaced conductor changes from 0.020085808222 to 0.018878712333 mm² as the dead-side corner is removed; this 0.001207095889 mm² difference is disclosed, not called identical contact area. It remains positive and the authorized active segment/contact set is intact. Right-side track and via support areas are unchanged. Every contact between unchanged original objects is unchanged.

The existing active-end via already creates an inherited reference deficit on this retained segment: full projection 0.068332661731 mm² and actual drill-subtracted physical copper 0.051567445617 mm². Both are exactly equal before and after. This is not described as a newly zero-deficit route: no new copper or new reference deficit is introduced, and no endpoint mask is used.

## Normal native checks and same-snapshot totals
- Source: 9,752 tracks; 919 vias; 382 footprints; 13,181.60473138763 mm track length.
- Candidate: **9,752 tracks; 918 vias; 382 footprints; 13,178.75473138763 mm**.
- DRC: **12 unchanged opens, 0 other errors, 67 warnings**.
- Exactly one warning removed: the retired BUCK_FB via's dangling-via warning. No warning added; no replacement track-dangling warning.
- Schematic parity: 0. ERC: 0.
- All **245 named-net physical pad partitions are identical**, including U18.8/R159.2/R160.1 in the same FB component.
- All unchanged original direct contacts and all old zone contacts are preserved. No GND pad-root partition is split; all physical zone-island counts are unchanged.

These graph checks use positive native copper overlap after physical-drill subtraction, with each real filled-plane island treated separately.

## Real drill and fill effects
One 0.25 mm physical drill is removed: total physical drills 1,270→1,269, vias 919→918. Its native projected hole area is 0.049087681002 mm². It is not normalized away.

All outer F.Cu/B.Cu saved fills are exact. Inner native differential results:
- In1 GND gain: 0.641253861231 mm²; reported loss: **0.000000142282 mm²**.
- In2 GND gain: 0.641253859923 mm²; reported loss: **0.000000140974 mm²**.

The local restored plane covers the full former drill footprint and its former clearance region. `qa/geometry-effects.json` reports gain inside the drill, explicit native outside subtraction, arithmetic remainder, and their Boolean area-accounting residual separately. Those clipped-area figures are not silently forced to sum.

Full old non-GND reference-shadow loss is zero, including source objects later retired. All old inner-plane GND copper/annular contact-support intersections with the reported loss polygons are zero. These facts do **not** cure the global plane-loss failure.

## Exact remote-contour blocker
Native differential output contains 17 In1 and 16 In2 tiny loss polygons. They lie remotely along the lower-row contour region (roughly x9.83–268.97, y85.30–86.18 mm), not in the authorized removed-arm/via cut. Each polygon, integer-nanometre vertex list, location and bounds is retained in `qa/contour-controls.json`; none is discarded.

Raw serialized vertex multisets differ: 110 removed and 54 added vertex occurrences per inner layer. These are fractured single outlines with zero-width bridge paths around holes, not independently stored hole rings. Raw changes are not assumed to be material loss by themselves.

Independent exact rational point-membership tests, without Boolean operations, rounding or epsilon, prove actual source-inside/candidate-outside witnesses in **10/17 In1** and **9/16 In2** reported polygons. The rest are not automatically asserted to be true material loss merely because native subtraction lists them. The enclosing-strip width upper bound across reported slivers is 0.811798143432 nm. Width alone does not establish an acceptable coordinate-precision criterion.

Controls source-minus-self, candidate-minus-self and identical reparses are exactly zero. Thus at least some loss is real in the saved serialized geometry, not solely a subtraction artifact. Strict global preservation remains failed regardless of unchanged shadows/roots or small size.

## Separate deterministic-refill controls
Separate diagnostic directories preserve all originals:
- `/tmp/v7-buck-deadarm-noedit-control/`: no-electrical-edit normal refill of selected 2c7 saves **byte-identical 2c7**, with every contour unchanged.
- `/tmp/v7-buck-deadarm-repeat-control/`: repeat normal refill of exact candidate aead saves **byte-identical aead**, with every contour unchanged.

The remote fracture differences arise with the geometry deletion, not generic repeat-fill drift. These controls do not rebase acceptance or erase the source→candidate failure.

Installed native API receipt: KiCad 9.0.2+dfsg-1, `FromMM(1)=1000000`, `ToMM(1)=0.000001 mm`, `VECTOR2I` is C++ `VECTOR2<int>`. One internal coordinate unit is 1 nm. This describes storage precision only, not an authorized tolerance.

## Electrical interpretation
The historical passive study is context, not an actual board noise/loop model. It warns that reducing shunt capacitance alone can increase pickup; removing an unused arm may change coupling differently. The actual capacitance/coupling and converter-loop change are not extracted here. The prior manufacturer-width observation is not addressed by this narrow experiment, and no broader routing change is implied.

## Evidence
`qa/build.json`, `qa/fill.json`, `qa/actual-reference-comparison.json`, `qa/geometry-effects.json`, `qa/all-net-partition-comparison.json`, `qa/warning-delta.json`, `qa/drc.json`, `qa/erc.json`, `qa/contour-controls.json`, and `qa/loss-support.json` bind results to exact source/candidate hashes. Original plans, the interrupted inefficient read-only calculation attempt, native outputs and rejected trial remain preserved. Independent strict review and any separately labeled coordinate-precision addendum are kept unchanged, not merged into an adoption claim.
