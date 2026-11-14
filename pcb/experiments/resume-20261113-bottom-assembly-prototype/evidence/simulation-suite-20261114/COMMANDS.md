# Reproduction

Run from the repository root. The commands below name the accepted run directory; use a **new** `SIM` directory when repeating. The power wrapper and portable firmware checker require fresh output directories. No command below modifies the saved board. `source/` contains the final simulation tools; `source-at-power-run/` preserves the earlier wrapper with the inherited label error. Dependency versions and Docker image ID are in `manifest.json`.

```bash
CAND=pcb/experiments/resume-20261113-bottom-assembly-prototype
SIM=build/bottom-sim-20261114
mkdir -p "$SIM"
cp "$CAND/evidence/final-geometry.json" "$SIM/geometry.json"
tools/run_kicad9.sh kicad-cli sch export netlist --format kicadxml \
  --output "$SIM/netlist.xml" "$CAND/pcb/maru60.kicad_sch"

for STEP in extract_geometry sim_matrix check_misc sim_usb sim_xtal; do
  .venv/bin/python pcb/tools/signal_integrity/run_candidate.py \
    "$SIM/geometry.json" "$CAND/pcb/maru60.kicad_pcb" "$SIM/si-final" "$STEP" || exit 1
done
.venv/bin/python pcb/tools/signal_integrity/fieldsolve.py --selftest
.venv/bin/python pcb/tools/signal_integrity/check_usb_dielectric.py \
  "$SIM/geometry.json" "$SIM/si-final/out/lines.json" \
  "$SIM/usb-dielectric-final.json" --scratch "$SIM/dielectric-final"
.venv/bin/python pcb/tools/run_bottom_power_suite.py \
  "$SIM/geometry.json" "$SIM/netlist.xml" \
  "$CAND/evidence/pdn/primary/results.json" "$SIM/power2"
.venv/bin/python pcb/tools/signal_integrity/sim_mixed_led.py \
  "$SIM/geometry.json" "$SIM/si-final/out/lines.json" "$SIM/mixed-led" --workers 4
.venv/bin/python pcb/tools/signal_integrity/sim_bottom_supplement.py \
  "$SIM/geometry.json" "$SIM/si-final/out/geometry.json" \
  "$SIM/si-final/out/lines.json" "$SIM/mixed-led" "$SIM/supplement"
.venv/bin/python pcb/tools/simulate_bottom_pwm.py "$SIM/pwm"
.venv/bin/python pcb/tools/simulate_bottom_thermal.py "$SIM/geometry.json" "$SIM/thermal-final"
.venv/bin/python tools/check_pcb_portable.py --output "$SIM/firmware"
python3 pcb/experiments/led-startup-recovery/evidence/static-v7/check.py \
  --netlist "$SIM/netlist.xml" \
  --expected-sha256 3c7ef4f3d6651cfe8e5cbc5594be1d8c4a1d565d2c04ae9b03dbaa6e79154392 \
  --source pcb/firmware/qmk/keyboards/maru60/rp2350 \
  --matrix-script pcb/firmware/tests/matrix_simultaneous_model.py \
  --output "$SIM/current-firmware-netlist.json"
for TEST in test_signal_geometry test_spice_runner test_bottom_simulation test_reverse_led_analysis; do
  PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p "$TEST.py" || exit 1
done
```

KiCad netlist export includes a generation timestamp. A newly exported file can have a different byte hash even when connectivity is unchanged. Inspect a repeat export and use its actual hash for the static checker; the hash above pins the accepted run's exact file, archived as `inputs/netlist.xml`. Do not bypass the hash check without checking the input.

`source/refine_first_hop.py` replays the two flagged full first-hop decks at 0.025 ns with tighter tolerance. It binds the original `build/bottom-sim-20261114/` path; adjust that path explicitly for a fresh run. Its output is `first-refinement/results.json`.

The final power wrapper fixes presentation labels; its numerical models/stimuli match the accepted run. The accepted raw JSON retained the old `150mA` label even though `params.inc` has `iled=0.058`. `power/corrected-results.json` contains the same numbers with the proper `58mA_drive` keys. `source-at-power-run/run_bottom_power_suite.py` hashes to the executed wrapper recorded in `power/provenance.json`.

The report compiler `assemble_report.py` copies accepted outputs and hashes large raw artifacts. It binds the original workspace paths and is a packaging script, not another simulation. The HTML dashboard and report are derived from the compact result files. The manifest seals their final bytes separately.

Accepted results are only in `si-final`, `power2`, `mixed-led`, `supplement`, `first-refinement`, `pwm`, `thermal-final`, `dielectric-final`, and the stated firmware reports. The earlier `si`, `power`, `thermal`, `dielectric` directories are development/superseded runs and do not count toward this campaign. Within `si-final`, the unsuffixed `xtal_negative_resistance` deck/raw files predate the unique case filenames and are duplicates, not extra accepted cases. The final crystal results are `xtal_negative_resistance_pin2_c02` and `xtal_negative_resistance_pin4_c03` plus the three drive decks.

Large `.npz`/`.txt` waveforms remain under the local `build/` directory. `raw-artifacts.json` records their relative paths, sizes and SHA256 values; `spice-decks.zip` carries the input decks and model files. A clone of the committed source alone would not include those ignored build files. No commit was made here.
