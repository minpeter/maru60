"""Run every signal-integrity step and merge the outputs into results.json.

    build/si/venv/bin/python pcb/tools/signal_integrity/run_all.py

Steps: extract_geometry -> sim_led -> sim_usb -> sim_xtal -> sim_matrix -> check_misc.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "build" / "si" / "out"
BOARD = ROOT / "pcb" / "experiments" / "resume-20261111-order-candidate" / "pcb" / "maru60.kicad_pcb"
STEPS = ["extract_geometry.py", "sim_led.py", "sim_usb.py", "sim_xtal.py", "sim_matrix.py", "check_misc.py"]


def main():
    only = sys.argv[1:]
    for step in STEPS:
        if only and step not in only:
            continue
        print("==", step, flush=True)
        subprocess.run([sys.executable, str(HERE / step)], check=True, stdout=subprocess.DEVNULL)
    g = json.loads((OUT / "geometry.json").read_text())
    led_rows = []
    for chain in ("key", "underglow"):
        for h in g["led"][chain]:
            led_rows.append({"chain": chain, "net": h["net"], "from": h["from"], "to": h["to"], "length_mm": h["length_mm"],
                             "by_layer_width": h["by_layer_width"], "vias": h["vias"], "stub_total_mm": h["stub_total_mm"],
                             "C_copper_pF": h["cap"]["C_copper_pF"], "delay_ps": h["delay_ps"],
                             "plane_openings_not_own_via_mm": h["plane_openings_not_own_via_mm"],
                             "neighbours": {k: [v["min_gap"], v["len_le_0p35"], v["len_le_0p6"]] for k, v in list(h["neighbours"].items())[:3]},
                             "near_buck": h["near_buck"]})
    res = {
        "board": str(BOARD.relative_to(ROOT)), "board_sha256": hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        "geometry_source": g["source"], "basis_note": "computed and simulated values only; no hardware exists and nothing was measured",
        "field_solve": json.loads((OUT / "lines.json").read_text()),
        "led_hop_table": led_rows, "led_caps_variants": {k: [{kk: vv for kk, vv in h.items() if kk in ("net", "length_mm", "by_layer_width", "vias", "stubs", "stub_total_mm")} for h in v]
                                                           for k, v in g["led"]["caps_variants"].items()},
        "led": json.loads((OUT / "led.json").read_text()),
        "usb_geometry": g["usb"], "usb": json.loads((OUT / "usb.json").read_text()),
        "crystal": json.loads((OUT / "xtal.json").read_text()),
        "matrix": json.loads((OUT / "matrix.json").read_text()),
        "misc": json.loads((OUT / "misc.json").read_text()),
        "buck_switch_node": g["buck_switch_node"],
    }
    (HERE / "results.json").write_text(json.dumps(res, indent=1) + "\n")
    print("wrote", HERE / "results.json")


if __name__ == "__main__":
    main()
