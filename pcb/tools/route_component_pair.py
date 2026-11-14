#!/usr/bin/env python3
"""Configurable-layer multi-component route search for incremental PCB repair.

Derived from the project's component router. Native board-material apertures
and inner-layer via obstacles are included. New routes still require an exact
geometry screen and native KiCad DRC before acceptance.
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import Polygon
from shapely.ops import unary_union

G = 0.05                  # raster pitch of the clearance maps
STEP = 2                  # search pitch in raster cells (0.1 mm)
HALF = 0.35               # ribbon half width: 0.25 mm tracks, 0.20 mm gap
CLEAR = 0.18              # to other copper (board rule 0.15)
HOLE_EXTRA = 0.08         # holes are grown by this: 0.26 mm from the ribbon edge to a hole
VIA_ROOM = 0.78           # free radius on both layers at a layer change: two vias side by side, 0.68 mm apart
LAYERS = ("F.Cu", "B.Cu")


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


class Maps:
    def __init__(self, d, own, window, keep=(), avoid=(), protected=()):
        # Rasterize obstacles beyond the allowed search rectangle, so copper
        # just outside it still constrains the distance transform inside it.
        wx0, wy0, wx1, wy1 = window
        self.x0, self.y0, x1, y1 = wx0-1, wy0-1, wx1+1, wy1+1
        self.w, self.h = int(round((x1 - self.x0) / G)) + 1, int(round((y1 - self.y0) / G)) + 1
        hard = {L: Image.new("1", (self.w, self.h), 0) for L in LAYERS}
        soft = {L: Image.new("1", (self.w, self.h), 0) for L in LAYERS}
        smd = Image.new("1", (self.w, self.h), 0)
        holes = Image.new("1", (self.w, self.h), 0)
        self.soft_items = {L: [] for L in LAYERS}
        px = lambda x, y: ((x - self.x0) / G, (y - self.y0) / G)

        def disc(img, x, y, r):
            cx, cy = px(x, y)
            ImageDraw.Draw(img).ellipse([cx - r / G, cy - r / G, cx + r / G, cy + r / G], fill=1)

        def seg(img, t, extra=0.0):
            a, b = px(t["x1"], t["y1"]), px(t["x2"], t["y2"])
            wpx = (t["w"] + 2 * extra) / G
            dr = ImageDraw.Draw(img)
            dr.line([a, b], fill=1, width=max(1, int(round(wpx))))
            for q in (a, b):
                dr.ellipse([q[0] - wpx / 2, q[1] - wpx / 2, q[0] + wpx / 2, q[1] + wpx / 2], fill=1)

        for f in d["fps"]:
            for p in f["pads"]:
                if not p["drill"][0]:
                    for pl in p["poly"]:
                        if len(pl) >= 3:
                            ImageDraw.Draw(smd).polygon([px(*q) for q in pl], fill=1)
                if p["drill"][0] > 0:
                    disc(holes, p["x"], p["y"], max(p["drill"]) / 2)
                    # A same-net plated pad is a legitimate route terminal.
                    # Its annulus/barrel joins the copper around its drill;
                    # NPTH holes and every foreign-net drill remain obstacles.
                    if not (p.get("attr") == 0 and p["net"] in own):
                        for L in LAYERS:
                            disc(hard[L], p["x"], p["y"], max(p["drill"]) / 2 + HOLE_EXTRA)
                if p["net"] in own and not (f["ref"], p["num"]) in keep:
                    continue
                for L in LAYERS:
                    if L in p["layers"]:
                        for pl in p["poly"]:
                            if len(pl) >= 3:
                                ImageDraw.Draw(hard[L]).polygon([px(*q) for q in pl], fill=1)
        for v in d["vias"]:
            if v["net"] in own:
                # Avoid drilling a second via close to an existing own-net
                # barrel. Its exact grid location is enabled for reuse below.
                disc(holes, v["x"], v["y"], v["drill"] / 2)
                continue
            for L in LAYERS:
                disc(hard[L], v["x"], v["y"], v["d"] / 2)
        for x, y, r in avoid:
            for L in LAYERS:
                disc(hard[L], x, y, r)
        for z in d["zones"]:
            # small pours of a named net beside the MCU do not move; the two large refilled pours do
            for L, isls in z["fill"].items():
                if L not in LAYERS:
                    continue
                for isl in isls:
                    if isl and len(isl[0]) >= 3 and z["net"] not in own and z["net"] not in ("GND", "+3V3"):
                        ImageDraw.Draw(hard[L]).polygon([px(*q) for q in isl[0]], fill=1)
            if z.get("keepout"):
                for L in z["layers"]:
                    if L in LAYERS:
                        for o in z["outline"]:
                            ImageDraw.Draw(hard[L]).polygon([px(*q) for q in o], fill=1)
        for t in d["tracks"]:
            if t["net"] in own or t["layer"] not in LAYERS:
                continue
            seg(hard[t["layer"]] if t["net"] in protected else soft[t["layer"]], t)
            self.soft_items[t["layer"]].append(t)
        # Internal routed windows are physical absence of board on every layer.
        voids = Image.new("1", (self.w, self.h), 0)
        if d.get("board_material"):
            material = unary_union([Polygon(o[0], o[1:]) for o in d["board_material"]])
            for o in d["board_material"]:
                for h in o[1:]:
                    cut = Polygon(h).buffer(.32)
                    for L in LAYERS:
                        ImageDraw.Draw(hard[L]).polygon([px(*q) for q in cut.exterior.coords], fill=1)
        inner = Image.new("1", (self.w, self.h), 0)
        for t in d["tracks"]:
            if t["layer"] not in LAYERS and t["net"] not in own:
                seg(inner, t)
        for z in d["zones"]:
            if z.get("keepout"):
                for o in z["outline"]:
                    ImageDraw.Draw(inner).polygon([px(*q) for q in o], fill=1)
            else:
                for layer, islands in z["fill"].items():
                    if layer in LAYERS or z["net"] in own or z["net"] == "GND":
                        continue
                    for island in islands:
                        if island:
                            ImageDraw.Draw(inner).polygon([px(*q) for q in island[0]], fill=1)
        self.dist_inner = ndimage.distance_transform_edt(~np.array(inner, dtype=bool)) * G
        xs = [e["x1"] for e in d["edges"]] + [e["x2"] for e in d["edges"]]
        ys = [e["y1"] for e in d["edges"]] + [e["y2"] for e in d["edges"]]
        # Own-net copper is traversable by a track, but an ordinary drilled
        # via must not be placed in an SMD land. Reserve 0.10 mm of mask
        # beyond the 0.125 mm drill radius, including the route endpoints.
        self.dist_smd = ndimage.distance_transform_edt(~np.array(smd, dtype=bool)) * G
        self.dist_holes = ndimage.distance_transform_edt(~np.array(holes, dtype=bool)) * G
        self.reuse_vias = [(v["x"], v["y"]) for v in d["vias"] if v["net"] in own]
        self.dist_hard, self.dist_all = {}, {}
        for L in LAYERS:
            h = np.array(hard[L], dtype=bool)
            yy, xx = np.mgrid[0:self.h, 0:self.w]
            gx, gy = self.x0 + xx * G, self.y0 + yy * G
            h |= (gx < min(xs) + 0.32) | (gx > max(xs) - 0.32) | (gy < min(ys) + 0.32) | (gy > max(ys) - 0.32)   # 0.5 mm to the edge
            s = np.array(soft[L], dtype=bool)
            self.dist_hard[L] = ndimage.distance_transform_edt(~h) * G
            self.dist_all[L] = ndimage.distance_transform_edt(~(h | s)) * G
            outside = (gx < wx0) | (gx > wx1) | (gy < wy0) | (gy > wy1)
            self.dist_hard[L][outside] = 0
            self.dist_all[L][outside] = 0

    def cell(self, x, y):
        return int(round((y - self.y0) / G)), int(round((x - self.x0) / G))

    def los(self, dist, a, b, need):
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / (G / 2)))
        t = np.linspace(0, 1, n + 1)
        ix = np.round((a[0] + (b[0] - a[0]) * t - self.x0) / G).astype(int)
        iy = np.round((a[1] + (b[1] - a[1]) * t - self.y0) / G).astype(int)
        return bool((dist[iy, ix] >= need).all())


def search(m, start, goal, soft_cost, via_cost, need=HALF + CLEAR, via_room=VIA_ROOM):
    global LAST_DIAGNOSTIC
    H, W = (m.h + STEP - 1) // STEP, (m.w + STEP - 1) // STEP
    n = H * W
    free, pen = {}, {}
    for L in LAYERS:
        hard_ok = m.dist_hard[L][::STEP, ::STEP] >= need
        all_ok = m.dist_all[L][::STEP, ::STEP] >= need
        free[L] = all_ok if soft_cost is None else hard_ok
        pen[L] = np.where(all_ok, 0.0, 0.0 if soft_cost is None else soft_cost)
    idx = np.arange(n).reshape(H, W)
    rows, cols, costs = [], [], []
    moves = [(0, 1), (1, 0), (1, 1), (1, -1), (1, 2), (2, 1), (1, -2), (2, -1)]
    for li, L in enumerate(LAYERS):
        f, p = free[L], pen[L]
        for dy, dx in moves:
            ya, yb = slice(0, H - dy), slice(dy, H)
            xa, xb = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
            ok = f[ya, xa] & f[yb, xb]
            if abs(dy) + abs(dx) == 3:      # knight move: the two cells it passes between must be free too
                sy, sx = (1 if dy == 2 else 0), (int(math.copysign(1, dx)) if abs(dx) == 2 else 0)
                y1 = slice(sy, H - dy + sy)
                x1 = (slice(sx, W - dx + sx) if dx >= 0 else slice(-dx + sx, W + sx))
                ok &= f[y1, x1]
                y2 = slice(dy - sy, H - sy)
                x2 = (slice(dx - sx, W - sx) if dx >= 0 else slice(-sx, W + dx - sx))
                ok &= f[y2, x2]
            length = math.hypot(dy, dx) * STEP * G
            c = length * (1 + (p[ya, xa] + p[yb, xb]) / 2)
            rows.append(idx[ya, xa][ok] + li * n)
            cols.append(idx[yb, xb][ok] + li * n)
            costs.append(c[ok])
    room = np.minimum.reduce([m.dist_all[L][::STEP, ::STEP] for L in LAYERS]) >= via_room
    room &= m.dist_inner[::STEP, ::STEP] >= 0.46
    room &= m.dist_smd[::STEP, ::STEP] >= 0.25  # drill radius + mask web + half a raster cell
    room &= m.dist_holes[::STEP, ::STEP] >= 0.50  # 0.35 mm drill gap + 0.125 mm drill radius + raster margin
    # An existing own-net barrel is already a physical layer transition.
    # Its grid point may fall inside the conservative mask exclusion above.
    existing_room = np.zeros((H, W), dtype=bool)
    for x, y in (m.reuse_vias if via_room < 0.7 else []):
        cy, cx = m.cell(x, y)
        cy, cx = cy // STEP, cx // STEP
        if 0 <= cy < H and 0 <= cx < W:
            existing_room[cy, cx] = True
    # Exact-screen retries can reject a layer transition without making its
    # otherwise useful track corridor impassable.
    for x, y, radius in getattr(m, "blocked_vias", []):
        cy, cx = m.cell(x, y)
        cy, cx = cy // STEP, cx // STEP
        rr = int(math.ceil(radius / (STEP * G)))
        room[max(0, cy-rr):min(H, cy+rr+1), max(0, cx-rr):min(W, cx+rr+1)] = False
        existing_room[max(0, cy-rr):min(H, cy+rr+1), max(0, cx-rr):min(W, cx+rr+1)] = False
    # A single through barrel can join any two enabled copper layers.
    for aa in range(len(LAYERS)):
        for bb in range(aa+1, len(LAYERS)):
            pair_room = room | (existing_room & free[LAYERS[aa]] & free[LAYERS[bb]])
            rows.append(idx[pair_room] + aa*n)
            cols.append(idx[pair_room] + bb*n)
            costs.append(np.full(int(pair_room.sum()), via_cost))
    r, c, w = np.concatenate(rows), np.concatenate(cols), np.concatenate(costs)
    g = coo_matrix((w, (r, c)), shape=(len(LAYERS) * n, len(LAYERS) * n)).tocsr()

    def node(p):
        L, x, y = p
        cy, cx = m.cell(x, y)
        cy, cx = cy // STEP, cx // STEP
        if not free[L][cy, cx]:          # snap to the nearest free cell within 1 mm
            ys, xs = np.nonzero(free[L][max(0, cy - 10):cy + 11, max(0, cx - 10):cx + 11])
            if not len(ys):
                raise SystemExit(f"no free cell near {p}")
            k = np.argmin((ys - min(cy, 10)) ** 2 + (xs - min(cx, 10)) ** 2)
            cy, cx = max(0, cy - 10) + ys[k], max(0, cx - 10) + xs[k]
        return LAYERS.index(L) * n + cy * W + cx

    with open(arg('--components')) as component_file:
        groups = json.load(component_file)
    maps=[]
    for group in groups:
        possible={}
        for L,x,y in group:
            cy,cx=m.cell(x,y);cy,cx=cy//STEP,cx//STEP
            if 0<=cy<H and 0<=cx<W and free[L][cy,cx]:
                possible[LAYERS.index(L)*n+cy*W+cx]=(L,x,y)
        maps.append(possible)
    if not all(maps):
        LAST_DIAGNOSTIC = {'reason': 'no legal component anchor', 'anchor_counts': [len(x) for x in maps]}
        return None
    dist,pred,sources=dijkstra(g,directed=False,indices=list(maps[0]),return_predecessors=True,min_only=True)
    t=min(maps[1],key=lambda k:dist[k])
    if not np.isfinite(dist[t]):
        LAST_DIAGNOSTIC = {'reason': 'disconnected search graph', 'anchor_counts': [len(x) for x in maps]}
        return None
    LAST_DIAGNOSTIC = {'reason': 'path found', 'anchor_counts': [len(x) for x in maps]}
    s=int(sources[t])
    global SELECTED
    SELECTED=(maps[0][s],maps[1][t])
    path,k=[],t
    while k!=s:
        path.append(k)
        k = pred[k]
    path.append(s)
    path.reverse()
    out = []
    for k in path:
        li, rem = divmod(int(k), n)
        cy, cx = divmod(rem, W)
        out.append((LAYERS[li], round(m.x0 + cx * STEP * G, 4), round(m.y0 + cy * STEP * G, 4)))
    return out, float(dist[t])


def pull(m, pts, need, soft_cost):
    """String pulling of one layer's run: drop every point whose neighbours see each other."""
    L = pts[0][0]
    dist = m.dist_all[L] if soft_cost is None else m.dist_hard[L]
    soft = m.dist_all[L]
    xy = [(p[1], p[2]) for p in pts]

    def ok(a, b):
        if not m.los(dist, a, b, need):
            return False
        return soft_cost is None or m.los(soft, a, b, need) or False

    out = [xy[0]]
    i = 0
    while i < len(xy) - 1:
        j = len(xy) - 1
        while j > i + 1 and not ok(xy[i], xy[j]):
            j -= 1
        out.append(xy[j])
        i = j
    return [(L, x, y) for x, y in out]


def refine(m, pts, need, rounds=40):
    """Move each inner corner toward the chord of its neighbours as far as the clearance map allows."""
    L = pts[0][0]
    dist = m.dist_all[L]
    xy = [list(p[1:]) for p in pts]
    for _ in range(rounds):
        moved = False
        # subdivide long segments so that corners can form where the obstacles are
        k = 0
        while k < len(xy) - 1:
            if math.hypot(xy[k + 1][0] - xy[k][0], xy[k + 1][1] - xy[k][1]) > 4.0:
                xy.insert(k + 1, [(xy[k][0] + xy[k + 1][0]) / 2, (xy[k][1] + xy[k + 1][1]) / 2])
            else:
                k += 1
        for k in range(1, len(xy) - 1):
            a, b, c = xy[k - 1], xy[k], xy[k + 1]
            t = ((b[0] - a[0]) * (c[0] - a[0]) + (b[1] - a[1]) * (c[1] - a[1])) / max(1e-9, (c[0] - a[0]) ** 2 + (c[1] - a[1]) ** 2)
            foot = (a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t)
            for f in (1.0, 0.5, 0.25, 0.1):
                q = (b[0] + (foot[0] - b[0]) * f, b[1] + (foot[1] - b[1]) * f)
                if math.hypot(q[0] - b[0], q[1] - b[1]) < 0.01:
                    break
                if m.los(dist, a, q, need) and m.los(dist, q, c, need):
                    xy[k] = [q[0], q[1]]
                    moved = True
                    break
        # drop points that became collinear
        k = 1
        while k < len(xy) - 1:
            a, b, c = xy[k - 1], xy[k], xy[k + 1]
            if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < 0.02 * math.hypot(c[0] - a[0], c[1] - a[1]) and m.los(dist, a, c, need):
                del xy[k]
            else:
                k += 1
        if not moved:
            break
    return [(L, round(x, 4), round(y, 4)) for x, y in xy]


def main():
    d = json.load(open(sys.argv[1]))
    own = set(arg("--nets").split(","))
    win = tuple(float(v) for v in arg("--window", "10:3:134:92").split(":"))
    soft_cost = float(arg("--soft")) if arg("--soft") else None
    via_cost = float(arg("--via-cost", "4.4"))
    parse = lambda s: (s.split(":")[0], float(s.split(":")[1]), float(s.split(":")[2]))
    start, goal = parse(arg("--from")), parse(arg("--to"))
    half, clear = float(arg("--half", HALF)), float(arg("--clear", CLEAR))
    drop = [tuple(float(v) for v in q.split(":")) for q in arg("--drop", "").split(",") if q]
    d["vias"] = [v for v in d["vias"] if not any(abs(v["x"] - x) < 1e-3 and abs(v["y"] - y) < 1e-3 for x, y in drop)]
    avoid = [tuple(float(v) for v in q.split(":")) for q in arg("--avoid", "").split(",") if q]
    m = Maps(d, own, win, avoid=avoid)
    need = half + clear
    res = search(m, start, goal, soft_cost, via_cost, need, VIA_ROOM + (clear - CLEAR) if half == HALF else 0.31 + clear)
    if res is None:
        raise SystemExit("no route")
    start,goal=SELECTED
    path, cost = res
    runs, cur = [], [path[0]]
    for p in path[1:]:
        if p[0] != cur[-1][0]:
            runs.append(cur)
            cur = [p]
        else:
            cur.append(p)
    runs.append(cur)
    out_runs = []
    for r in runs:
        if soft_cost is None:
            r = refine(m, pull(m, r, need, None), need)
        out_runs.append(r)
    length = sum(math.hypot(b[1] - a[1], b[2] - a[2]) for r in out_runs for a, b in zip(r, r[1:]))
    crossed = {}
    if soft_cost is not None:
        for r in out_runs:
            L = r[0][0]
            for p in r:
                cy, cx = m.cell(p[1], p[2])
                if m.dist_all[L][cy, cx] < need:
                    best = min(m.soft_items[L], key=lambda t: _seg_dist(p[1], p[2], t))
                    crossed.setdefault((L, best["net"]), []).append((p[1], p[2]))
    doc = {"from": start, "to": goal, "nets": sorted(own), "half_mm": half, "clear_mm": clear, "length_mm": round(length, 2), "vias": len(out_runs) - 1, "search_cost": round(cost, 2),
           "runs": [{"layer": r[0][0], "points": [[p[1], p[2]] for p in r]} for r in out_runs],
           "crossed": [{"layer": k[0], "net": k[1], "from": v[0], "to": v[-1], "cells": len(v)} for k, v in crossed.items()]}
    json.dump(doc, open(sys.argv[2], "w"), indent=1)
    print(f"length {length:.2f} mm, {len(out_runs) - 1} layer changes, cost {cost:.2f}")
    for r in out_runs:
        print(f"  {r[0][0]}: {len(r)} points, {sum(math.hypot(b[1] - a[1], b[2] - a[2]) for a, b in zip(r, r[1:])):.2f} mm, ({r[0][1]}, {r[0][2]}) -> ({r[-1][1]}, {r[-1][2]})")
    for c in doc["crossed"]:
        print("  crosses", c)


def _seg_dist(x, y, t):
    ax, ay, bx, by = t["x1"], t["y1"], t["x2"], t["y2"]
    l2 = (bx - ax) ** 2 + (by - ay) ** 2
    u = 0 if l2 == 0 else max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / l2))
    return math.hypot(x - ax - u * (bx - ax), y - ay - u * (by - ay)) - t["w"] / 2


if __name__ == "__main__":
    main()
