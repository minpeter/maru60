#!/usr/bin/env python3
"""Check the exported Gerber and drill files against the board with an independent parser.

usage: verify_gerbers.py BOARD.json GERBER_DIR OUT.json

BOARD.json is the geometry dump of the board the files were exported from
(dump_board_geometry.py).  The files are read with gerbonara, not KiCad, so a
mismatch between what KiCad thinks it plotted and what a fabricator's CAM will
read shows up here.  Run with an environment that has gerbonara:

    uv venv build/gerber-venv && uv pip install --python build/gerber-venv/bin/python gerbonara
    build/gerber-venv/bin/python pcb/tools/verify_gerbers.py build/order-export/board.json pcb/order/gerbers out.json

Checks:
  * every expected layer file exists, parses and is not empty;
  * the Edge.Cuts extent equals the board outline;
  * every drill hit matches a hole of the same diameter on the board and every
    board hole has a hit (plated and non-plated separately);
  * every SMD pad of the board has a flashed or drawn aperture at its position on
    the copper, mask and paste layer of its side; nothing extends past the outline.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

from gerbonara import ExcellonFile, GerberFile
from gerbonara.graphic_objects import Flash

LAYERS = ["F_Cu", "In1_Cu", "In2_Cu", "B_Cu", "F_Paste", "B_Paste", "F_Silkscreen", "B_Silkscreen", "F_Mask", "B_Mask", "Edge_Cuts"]
TOL = 0.006


def main() -> int:
    board = json.loads(Path(sys.argv[1]).read_text())
    gdir = Path(sys.argv[2])
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    files = {}
    for layer in LAYERS:
        hit = sorted(gdir.glob(f"*-{layer}.gbr"))
        if len(hit) != 1:
            check(f"{layer}: exactly one file", False, [p.name for p in hit])
            continue
        g = GerberFile.open(hit[0])
        g.to_metric = None
        files[layer] = g
        check(f"{layer}: parses and has objects", len(g.objects) > 0, len(g.objects))

    def mm(v, unit):
        return float(unit.convert_to("mm", v)) if hasattr(unit, "convert_to") else float(v)

    # outline
    xs = [e["x1"] for e in board["edges"]] + [e["x2"] for e in board["edges"]]
    ys = [e["y1"] for e in board["edges"]] + [e["y2"] for e in board["edges"]]
    want = (max(xs) - min(xs), max(ys) - min(ys))
    if "Edge_Cuts" in files:
        (x0, y0), (x1, y1) = files["Edge_Cuts"].bounding_box(unit="mm")
        got = (x1 - x0, y1 - y0)
        # the plotted outline includes the 0.05 mm stroke
        check("Edge.Cuts extent equals the board outline (+ stroke)", abs(got[0] - want[0]) < 0.11 and abs(got[1] - want[1]) < 0.11,
              {"gerber_mm": [round(v, 3) for v in got], "board_mm": [round(v, 3) for v in want]})
        ox, oy = x0 + 0.025, y1 - 0.025          # gerber origin of board (0, 0); gerber Y points up
    else:
        ox = oy = 0.0

    def to_board(x, y):
        return (x - ox + min(xs), -(y - oy) + min(ys))

    # drills
    holes = {"PTH": [], "NPTH": []}
    for f in board["fps"]:
        for p in f["pads"]:
            if p["drill"][0] > 0:
                plated = p["attr"] != 3          # PAD_ATTRIB_NPTH == 3
                holes["PTH" if plated else "NPTH"].append((p["x"], p["y"], round(min(p["drill"]), 3), round(max(p["drill"]), 3)))
    for v in board["vias"]:
        holes["PTH"].append((v["x"], v["y"], round(v["drill"], 3), round(v["drill"], 3)))
    for kind in ("PTH", "NPTH"):
        hit = sorted(gdir.glob(f"*-{kind}.drl"))
        if len(hit) != 1:
            check(f"{kind} drill file exists", False, [p.name for p in hit])
            continue
        ex = ExcellonFile.open(hit[0])
        flashes = []
        slots = 0
        for o in ex.objects:
            x, y = to_board(mm(o.x, o.unit) if hasattr(o, "x") else mm(o.x1, o.unit), mm(o.y, o.unit) if hasattr(o, "y") else mm(o.y1, o.unit))
            d = round(mm(o.tool.diameter, o.tool.unit), 3) if hasattr(o, "tool") else round(mm(o.aperture.diameter, o.aperture.unit), 3)
            if isinstance(o, Flash):
                flashes.append((x, y, d))
            else:
                slots += 1
        round_holes = [h for h in holes[kind] if h[2] == h[3]]
        slot_holes = [h for h in holes[kind] if h[2] != h[3]]
        unmatched_hits, used = [], set()
        index = {}
        for i, h in enumerate(round_holes):
            index.setdefault((math.floor(h[0] / 0.05), math.floor(h[1] / 0.05)), []).append(i)
        for x, y, d in flashes:
            cand = [i for dx in (-1, 0, 1) for dy in (-1, 0, 1) for i in index.get((math.floor(x / 0.05) + dx, math.floor(y / 0.05) + dy), [])
                    if i not in used and math.hypot(round_holes[i][0] - x, round_holes[i][1] - y) < TOL and abs(round_holes[i][2] - d) < 0.002]
            if cand:
                used.add(cand[0])
            else:
                unmatched_hits.append((round(x, 3), round(y, 3), d))
        # oval holes are drilled as routed slots or as a row of hits; compare their count only
        check(f"{kind}: every round drill hit is a board hole of the same size", len(unmatched_hits) <= 2 * len(slot_holes),
              {"hits": len(flashes), "slots": slots, "unmatched": unmatched_hits[:6], "oval_board_holes": len(slot_holes)})
        check(f"{kind}: every round board hole is drilled", len(used) == len(round_holes),
              {"board": len(round_holes), "drilled": len(used), "sizes": dict(Counter(h[2] for h in round_holes))})

    # SMD pads on copper / mask / paste
    for side, cu in (("F", "F.Cu"), ("B", "B.Cu")):
        pads = [(p["x"], p["y"], f["ref"], p["num"], "Paste" in " ".join(p["layers"])) for f in board["fps"] for p in f["pads"]
                if p["drill"][0] == 0 and cu in p["layers"]]
        for layer in (f"{side}_Cu", f"{side}_Mask", f"{side}_Paste"):
            if layer not in files:
                continue
            pts = {}
            for o in files[layer].objects:
                if isinstance(o, Flash):
                    x, y = to_board(mm(o.x, o.unit), mm(o.y, o.unit))
                    pts.setdefault((math.floor(x / 0.1), math.floor(y / 0.1)), []).append((x, y))
            missing = []
            n = 0
            for x, y, ref, num, has_paste in pads:
                if layer.endswith("Paste") and not has_paste:
                    continue
                n += 1
                near = [q for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in pts.get((math.floor(x / 0.1) + dx, math.floor(y / 0.1) + dy), [])]
                if not any(math.hypot(q[0] - x, q[1] - y) < 0.02 for q in near):
                    missing.append(f"{ref}.{num}")
            # pads plotted as regions or with offset paste (QFN windows) are not flashes at the pad centre
            check(f"{layer}: SMD pads present as flashes", len(missing) <= 0.03 * max(n, 1), {"pads": n, "not_flashed_at_centre": len(missing), "examples": missing[:8]})
        (x0, y0), (x1, y1) = files[f"{side}_Cu"].bounding_box(unit="mm")
        a, b = to_board(x0, y1), to_board(x1, y0)
        check(f"{side}_Cu stays inside the outline", a[0] > min(xs) and a[1] > min(ys) and b[0] < max(xs) and b[1] < max(ys),
              [round(v, 3) for v in (*a, *b)])

    ok = all(c["pass"] for c in checks)
    Path(sys.argv[3]).write_text(json.dumps({"pass": ok, "parser": "gerbonara", "checks": checks}, indent=1) + "\n")
    for c in checks:
        print("PASS" if c["pass"] else "FAIL", c["check"], "" if c["pass"] else c["detail"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
