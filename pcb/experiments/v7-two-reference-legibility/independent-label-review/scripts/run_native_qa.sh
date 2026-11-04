#!/bin/bash
set -euo pipefail
R=/tmp/v7-two-label-corrected-independent-review
N="$R/scripts/native_run.sh"
"$N" /usr/bin/python3 "$R/scripts/three_boundaries.py" > "$R/qa/three-boundaries.log" 2>&1
"$N" /usr/bin/python3 "$R/scripts/cold_fill.py" > "$R/qa/cold-refill.log" 2>&1
"$N" kicad-cli pcb drc --schematic-parity --format json --output "$R/qa/drc.json" /tmp/v7-two-label-corrected-7882/candidate/pcb/maru60.kicad_pcb > "$R/qa/drc.log" 2>&1
python "$R/scripts/raw_compare.py" > "$R/qa/raw-warning-comparison.log" 2>&1
python "$R/scripts/render_trial.py" > "$R/qa/render.log" 2>&1
