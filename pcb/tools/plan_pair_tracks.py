#!/usr/bin/env python3
"""Turn a pair centre line into two tracks and their vias, and check them against the board.

usage: plan_pair_tracks.py BOARD.json SPEC.json OPS.json

SPEC.json:
  {"nets": {"left": "USB_DP_CONN", "right": "USB_DM_CONN"},   left of the direction of travel, seen from the top
   "keep":  [[x0, y0, x1, y1], ...],     existing copper of the two nets inside these boxes stays
   "drop":  [[x, y], ...],               ... except tracks with an end on, and vias at, these points
   "width": 0.25, "pitch": 0.45, "via_pitch": 0.68,
   "sections": [
     {"route": "file.json" | {"runs": [...]},      output of plan_pair_route.py
      "lead_in": [x, y], "lead_out": [x, y],       optional: a point put in front of / behind the route
      "start": {"left": [x, y], "right": [x, y]},  optional: join these points instead of the offset ends
      "end":   {"left": [x, y], "right": [x, y]}}, optional
     {"track": {"net", "layer", "w", "points": [[x, y], ...]}},   a single track
     {"via": {"net", "x", "y"}}
   ]}

Each run of a route is offset to both sides by pitch/2 with mitred corners.
Where the route changes layer, two vias are set side by side, via_pitch apart,
and the tracks spread to them over the last 0.6 mm.

All existing tracks and vias of the two nets outside the keep boxes are
removed.  Before the operation list is written, every new track and via is
checked on the exact geometry: distance to copper of other nets on its layer,
to drilled holes and to the board edge.  KiCad DRC decides afterwards.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shapely.geometry import LineString, Point  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

import local_router as LR  # noqa: E402

TAPER = 0.6


def unit(a, b):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def left_normal(u):
    return (u[1], -u[0])          # y points down on the board: east -> north


def offset(pts, d):
    """Mitred offset of a polyline to the left (d > 0) or right (d < 0)."""
    out = []
    for i, p in enumerate(pts):
        n1 = left_normal(unit(pts[i - 1], p)) if i > 0 else None
        n2 = left_normal(unit(p, pts[i + 1])) if i < len(pts) - 1 else None
        if n1 is None or n2 is None:
            n = n1 or n2
            out.append((p[0] + d * n[0], p[1] + d * n[1]))
            continue
        k = 1 + n1[0] * n2[0] + n1[1] * n2[1]
        if k < 0.3:
            raise SystemExit(f"corner too sharp for a mitre at {p}")
        out.append((p[0] + d * (n1[0] + n2[0]) / k, p[1] + d * (n1[1] + n2[1]) / k))
    for (a, b), (c, e) in zip(zip(pts, pts[1:]), zip(out, out[1:])):
        if (b[0] - a[0]) * (e[0] - c[0]) + (b[1] - a[1]) * (e[1] - c[1]) <= 0:
            raise SystemExit(f"offset segment folds back near {a}")
    return out


def clean(pts, tol=0.15):
    """Drop points closer than tol to the previous one (the search grid leaves a few)."""
    out = [pts[0]]
    for p in pts[1:-1]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= tol and math.hypot(p[0] - pts[-1][0], p[1] - pts[-1][1]) >= tol:
            out.append(p)
    out.append(pts[-1])
    return out


def main():
    d = json.load(open(sys.argv[1]))
    spec_path = Path(sys.argv[2])
    spec = json.load(open(spec_path))
    left, right = spec["nets"]["left"], spec["nets"]["right"]
    own = {left, right}
    w, half, vhalf = spec.get("width", 0.25), spec.get("pitch", 0.45) / 2, spec.get("via_pitch", 0.68) / 2
    inside = lambda x, y: any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in spec.get("keep", []))
    dropped = lambda x, y: any(math.hypot(x - q[0], y - q[1]) < 1e-3 for q in spec.get("drop", []))
    rm_t = [t for t in d["tracks"] if t["net"] in own and not (inside(t["x1"], t["y1"]) and inside(t["x2"], t["y2"])
                                                                and not dropped(t["x1"], t["y1"]) and not dropped(t["x2"], t["y2"]))]
    rm_v = [v for v in d["vias"] if v["net"] in own and not (inside(v["x"], v["y"]) and not dropped(v["x"], v["y"]))]
    new_t, new_v = [], []
    # points given with three decimals are snapped to the exact end of the copper that stays
    kept = [(t["net"], q) for t in d["tracks"] if t["net"] in own and t not in rm_t for q in ((t["x1"], t["y1"]), (t["x2"], t["y2"]))] \
        + [(v["net"], (v["x"], v["y"])) for v in d["vias"] if v["net"] in own and v not in rm_v] \
        + [(p["net"], (p["x"], p["y"])) for f in d["fps"] for p in f["pads"] if p["net"] in own]

    def snap(net, q):
        near = [k for n, k in kept if n == net and math.hypot(k[0] - q[0], k[1] - q[1]) < 0.005]
        return near[0] if near else q

    def add_line(net, layer, pts, width):
        pts = [snap(net, pts[0])] + list(pts[1:-1]) + [snap(net, pts[-1])]
        for a, b in zip(pts, pts[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-4:
                new_t.append({"x1": round(a[0], 6), "y1": round(a[1], 6), "x2": round(b[0], 6), "y2": round(b[1], 6), "w": width, "layer": layer, "net": net})

    for sec in spec["sections"]:
        if "track" in sec:
            t = sec["track"]
            add_line(t["net"], t["layer"], t["points"], t["w"])
            continue
        if "via" in sec:
            new_v.append({"x": sec["via"]["x"], "y": sec["via"]["y"], "net": sec["via"]["net"]})
            continue
        route = sec["route"]
        if isinstance(route, str):
            route = json.load(open(spec_path.parent / route))
        runs = [(r["layer"], clean([tuple(p) for p in r["points"]])) for r in route["runs"] if len(r["points"]) >= 2]
        if "lead_in" in sec:                    # a fixed first point, so that the pair leaves in a given direction
            runs[0] = (runs[0][0], [tuple(sec["lead_in"])] + runs[0][1])
        if "lead_out" in sec:
            runs[-1] = (runs[-1][0], runs[-1][1] + [tuple(sec["lead_out"])])
        vias, vias_next = {}, {}
        for k, (layer, pts) in enumerate(runs):
            lines = {left: offset(pts, half), right: offset(pts, -half)}
            first, last = k == 0, k == len(runs) - 1
            for net, sign in ((left, 1), (right, -1)):
                line = lines[net]
                if not first:                       # leave the via pair of the layer change
                    u = unit(pts[0], pts[1])
                    if math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) <= TAPER + 0.1:
                        raise SystemExit(f"first segment after the layer change at {pts[0]} is shorter than the taper")
                    n = left_normal(u)
                    line = [vias[net], (pts[0][0] + u[0] * TAPER + sign * half * n[0], pts[0][1] + u[1] * TAPER + sign * half * n[1])] + line[1:]
                elif "start" in sec:
                    line = [tuple(sec["start"]["left" if net == left else "right"])] + line[1:]
                if not last:                        # arrive at the via pair
                    u = unit(pts[-2], pts[-1])
                    if math.hypot(pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]) <= TAPER + 0.1:
                        raise SystemExit(f"last segment before the layer change at {pts[-1]} is shorter than the taper")
                    n_in, n_out = left_normal(u), left_normal(unit(runs[k + 1][1][0], runs[k + 1][1][1]))
                    nv = (n_in[0] + n_out[0], n_in[1] + n_out[1])
                    L = math.hypot(*nv)
                    if L < 0.8:
                        raise SystemExit(f"the route turns back at the layer change at {pts[-1]}")
                    nv = (nv[0] / L, nv[1] / L)
                    via = (round(pts[-1][0] + sign * vhalf * nv[0], 4), round(pts[-1][1] + sign * vhalf * nv[1], 4))
                    line = line[:-1] + [(pts[-1][0] - u[0] * TAPER + sign * half * n_in[0], pts[-1][1] - u[1] * TAPER + sign * half * n_in[1]), via]
                    new_v.append({"x": via[0], "y": via[1], "net": net})
                    vias_next[net] = via
                elif "end" in sec:
                    line = line[:-1] + [tuple(sec["end"]["left" if net == left else "right"])]
                add_line(net, layer, line, w)
            vias, vias_next = vias_next, {}

    # --- exact check -------------------------------------------------------------
    for t in rm_t:
        d["tracks"].remove(t)
    for v in rm_v:
        d["vias"].remove(v)
    L = LR.Layout(d)
    xs = [e["x1"] for e in d["edges"]] + [e["x2"] for e in d["edges"]]
    ys = [e["y1"] for e in d["edges"]] + [e["y2"] for e in d["edges"]]
    trees = {lay: (STRtree([c[0] for c in L.cu[lay] if c[2] != "zone"]), [c for c in L.cu[lay] if c[2] != "zone"]) for lay in LR.OUTER}
    holes = [Point(p["x"], p["y"]).buffer(max(p["drill"]) / 2, 32) for f in d["fps"] for p in f["pads"] if p["drill"][0] > 0 and p["net"] not in own] \
        + [Point(v["x"], v["y"]).buffer(v["drill"] / 2, 32) for v in d["vias"] if v["net"] not in own]
    htree = STRtree(holes)
    worst = []

    def check(g, net, layers, what, hole_is_via=False):
        for lay in layers:
            tree, items = trees[lay]
            for i in tree.query(g.buffer(0.6)):
                c = items[i]
                if c[1] != net:
                    worst.append((round(c[0].distance(g), 4), what, lay, c[1], c[2]))
        for i in htree.query(g.buffer(0.8)):
            worst.append((round(holes[i].distance(g) - (0.05 if not hole_is_via else 0.0), 4), what, "hole", "", "hole"))

    geoms = []
    for t in new_t:
        g = LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 16)
        check(g, t["net"], [t["layer"]], f"track {t['net']} {t['layer']} ({t['x1']}, {t['y1']})-({t['x2']}, {t['y2']})")
        geoms.append((g, t["net"], t["layer"]))
        if min(t["x1"], t["x2"]) - t["w"] / 2 < min(xs) + 0.5 or max(t["y1"], t["y2"]) + t["w"] / 2 > max(ys) - 0.5 or min(t["y1"], t["y2"]) - t["w"] / 2 < min(ys) + 0.5:
            worst.append((0.0, "track near the board edge", t["layer"], "", "edge"))
    for v in new_v:
        g = Point(v["x"], v["y"]).buffer(0.25, 32)
        check(g, v["net"], LR.OUTER, f"via {v['net']} ({v['x']}, {v['y']})")
        for i in htree.query(g.buffer(1.0)):
            worst.append((round(holes[i].distance(Point(v["x"], v["y"]).buffer(0.125, 32)) - 0.25, 4), f"via hole {v['net']} ({v['x']}, {v['y']})", "hole", "", "hole to hole (0.45 wanted)"))
        geoms.append((g, v["net"], None))
    # the two new lines against each other
    for i, (g, net, lay) in enumerate(geoms):
        for h, net2, lay2 in geoms[i + 1:]:
            if net2 != net and (lay is None or lay2 is None or lay == lay2):
                dd = g.distance(h)
                if dd < 0.6:
                    worst.append((round(dd, 4), "the pair's own gap", lay or lay2, net2, "pair"))
    worst.sort()
    length = {n: round(sum(math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"]) for t in new_t if t["net"] == n), 2) for n in (left, right)}
    print(f"removed {len(rm_t)} tracks and {len(rm_v)} vias, added {len(new_t)} tracks and {len(new_v)} vias; new copper {length} mm")
    print("smallest distances (other copper: 0.15 needed; holes: 0.20 needed, shown minus 0.05; own gap):")
    for row in worst[:12]:
        print("  ", row)
    bad = [r for r in worst if r[0] < 0.1495]
    plain = lambda t: {k: t[k] for k in ("x1", "y1", "x2", "y2", "layer", "net")}
    json.dump({"note": spec.get("note", ""), "lengths_mm": length, "ops": [
        {"op": "remove_tracks", "tracks": [plain(t) for t in rm_t]},
        {"op": "remove_vias", "vias": [{"x": v["x"], "y": v["y"], "net": v["net"]} for v in rm_v]},
        {"op": "add_vias", "vias": new_v},
        {"op": "add_tracks", "tracks": new_t}]}, open(sys.argv[3], "w"), indent=1)
    if bad:
        print(f"{len(bad)} distances below 0.15 mm")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
