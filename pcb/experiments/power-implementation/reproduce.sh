#!/usr/bin/env bash
set -euo pipefail
D=$(cd -- "$(dirname -- "$0")" && pwd)
export XDG_CONFIG_HOME=/tmp/maru-implementation-kicad/config
export XDG_CACHE_HOME=/tmp/maru-implementation-kicad/cache
export XDG_DATA_HOME=/tmp/maru-implementation-kicad/data
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME"
python "$D/create_native.py"
/usr/bin/python3 "$D/create_placement.py"
kicad-cli sch export netlist --format kicadxml -o "$D/native-max38902a/v6-protection.xml" "$D/native-max38902a/v6-protection.kicad_sch"
kicad-cli sch erc --format json --severity-all --exit-code-violations -o "$D/native-max38902a/erc.json" "$D/native-max38902a/v6-protection.kicad_sch"
kicad-cli sch export pdf -o "$D/native-max38902a/v6-protection.pdf" "$D/native-max38902a/v6-protection.kicad_sch"
kicad-cli pcb export svg --layers F.Cu,F.Fab,F.SilkS,Edge.Cuts --mode-single --fit-page-to-board --exclude-drawing-sheet --sketch-pads-on-fab-layers -o "$D/qa/placement.svg" "$D/native-max38902a/ldo-placement-only.kicad_pcb"
kicad-cli pcb drc --format json --severity-all -o "$D/native-max38902a/placement-drc.json" "$D/native-max38902a/ldo-placement-only.kicad_pcb"
python "$D/verify.py"
