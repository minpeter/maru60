#!/usr/bin/env python3
"""Plan the track changes that bring copper to 0.2 mm from non-plated holes.

usage: .venv/bin/python pcb/tools/plan_npth_clearance.py BOARD.json OUT_OPS.json

BOARD.json is the geometry dump (dump_board_geometry.py).  JLCPCB asks for
0.2 mm between a non-plated hole and copper; the board rule is 0.15 mm.  For
every hole with a track closer than 0.2 mm, the chain of track segments that
passes the hole is cut where it enters the circle of radius

    R = hole radius + keep + track width / 2

and the piece inside is replaced by a polygon tangent to that circle, so the
track follows the hole at exactly the wanted distance.  The new copper is
checked against every other net on the layer and against every other
non-plated hole (it may not come closer to one than it already was).

  * When the neighbour in the way is another track, that track is moved round
    the same hole first, on a larger radius.
  * When a pad or via is in the way and the track is wider than 0.3 mm, the
    piece inside the circle is drawn narrower by the missing amount, on a
    radius that keeps its outer edge on the outer edge of the original track:
    no copper is added, the track loses up to 0.06 mm of width beside the hole.
  * A second pass uses the tightest numbers that still meet both rules
    (0.2008 mm to the hole, 0.1502 mm to other nets) for the tracks that run
    through the 0.50 mm gap between a switch pin hole and its socket pad.

The result is an operation list for apply_layout_ops.py.  Holes that cannot be
fixed are listed under "left" with the reason.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

GOAL = 0.2                                           # JLCPCB: NPTH to copper
PASSES = ((0.204, 0.1505, 0.1), (0.2008, 0.1502, 0.05))   # keep, other-net clearance, polygon step (rad)
KEY = 4                                              # decimals used to match track ends


class Blocked(Exception):
    pass


class World:
    def __init__(self, board):
        self.holes = [(f["ref"], p["x"], p["y"], p["drill"][0] / 2) for f in board["fps"] for p in f["pads"]
                      if p["attr"] == 3 and p["drill"][0] > 0 and abs(p["drill"][0] - p["drill"][1]) < 1e-6]
        self.hole_geoms = [Point(x, y).buffer(r, 64) for ref, x, y, r in self.holes]
        self.hole_tree = STRtree(self.hole_geoms)
        self.tracks = [dict(t, alive=True) for t in board["tracks"]]
        self.n0 = len(self.tracks)
        self.geoms = [self.geom(t) for t in self.tracks]
        self.by_layer = defaultdict(list)
        for i, t in enumerate(self.tracks):
            self.by_layer[t["layer"]].append(i)
        self.trees = {layer: STRtree([self.geoms[i] for i in idx]) for layer, idx in self.by_layer.items()}
        self.added = defaultdict(list)
        self.by_end = defaultdict(set)
        for i in range(self.n0):
            self.index(i, True)
        self.via_at = {(round(v["x"], KEY), round(v["y"], KEY)) for v in board["vias"]}
        self.pads = [(f["ref"], p["num"], p["net"], p["layers"], Polygon(p["poly"][0])) for f in board["fps"] for p in f["pads"] if p["poly"]]
        self.pad_tree = STRtree([p[4] for p in self.pads])
        self.fixed = defaultdict(list)                # layer -> [(geom, net, what)]: pads and vias
        for v in board["vias"]:
            for layer in ("F.Cu", "B.Cu", "In1.Cu", "In2.Cu"):
                self.fixed[layer].append((Point(v["x"], v["y"]).buffer(v["d"] / 2, 32), v["net"], "via"))
        for ref, num, net, layers, g in self.pads:
            for layer in layers:
                if layer.endswith(".Cu"):
                    self.fixed[layer].append((g, net, f"pad {ref}.{num}"))
        self.fixed_trees = {layer: STRtree([g for g, n, w in items]) for layer, items in self.fixed.items()}

    @staticmethod
    def geom(t):
        a, b = (t["x1"], t["y1"]), (t["x2"], t["y2"])
        return LineString([a, b]).buffer(t["w"] / 2, 32) if a != b else Point(a).buffer(t["w"] / 2, 32)

    def index(self, i, on):
        t = self.tracks[i]
        for k in ((t["layer"], round(t["x1"], KEY), round(t["y1"], KEY)), (t["layer"], round(t["x2"], KEY), round(t["y2"], KEY))):
            (self.by_end[k].add if on else self.by_end[k].discard)(i)

    def kill(self, i):
        self.tracks[i]["alive"] = False
        self.index(i, False)

    def revive(self, i):
        self.tracks[i]["alive"] = True
        self.index(i, True)

    def add(self, t):
        self.tracks.append(dict(t, alive=True))
        self.geoms.append(self.geom(t))
        i = len(self.tracks) - 1
        self.added[t["layer"]].append(i)
        self.index(i, True)
        return i

    def tracks_near(self, layer, g, dist):
        box = g.buffer(dist)
        for k in self.trees[layer].query(box):
            i = self.by_layer[layer][k]
            if self.tracks[i]["alive"]:
                yield i
        for i in self.added[layer]:
            if self.tracks[i]["alive"]:
                yield i

    def anchored(self, layer, x, y):
        if (round(x, KEY), round(y, KEY)) in self.via_at:
            return True
        pt = Point(x, y)
        return any(layer in self.pads[i][3] and self.pads[i][4].distance(pt) < 1e-3 for i in self.pad_tree.query(pt.buffer(0.01)))


def crossings(path, ring):
    hit = path.intersection(ring)
    parts = list(getattr(hit, "geoms", [hit]))
    out = []
    for p in parts:
        if p.is_empty:
            continue
        for c in (p.coords if p.geom_type != "Point" else [p.coords[0]]):
            out.append(path.project(Point(c)))
    return sorted(out)


def attempt(w: World, h, layer, net, keep, other, step, depth, frozen, journal):
    """Move the chain of `net` round hole h so its near edge is `keep` from the hole wall.  Returns a report."""
    ref, cx, cy, r = w.holes[h]
    hole = w.hole_geoms[h]
    cands = [(w.geoms[i].distance(hole), i) for i in w.tracks_near(layer, hole, keep + 0.01) if w.tracks[i]["net"] == net]
    cands = [(d, i) for d, i in cands if d < keep - 1e-4]
    if not cands:
        return None
    worst, start = min(cands)
    width = w.tracks[start]["w"]
    R = r + keep + width / 2
    chain = [start]
    pts = [(w.tracks[start]["x1"], w.tracks[start]["y1"]), (w.tracks[start]["x2"], w.tracks[start]["y2"])]
    for side in (0, 1):
        while True:
            end = pts[0] if side == 0 else pts[-1]
            if math.hypot(end[0] - cx, end[1] - cy) > R + 0.02:
                break
            others = [j for j in w.by_end[(layer, round(end[0], KEY), round(end[1], KEY))] if j not in chain and w.tracks[j]["net"] == net]
            if len(others) != 1 or w.anchored(layer, end[0], end[1]):
                raise Blocked("the track branches or ends on a pad or via inside the clearance circle")
            j = others[0]
            if abs(w.tracks[j]["w"] - width) > 1e-6:
                raise Blocked("the track changes width inside the clearance circle")
            a, b = (w.tracks[j]["x1"], w.tracks[j]["y1"]), (w.tracks[j]["x2"], w.tracks[j]["y2"])
            nxt = b if (round(a[0], KEY), round(a[1], KEY)) == (round(end[0], KEY), round(end[1], KEY)) else a
            if side == 0:
                chain.insert(0, j)
                pts.insert(0, nxt)
            else:
                chain.append(j)
                pts.append(nxt)
    path = LineString(pts)
    old_geoms = [w.geoms[j] for j in chain]
    old_hole = {i: min(g.distance(w.hole_geoms[i]) for g in old_geoms) for g0 in old_geoms for i in w.hole_tree.query(g0.buffer(GOAL))}

    def detour(wd):
        rin = r + keep + wd / 2
        so = crossings(path, Point(cx, cy).buffer(R, 256).exterior)
        si = crossings(path, Point(cx, cy).buffer(rin, 256).exterior)
        if len(so) < 2 or len(si) < 2:
            return None
        s1, s2, t1, t2 = so[0], so[-1], si[0], si[-1]
        e1, e2 = path.interpolate(t1), path.interpolate(t2)
        a1, a2 = math.atan2(e1.y - cy, e1.x - cx), math.atan2(e2.y - cy, e2.x - cx)
        da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi            # the short way round
        n = max(1, math.ceil(abs(da) / step))
        rv = rin / math.cos(abs(da) / n / 2)
        arc = [(e1.x, e1.y)] + [(cx + rv * math.cos(a1 + da * (k + 0.5) / n), cy + rv * math.sin(a1 + da * (k + 0.5) / n)) for k in range(n)] + [(e2.x, e2.y)]

        def piece(a, b):
            out = [tuple(path.interpolate(a).coords[0])]
            acc = 0.0
            for p, q in zip(pts, pts[1:]):
                acc += math.hypot(q[0] - p[0], q[1] - p[1])
                if a + 1e-9 < acc < b - 1e-9:
                    out.append(q)
            out.append(tuple(path.interpolate(b).coords[0]))
            return out

        pieces = [(piece(0, s1), width)]
        pieces += [(piece(s1, t1), wd), (arc, wd), (piece(t2, s2), wd)] if wd < width - 1e-9 else [(arc, wd)]
        pieces += [(piece(s2, path.length), width)]
        segs = []
        for points, pw in pieces:
            pr = [(round(x, 4), round(y, 4)) for x, y in points]
            # the chain's own ends keep their exact coordinates
            for a, b in zip(pr, pr[1:]):
                if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-4:
                    segs.append({"x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1], "w": pw, "layer": layer, "net": net})
        segs[0]["x1"], segs[0]["y1"] = pts[0]
        segs[-1]["x2"], segs[-1]["y2"] = pts[-1]
        return segs

    reasons = []
    variants = [width] + ([round(width - (keep - worst) - 0.006, 4)] if width >= 0.3 and depth == 0 else [])
    for wd in variants:
        segs = detour(wd)
        if segs is None:
            reasons.append("no clean crossing of the clearance circle")
            continue
        geoms = [World.geom(s) for s in segs]
        near = min(g.distance(hole) for g in geoms)
        hard, soft = [], set()
        if near < min(keep, GOAL + 0.0005) - 1e-4:
            hard.append(f"only {round(near, 4)} mm from the hole")
        for g in geoms:
            for k in w.fixed_trees[layer].query(g.buffer(other)):
                og, onet, what = w.fixed[layer][k]
                if onet != net and g.distance(og) < other:
                    hard.append(f"{what} ({onet}) at {round(g.distance(og), 4)} mm")
            for i in w.hole_tree.query(g.buffer(GOAL)):
                d = g.distance(w.hole_geoms[i])
                if i != h and d < GOAL - 1e-4 and d < old_hole.get(i, 9) - 1e-6:
                    hard.append(f"hole of {w.holes[i][0]} at {round(d, 4)} mm")
            for i in w.tracks_near(layer, g, other):
                t = w.tracks[i]
                if t["net"] != net and i not in chain and g.distance(w.geoms[i]) < other:
                    (hard.append(f"track {t['net']} at {round(g.distance(w.geoms[i]), 4)} mm") if t["net"] in frozen or depth >= 2 else soft.add(t["net"]))
        if hard:
            reasons.append("; ".join(sorted(set(hard))[:3]))
            continue
        mark = len(journal)
        for j in chain:
            w.kill(j)
        new = [w.add(s) for s in segs]
        journal.append((chain, new))
        report = {"hole_of": ref, "hole": [round(cx, 4), round(cy, 4)], "layer": layer, "net": net, "was_mm": round(worst, 4), "now_mm": round(near, 4),
                  "track_width": width, "width_beside_hole": wd, "removed": len(chain), "added": len(segs), "pushed": []}
        try:
            for other_net in sorted(soft):
                sub = attempt(w, h, layer, other_net, keep + wd + other + 0.003, other, step, depth + 1, frozen | {net}, journal)
                if sub is None:
                    raise Blocked(f"track {other_net} is in the way and is not near the hole")
                report["pushed"].append(sub)
            # the neighbours have moved: the new copper must now be clear of every other track
            for i in new:
                for k in w.tracks_near(layer, w.geoms[i], other):
                    t = w.tracks[k]
                    if t["net"] != net and w.geoms[i].distance(w.geoms[k]) < other:
                        raise Blocked(f"track {t['net']} still at {round(w.geoms[i].distance(w.geoms[k]), 4)} mm")
            return report
        except Blocked as e:
            while len(journal) > mark:
                killed, added = journal.pop()
                for i in added:
                    w.kill(i)
                for i in killed:
                    w.revive(i)
            reasons.append(str(e))
    raise Blocked(" | ".join(reasons))


def violations(w: World, keep=GOAL):
    out = defaultdict(list)
    for h, hole in enumerate(w.hole_geoms):
        ref, cx, cy, r = w.holes[h]
        for layer in w.by_layer:
            for i in w.tracks_near(layer, hole, keep):
                d = w.geoms[i].distance(hole)
                if d < keep - 1e-4:
                    out[(h, layer, w.tracks[i]["net"])].append(d)
    return out


def main():
    board = json.loads(Path(sys.argv[1]).read_text())
    w = World(board)
    before = violations(w)
    done, why = [], {}
    for keep, other, step in PASSES:
        tries = defaultdict(int)
        while True:
            todo = [(k, ds) for k, ds in sorted(violations(w).items(), key=lambda kv: min(kv[1])) if tries[k] < 4 and k not in why]
            if not todo:
                break
            for (h, layer, net), ds in todo:           # a net can pass the same hole more than once: repeat until it is clear
                tries[(h, layer, net)] += 1
                try:
                    rep = attempt(w, h, layer, net, keep, other, step, 0, frozenset(), [])
                    if rep:
                        rep["other_net_clearance"] = other
                        done.append(rep)
                except Blocked as e:
                    why[(h, layer, net)] = str(e)
        if (keep, other, step) != PASSES[-1]:
            why.clear()
    after = violations(w)
    left = [{"hole_of": w.holes[h][0], "hole": [round(w.holes[h][1], 4), round(w.holes[h][2], 4)], "layer": layer, "net": net, "mm": round(min(ds), 4),
             "why": why.get((h, layer, net), "")} for (h, layer, net), ds in sorted(after.items(), key=lambda kv: min(kv[1]))]
    remove = [{k: t[k] for k in ("x1", "y1", "x2", "y2", "layer", "net")} for t in w.tracks[:w.n0] if not t["alive"]]
    add = [{k: t[k] for k in ("x1", "y1", "x2", "y2", "w", "layer", "net")} for t in w.tracks[w.n0:] if t["alive"]]
    ops = {"ops": [{"op": "remove_tracks", "tracks": remove}, {"op": "add_tracks", "tracks": add}],
           "holes_with_a_track_under_0p2_before": len(before), "fixed": done, "left": left}
    Path(sys.argv[2]).write_text(json.dumps(ops, indent=1) + "\n")
    print(json.dumps({"before": len(before), "fixed": len(done), "left": len(left), "removed": len(remove), "added": len(add)}))
    for d in done:
        print("  fixed", {k: v for k, v in d.items() if k != "pushed"}, "pushed:", [(p["net"], p["now_mm"]) for p in d["pushed"]])
    for d in left:
        print("  LEFT ", d)


if __name__ == "__main__":
    main()
