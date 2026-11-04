# MARU60 V7 exact-CAD recovery baseline

This isolated recovery repository preserves the exact selected PCB after the execution workspace was replaced. It does not invent or restore the lost Git history.

Open `pcb/experiments/v7-reference-legibility/candidate/pcb/maru60.kicad_pro`.

- Selected PCB SHA256: `7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1`.
- Original selection commit: `b42351518b0007177a85fa3ce44f8d41967c9af9`.
- Last known original evidence-only HEAD: `3bed855f70875e1466f3a0a253d549ae581baaf4`.
- Original working branch: `feat/maru60-v7-protection-layout`.
- This repository starts a separate recovery history. The original Git objects and full historical QA suites are missing, not recreated from summaries.

## Exact recovery and fresh checks

All six complete board hashes, from integration baseline through U10, C128, width repair and typography, match their historical targets exactly. The independent review verifies raw deltas and unchanged saved fill bytes. This is full-byte recovery, not approximate geometry recreation.

The earlier 53-file CAD bundle was recovered from the saved tscircuit archive and verified against all 53 input hashes and all 235 delivery hashes. The selected board replaced only its earlier PCB. The expansion schematic received the same two test-point value corrections (+4V TEST and +4V_LED TEST). The complete later 54-file historical manifest is unavailable, so exact recovery is claimed for the board and the individually proven companion files, not for that missing full project map.

Fresh KiCad 9.0.2 DRC, schematic parity, ERC and netlist export completed without source changes: 12 expansion-GPIO opens, zero critical power/USB source opens, 92 warnings, zero other DRC errors, zero parity issues and zero ERC violations. Fresh native counts are 9,752 tracks, 919 vias, 382 footprints and 13,181.60473138763 mm summed track length.

Fresh receipts are under the selected unit's `qa/recovery-native`. Their execution paths identify the isolated recovery staging directory where the exact same bytes were checked. Historical full physical-graph/frozen replay is not claimed to have been rerun or recovered. Source-bound simulation archives remain separate saved artifacts; full hardware, PDN, SI, ESD, EMC, mechanical and manufacturing qualification remain false.

## Missing work and safe continuation

A reviewed, newly tested LED startup-guard recovery implementation is now active at `pcb/firmware`, with exact copies of its supporting engineering files at `pcb/engineering`. Nineteen of the 22 former fixed overlay files were recovered exactly; three guard source files are explicitly new implementations. The immutable baseline, reviewed candidate, fresh host tests and static V7 mapping are preserved under `pcb/experiments/led-startup-recovery`. Qualification remains OFF. Full pinned QMK/ARM builds and hardware acceptance have not been performed; do not flash or enable qualification. Original C124 rejected-trial packets and later unselected label/C124 studies are also not fully restored. No unselected trial is promoted here.

Continue new experiments from the exact selected board in isolated directories, with new source-bound checks and independent review before adoption. Do not weaken clearance, old conductor/reference preservation or qualification gates. Do not push or fabricate from this baseline.

`recovery/` contains reconstruction inputs, scripts, source manifests, explicit historical limitations, independent review and the exact selected-board preview. Reconstruction scripts preserve their original execution layout; they are provenance artifacts, not a relocated one-command replay promise. The saved board can be opened directly without reconstruction.
