#!/usr/bin/env python3
"""Plan moving via holes out of SMD pads (open via-in-pad wicks solder away from the joint).

usage: plan_via_out_of_pad.py BOARD.json OPS.json [--skip x:y,x:y]

For each via whose hole overlaps an SMD pad of its own net, a position is sought
0.35-0.9 mm outside every pad opening where the via passes the all-layer
clearance check.  The via moves there, every track end that sat on the old
position moves with it, and a short track on the pad's layer joins the pad to
the via.  KiCad DRC decides afterwards; rejected moves are listed with --skip.
"""
import json
import math
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from shapely.geometry import LineString, Point, Polygon  # noqa: E402

import local_router as LR  # noqa: E402

PAD_EDGE = 0.36          # via centre to the nearest pad opening: 0.25 mm via land radius + 0.11


def main():
    d = json.load(open(sys.argv[1]))
    skip = set()
    if "--skip" in sys.argv:
        skip = {tuple(round(float(v), 3) for v in s.split(":")) for s in sys.argv[sys.argv.index("--skip") + 1].split(",") if s}
    L = LR.Layout(d)
    smd = [(Polygon(p["poly"][0]), f["ref"], p["num"], p["net"], "F.Cu" if "F.Cu" in p["layers"] else "B.Cu", p)
           for f in d["fps"] for p in f["pads"] if p["drill"][0] == 0 and p["poly"] and any(l in ("F.Cu", "B.Cu") for l in p["layers"])]
    moves, vias_moved, stubs, report = [], [], [], []
    for v in d["vias"]:
        pt = Point(v["x"], v["y"])
        hit = [s for s in smd if abs(s[5]["x"] - v["x"]) < 4 and abs(s[5]["y"] - v["y"]) < 4 and s[0].distance(pt) < v["drill"] / 2]
        if not hit:
            continue
        key = (round(v["x"], 3), round(v["y"], 3))
        g, ref, num, net, layer, p = hit[0]
        if key in skip or net != v["net"]:
            report.append({"via": key, "pad": f"{ref}.{num}", "moved": False, "why": "skipped"})
            continue
        # take the old via out of the model
        for lay in LR.OUTER:
            L.cu[lay] = [c for c in L.cu[lay] if not (c[2] == "via" and c[3] is v)]
        L.via_holes = [h for h in L.via_holes if h.distance(pt) > 1e-6]
        L.inner = [(gg, nn) for gg, nn in L.inner if not (nn == v["net"] and gg.distance(pt) < 1e-6 and gg.area < 0.25)]
        near_pads = [s[0] for s in smd if abs(s[5]["x"] - v["x"]) < 3 and abs(s[5]["y"] - v["y"]) < 3]
        best = None
        for r in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.15, 1.3):
            for k in range(24):
                a = k * math.pi / 12
                x, y = round(v["x"] + r * math.cos(a), 4), round(v["y"] + r * math.sin(a), 4)
                q = Point(x, y)
                if any(s.distance(q) < PAD_EDGE for s in near_pads):
                    continue
                if not L.via_ok(x, y, v["net"], own_ref=ref):
                    continue
                stub = LineString([(v["x"], v["y"]), (x, y)]).buffer(0.125, 8)
                if any(c[1] != v["net"] and LR.R.near_box(c[0], x, y, 2.5) and c[0].distance(stub) < LR.CLEARANCE for c in L.cu[layer]):
                    continue
                if any(LR.R.near_box(h, x, y, 3.0) and h.distance(stub) < LR.HOLE_CLEARANCE for h in L.pad_holes):
                    continue
                best = (x, y)
                break
            if best:
                break
        if not best:
            L.add_via(v["x"], v["y"], v["net"])
            report.append({"via": key, "pad": f"{ref}.{num}", "moved": False, "why": "no free position"})
            continue
        L.add_via(best[0], best[1], v["net"])
        vias_moved.append({"net": v["net"], "from": [v["x"], v["y"]], "to": list(best)})
        for t in d["tracks"]:
            if t["net"] != v["net"]:
                continue
            for ex, ey in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
                if abs(ex - v["x"]) < 1e-4 and abs(ey - v["y"]) < 1e-4:
                    m = {"layer": t["layer"], "net": t["net"], "from": [ex, ey], "to": list(best)}
                    if m not in moves:
                        moves.append(m)
        st = {"x1": v["x"], "y1": v["y"], "x2": best[0], "y2": best[1], "w": 0.25, "layer": layer, "net": v["net"]}
        stubs.append(st)
        L.add_track(st)
        report.append({"via": key, "pad": f"{ref}.{num}", "moved": True, "to": list(best)})
    json.dump({"note": "Via holes moved out of SMD pads; each pad keeps a 0.25 mm track to its via.", "report": report,
               "ops": [{"op": "move_track_points", "moves": moves}, {"op": "move_vias", "moves": vias_moved}, {"op": "add_tracks", "tracks": stubs}]},
              open(sys.argv[2], "w"), indent=1)
    print(f"{len(report)} vias in pads: {sum(1 for r in report if r['moved'])} planned, {sum(1 for r in report if not r['moved'])} left")
    for r in report:
        if not r["moved"]:
            print("  left:", r["pad"], r["via"], r["why"])


if __name__ == "__main__":
    main()
