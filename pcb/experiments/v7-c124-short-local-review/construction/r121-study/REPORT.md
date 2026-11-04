# R121 bounded native geometry study

Source: `/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104/selected-recovered/pcb/maru60.kicad_pcb`
SHA-256 before and after: `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1`.
KiCad pcbnew 9.0.2+dfsg-1; private XDG directory; one BOARD in each bounded process. No CAD saves, fills, production edits, track deletions, or whole-board connectivity graph. Trials restore original pad and courtyard primitives before each transform to prevent incremental-rotation nanometre rounding accumulation.

## Main findings

There is a nominal-copper placement opening, not an assembly-approved solution. R121's MPN, terminal envelope, and assembly tolerances are unknown. The exact fixed prospective R125 center (15.600,20.100) and C124 center (15.600,19.050) have two courtyard tangencies: R125–U8 at x=16.500 and R125–C124 at y=19.575. R121 movement alone cannot remove these two tangencies.

A concrete strictly positive courtyard screen uses R125=(15.595,20.100), size 1.800×1.050; C124=(15.600,19.045), size 1.600×1.050; and R121=(14.000,18.500), angle 88°. R121's centroid does not move. R125–U8 and R125–C124 source-line courtyard gaps are each 0.005000 mm. R121–R125 native gap bracket is 0.002093–0.002094 mm. R121 minimum different-net copper gap is 0.156203–0.156204 mm; all tested nearby native copper passes 0.150 mm, with 1 nm inside/outside expanded-polygon verification on governing obstacles. Both original R121 contacts remain positive.

The optional R121 center (14.000,18.475), still 88°, improves minimum different-net copper gap to 0.164396–0.164397 mm and R121–R125 courtyard gap to 0.002966–0.002967 mm. R121–new C124 courtyard gap is 0.071082–0.071083 mm. No neighboring existing source courtyard collision was found (C124 retired/replaced; SW16 is well below the region).

These 2–5 µm courtyard margins are very small. They do not establish real-terminal or assembly feasibility and are not a waiver. Full new R125/C124 copper routing, terminal bounds, and bridge validation remain with the parent worker.

## Actual R121 metadata

- Footprint `Resistor_SMD:R_0603_1608Metric`, UUID `d422a027-2eda-4bf9-9c83-1580d56a84b7`.
- B.Cu center (14.000,18.500), original angle 90°; value `156k 0.1%`.
- PCB fields are Reference, Value, empty Datasheet, empty Description. No manufacturer or MPN exists in this footprint.
- Matching source schematic R121, UUID `3c9a1e86-b5b6-52b9-8936-5c621f352915`, has empty Datasheet and Status `CANDIDATE - not procurement approved`.
- Pad1 UUID `2ceda713-c41e-4c74-9962-f6a642f1e236`: USB_OVLO, center (14.000,19.325), native 0.800×0.950 roundrect, 90°, radius 0.200 mm.
- Pad2 UUID `437d8abf-8e4f-4587-99b7-93c610dd4000`: GND, center (14.000,17.675), same shape.
- Nominal B.Fab body is 1.600×0.825 mm. This is not a measured or manufacturer-qualified terminal envelope.

## Pure-left bound

The straight UVLO track is not the limiting geometry: its nominal gap is 0.200000 mm. UVLO endpoint/corner contacts limit both R121 pads to nominal gap

`sqrt(0.425²+0.175²) − (0.200+0.075) = 0.184619407771 mm`.

At 0.150 mm clearance, exact idealized roundrect/capsule pure-left bound is

`0.425 − sqrt(0.425²−0.175²) = 0.037701665379 mm`.

Native effective-shape tests pass 37,701 nm left and fail 37,702 nm left. The 1 nm polygon inside/outside proof conservatively passes 37,700 nm; 37,701–37,702 nm is too close to the approximation boundary for a conservative pass. Do not round the allowance to 0.050 mm.

Governing UVLO UUIDs:
- Pad1: `3a13a9a0-dbbd-42a5-ad34-f1171f7bdf93`, `4174a692-19ae-4049-916a-e21e775415e2`.
- Pad2: `a621cda3-f605-4bff-b3d7-2213de164c79`, `db0f565d-8915-441b-b9f8-50cdd933467c`.
- Nearby ILM via `ff31c038-3a4c-4c1b-880e-025462019509` has original pad2 gap 0.187377–0.187378 mm.

At original prospective R125 x=15.600, the minimum integer-grid pure-left displacement for strictly positive R121–R125 source courtyard separation is 30,001 nm. At R125 x=15.595, it is 35,001 nm, giving only 1 nm courtyard gap. Neither is a practical safety margin. Pure Y translations within ±0.200 mm do not eliminate the original courtyard overlap. A bounded sampled Y/angle study was also performed, not an exhaustive global placement search. Rotations to 87° and below in the sampled upward-shift cases fail the fixed straight UVLO track; these were rejected.

## Courtyard source evidence

- Actual R121 centerline rectangle: x=13.270..14.730, y=17.020..19.980.
- Actual U8 centerline rectangle: x=16.500..19.500, y=17.000..20.000.
- Native cached courtyard polygon shrinks these edges inward by 0.005 mm on this board. Its bbox additionally expands by a different amount. Neither cached result was treated as the exact source outline. Checks use native polygons made from actual native source courtyard line/rectangle vertices.
- Original R125 center15.600/source court right16.500 touches U8, despite a misleading cached 5 µm gap.

## Original contacts and overlap changes

Original native track contacts are exactly:
- R121.1 → OVLO `05a0b97d-79af-50e5-b191-fe26b55d2c02`.
- R121.2 → GND `abcd4fb1-881b-43f9-906e-39d93366692e`.

R121.2 does not directly contact via `763086b7-5549-4f5e-bb08-ce25387b3627`: its gap is 0.206220–0.206221 mm. The existing GND spur does contact that via, with native 1 nm inside/outside overlap area approximately 0.06434031–0.06434078 mm². No old GND object was moved, cut, retired, or bypassed.

Approximate copper-contact intersection areas (mm²; rounded to 6 decimals, native clipping/approximation uncertainty approximately ±0.000002 mm²):

| Candidate | Contact | Original area | New area | Lost overlap | Gained overlap |
|---|---|---:|---:|---:|---:|
| Center14,18.5;88° | pad1→old OVLO | 0.088252 | 0.083270 | 0.004983 | ~0 |
| Center14,18.5;88° | pad2→old GND spur | 0.118392 | 0.125116 | ~0 | 0.006724 |
| Center14,18.475;88° | pad1→old OVLO | 0.088252 | 0.082264 | 0.005988 | ~0 |
| Center14,18.475;88° | pad2→old GND spur | 0.118392 | 0.125996 | ~0 | 0.007604 |
| Center13.964999,18.5;90° | pad1→old OVLO | 0.088252 | 0.083059 | 0.005193 | ~0 |
| Center13.964999,18.5;90° | pad2→old GND spur | 0.118392 | 0.111155 | 0.007237 | ~0 |

Both original contacts persist, with no new track contact, in each listed case. The old OVLO contact is historical evidence only: the parent's replacement of four OVLO arm tracks must reconnect pad1 after those tracks are analytically retired. Small sub-micro-mm² clipping residuals in raw files are numerical artifacts and are not claimed as real gained/lost copper islands.

## Files

- `initial.json`: original source metadata/local native copper.
- `evaluate.json`: pure-left native bound, original contacts, cached court diagnostic.
- `refine.json`: corrected anchored rotation/translation checks and 1 nm polygon proof.
- `scan.json`: bounded Y/angle samples and preferred inside/outside proof.
- `final_verify.json`: final exact-coordinate candidates, retained contacts, intersection areas, source hash.
- `run_refine.py`, `run_scan.py`, `run_final_verify.py` plus helper scripts reproduce only read-only source loading and isolated in-memory native geometry trials. There is no CAD output to apply.


---

# Drill-aware correction: existing R121 GND spur to via

This supersedes only the approximately 0.064340 mm² spur-to-via contact area stated in REPORT.md and final_verify.json. That earlier value was the intersection with the via's full outer disk and incorrectly counted the drilled hole as copper. The mistake is recorded here; physical via-contact calculations must subtract the actual native drill before interpreting intersection area as conductive copper.

Fresh read-only native measurement from the same verified source:

- GND track: `abcd4fb1-881b-43f9-906e-39d93366692e`, width 0.200 mm, from (14.000,17.675) to (14.900,17.275).
- GND via: `763086b7-5549-4f5e-bb08-ce25387b3627`, center (14.900,17.275), B.Cu outer diameter **0.500 mm**, actual and stored drill diameter **0.250 mm**.
- Native hole geometry comes directly from `GetEffectiveHoleShape()`. It was converted with 1 nm inside/outside approximations, rather than deriving a hole from a remembered drill size.
- Conservative annulus construction: lower copper = inside outer disk minus outside actual hole; upper copper = outside outer disk minus inside actual hole. Intersect these with inside/outside track copper respectively.
- **Physical annular contact area: 0.026643447977 to 0.0266438978185 mm². Both native results are strictly positive.**
- Earlier full-disk intersection: 0.0643403097475 to 0.064340777041 mm². This is an outer-envelope overlap, not a physical conductive-contact area.
- Native track/drill-hole overlap: 0.037696617479 to 0.037697177913 mm².
- Independent operation-order check, intersection first then hole subtraction: 0.026643486929 to 0.0266438665085 mm², within the stated annular interval. Small differences are integer polygon-clipping quantization.

The retained original GND spur still makes positive physical annular contact with its existing via. No conclusion about the nominal R121 placement, pure-left bound, or original pad-to-track contacts changes.

## Other disk-based measurements

No other nonzero track-to-via or pad-to-via intersection area was reported in this study. The R121 overlap tables measure SMD-pad/track intersections, neither object having a hole. They do not count a via disk as copper.

The original R121.2-to-GND-via distance and R121-to-ILM-via clearances used via outer-copper envelopes. The evaluated pads are outside those disks, so their nearest copper is on the outer annular edge; subtracting the central drill does not alter those distances. Any future claim of actual contact with any via must use drill-subtracted copper rather than an outer disk.

## Retention and evidence

The completed source remains unchanged, SHA-256 `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1`.

All completed JSON and raw log files were retained unchanged. Their before/after SHA-256 verification is recorded in `drill_annulus_correction.json`.

New artifacts only: `drill_annulus_correction.py`, `drill_annulus_correction.json`, `drill_annulus_correction.log`, and this correction. This correction is also appended to REPORT.md. No CAD was saved, filled, or edited.
