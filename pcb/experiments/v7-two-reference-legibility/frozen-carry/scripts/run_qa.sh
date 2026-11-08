#!/bin/bash
set -euo pipefail
R=/tmp/v7-serial-legs-plus-two-labels
N="$R/scripts/native_run.sh"
"$N" /usr/bin/python3 "$R/scripts/fill_serial_trial.py" > "$R/qa/native-fill.log" 2>&1
"$N" kicad-cli pcb drc --schematic-parity --format json --output "$R/qa/drc.json" "$R/filled/pcb/maru60.kicad_pcb" > "$R/qa/drc.log" 2>&1
"$N" /usr/bin/python3 "$R/scripts/three_boundaries.py" > "$R/qa/three-boundaries.log" 2>&1
python "$R/scripts/render_trial.py" > "$R/qa/render.log" 2>&1
