"""Run every signal-integrity step and merge the outputs into results.json.

    build/si/venv/bin/python pcb/tools/signal_integrity/run_all.py             # everything
    build/si/venv/bin/python pcb/tools/signal_integrity/run_all.py sim_usb.py  # one step, same geometry
    build/si/venv/bin/python pcb/tools/signal_integrity/run_all.py --check     # is results.json for this board?

Steps: board dump (KiCad container) -> extract_geometry -> sim_led -> sim_usb -> sim_xtal
-> sim_matrix -> check_misc. The dump is stamped with the SHA-256 of the board file it
was made from, and results.json carries that hash, so a result can always be tied to
one board.
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
GEOMETRY = ROOT / "build" / "si" / "board.json"
STAMP = ROOT / "build" / "si" / "board.sha256"
STEPS = ["extract_geometry.py", "sim_led.py", "sim_usb.py", "sim_xtal.py", "sim_matrix.py", "check_misc.py"]


def board_sha():
    return hashlib.sha256(BOARD.read_bytes()).hexdigest()


def dump_board():
    """Geometry dump of the board, refused if the file changes while KiCad reads it."""
    before = board_sha()
    GEOMETRY.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(ROOT / "tools" / "run_kicad9.sh"), "python3", "pcb/tools/dump_board_geometry.py",
                    str(BOARD.relative_to(ROOT)), str(GEOMETRY.relative_to(ROOT))], check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
    if board_sha() != before:
        sys.exit("the board file changed while it was being dumped; run again")
    STAMP.write_text(before + "\n")


def main():
    if "--check" in sys.argv:
        have = json.loads((HERE / "results.json").read_text())["board_sha256"]
        now = board_sha()
        print("results.json:", have, "\nboard now   :", now, "\n" + ("match" if have == now else "STALE: rerun run_all.py"))
        sys.exit(0 if have == now else 1)
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not only or "extract_geometry.py" in only:
        print("== board dump", flush=True)
        dump_board()
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
            if "series_at_source" in h:   # R115: resistor between the previous DOUT and this hop
                ser = h["series_at_source"]
                led_rows[-1]["series_at_source"] = {"ref": ser["ref"], "ohm": ser["ohm"], "net": ser["source_side"]["net"],
                                                    "from": ser["source_side"]["from"], "length_mm": ser["source_side"]["length_mm"]}
    res = {
        "board": str(BOARD.relative_to(ROOT)), "board_sha256": STAMP.read_text().strip(),
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
    if board_sha() != res["board_sha256"]:
        print("WARNING: the board file changed during the run; results.json is for", res["board_sha256"])


if __name__ == "__main__":
    main()
