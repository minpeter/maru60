#!/usr/bin/env python3
"""Plan removal of copper invalidated by new pads and actual routed apertures.

All four layers are checked. No removed conductor is considered reconnected.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("geometry", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--design", type=Path, required=True)
    args = ap.parse_args()
    g = json.loads(args.geometry.read_text())
    windows = unary_union([Polygon(h) for o in g["board_material"] for h in o[1:]])
    exclusion = windows.buffer(.52)
    # The validated baseline already passed its 0.15 mm copper rules. Only
    # changed pads invalidate that evidence; do not rip up unchanged MCU pin
    # escapes just because this planner's margin is more conservative.
    plan = json.loads((args.design/"bottom-assembly-plan.json").read_text())
    changed = set(plan["relocate_top"]+plan["relocate_bottom"]) | {s["ref"] for s in plan["sites"]}
    pad_shapes, pads, smd = [], [], []
    for f in g["fps"]:
        if f["ref"] not in changed:
            continue
        for p in f["pads"]:
            shape = unary_union([Polygon(o) for o in p["poly"] if len(o) >= 3])
            pad_shapes.append(shape)
            pads.append((p["net"], p["layers"], f["ref"]))
            if not p["drill"][0]:
                smd.append(shape)
    tree, smd_tree = STRtree(pad_shapes), STRtree(smd)
    tracks, vias, why = [], [], []
    for t in g["tracks"]:
        if "arc" in t:
            raise RuntimeError("Arc track requires native geometry; do not approximate by its chord")
        geom = LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"]/2, 24)
        reasons = []
        if geom.intersects(exclusion):
            reasons.append("new routed aperture / 0.52mm edge margin")
        for i in tree.query(geom.buffer(.16)):
            net, layers, ref = pads[i]
            if t["layer"] in layers and net != t["net"] and geom.distance(pad_shapes[i]) < .16:
                reasons.append("pad clearance "+ref)
        if reasons:
            tracks.append(t)
            why.append({"kind": "track", "net": t["net"], "layer": t["layer"], "reasons": sorted(set(reasons))})
    for v in g["vias"]:
        geom = Point(v["x"], v["y"]).buffer(v["d"]/2, 32)
        drill = Point(v["x"], v["y"]).buffer(v["drill"]/2, 32)
        reasons = []
        if geom.intersects(exclusion):
            reasons.append("new routed aperture / 0.52mm edge margin")
        for i in tree.query(geom.buffer(.16)):
            net, layers, ref = pads[i]
            if net != v["net"] and geom.distance(pad_shapes[i]) < .16:
                reasons.append("pad clearance "+ref)
        if any(drill.distance(smd[i]) < .10 for i in smd_tree.query(drill.buffer(.10))):
            reasons.append("drill in/near SMT land")
        if reasons:
            vias.append(v)
            why.append({"kind": "via", "net": v["net"], "reasons": sorted(set(reasons))})
    args.output.write_text(json.dumps({"status": "removal only; every new open requires rerouting and fresh validation",
                                       "ops": [{"op": "remove_tracks", "tracks": tracks}, {"op": "remove_vias", "vias": vias}],
                                       "removed_by_net": dict(Counter(w["net"] for w in why)), "reasons": why}, indent=2)+"\n")
    print("Removal plan:", len(tracks), "tracks,", len(vias), "vias;", len({w['net'] for w in why}), "nets")


if __name__ == "__main__":
    main()
