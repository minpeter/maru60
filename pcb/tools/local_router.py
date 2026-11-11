#!/usr/bin/env python3
"""Small single-layer router and via placer used by the order-candidate edit plans.

It works on the geometry dump written by ``dump_board_geometry.py`` and produces
track and via records for ``apply_layout_ops.py``.  It is deliberately local:
one pad to the nearest copper of the same net on one layer, octilinear, with a
clearance target above the board rule and an exact-geometry check afterwards.
KiCad DRC on the edited board remains the acceptance test.
"""
from __future__ import annotations

import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

import plan_topside_relocation as R

CLEARANCE = 0.18
MIN_CLEARANCE = 0.155
HOLE_CLEARANCE = 0.30
EDGE_CLEARANCE = 0.60
GRID = 0.05
OUTER = ("F.Cu", "B.Cu")


class Layout:
    def __init__(self, d):
        self.d = d
        self.fps = {f["ref"]: f for f in d["fps"]}
        xs = [e["x1"] for e in d["edges"]] + [e["x2"] for e in d["edges"]]
        ys = [e["y1"] for e in d["edges"]] + [e["y2"] for e in d["edges"]]
        self.outline = box(min(xs), min(ys), max(xs), max(ys))
        self.cu = {L: [] for L in OUTER}          # [geom, net, kind, payload]
        self.pad_holes, self.via_holes = [], []
        self.inner = []                            # (geom, net) on inner layers / all-layer items other than vias and tht pads
        self.smd = []                              # (geom, ref)
        self.courts = {L: {} for L in OUTER}
        for f in d["fps"]:
            for p in f["pads"]:
                polys = [Polygon(pl) for pl in p["poly"] if len(pl) >= 3]
                if p["drill"][0] > 0:
                    self.pad_holes.append(Point(p["x"], p["y"]).buffer(max(p["drill"]) / 2, 24))
                else:
                    self.smd.extend((g, f["ref"]) for g in polys)
                for L in OUTER:
                    if L in p["layers"]:
                        for g in polys:
                            self.cu[L].append([g, p["net"], "pad", (f["ref"], p["num"], p["x"], p["y"])])
                if p["drill"][0] > 0:
                    self.inner.extend((g, p["net"]) for g in polys)
            if f["layer"] in OUTER and f["pads"]:
                cy = [Polygon(c) for c in f.get("courtyard", []) if len(c) >= 3]
                self.courts[f["layer"]][f["ref"]] = unary_union(cy) if cy else unary_union([Polygon(pl) for p in f["pads"] for pl in p["poly"]]).envelope
        for t in d["tracks"]:
            g = LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 8)
            if t["layer"] in OUTER:
                self.cu[t["layer"]].append([g, t["net"], "track", t])
            else:
                self.inner.append((g, t["net"]))
        for v in d["vias"]:
            g = Point(v["x"], v["y"]).buffer(v["d"] / 2, 16)
            for L in OUTER:
                self.cu[L].append([g, v["net"], "via", v])
            self.via_holes.append(Point(v["x"], v["y"]).buffer(v["drill"] / 2, 16))
        self.gnd_planes = {"In1.Cu": [], "In2.Cu": []}
        for z in d["zones"]:
            for layer, isls in z["fill"].items():
                for isl in isls:
                    if not isl or len(isl[0]) < 3:
                        continue
                    g = Polygon(isl[0], [h for h in isl[1:] if len(h) >= 3])
                    if layer in OUTER:
                        self.cu[layer].append([g, z["net"], "zone", None])
                    elif z["net"] == "GND" and layer in self.gnd_planes:
                        self.gnd_planes[layer].append(g)
                    else:
                        self.inner.append((g, z["net"]))
            if z.get("keepout") or not z["net"]:
                for o in z["outline"]:
                    if len(o) >= 3:
                        self.inner.append((Polygon(o), "<keepout>"))

    # --- edits -----------------------------------------------------------------
    def remove_ref(self, ref):
        for L in OUTER:
            self.cu[L] = [c for c in self.cu[L] if not (c[2] == "pad" and c[3][0] == ref)]
            self.courts[L].pop(ref, None)
        self.smd = [s for s in self.smd if s[1] != ref]

    def remove_track(self, t):
        self.cu[t["layer"]] = [c for c in self.cu[t["layer"]] if c[3] is not t]

    def add_track(self, t):
        self.cu[t["layer"]].append([LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 8), t["net"], "track", t])

    def add_pad(self, layer, ref, num, net, x, y, sx, sy):
        g = box(x - sx / 2, y - sy / 2, x + sx / 2, y + sy / 2)
        self.cu[layer].append([g, net, "pad", (ref, num, x, y)])
        self.smd.append((g, ref))
        return g

    def add_via(self, x, y, net, d=0.5, drill=0.25):
        v = {"x": x, "y": y, "d": d, "drill": drill, "net": net}
        g = Point(x, y).buffer(d / 2, 16)
        for L in OUTER:
            self.cu[L].append([g, net, "via", v])
        self.via_holes.append(Point(x, y).buffer(drill / 2, 16))
        self.inner.append((g, net))
        return v

    def tracks_touching(self, layer, geoms, nets=None):
        """Tracks on a layer with an end point inside any of the given shapes."""
        out = []
        for c in self.cu[layer]:
            if c[2] != "track" or (nets is not None and c[1] not in nets):
                continue
            t = c[3]
            for ex, ey in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
                if any(g.distance(Point(ex, ey)) < 1e-3 for g in geoms):
                    out.append(t)
                    break
        return out

    def prune_stubs(self, layer, seeds):
        """Remove tracks left dangling next to the seed points; never past a junction."""
        removed = []
        pts = list(seeds)
        changed = True
        while changed:
            changed = False
            for c in list(self.cu[layer]):
                if c[2] != "track":
                    continue
                t = c[3]
                for ex, ey in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
                    if not any(math.hypot(ex - px, ey - py) < 0.35 for px, py in pts):
                        continue
                    pt = Point(ex, ey)
                    if not any(o[1] == c[1] and o[3] is not t and R.near_box(o[0], ex, ey, 0.5) and o[0].distance(pt) < 1e-3 for o in self.cu[layer]):
                        self.remove_track(t)
                        removed.append(t)
                        pts += [(t["x1"], t["y1"]), (t["x2"], t["y2"])]
                        changed = True
                        break
        return removed

    # --- routing ---------------------------------------------------------------
    def route(self, layer, start, net, width=0.25, half=9.0, avoid=(), goal_filter=None, grid=GRID):
        """Route from start to the nearest same-net copper on the layer. Returns track dicts or None."""
        sx, sy = start
        x0, y0 = sx - half, sy - half
        n = int(2 * half / grid) + 1
        win = box(x0, y0, x0 + 2 * half, y0 + 2 * half)
        local = [c for c in self.cu[layer] if c[0].intersects(win)]
        holes = [h for h in self.pad_holes if h.intersects(win)]
        infl = CLEARANCE + width / 2
        old_grid = R.GRID
        R.GRID = grid
        try:
            blocked = R.raster([c[0].buffer(infl, 4) for c in local if c[1] != net] + [g.buffer(infl, 4) for g in avoid], x0, y0, n)
            blocked |= R.raster([h.buffer(HOLE_CLEARANCE + width / 2, 6) for h in holes], x0, y0, n)
            ex = self.outline.buffer(-(EDGE_CLEARANCE + width / 2))
            yy, xx = np.mgrid[0:n, 0:n]
            gx, gy = x0 + xx * grid, y0 + yy * grid
            bx0, by0, bx1, by1 = ex.bounds
            blocked |= (gx < bx0) | (gx > bx1) | (gy < by0) | (gy > by1)
            inside = R.raster([g for g in (c[0].buffer(-(width / 2 + 0.01), 4) for c in local if c[1] == net and c[2] != "zone") if not g.is_empty], x0, y0, n)
            blocked &= ~inside
            anchors = {}
            for c in local:
                if c[1] != net or c[2] == "zone":
                    continue
                if goal_filter is not None and not goal_filter(c):
                    continue
                if c[2] == "track":
                    t = c[3]
                    L = math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"])
                    k = max(1, int(L / (grid / 2)))
                    pts = [(t["x1"] + (t["x2"] - t["x1"]) * i / k, t["y1"] + (t["y2"] - t["y1"]) * i / k) for i in range(k + 1)]
                elif c[2] == "via":
                    pts = [(c[3]["x"], c[3]["y"])]
                else:
                    pts = [(c[3][2], c[3][3])]
                for qx, qy in pts:
                    if math.hypot(qx - sx, qy - sy) < 1e-6:
                        continue
                    cx, cy = int(round((qx - x0) / grid)), int(round((qy - y0) / grid))
                    if 0 <= cx < n and 0 <= cy < n and not blocked[cy, cx]:
                        dd = math.hypot(x0 + cx * grid - qx, y0 + cy * grid - qy)
                        if (cy, cx) not in anchors or dd < anchors[(cy, cx)][0]:
                            anchors[(cy, cx)] = (dd, qx, qy)
            goals = np.zeros((n, n), bool)
            for cy, cx in anchors:
                goals[cy, cx] = True
            c0 = (int(round((sy - y0) / grid)), int(round((sx - x0) / grid)))
            blocked[max(0, c0[0] - 2):c0[0] + 3, max(0, c0[1] - 2):c0[1] + 3] = False
            dmap = R.flood(blocked, goals)
            path = R.descend(dmap, blocked, c0)
        finally:
            R.GRID = old_grid
        if path is None:
            return None
        pts = R.simplify(path) if len(path) > 1 else path
        coords = [(sx, sy)] + [(round(x0 + cx * grid, 4), round(y0 + cy * grid, 4)) for cy, cx in pts]
        _, qx, qy = anchors[path[-1]]
        coords.append((round(qx, 6), round(qy, 6)))
        cc = [coords[0]]
        for q in coords[1:]:
            if math.hypot(q[0] - cc[-1][0], q[1] - cc[-1][1]) > 1e-6:
                cc.append(q)
        if len(cc) < 2:
            return []
        g = LineString(cc).buffer(width / 2, 8)
        if any(c[1] != net and c[0].distance(g) < MIN_CLEARANCE for c in local) or any(h.distance(g) < HOLE_CLEARANCE - 0.03 for h in holes) \
                or any(a.distance(g) < MIN_CLEARANCE for a in avoid):
            return None
        out = []
        for a, b in zip(cc, cc[1:]):
            t = {"x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1], "w": width, "layer": layer, "net": net}
            out.append(t)
            self.add_track(t)
        return out

    # --- vias ------------------------------------------------------------------
    def via_ok(self, x, y, net, d=0.5, drill=0.25, clear=0.20, hole_clear=0.35, own_ref=None):
        pad = Point(x, y).buffer(d / 2, 16)
        hole = Point(x, y).buffer(drill / 2, 16)
        if not self.outline.buffer(-(EDGE_CLEARANCE + d / 2)).contains(Point(x, y)):
            return False
        for L in OUTER:
            for c in self.cu[L]:
                if c[1] != net and R.near_box(c[0], x, y, 1.5) and c[0].distance(pad) < clear:
                    return False
        if any(nn != net and R.near_box(g, x, y, 1.5) and g.distance(pad) < clear for g, nn in self.inner):
            return False
        if any(ref != own_ref and R.near_box(g, x, y, 1.5) and g.distance(pad) < clear for g, ref in self.smd):
            return False
        if any(R.near_box(h, x, y, 3.0) and h.distance(hole) < hole_clear for h in self.pad_holes + self.via_holes):
            return False
        if net == "GND":
            core = Point(x, y).buffer(d / 2 + 0.1, 16)
            if not all(any(g.contains(core) for g in self.gnd_planes[L] if R.near_box(g, x, y, 1.0)) for L in self.gnd_planes):
                return False
        return True

    def via_on_track(self, net, layer, near, radius=6.0, step=0.1, **kw):
        """Best via position on the centre line of an existing same-net track on the layer, closest to `near`."""
        best = None
        for c in self.cu[layer]:
            if c[1] != net or c[2] != "track":
                continue
            t = c[3]
            L = math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"])
            k = max(1, int(L / step))
            for i in range(k + 1):
                x, y = t["x1"] + (t["x2"] - t["x1"]) * i / k, t["y1"] + (t["y2"] - t["y1"]) * i / k
                dd = math.hypot(x - near[0], y - near[1])
                if dd > radius or (best is not None and dd >= best[0]):
                    continue
                if self.via_ok(x, y, net, **kw):
                    best = (dd, round(x, 4), round(y, 4))
        return None if best is None else (best[1], best[2])

    def via_near(self, net, near, radii=(0.0, 0.5, 0.8, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0), **kw):
        """Free via position near a point (for GND, or a net that is then routed to it)."""
        for r in radii:
            for k in range(1 if r == 0 else 24):
                a = k * math.pi / 12
                x, y = round(near[0] + r * math.cos(a), 4), round(near[1] + r * math.sin(a), 4)
                if self.via_ok(x, y, net, **kw):
                    return x, y
        return None
