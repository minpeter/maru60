# Direct B.Cu route screen: no path found

Invocation from repository root:
`tools/run_kicad9.sh python3 .omo/evidence/pcb-routing-20261109/header-candidates/no-new-vias/plan.py`

Scenario: remove the same six local GPIO10 B.Cu segments and insert the previously screened GPIO10 detour. Keep every existing via fixed and add no vias. Search from U13.12 to each of the five existing EXT_GPIO24 B.Cu endpoints belonging to J3.5's source material component.

Binary observable: `path_found=false` in `qa/RESULT.json`; five `FAILED EXT_GPIO24 B.Cu` rows in `planning.log`. Each finite search exhausted1331 reachable grid nodes in a25um grid, bounded by x88.275..90.15mm,y40.625..42.7mm, strictly inside the requested x80..112mm,y30..50mm search box. `qa/reach-last.json` records the reachable coordinates. Clearances remain150um for surface copper and205um to drilled signal conductors. No track widths or via dimensions were weakened.

This is a finite-grid screen, not a proof of continuous geometric impossibility. No candidate was built, and no native or plane-validation pass is claimed. The prior three-via rejected candidate remains unchanged.
