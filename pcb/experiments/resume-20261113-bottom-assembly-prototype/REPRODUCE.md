# Recheck the routed bottom-assembly candidate

Run from the repository root. Use the pinned `maru60-kicad:9.0.2` Docker image
through `tools/run_kicad9.sh` and the repository `.venv` for Shapely/SciPy.
The optional USB/crystal calculations also require `maru60-ngspice:bookworm`.
Use a fresh repository-relative output directory. These commands copy the CAD;
they do not replace the working candidate or change `pcb/current.json`.

```bash
candidate=pcb/experiments/resume-20261113-bottom-assembly-prototype
baseline=pcb/experiments/resume-20261113-mcu-near-usb-zero-opens
checkdir=build/bottom-assembly-recheck
mkdir "$checkdir"
cp -a "$candidate/pcb" "$checkdir/cad"

tools/run_kicad9.sh python3 -c 'import pcbnew as p,sys; b=p.LoadBoard(sys.argv[1]); [z.UnFill() for z in b.Zones() if not z.GetIsRuleArea()]; p.ZONE_FILLER(b).Fill(b.Zones()); p.SaveBoard(sys.argv[1],b)' "$checkdir/cad/maru60.kicad_pcb"
tools/run_kicad9.sh kicad-cli pcb drc --format json --schematic-parity --exit-code-violations -o "$checkdir/drc.json" "$checkdir/cad/maru60.kicad_pcb"
tools/run_kicad9.sh kicad-cli sch erc --format json --exit-code-violations -o "$checkdir/erc.json" "$checkdir/cad/maru60.kicad_sch"
tools/run_kicad9.sh python3 pcb/tools/dump_board_geometry.py "$checkdir/cad/maru60.kicad_pcb" "$checkdir/geometry.json"
tools/run_kicad9.sh python3 pcb/tools/dump_board_geometry.py "$baseline/pcb/maru60.kicad_pcb" "$checkdir/baseline.json"
tools/run_kicad9.sh python3 pcb/tools/export_material_graph.py "$checkdir/cad/maru60.kicad_pcb" "$checkdir/material.json"

.venv/bin/python pcb/tools/verify_bottom_assembly_invariants.py "$checkdir/baseline.json" "$checkdir/geometry.json" "$candidate/design/bottom-assembly-plan.json" "$checkdir/invariants.json"
.venv/bin/python pcb/tools/compare_critical_return_planes.py "$checkdir/baseline.json" "$checkdir/geometry.json" "$checkdir/return-planes.json"
for site14 in 0 1; do
  for site15 in 0 1; do
    .venv/bin/python pcb/tools/analyze_pdn.py "$checkdir/geometry.json" "$checkdir/pdn-$site14-$site15" --led-site "LED14=$site14" --led-site "LED15=$site15"
  done
done
.venv/bin/python pcb/tools/signal_integrity/run_candidate.py "$checkdir/geometry.json" "$checkdir/cad/maru60.kicad_pcb" "$checkdir/si" extract_geometry
.venv/bin/python pcb/tools/signal_integrity/run_candidate.py "$checkdir/geometry.json" "$checkdir/cad/maru60.kicad_pcb" "$checkdir/si" sim_usb
.venv/bin/python pcb/tools/signal_integrity/run_candidate.py "$checkdir/geometry.json" "$checkdir/cad/maru60.kicad_pcb" "$checkdir/si" sim_xtal
```

Inspect the reports as well as process exit codes:

- DRC violations, unconnected items, parity issues and ERC violations: zero.
- Material graph: 274 named nets, **one pad partition per net**; board hash
  unchanged during analysis. Every contact rejected by the 2 nm inward guard is
  excluded from unioning. The remaining positive contacts must connect all pads.
  Individual unproved contacts are not waived or promoted to a strict baseline.
- Invariants: `pass: true`; 67 mechanical footprints unchanged, 64 reverse LEDs,
  66 windows, two exclusive sites each for LED14/15, no top SMT.
- Return planes: `no_new_centerline_loss_at_native_resolution: true`; inspect the
  retained raw differences and corridor areas. This is not an EM simulation.
- PDN: all loaded nodes connect; check all four population cases. Compare each
  reported segment current to its empirical `ipc2221_10C_limit_a`. DC success
  does **not** establish PWM pulse support, inrush, or temperature qualification.
- SI: key/underglow chain counts 64/12, eight alternate-site hop cases. USB board
  propagation is compared to 1 ns. Source edges, receiver loads, crystal gain and
  pin capacitances remain stated model assumptions. The fastest host-source
  corner rings; its automatically extracted edge metrics are not a USB compliance
  verdict. The mixed-part LED analog simulator intentionally refuses this board.

Regression checks used for this change:

```bash
tools/run_kicad9.sh python3 tests/test_prune_track_junction.py
tools/run_kicad9.sh python3 tests/test_board_cutout_material.py
.venv/bin/python tests/test_local_router_cutouts.py
.venv/bin/python tests/test_component_router_layers.py
.venv/bin/python tests/test_reverse_led_analysis.py
PYTHONPATH=. .venv/bin/python tests/test_pdn_network.py
git diff --check
```

The saved board is the reviewable CAD source. Historical operation files include
rejected attempts. `design/supply-track-repair-ops.json` and
`design/restore-critical-planes.py` record the final supply/return-plane repair;
see its input hash in `evidence/supply-return-repair.json`. Do not apply these
operations a second time to the final board. Never use
`apply_reverse_led_candidate.py --reset-board` to replay this routed snapshot.

Passing these checks does not close the reverse-LED supply transient, mixed LED
signal-model, custom land/window assembly, mechanical tolerance, or final
manufacturing-export checks. No new order files are generated here.

## Supplementary simulation campaign (2026-11-14)

See [simulation commands](evidence/simulation-suite-20261114/COMMANDS.md) and the separate [manifest](evidence/simulation-suite-20261114/manifest.json). This campaign corrects the SI route extractor and USB edge measurement; prior tool hashes remain historical. The saved PCB and baseline are unchanged. RGB remains unqualified.
