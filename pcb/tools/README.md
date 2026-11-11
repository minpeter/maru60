# PCB tools

## Relocated-expansion zero-open audit

`audit_relocated_zero_opens.py` is the promoted native audit for the
`resume-20261109-relocated-expansion-zero-opens` checkpoint. It compares the
candidate against the preserved header25/U13 seven-open checkpoint, checks the
383-footprint identity, the material graph, the inner GND planes and the
reference coverage, and writes `audit-summary.json`, `material-comparison.json`,
`routing-scope.json` and `exact-native-plane-inputs.json`. It needs the KiCad
9.0.2+dfsg-1 `pcbnew` bindings and must run through the pinned container:

```sh
tools/run_kicad9.sh python3 pcb/tools/audit_relocated_zero_opens.py \
  --out-dir .omo/evidence/relocated0-audit-new
```

The source and candidate paths default to the tracked checkpoints; all paths
are resolved from the repository root, not the current directory.

`geos_witness_zero_opens.py` is the independent GEOS + exact-rational Q^2
replay. It reads `exact-native-plane-inputs.json` from the audit output and
writes `geos-audit.json` and `geos-rational-witnesses.json` there. It runs in
the repository virtual environment (shapely 2.2.0 / GEOS 3.14.1), not `uv`:

```sh
.venv/bin/python pcb/tools/geos_witness_zero_opens.py \
  --qa-dir .omo/evidence/relocated0-audit-new
```

See `../experiments/resume-20261109-relocated-expansion-zero-opens/REPRODUCE.md`
for the full sequence and expected numbers.

## Review and fabrication tools

| Tool | Purpose | Output |
| --- | --- | --- |
| `analyze_strict_promotion.py` | Classifies the 1,837 exact-rational witnesses and writes the strict-promotion decision memo. | `qa/strict-promotion/{REPORT.md,witness-map.json,witness-map.svg}` |
| `check_mechanical_fit.py` | Ray-casts the bottom-case 3MF for the relocated block, USB-C notch and 7U stabilizer. | `qa/mechanical-fit/{REPORT.md,fit.json}` |
| `analyze_power.py` | Input capacitance, inrush, UVLO/OVLO, soft-start, LED limiter and sequencing arithmetic. | `qa/power-review/{REPORT.md,power-review.json}` |
| `export_fabrication.py` | Parses the board, writes BOM/CPL, runs the KiCad CLI for Gerbers/drill/IPC-D-356/STEP, and records provenance. | `../fabrication/` |
| `build_plate_pcb_mount.py` | Generates the PCB-mount 7U plate variant (enlarged cutout) from the INKC outline. | `models/rule60-v3-hhkb-gas-plate-pcb-mount.dxf` + FR4 zip |
| `build_topcase_usb14p75.py` | Generates the right top-case half with the 14.75 mm USB-C notch centred on J1. | `models/maru60-hhkb-topcase-right-usb-14p75-j1centred.3mf` |
| `build_bottomcase_j3_relief.py` | Generates the bottom-case halves with the local J3 relief pocket. | `models/maru60-hhkb-bottomcase-j3-relief-{left,right}.3mf` |
| `simulate_power.py` | Deterministic transient model of the eFuse, buck, UVLO/OVLO, LED rail and sequencing. | `qa/power-sim/{REPORT.md,power-sim.json,*.png}` |
| `simulate_thermal.py` | Lumped thermal network and 2D board spreading for U2/U18/U7/LEDs. | `qa/thermal-sim/{REPORT.md,thermal-sim.json,*.png}` |
| `simulate_usb_si.py` | Extracts the D+/D- route, solves the microstrip impedance and runs a PRBS-7 eye at the MCU. | `qa/usb-si-sim/{REPORT.md,usb-si-sim.json,*.png}` |

All run with the repository venv (`.venv/bin/python`), except
`export_fabrication.py`, which also calls `tools/run_kicad9.sh`. They are
analysis/export tools, not qualification: see each report's limitations.

## Order-candidate tools

These produced `experiments/resume-20261111-order-candidate` from the 0/0
prototype and export the JLCPCB package. The planners run in the repository
venv; the `apply_*`, `prune_*`, `save_*`, `dump_*` tools and the `--board` mode
of `set_component_values.py` need the KiCad 9 `pcbnew` bindings and run through
`tools/run_kicad9.sh`. They edit the board in place: use a checkpoint copy.

| Tool | Purpose |
| --- | --- |
| `dump_board_geometry.py` | Board geometry (pads, tracks, vias, zone fills, courtyards) as JSON for the planners. |
| `plan_topside_relocation.py` | Finds two-pad top-side parts under a switch or stabilizer housing, picks a position in the gap between housings and routes both pads on F.Cu (new GND via where no top-side ground is in reach). Writes a plan. |
| `apply_topside_relocation.py` | Applies that plan; `--dnp REF,...` marks parts with no possible position. |
| `prune_dangling_tracks.py` | Trims or removes the stubs a KiCad DRC report calls dangling, never past a T-junction. |
| `plan_led_alt_sites.py` | Plans a second top-side land site for an option-position LED. |
| `apply_led_alt_sites.py` | Adds planned top sites and hand-specified bottom relay sites to LED footprints. |
| `save_board_footprint_to_lib.py` | Renames an edited footprint and saves a normalised copy to a project library. |
| `apply_review_fixes.py` | U13 land pattern, L1 pour keep-out, C102 position. |
| `set_component_values.py` | Sets values in the schematic sheets and on the board from one change list. |
| `local_router.py` | Library: one-pad single-layer router with exact clearance check, and via placement checked on all layers. |
| `apply_layout_ops.py` | Applies an operation list (tracks, vias, footprints, pads, drills, text, graphics) to a board. |
| `plan_ldo_swap.py`, `edit_schematic_ldo_swap.py` | Board and schematic side of replacing the MAX38902A by an AP2112K-3.3. |
| `plan_bottom_sites.py` | Bottom-side land sites fed through new vias (used for `C200`). |
| `plan_series_resistor.py` | `R115`–`R119`, `R170`–`R186`: follows an LED data hop from DOUT through tracks and vias, cuts it near the source and places a series resistor at the cut, on B.Cu or (outside the switch keep-out) F.Cu. With `MIN_MM` it may also start at a track end, for hops that run under housings without a via. `R181`, `R184`–`R186` were planned by hand (their operation lists say why). |
| `plan_two_pad_part.py` | A new 0402 two-pad part beside an existing one, routed to its two nets (`C143`, the buck feed-forward capacitor). |
| `fit_jlcpcb_placement.py` | Fetches JLCPCB's footprint for each part and solves the placement rotation and centre. Needs network. |
| `export_order_package.py` | DRC, BOM, CPL (using the fitted placements), Gerbers, drill files and provenance into `../order/`. |
| `verify_gerbers.py` | Reads the exported Gerber and drill files with gerbonara and compares holes, pads and outline with the board. |
| `analyze_pdn.py` | Resistance network of the power nets from the routed copper: drops, track loading, LED rail voltage. |
| `power_sim/` | ngspice decks and behavioural models of the power tree; `run_power_sim.py` runs every case. |
| `signal_integrity/` | Field solver, line models and ngspice decks for LED data, USB, crystal, matrix and flash. |
| `check_dfm_jlcpcb.py` | JLCPCB checks a rule deck cannot express: via holes in SMD pads, mask web on fine-pitch parts, stencil area ratio, parts near the edge, fiducials. Holds the JLCPCB limits with their sources; the rule deck itself is in the checkpoint's `qa/dfm-jlcpcb/`. |
| `run_dfm_jlcpcb_drc.py` | Runs KiCad DRC once per rule of the JLCPCB rule deck on scratch copies of the project and collects every finding (`qa/dfm-jlcpcb/drc-per-rule.json`). |
| `plan_npth_clearance.py` | Plans the track detours that keep copper 0.2 mm from non-plated holes: tangent polygons round the hole, neighbours pushed outward where needed. Output is an operation list for `apply_layout_ops.py`. |
| `plan_via_out_of_pad.py` | Moves via holes out of SMD pads where a free position exists. |
| `plan_via_relocate.py` | For the vias that could not simply be nudged: takes the via out of the pad, finds a free position up to a few millimetres away and routes both layers to it. |
| `plan_pair_route.py` | Shortest any-angle route for a differential pair over both outer layers: Dijkstra on a 0.1 mm grid with 16 directions, then string pulling on a 0.05 mm clearance map. Used to lay the USB pair again (156 mm → 138 mm). `--soft` lists the tracks a still shorter route would have to cross. |
| `plan_pair_tracks.py` | Turns that centre line into the two tracks and the via pairs, removes the old pair, and checks every new piece of copper on the exact geometry before it writes the operation list. |
| `edit_schematic_added_parts.py` | Writes the symbols of parts added by the layout tools (two-pin part with a global label on each pin, Core sheet) and renames the label on the driving LED's DOUT pin. |

## Current physical-material checker

`export_material_graph.py` is the exact reviewed R2 implementation, SHA256 57987368b095de525fc729a0d4b729b14cfc207afd07b4bd214ee5463a7719b9. It accepts an input PCB path and an output JSON path. It requires the checked KiCad 9.0.2+dfsg-1 Python bindings, exactly four copper layers and the asserted through-hole geometry. Unsupported cases fail closed. Do not use optimized Python.

The caller must supply a new output path distinct from the input board; the preserved checker itself does not enforce output-path exclusivity. The following example uses a separate output file. Do not pass an existing CAD or evidence file as the output.

Example from this repository:

`/usr/bin/python3 pcb/tools/export_material_graph.py pcb/experiments/v7-buck-feedback-cleanup/candidate/pcb/maru60.kicad_pcb /tmp/v7-material-graph.json`

For isolated runs, set fresh private XDG_CONFIG_HOME, XDG_CACHE_HOME, XDG_DATA_HOME, XDG_STATE_HOME and XDG_RUNTIME_DIR directories; the runtime directory must have mode 0700. This script does not configure isolation itself. The historical runner's XDG_RUNTIME_HOME typo is explicitly recorded in the erratum, not silently fixed in its receipts.

This is a source-specific nominal material-connectivity checker, not a DRC/ERC/parity checker, independent CAD kernel, analog/SI simulator, manufacturing or hardware qualification. Native candidate-pair discovery can omit a geometric contact; accepted contacts require conservative positive material overlap. See `../experiments/v7-material-contact-correction/` for all reviewed controls, exact selected-board contact witnesses, original limitations and superseded evidence. Stored test/report paths preserve execution provenance; no relocated one-command replay of every historical suite is claimed.
