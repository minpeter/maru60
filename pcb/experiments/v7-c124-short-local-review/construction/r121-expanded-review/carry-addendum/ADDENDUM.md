# Independent artwork-carry addendum

Result: the separate unselected successor preserves the reviewed 8c45 trial's electrical geometry, drills, complete fills, nets and settings exactly. No new carry blocker was found. This is neither qualification nor adoption, and it does not waive any existing issue or turn proposed parts/process tolerances into assembly approval.

## Exact files

- Reviewed immutable trial: `/tmp/v7-c124-rebound-short/isolated-v4/filled/pcb/maru60.kicad_pcb`, SHA-256 `8c45df3642599be269697ce9b225fe55ee6b886dce713b77f6ced533ea268fb6`.
- Artwork-carry successor: `/tmp/v7-c124-rebound-short/isolated-v4-label-carry/pcb/maru60.kicad_pcb`, SHA-256 `ec48735f21b813f84873a4dfcd8a984a395f59a6d48d30e5bcfff19aaefe52a7`.
- Accepted artwork source: `/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb/maru60.kicad_pcb`, SHA-256 `2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373`.

## Independent checks

A string-aware S-expression span parser compared original bytes, independently of CARRY_PROOF's assertions. Exactly five footprint blocks differ. Each new block is an exact complete-block copy from selected 2c7. Within C100, R140, R160 and R134, only the Reference property differs, and those fields are B.SilkS before and after. The complete LOGO1 footprint is copied intact; both old and new LOGO1 contain only B.SilkS/B.Fab graphics/properties, with no pad, drill, zone or conductive primitive. Its B.Cu footprint container layer does not itself draw copper.

After replacing those five blocks with identical markers, the entire board strings are byte-identical, including ordering and whitespace. All 378 other footprints, all 9,742 segments, all 919 vias, all 247 net definitions, all 12 complete zone/fill records, board settings and other root records are unchanged. The unchanged contents inside the four reference-only footprints preserve their pads/drills; neither LOGO1 has conductive geometry. All common companion files, including maru60.kicad_pro, are byte-identical.

## Provided fresh DRC

The supplied `qa/drc.json` is KiCad 9.0.2, dated 2026-11-04T19:12:50+0900 (10:12:50 UTC). Its accompanying log names this successor's report path. No DRC/native board load was rerun during this review.

- 64 warnings: 22 text_height, 19 silk_over_copper, 15 silk_overlap, 6 track_dangling, 2 via_dangling.
- Compared with the reviewed 8c45 report: exactly 24 warning records removed, zero added. Removals comprise 4 text-height, 5 silk-over-copper and 15 silk-overlap warnings.
- All 12 unconnected-error records remain exactly identical. Schematic parity has zero entries.
- GROUND_BRIDGE_B UUID `0dd51559-bc06-502f-8bb1-1b186fa751d0` still has the unchanged track_dangling warning at (15.5,17.85). The prior native physical-contact result remains valid because its geometry is unchanged; the warning is unresolved and unwaived. Do not call the board DRC-clean.

## Preservation and artifacts

Only this new addendum directory was written. No source, successor, project, fill or prior sealed actual-review artifact was changed. All three PCB hashes and CARRY_PROOF hash were rechecked after parsing. No pcbnew import, BOARD load, native fill, export or geometric sweep was performed.

Evidence: `review_carry.py`, `review_carry.log`, and `pure_file_review.json`. The JSON contains exact per-block hashes, field diffs, companion hashes, complete DRC record differences and final input hashes. The earlier sealed `../actual/REVIEW_ACTUAL.md` remains unchanged and applies to the electrically identical successor within its original scope and limitations.
