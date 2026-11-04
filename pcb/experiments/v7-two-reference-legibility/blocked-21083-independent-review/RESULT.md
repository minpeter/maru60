# Independent U18 / L2 label review

Status: original trial 21083 remains UNSELECTED and does not meet the exact nominal 0.150 mm courtyard criterion at U18. No source or candidate geometry was changed by this review.

Source: 7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401. Trial: 21083e9498512939d40d95eb6866850367939e590fcf949440b4d4642b46727b.

## Exact scope and native results

Independent raw-byte reconstruction proves only the U18 and L2 Reference property children changed. All other bytes within those footprints, every other raw top-level object, all 12 zones, all copper/pads/holes/settings and all 57 companion files are exact. All eight selected-scope footprints queried below are entirely byte-identical to source. Native report comparison independently confirms exactly six retired warnings, none added, 64 → 58 warnings, all 12 raw opens unchanged, no other hard error and parity 0. A separate cold normal refill of the copied trial is byte-identical in 2.106992580 s, using one BOARD and five private XDG directories.

The six retired records are U18 and L2 silk-over-copper, their two text-height warnings, U18 overlap with R159 reference, and U18 overlap with C139 silk. Exact warning objects are in qa/raw-warning-comparison.json.

The native before/after pixels show clearer immediate ownership: U18 alongside its IC and L2 above its inductor. The image is hash-bound in inputs; its original courtyard caption is cached-only and is superseded by this three-boundary audit. Improved pixels do not override the failing numerical U18 gap.

## Three separate courtyard meanings

The existing native cached filled courtyard, the raw closed nominal centerline interior, and the actual drawing stroke envelope are distinct shapes. The stroke envelope is an additional stricter screen; it is not retroactively substituted for the earlier selected-label courtyard/Fab-proxy criterion. The original report is retained. qa/three-boundaries.json supersedes only the courtyard interpretation in the earlier audit.

| Reference | Cached filled gap mm | Raw closed nominal gap mm | Drawn stroke gap mm |
|---|---:|---:|---:|
| U18 | 0.154525 | 0.149525 | 0.124525 |
| L2 | 0.181145 | 0.176145 | 0.151145 |
| C100 | 0.169895 | 0.164895 | 0.139895 |
| R140 | 0.204523 | 0.199523 | 0.174523 |
| R160 | 0.239895 | 0.234895 | 0.209895 |
| R134 | 0.159895 | 0.154895 | 0.129895 |
| C124 | 0.176332 | 0.169964 | 0.144964 |
| R121 | 0.162620 | 0.157620 | 0.132620 |
| R125 | intersection | intersection | intersection |
| U8 | intersection | intersection | intersection |

U18 raw nominal gap is 0.149525–0.149526 mm, which fails 0.150 mm independently of the optional stroke-envelope interpretation. The four already-selected labels C100/R140/R160/R134 still exceed 0.150 mm against exact nominal boundaries; their lower stroke gaps are disclosed, not declared retroactive failures. C124 and R121 also pass nominal. R125 and U8 already intersect courtyards under all three methods; they are unchanged inherited limitations and were not repaired or newly introduced by this text trial.

For ordinary straight sides the cache is inset 0.005 mm from the raw nominal line; a 0.050 mm drawn stroke adds another 0.025 mm outward. This is not assumed universally: C124 is corner-limited, and the full actual partner width inventory includes SW16’s 0.127 mm strokes. Every reported positive nearest nominal partner is a raw integer line/rectangle contour (no arc approximation). SW16’s closed interior includes two source three-point arcs, reconstructed with chord sagitta ≤0.25 nm plus ≤0.708 nm rounding; R125 already intersects its straight boundary, so that arc approximation cannot change the disposition.

## Read-only successor proposal

At unchanged size 0.80 × 0.80 mm, stroke 0.12 mm, orientation 0°, mirrored visible B.Silk:
- U18 global anchor (176.65,84.25) mm: cached / nominal / stroked gaps 0.254525 / 0.249525 / 0.224525 mm.
- L2 global anchor (174.95,77.90) mm: cached / nominal / stroked gaps 0.281145 / 0.276145 / 0.251145 mm.

Both proposed fields pass every ordinary native mask/silk/Fab/edge check, whole-ink-inside-board, and both nominal and optional stroked courtyard spacing ≥0.200 mm. These poses were changed only in memory for measurement; no successor CAD has been constructed. Parent may build a separate successor and verify its exact fields/native DRC/pixels/refill.

No global assembly, visibility under installed components, manufacturing, SI, hardware or active-startup qualification is made. The selected source and all frozen evidence remain untouched. Initial closed-contour reconstruction failures on arc-containing switch courtyards are preserved in v0/v1/v2 logs; they caused no saved geometry changes. The final successful method handles their arcs explicitly.
