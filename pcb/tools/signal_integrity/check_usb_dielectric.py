"""Sweep assumed prepreg permittivity in the existing full-speed USB delay model.

This is sensitivity analysis, not a guaranteed laminate tolerance or hardware
qualification. Generate geometry with dump_board_geometry.py and lines.json
with fieldsolve.py (see README.md). No production simulation files are replaced.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import fieldsolve as fs
import sim_usb
import spice
from geom import Board


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("geometry", type=Path)
    ap.add_argument("lines", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--scratch", type=Path, default=Path("build/usb-dielectric"))
    args = ap.parse_args()
    board = Board(args.geometry)
    table = json.loads(args.lines.read_text())
    cases = []
    for er in (3.8, 4.1, 4.4, 4.7, 5.0):
        pair = fs.pair(.25, .20, er=er)
        corner_table = copy.deepcopy(table)
        for width in corner_table["single"]:
            corner_table["single"][width] = fs.single(float(width), er=er)
        case_dir = args.scratch.resolve() / str(er)
        spice.DECKS, spice.OUT = case_dir / "decks", case_dir / "out"
        spice.DECKS.mkdir(parents=True, exist_ok=True)
        row = sim_usb.sim_delay(board, corner_table, pair)
        row.update(assumed_er=er, Zdiff_ohm=round(pair["Z_diff"], 3))
        row["pass"] = row["J1_to_RP2350_pins_ns"] <= row["limit_ns"]
        cases.append(row)
        print(row, flush=True)
    result = {
        "scope": "Assumed dielectric sensitivity only; no measured or supplier-guaranteed corners",
        "inputs": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                   for p in (args.geometry, args.lines)],
        "held_constant": "Geometry, copper thickness, mask, plane spacing, via L/C, ESD and connector capacitance",
        "cases": cases,
        "pass": all(c["pass"] for c in cases),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
