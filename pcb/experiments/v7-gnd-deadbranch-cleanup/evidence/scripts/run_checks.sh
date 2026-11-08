#!/bin/bash
set -euo pipefail
R=/tmp/v7-gnd-tail-cleanup-aead
P="$R/filled/pcb"
"$R/scripts/native_run.sh" kicad-cli pcb drc --format json --schematic-parity --output "$R/qa/drc.json" "$P/maru60.kicad_pcb" > "$R/qa/drc.log" 2>&1
"$R/scripts/native_run.sh" kicad-cli sch erc --format json --output "$R/qa/erc.json" "$P/maru60.kicad_sch" > "$R/qa/erc.log" 2>&1
"$R/scripts/native_run.sh" /usr/bin/python3 "$R/scripts/export_material_graph.py" "$P/maru60.kicad_pcb" "$R/qa/material-graph.json" > "$R/qa/material-graph.log" 2>&1
printf 'ALL_CHECKS_EXIT_ZERO\n'
