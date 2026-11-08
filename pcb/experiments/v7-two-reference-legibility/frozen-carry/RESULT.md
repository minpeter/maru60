# Actual two-label carry onto selected serial-leg source

Status: UNSELECTED, scoped carry eligible for parent review/integration. No repository entrypoint was modified by this work.

Selected electrical source: abdbf4c80e11cadc525389060d2215b73fc3cbcc85b2bff6ddb0e8d2581e052d, installed by parent in commit 4f2d101b1338601a9bb37882153083851d1f905d. Exact label source: 99c2ef0ef03406fda6bff02d1d9dcf81712698eed2657514826593911b12c552, separately independently reviewed in /tmp/v7-two-label-corrected-independent-review. The original blocked 21083 packet remains untouched.

Actual filled board: 4765dfd82f70cfcfc00c06b4d9abfb614c7d657ec086fcf57c28d49bc3236136 at filled/pcb/maru60.kicad_pcb. Source/prefill/filled are separate trees. Normal refill is byte-identical to prefill in 2.354867303 seconds.

## Exact changes and results

Only the U18 and L2 Reference properties are carried, byte-exact from corrected99c2. Restoring exactly these two property children recovers the complete abdb source file byte for byte. All 57 companions are also exact. This is stronger than net or topology equivalence: every electrical object, pad, hole, plane fill, rule and component identity is unchanged. The previous corrected R2, actual strong-support, all-hole reference and all-net comparisons therefore inherit exactly. No duplicate full graph was run and no new circuit/noise/stability inference is made.

Fresh native DRC explicitly included --schematic-parity: 55 warnings, the same 12 raw open entries, zero other hard DRC errors, parity 0. Exactly the six independently reviewed label warnings retire relative to abdb (61 → 55), with no new warning. Relative to earlier7882, all nine expected warning retirements are exact: three serial-support warnings plus six label warnings. Schematics are byte-identical to abdb, so its fresh ERC0 result inherits; this carry did not rerun ERC.

Same-snapshot native totals: 9,750 tracks, 919 vias, 383 footprints, 13,184.45545001526 mm. No copper geometry changed in this label carry.

## Actual saved-field geometry and visual review

U18 is at (176.65,84.25) mm; L2 at (174.95,77.90) mm. Both are visible mirrored B.Silk, 0.80 mm size, 0.12 mm stroke, 0 degrees. A fresh read-only native inspection of the combined saved board reproduces every actual field geometry measurement from independently reviewed99c2 exactly.

Cached filled / exact raw nominal / actual drawn-stroke courtyard gaps:
- U18: 0.254525 / 0.249525 / 0.224525 mm.
- L2: 0.281145 / 0.276145 / 0.251145 mm.

Both nominal and optional stroked envelopes exceed 0.20 mm. All ordinary silk/mask/Fab/board-edge checks pass; minimum actual ink-to-mask gap among these fields is 0.576680 mm and ink-to-other-silk gap 0.286708 mm. The native before/after image was viewed and shows clear ownership beside U18 and above L2. Actual image, plot and board hashes are in images/IMAGE_BINDING.json.

The three-way scope audit retains earlier meanings: four previously accepted labels and C124/R121 pass nominal 0.150 mm; their stricter stroke-envelope numbers are disclosed separately. Unchanged R125/U8 courtyard intersections remain inherited limitations, not waived or newly repaired. No global assembly, manufacturing, installed-component visibility, hardware, active-startup, pulse/reset, SI/ESD, noise or stability qualification is asserted.

## Evidence

- BUILD_CONTRACT.json: exact old/new raw Reference fields.
- qa/combined-comparison.json: complete byte reversion, all companions, exact warning/open deltas, actual geometry equality and inherited electrical-proof hashes.
- qa/native-fill.json and qa/drc.json: actual native outcome.
- qa/three-boundaries.json: saved-board actual full ink and distinct courtyard shapes.
- FILLED_TREE_MANIFEST.json: all58 project-file hashes.
- inputs/: sealed independent serial and corrected-label review bindings.

All successful CAD measurement/fill/DRC/export processes used private XDG directories. One earlier CLI-help-only lookup (before these runs) lacked private XDG and logged read-only configuration-creation failures; it is not used as geometry or acceptance evidence. No private configuration write succeeded there.
