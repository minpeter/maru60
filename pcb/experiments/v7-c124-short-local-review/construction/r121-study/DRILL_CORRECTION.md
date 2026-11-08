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
