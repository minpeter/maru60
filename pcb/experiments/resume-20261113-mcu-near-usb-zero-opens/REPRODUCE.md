# Revalidate the delivered candidate

Run from repository root with the project Python environment, the pinned
KiCad 9.0.2 wrapper and `maru60-ngspice:bookworm` image. The SI dependencies and
image build command are in [the tools README](../../tools/signal_integrity/README.md).
Gerber readback additionally needs `gerbonara` (the existing
`build/gerber-venv/bin/python` environment contains it).

Use a fresh native-output directory. These checks do not promote a baseline
or resolve physical-fit gates.

```sh
candidate=pcb/experiments/resume-20261113-mcu-near-usb-zero-opens
work=build/mcu-zero-recheck
mkdir -p "$work"
tools/run_kicad9.sh python3 tools/check_pcb_native.py --checkpoint "$candidate" --expected-opens 0 --expected-warnings 0 --output "$work/native" --material
tools/run_kicad9.sh python3 pcb/tools/dump_board_geometry.py "$candidate/pcb/maru60.kicad_pcb" "$work/geometry.json"
.venv/bin/python pcb/tools/run_dfm_jlcpcb_drc.py "$candidate/pcb" "$candidate/qa/jlcpcb.kicad_dru" "$work/dfm.json"
.venv/bin/python pcb/tools/check_dfm_jlcpcb.py "$work/geometry.json" "$work/dfm-geometry.json"
.venv/bin/python pcb/tools/check_backspace_fit.py "$candidate/pcb/maru60.kicad_pcb" "$work/backspace-fit.json"
.venv/bin/python "$candidate/qa/check_moved_fit.py" "$candidate/pcb/maru60.kicad_pcb" "$work/geometry.json" "$work/mechanical"
.venv/bin/python pcb/tools/analyze_pdn.py "$work/geometry.json" "$work/pdn"
```

Expected native values: 0 opens / warnings / other errors / ERC / parity;
81 CAD files unchanged by cold refill. Material connectivity is checked by
inspecting `pad_partitions_by_net`: every net has one pad partition. Individual
guard failures remain recorded and are not a strict-promotion pass.

The mechanical wrapper extends the original 19-part list with 31 moved
bottom-side parts, using the documented conservative height assumptions.
The expected raw result is `ATTENTION` because its PCB-mount 7U probe is
inapplicable to the selected plate-mount hardware; preserve that result.

```sh
.venv/bin/python pcb/tools/signal_integrity/run_candidate.py "$work/geometry.json" "$candidate/pcb/maru60.kicad_pcb" "$work/si" extract_geometry
export MARU60_SI_WORKERS=4
for step in sim_usb sim_xtal sim_matrix check_misc sim_led; do
  .venv/bin/python pcb/tools/signal_integrity/run_candidate.py "$work/geometry.json" "$candidate/pcb/maru60.kicad_pcb" "$work/si" "$step" || break
done
.venv/bin/python pcb/tools/signal_integrity/check_backspace_leds.py "$work/geometry.json" "$candidate/pcb/maru60.kicad_pcb" "$work/backspace-led/results.json" --lines "$work/si/out/lines.json"
```

Compare the resulting JSON with the archived reports and their model limits;
a zero process exit alone does not mean all scenarios passed. The LED report
also contains intentional resistor-removal counterfactuals. The numerical
failure archive documents a former roundoff-length LC section; the corrected
model treats lengths ≤1e-9 mm as a junction, 1000× below KiCad's 1 nm grid.
No automatic solver retry or relaxed electrical limit is used.

To regenerate the package, fit placements using **this candidate's `parts.json`**:
the root package's rules incorrectly auto-populate the alternative Backspace LEDs.

```sh
.venv/bin/python pcb/tools/fit_jlcpcb_placement.py "$work/geometry.json" "$candidate/order/parts.json" "$candidate/order/jlcpcb-placement.json"
.venv/bin/python pcb/tools/export_order_package.py --checkpoint "$candidate" --out "$candidate/order" --parts "$candidate/order/parts.json"
build/gerber-venv/bin/python pcb/tools/verify_gerbers.py "$work/geometry.json" "$candidate/order/gerbers" "$work/gerber-readback.json"
```

Expect 336 CPL rows, 55 LCSC part numbers, 136 top / 200 bottom placements,
and no SW14, SW15, LED14 or LED15 in automated BOM/CPL. Export regenerates
timestamps and package hashes; update the manifest only after reviewing fresh
results. The preserved firmware is reused after MCU pin equality and explicit contraction of only R192/R193; the raw netlists differ by those two series nets and R115 value.

```sh
.venv/bin/python -m unittest tests.test_signal_geometry tests.test_spice_runner tests.test_pdn_network tests.test_mcu_candidate
git diff --check
```

The archived electrical runs used the board before the final R193 reference-text
move. `qa/geometry-equivalence.json` proves the exact text-only edit and identical
geometry; native, DFM and Gerber checks were rerun on final CAD. A fresh run above
will name the final CAD hash directly. Archived LED measurements also include
completed-waveform reuse only when electrical deck content, solver settings and
requested vectors are identical; `qa/signal-integrity/waveform-reuse.json` records
each case. The ordinary reproduction commands above run ngspice afresh.
