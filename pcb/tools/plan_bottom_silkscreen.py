#!/usr/bin/env python3
"""Relocate obstructed reference text and the logo without hiding them."""
import argparse
import json
import math
import re
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("geometry", type=Path)
ap.add_argument("silkscreen", type=Path)
ap.add_argument("drc", type=Path)
ap.add_argument("output", type=Path)
a = ap.parse_args()
g, silk, drc = (json.loads(p.read_text()) for p in (a.geometry, a.silkscreen, a.drc))
poly = lambda rings: unary_union([Polygon(r) for r in rings if len(r) >= 3])
refs = {m[1] for v in drc["violations"] if v["type"].startswith("silk") for i in v["items"]
        if (m := re.search(r'Reference field of (\w+)', i["description"]))}
logo = any("LOGO1" in i["description"] for v in drc["violations"] if v["type"].startswith("silk") for i in v["items"])
targets = [item for item in silk if item["ref"] in refs and item["kind"] == "reference"]
fixed = {"F.Silkscreen": [], "B.Silkscreen": []}
def key(layer):
    return "B.Silkscreen" if layer.startswith("B.") else "F.Silkscreen"
for item in silk:
    if item in targets or (logo and item["ref"] == "LOGO1"):
        continue
    fixed[key(item["layer"])].append(poly(item["poly"]))
for f in g["fps"]:
    for p in f["pads"]:
        shape = poly(p["poly"])
        for side in ("F", "B"):
            if side+".Cu" in p["layers"] or p["drill"][0]:
                fixed[side+".Silkscreen"].append(shape)
material = unary_union([Polygon(o[0], o[1:]) for o in g["board_material"]]).buffer(-.20)
trees = {side: STRtree(shapes) for side, shapes in fixed.items()}
placed = {side: [] for side in fixed}
ops, report = [], []
if logo:
    f = next(f for f in g["fps"] if f["ref"] == "LOGO1")
    shape = unary_union([poly(item["poly"]) for item in silk if item["ref"] == "LOGO1"])
    targets.insert(0, dict(ref="LOGO1", kind="logo", layer="B.Silkscreen", x=f["x"], y=f["y"], geometry=shape))
for item in targets:
    side = key(item["layer"])
    shape = item.get("geometry") if "geometry" in item else poly(item["poly"])
    maximum, step = (65, .5) if item["kind"] == "logo" else (9, .25)
    limit = round(maximum/step)
    offsets = sorted((math.hypot(i*step, j*step), i*step, j*step)
                     for i in range(-limit, limit+1) for j in range(-limit, limit+1)
                     if math.hypot(i*step, j*step) <= maximum)
    found = None
    # Conservative bounding boxes keep labels readily legible, rather than
    # threading pad copper through gaps between strokes of printed letters.
    bb = box(*shape.bounds)
    for dist, dx, dy in offsets:
        probe = translate(bb, dx, dy)
        if not material.contains(probe):
            continue
        probe = probe.buffer(.20)
        if any(probe.intersects(fixed[side][i]) for i in trees[side].query(probe)):
            continue
        if any(probe.intersects(q) for q in placed[side]):
            continue
        found = dx, dy
        break
    if found is None:
        raise RuntimeError("No legible silkscreen site for "+item["ref"])
    dx, dy = found
    placed[side].append(translate(bb, dx, dy))
    x, y = item["x"]+dx, item["y"]+dy
    ops.append(dict(op="move_footprint" if item["kind"] == "logo" else "move_ref_text", ref=item["ref"], x=x, y=y))
    report.append(dict(ref=item["ref"], from_xy=[item["x"], item["y"]], to_xy=[x, y], side=side))
    print(item["ref"], round(x, 3), round(y, 3), flush=True)
a.output.write_text(json.dumps(dict(ops=ops, report=report), indent=2)+"\n")
