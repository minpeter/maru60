# Unselected natural serial-leg trial

Source: experimental selection 7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401.
Actual filled candidate: abdbf4c80e11cadc525389060d2215b73fc3cbcc85b2bff6ddb0e8d2581e052d, `filled/pcb/maru60.kicad_pcb`.

Only three existing main-track endpoints change. The three old support tracks retain their complete records and now form genuine serial conductive legs. There are no duplicate tracks, added or removed objects, zero-length objects, fake loops, changed item types, drill changes, or footprint changes. BUILD_CONTRACT.json contains exact endpoints and UUIDs.

- GND abcd4fb1 starts at (14.54,17.435) instead of (14,17.675), reached through existing f58bc791.
- OVLO ae94ea04 ends at (20.0725,20.9785) instead of (20.175,21), continuing through existing cc1282fe.
- UVLO f41eeb49 starts at (14.1,16.45) instead of (14.2,16.35), reached through existing d4be2091.

KiCad's endpoint-dangling heuristic can assign a neighboring track touching both endpoint disks to only the nearer endpoint. Previously broad overlapping support branches therefore generated real open-end warnings despite positive metal support. This trial does not conceal those branches: the main paths now use them serially, and all six affected native endpoint checks are non-dangling.

## Actual results

Normal refill is byte-identical to prefill. Native DRC: 61 warnings (64 before), zero other hard errors, all 12 raw open entries unchanged, parity 0; fresh ERC 0. Exactly the three support-end warnings retire, with no added warning. Same-snapshot totals: 9,750 tracks / 919 vias / 383 footprints / 13,184.45545001526 mm.

All 57 companion files, all footprints/pads/drills, all 12 serialized zone records and every other native top-level object are byte-exact. Consequently actual saved plane material and every original/current/historical reference projection are unchanged, including the far connector drill. New OVLO/UVLO full outward-2-nm projections are also covered by the actual saved all-hole plane material. All 14 original/source support patches pass exact and expanded-old/eroded-new 2-nm coverage without a numeric tolerance.

The one corrected R2 export (checker SHA 57987368b095de525fc729a0d4b729b14cfc207afd07b4bd214ee5463a7719b9) passes all nine comparison gates: full net component equivalence and pad partitions, unchanged objects/nodes outside the three tracks, unchanged nonincident material contacts, barrel proofs, guard results and pad inventory. Individual contact witnesses incident to the three tracks intentionally change. Two old main-track edges disappear, while the complete support union remains and every old net component is preserved. See qa/material-comparison.json rather than treating old pairwise contact areas as invariant.

## Explicit material delta

The ideal GND capsule union is equivalent, but native polygon tessellation is not bit-identical. Measured local union old-minus-new/new-minus-old areas in mm² are:
- GND: 0.000000053943 / 0.0000002814105.
- OVLO: 0.020167169438 / 0.018984262772.
- UVLO: 0.019024172307 / 0.016339260869.

These nonzero differences are retained as actual geometry evidence. They are not rounded away or excused by a tolerance. The exact support/reference gates independently pass. Minimum actual foreign-copper clearance among the changed tracks is 0.193392 mm; minimum checked component-terminal-envelope clearance is 0.883943 mm.

## Evidence provenance and limits

qa/actual-serial-guards.json explicitly binds actual abdb to comparison baseline 7882. `loaded_actual_*` fields are the saved candidate coordinates; `original_source_*` are the source contract coordinates. The original schema-v0 report is preserved separately. No numeric results were changed by the schema clarification. Cached local old-object metal from immutable D/f987 equals 7882 because the sole intervening connector drill is remote and the combined exact material replay proved all original objects unchanged. Cached D planes are NOT used: this actual guard run subtracts every actual physical drill from actual saved abdb zones. The raw serialized zone/drill equality is a separate global invariance proof.

Earlier pure-split screens are exploratory and are not the construction contract. Their historical `original_end_mm` field can contain a mutated SWIG vector; source raw records and this actual contract are authoritative. No exploratory split was saved to CAD.

This candidate remains UNSELECTED pending the parent's independent review. No electrical/active-startup, pulse/reset, SI/ESD, assembly, manufacturing or hardware qualification is inferred. The selected source and all frozen earlier evidence remain unchanged. Independent text-only label work is separate and has not been carried onto this copper candidate.
