#!/usr/bin/env python3
"""Set component values consistently in the schematic sheets and on the board.

usage: set_component_values.py PCB_DIR CHANGES.json            (schematic sheets, plain Python)
       set_component_values.py --board BOARD.kicad_pcb CHANGES.json   (board, KiCad 9 pcbnew)

CHANGES.json maps reference -> {"from": old value, "to": new value}.  The old
value must match exactly, so a stale change list fails instead of guessing.
"""
import glob
import json
import re
import sys


def sheets(pcb_dir, changes):
    done = set()
    for path in sorted(glob.glob(f"{pcb_dir}/*.kicad_sch")):
        lines = open(path).read().split("\n")
        hit = False
        for i, line in enumerate(lines):
            m = re.search(r'\(property "Reference" "([^"]+)"', line)
            if not m or m.group(1) not in changes or not line.startswith("(symbol (lib_id"):
                continue
            ref = m.group(1)
            old = f'(property "Value" "{changes[ref]["from"]}"'
            if old not in line:
                raise SystemExit(f"{path}: {ref} value is not {changes[ref]['from']!r}")
            lines[i] = line.replace(old, f'(property "Value" "{changes[ref]["to"]}"', 1)
            done.add(ref)
            hit = True
        if hit:
            open(path, "w").write("\n".join(lines))
    missing = sorted(set(changes) - done)
    if missing:
        raise SystemExit(f"not found in any sheet: {missing}")
    print(f"schematic: {len(done)} values set")


def board(path, changes):
    import pcbnew
    b = pcbnew.LoadBoard(path)
    for ref, c in changes.items():
        fp = b.FindFootprintByReference(ref)
        if fp is None or fp.GetValue() != c["from"]:
            raise SystemExit(f"{ref}: board value is {fp.GetValue() if fp else None!r}, not {c['from']!r}")
        fp.SetValue(c["to"])
    pcbnew.SaveBoard(path, b)
    print(f"board: {len(changes)} values set")


if __name__ == "__main__":
    if sys.argv[1] == "--board":
        board(sys.argv[2], json.load(open(sys.argv[3])))
    else:
        sheets(sys.argv[1], json.load(open(sys.argv[2])))
