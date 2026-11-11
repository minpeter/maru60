#!/usr/bin/env python3
"""Plan the relocation of top-side (F.Cu) parts out from under switch housings.

MX switch housings sit flush on the top of the PCB.  Only the per-key LED fits
the housing's LED aperture; any other top-side part inside the 14 x 14 mm
housing outline (or under a PCB-mount stabilizer housing) keeps the switch from
seating.  This tool reads a geometry dump of the board (see
``dump_board_geometry.py``), finds every two-pad top-side part that violates
that keep-out, picks a new position in the gap between housings and routes both
pads back to their nets on F.Cu only (no new vias, inner planes untouched).

It writes an edit plan (JSON) that ``apply_topside_relocation.py`` applies with
the KiCad ``pcbnew`` bindings.  The plan is deterministic.

usage: plan_topside_relocation.py BOARD.json PLAN.json
"""
from __future__ import annotations

import heapq
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely.strtree import STRtree

HOUSING_HALF = 7.0        # MX housing outline is 14.0 x 14.0 mm
HOUSING_MARGIN = 0.35     # courtyard must stay this far outside the outline
STAB_HALF_X = 4.3         # PCB-mount stabilizer housing half width incl. margin
STAB_MARGIN_Y = 3.5       # beyond the two stabilizer holes
CLEARANCE = 0.18          # copper clearance aimed for by the router (board rule 0.15)
MIN_CLEARANCE = 0.155     # hard floor verified on the exact geometry
HOLE_CLEARANCE = 0.30     # new copper to any drilled hole edge
EDGE_CLEARANCE = 0.60     # new copper / courtyard to the board edge (rule 0.5)
TRACK_W = 0.25
GRID = 0.05
SEARCH_R = 9.0            # candidate positions within this radius of the anchor
WINDOW = 11.0             # routing window half size around the new position
COURT_HX, COURT_HY = 0.93, 0.47   # 0402 courtyard half extents
PART_CLEAR = 0.15         # courtyard to other top-side courtyards
VIA_D, VIA_DRILL = 0.5, 0.25      # the board's standard via
VIA_CLEAR = 0.20          # new via pad to other-net copper on any layer
VIA_HOLE_CLEAR = 0.35     # new via hole edge to any other hole edge
VIA_PAD_CLEAR = 0.20      # new via pad to any SMD pad (no via-in-pad)
GND_REUSE_MM = 3.0        # reuse existing F.Cu GND copper when a route this short exists


def switch_centers(fps):
    out = []
    for f in fps:
        if not f["ref"].startswith("SW") or f["ref"] in ("SW100", "SW101"):
            continue
        hubs = [p for p in f["pads"] if abs(p["drill"][0] - 3.9878) < 0.01]
        pegs = [p for p in f["pads"] if p["drill"][0] and (abs(p["drill"][0] - 1.7018) < 0.01 or abs(p["drill"][0] - 2.3368) < 0.01)]
        for h in hubs:
            if any(abs(abs(q["x"] - h["x"]) - 5.08) < 0.4 and abs(q["y"] - h["y"]) < 0.01 for q in pegs):
                out.append((f["ref"], h["x"], h["y"]))
    return out


def stab_zones(fps):
    out = []
    for f in fps:
        big = [p for p in f["pads"] if abs(p["drill"][0] - 3.9878) < 0.01]
        small = [p for p in f["pads"] if abs(p["drill"][0] - 3.048) < 0.01]
        for s in small:
            for b in big:
                if abs(b["x"] - s["x"]) < 0.05 and abs(abs(b["y"] - s["y"]) - 15.24) < 0.1:
                    y0, y1 = sorted([s["y"], b["y"]])
                    out.append(box(s["x"] - STAB_HALF_X, y0 - STAB_MARGIN_Y, s["x"] + STAB_HALF_X, y1 + STAB_MARGIN_Y))
    return out


def courtyard_of(f):
    polys = [Polygon(c) for c in f.get("courtyard", []) if len(c) >= 3]
    if polys:
        return unary_union(polys)
    return unary_union([Polygon(pl) for p in f["pads"] for pl in p["poly"]]).envelope


class Board:
    def __init__(self, d):
        self.d = d
        self.fps = {f["ref"]: f for f in d["fps"]}
        self.centers = switch_centers(d["fps"])
        self.keepout = unary_union(
            [box(x - HOUSING_HALF, y - HOUSING_HALF, x + HOUSING_HALF, y + HOUSING_HALF) for _, x, y in self.centers]
            + stab_zones(d["fps"])
        )
        xs = [e["x1"] for e in d["edges"]] + [e["x2"] for e in d["edges"]]
        ys = [e["y1"] for e in d["edges"]] + [e["y2"] for e in d["edges"]]
        self.outline = box(min(xs), min(ys), max(xs), max(ys))
        self.holes = []
        for f in d["fps"]:
            for p in f["pads"]:
                if p["drill"][0] > 0:
                    r = max(p["drill"]) / 2
                    self.holes.append(Point(p["x"], p["y"]).buffer(r, 24))
        self.pad_holes = list(self.holes)   # routing obstacles: tracks may run into same-net vias
        for v in d["vias"]:
            self.holes.append(Point(v["x"], v["y"]).buffer(v["drill"] / 2, 16))
        # F.Cu copper items: (geometry, net, kind, payload)
        self.cu = []
        for f in d["fps"]:
            for p in f["pads"]:
                if "F.Cu" in p["layers"]:
                    for pl in p["poly"]:
                        self.cu.append([Polygon(pl), p["net"], "pad", (f["ref"], p["num"], p["x"], p["y"])])
        self.tracks = [t for t in d["tracks"] if t["layer"] == "F.Cu"]
        for t in self.tracks:
            g = LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 8)
            self.cu.append([g, t["net"], "track", t])
        for v in d["vias"]:
            self.cu.append([Point(v["x"], v["y"]).buffer(v["d"] / 2, 16), v["net"], "via", v])
        for z in d["zones"]:
            for isl in z["fill"].get("F.Cu", []):
                if isl and len(isl[0]) >= 3:
                    self.cu.append([Polygon(isl[0], [h for h in isl[1:] if len(h) >= 3]), z["net"], "zone", None])
        # copper on every layer, for placing new GND vias: (geometry, net)
        self.all_cu = []
        self.smd_pads = []
        for f in d["fps"]:
            for p in f["pads"]:
                for pl in p["poly"]:
                    g = Polygon(pl)
                    if p["drill"][0] > 0:
                        self.all_cu.append((g, p["net"]))
                    else:
                        self.smd_pads.append((g, f["ref"]))
        for t in d["tracks"]:
            self.all_cu.append((LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 8), t["net"]))
        for v in d["vias"]:
            self.all_cu.append((Point(v["x"], v["y"]).buffer(v["d"] / 2, 16), v["net"]))
        self.gnd_planes = {"In1.Cu": [], "In2.Cu": []}
        for z in d["zones"]:
            for layer, isls in z["fill"].items():
                for isl in isls:
                    if not isl or len(isl[0]) < 3:
                        continue
                    g = Polygon(isl[0], [h for h in isl[1:] if len(h) >= 3])
                    if z["net"] == "GND" and layer in self.gnd_planes:
                        self.gnd_planes[layer].append(g)
                    elif z["net"] != "GND":
                        self.all_cu.append((g, z["net"]))
            if z.get("keepout") or not z["net"]:
                for o in z["outline"]:
                    if len(o) >= 3:
                        self.all_cu.append((Polygon(o), "<keepout>"))
        self.all_tree = STRtree([g for g, _ in self.all_cu])
        self.smd_tree = STRtree([g for g, _ in self.smd_pads])
        self.hole_tree = STRtree(self.holes)
        self.plane_tree = {k: STRtree(v) for k, v in self.gnd_planes.items()}
        self.courts = {f["ref"]: courtyard_of(f) for f in d["fps"] if f["layer"] == "F.Cu" and f["pads"] and not f["ref"].startswith(("SW", "STAB"))}

    def violators(self):
        out = []
        for ref, c in sorted(self.courts.items()):
            f = self.fps[ref]
            if ref.startswith("LED") or len(f["pads"]) != 2:
                continue
            if c.intersects(self.keepout.buffer(HOUSING_MARGIN - 0.05)):
                out.append(ref)
        return out


def raster(geoms, x0, y0, n):
    img = Image.new("1", (n, n), 0)
    dr = ImageDraw.Draw(img)

    def draw(g):
        if g.is_empty:
            return
        if g.geom_type == "Polygon":
            dr.polygon([((x - x0) / GRID, (y - y0) / GRID) for x, y in g.exterior.coords], fill=1)
            for h in g.interiors:
                dr.polygon([((x - x0) / GRID, (y - y0) / GRID) for x, y in h.coords], fill=0)
        elif hasattr(g, "geoms"):
            for s in g.geoms:
                draw(s)

    for g in geoms:
        draw(g)
    return np.array(img, dtype=bool)


def near_box(g, x, y, r):
    b = g.bounds
    return b[0] <= x + r and b[2] >= x - r and b[1] <= y + r and b[3] >= y - r


DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def flood(blocked, goals):
    """Multi-source octilinear wavefront from the goal cells. Returns the step map (-1 = unreachable)."""
    n = blocked.shape[0]
    free = ~blocked
    dist = np.full((n, n), -1, dtype=np.int32)
    front = goals & free
    dist[front] = 0
    k = 0
    while front.any():
        k += 1
        nxt = np.zeros((n, n), bool)
        for dx, dy in DIRS:
            ys0, ys1 = max(0, dy), n + min(0, dy)
            xs0, xs1 = max(0, dx), n + min(0, dx)
            src = front[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
            if dx and dy:
                src = src & free[ys0 - dy:ys1 - dy, xs0:xs1] & free[ys0:ys1, xs0 - dx:xs1 - dx]
            nxt[ys0:ys1, xs0:xs1] |= src
        nxt &= free & (dist < 0)
        dist[nxt] = k
        front = nxt
    return dist


def descend(dist, blocked, start):
    """Walk from start down the step map to a goal cell, keeping direction where possible."""
    n = dist.shape[0]
    y, x = start
    if dist[y, x] < 0:
        return None
    free = ~blocked
    path = [(y, x)]
    prev = None
    while dist[y, x] > 0:
        d = dist[y, x]
        order = ([prev] if prev is not None else []) + [q for q in DIRS if q != prev]
        for dx, dy in order:
            ny, nx = y + dy, x + dx
            if 0 <= ny < n and 0 <= nx < n and dist[ny, nx] == d - 1:
                if dx and dy and not (free[ny, x] and free[y, nx]):
                    continue
                y, x, prev = ny, nx, (dx, dy)
                path.append((y, x))
                break
        else:
            return None
    return path


def simplify(cells):
    pts = [cells[0]]
    for i in range(1, len(cells) - 1):
        a, b, c = cells[i - 1], cells[i], cells[i + 1]
        if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
            pts.append(b)
    pts.append(cells[-1])
    return pts


def find_gnd_via(board, px, py, own_ref, new_vias, forbid, f_local, f_holes):
    """Find a spot for a new GND via next to (px, py). Returns (vx, vy) or None."""
    best = None
    for r in (0.85, 1.0, 1.2, 1.4, 1.7, 2.0):
        for k in range(16):
            a = k * math.pi / 8
            vx, vy = round(px + r * math.cos(a), 4), round(py + r * math.sin(a), 4)
            pad = Point(vx, vy).buffer(VIA_D / 2, 16)
            hole = Point(vx, vy).buffer(VIA_DRILL / 2, 16)
            if not board.outline.buffer(-(EDGE_CLEARANCE + VIA_D / 2)).contains(Point(vx, vy)):
                continue
            if any(board.all_cu[i][1] != "GND" for i in board.all_tree.query(pad.buffer(VIA_CLEAR))if board.all_cu[i][0].distance(pad) < VIA_CLEAR):
                continue
            if any(board.smd_pads[i][1] != own_ref and board.smd_pads[i][0].distance(pad) < VIA_PAD_CLEAR for i in board.smd_tree.query(pad.buffer(VIA_PAD_CLEAR))):
                continue
            if any(board.holes[i].distance(hole) < VIA_HOLE_CLEAR for i in board.hole_tree.query(hole.buffer(VIA_HOLE_CLEAR))):
                continue
            if any(Point(q[0], q[1]).distance(Point(vx, vy)) < VIA_D + VIA_CLEAR for q in new_vias):
                continue
            if any(g.distance(pad) < CLEARANCE for g in forbid):
                continue
            # must land in solid GND plane on both inner layers
            core = Point(vx, vy).buffer(VIA_D / 2 + 0.1, 16)
            if not all(any(board.gnd_planes[L][i].contains(core) for i in board.plane_tree[L].query(core)) for L in board.gnd_planes):
                continue
            # F.Cu stub pad -> via
            stub = LineString([(px, py), (vx, vy)]).buffer(TRACK_W / 2, 8)
            if any(c[1] != "GND" and c[0].distance(stub) < CLEARANCE for c in f_local if near_box(c[0], vx, vy, 3.0)):
                continue
            if any(c[1] != "GND" and c[0].distance(pad) < CLEARANCE for c in f_local if near_box(c[0], vx, vy, 3.0)):
                continue
            if any(h.distance(stub) < HOLE_CLEARANCE for h in f_holes if near_box(h, vx, vy, 4.0)):
                continue
            if any(g.distance(stub) < CLEARANCE for g in forbid):
                continue
            return vx, vy
    return best


def plan(board: Board, refs):
    edits = []
    new_vias = []
    tracks = list(board.tracks)          # live F.Cu track list (dicts)
    cu = list(board.cu)
    courts = dict(board.courts)
    keep = board.keepout.buffer(HOUSING_MARGIN)
    edge_ok = board.outline.buffer(-EDGE_CLEARANCE)

    for ref in refs:
        f = board.fps[ref]
        snapshot = (list(tracks), list(cu), dict(courts))
        nets = {p["num"]: p["net"] for p in f["pads"]}
        pad_local = {p["num"]: (p["sx"], p["sy"]) for p in f["pads"]}
        # anchor: the LED this capacitor decouples (nearest LED sharing a net), else itself
        ax, ay = f["x"], f["y"]
        if ref.startswith("C"):
            leds = [g for g in board.d["fps"] if g["ref"].startswith("LED") and g["layer"] == "F.Cu"]
            if leds and "+4V_LED" in nets.values():
                led = min(leds, key=lambda g: math.hypot(g["x"] - f["x"], g["y"] - f["y"]))
                if math.hypot(led["x"] - f["x"], led["y"] - f["y"]) < 6:
                    ax, ay = led["x"], led["y"]
        # remove this part's own copper and courtyard from the obstacle sets
        cu = [c for c in cu if not (c[2] == "pad" and c[3][0] == ref)]
        courts.pop(ref, None)
        # the old pad copper may have been the only bridge between tracks that end inside it:
        # keep that connection with short tracks to the old pad centre (inside the old pad outline)
        bridges = []
        for p in f["pads"]:
            pg = unary_union([Polygon(pl) for pl in p["poly"]])
            ends = {}
            for t in tracks:
                if t["net"] != p["net"]:
                    continue
                for ex, ey in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
                    if abs(ex - p["x"]) < 1.5 and abs(ey - p["y"]) < 1.5 and pg.distance(Point(ex, ey)) < 1e-3:
                        ends[(round(ex, 4), round(ey, 4))] = min(t["w"], ends.get((round(ex, 4), round(ey, 4)), 9))
            if len(ends) >= 2:
                for (ex, ey), w in sorted(ends.items()):
                    if math.hypot(ex - p["x"], ey - p["y"]) > 1e-4:
                        bt = {"x1": ex, "y1": ey, "x2": p["x"], "y2": p["y"], "w": min(w, min(p["sx"], p["sy"])), "layer": "F.Cu", "net": p["net"]}
                        bridges.append(bt)
                        tracks.append(bt)
                        cu.append([LineString([(ex, ey), (p["x"], p["y"])]).buffer(bt["w"] / 2, 8), p["net"], "track", bt])
        all_bridges = list(bridges)
        # prune stubs that only served the old pads
        old_pts = [(p["x"], p["y"]) for p in f["pads"]]
        cu_near_old = [c for c in cu if near_box(c[0], f["x"], f["y"], 6.0)]
        tr_near_old = [t for t in tracks if t["net"] in nets.values() and min(math.hypot(t["x1"] - f["x"], t["y1"] - f["y"]), math.hypot(t["x2"] - f["x"], t["y2"] - f["y"])) < 6.0]
        removed = []
        changed = True
        while changed:
            changed = False
            for t in list(tr_near_old):
                for ex, ey, ox, oy in ((t["x1"], t["y1"], t["x2"], t["y2"]), (t["x2"], t["y2"], t["x1"], t["y1"])):
                    if not any(math.hypot(ex - px, ey - py) < 0.3 for px, py in old_pts + [(r["x1"], r["y1"]) for r in removed] + [(r["x2"], r["y2"]) for r in removed]):
                        continue
                    pt = Point(ex, ey)
                    touching = [c for c in cu_near_old if c[1] == t["net"] and c[3] is not t and c[0].distance(pt) < 1e-3]
                    if not touching:
                        if t in bridges:
                            bridges.remove(t)
                        tracks.remove(t)
                        tr_near_old.remove(t)
                        cu = [c for c in cu if c[3] is not t]
                        cu_near_old = [c for c in cu_near_old if c[3] is not t]
                        removed.append(t)
                        changed = True
                        break
        other_courts = unary_union(list(courts.values())) if courts else Polygon()
        # candidate positions
        cands = []
        steps = int(SEARCH_R / 0.25)
        for iy in range(-steps, steps + 1):
            for ix in range(-steps, steps + 1):
                x, y = round(ax + ix * 0.25, 4), round(ay + iy * 0.25, 4)
                dist = math.hypot(x - ax, y - ay)
                if dist > SEARCH_R:
                    continue
                for rot in (0, 90, 180, 270):
                    cands.append((dist + (0.01 if rot else 0), x, y, rot))
        cands.sort(key=lambda t: t[0])
        keep_p = prep(keep)
        edge_p = prep(edge_ok)
        cu_area = [c for c in cu if near_box(c[0], ax, ay, SEARCH_R + WINDOW + 1)]
        holes_area = [h for h in board.pad_holes if near_box(h, ax, ay, SEARCH_R + WINDOW + 1)]
        done = False
        tried = 0
        why = {"keepout": 0, "courtyard": 0, "unreachable": 0, "pad_clearance": 0, "route": 0}
        half = SEARCH_R + 2.5
        x0, y0 = ax - half, ay - half
        n = int(2 * half / GRID) + 1
        win = box(x0, y0, x0 + 2 * half, y0 + 2 * half)
        local = [c for c in cu_area if c[0].intersects(win)]
        holes = [h for h in holes_area if h.intersects(win)]
        infl = CLEARANCE + TRACK_W / 2
        ex = board.outline.buffer(-(EDGE_CLEARANCE + TRACK_W / 2))
        yy, xx = np.mgrid[0:n, 0:n]
        gxx, gyy = x0 + xx * GRID, y0 + yy * GRID
        bx0, by0, bx1, by1 = ex.bounds
        edge_block = (gxx < bx0) | (gxx > bx1) | (gyy < by0) | (gyy > by1)
        hole_block = raster([h.buffer(HOLE_CLEARANCE + TRACK_W / 2, 6) for h in holes], x0, y0, n)
        base = {}
        for num in ("1", "2"):
            net = nets[num]
            blocked = raster([c[0].buffer(infl, 4) for c in local if c[1] != net], x0, y0, n) | edge_block | hole_block
            # a track lying wholly inside existing same-net copper adds no new copper: always allowed
            inside = raster([g for g in (c[0].buffer(-(TRACK_W / 2 + 0.01), 4) for c in local if c[1] == net and c[2] != "zone") if not g.is_empty], x0, y0, n)
            blocked &= ~inside
            cell_anchor = {}
            for c in local:
                if c[1] != net:
                    continue
                pts = []
                if c[2] == "track":
                    t = c[3]
                    L = math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"])
                    k = max(1, int(L / (GRID / 2)))
                    pts = [(t["x1"] + (t["x2"] - t["x1"]) * i / k, t["y1"] + (t["y2"] - t["y1"]) * i / k) for i in range(k + 1)]
                elif c[2] == "via":
                    pts = [(c[3]["x"], c[3]["y"])]
                elif c[2] == "pad":
                    pts = [(c[3][2], c[3][3])]
                for qx, qy in pts:
                    cx, cy = int(round((qx - x0) / GRID)), int(round((qy - y0) / GRID))
                    if 0 <= cx < n and 0 <= cy < n and not blocked[cy, cx]:
                        dd = math.hypot(x0 + cx * GRID - qx, y0 + cy * GRID - qy)
                        if (cy, cx) not in cell_anchor or dd < cell_anchor[(cy, cx)][0]:
                            cell_anchor[(cy, cx)] = (dd, qx, qy)
            goals = np.zeros((n, n), bool)
            for cy, cx in cell_anchor:
                goals[cy, cx] = True
            base[num] = (blocked, goals, cell_anchor, flood(blocked, goals))

        def cell(px, py):
            return int(round((py - y0) / GRID)), int(round((px - x0) / GRID))

        for dist, x, y, rot in cands:
            hx, hy = (COURT_HX, COURT_HY) if rot in (0, 180) else (COURT_HY, COURT_HX)
            court = box(x - hx, y - hy, x + hx, y + hy)
            if keep_p.intersects(court) or not edge_p.contains(court):
                why["keepout"] += 1
                continue
            if court.distance(other_courts) < PART_CLEAR:
                why["courtyard"] += 1
                continue
            th = math.radians(rot)
            pads = {}
            for num, lx in (("1", -0.48), ("2", 0.48)):
                px = round(x + lx * math.cos(th), 6)
                py = round(y - lx * math.sin(th), 6)
                sx, sy = pad_local[num]
                if rot in (90, 270):
                    sx, sy = sy, sx
                pads[num] = (px, py, box(px - sx / 2, py - sy / 2, px + sx / 2, py + sy / 2))
            # quick reachability screen on the unmodified step maps
            if any(base[num][3][cell(pads[num][0], pads[num][1])] < 0 for num in pads if nets[num] != "GND"):
                why["unreachable"] += 1
                continue
            ok = True
            near = [c for c in local if near_box(c[0], x, y, 2.5) and c[0].distance(court) < 1.2]
            holes_near = [h for h in holes if near_box(h, x, y, 3.0)]
            for num, (px, py, g) in pads.items():
                if any(c[1] != nets[num] and c[0].distance(g) < CLEARANCE for c in near) or any(h.distance(g) < HOLE_CLEARANCE for h in holes_near):
                    ok = False
                    break
            if not ok:
                why["pad_clearance"] += 1
                continue
            tried += 1
            if tried > 40:
                break
            new_tracks = []
            add_vias = []
            extra = []
            fail = False
            for num in sorted(pads, key=lambda q: nets[q] == "GND"):
                net = nets[num]
                px, py, pg = pads[num]
                blocked, goals, cell_anchor, dmap = base[num]
                add = [pads[o][2].buffer(infl, 4) for o in pads if o != num and nets[o] != net] + [g.buffer(infl, 4) for g, nn in extra if nn != net]
                if add:
                    blocked = blocked | raster(add, x0, y0, n)
                    dmap = flood(blocked, goals)
                path = descend(dmap, blocked, cell(px, py))
                if net == "GND" and (path is None or len(path) * GRID > GND_REUSE_MM):
                    forbid = [gg for gg, nn in extra if nn != net] + [pads[o][2] for o in pads if o != num and nets[o] != net]
                    v = find_gnd_via(board, px, py, ref, new_vias + [(q["x"], q["y"]) for q in add_vias], forbid, local, holes)
                    if v is None:
                        fail = True
                        break
                    add_vias.append({"x": v[0], "y": v[1], "d": VIA_D, "drill": VIA_DRILL, "net": "GND"})
                    new_tracks.append({"x1": px, "y1": py, "x2": v[0], "y2": v[1], "w": TRACK_W, "layer": "F.Cu", "net": net})
                    extra.append((LineString([(px, py), v]).buffer(TRACK_W / 2, 8), net))
                    extra.append((Point(v).buffer(VIA_D / 2, 16), net))
                    extra.append((pg, net))
                    continue
                if path is None:
                    fail = True
                    break
                pts = simplify(path) if len(path) > 1 else path
                coords = [(px, py)] + [(round(x0 + cx * GRID, 4), round(y0 + cy * GRID, 4)) for cy, cx in pts]
                _, qx, qy = cell_anchor[path[-1]]
                coords.append((round(qx, 6), round(qy, 6)))
                cc = [coords[0]]
                for q in coords[1:]:
                    if math.hypot(q[0] - cc[-1][0], q[1] - cc[-1][1]) > 1e-6:
                        cc.append(q)
                if len(cc) > 1:
                    g = LineString(cc).buffer(TRACK_W / 2, 8)
                    if any(c[1] != net and c[0].distance(g) < MIN_CLEARANCE for c in local) or any(h.distance(g) < HOLE_CLEARANCE - 0.03 for h in holes) \
                            or any(nn != net and gg.distance(g) < MIN_CLEARANCE for gg, nn in extra) \
                            or any(nets[o] != net and pads[o][2].distance(g) < MIN_CLEARANCE for o in pads if o != num):
                        fail = True
                        break
                    extra.append((g, net))
                    for p1, p2 in zip(cc, cc[1:]):
                        new_tracks.append({"x1": p1[0], "y1": p1[1], "x2": p2[0], "y2": p2[1], "w": TRACK_W, "layer": "F.Cu", "net": net})
                extra.append((pg, net))
            if fail:
                why["route"] += 1
                continue
            for t in new_tracks:
                tracks.append(t)
                cu.append([LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 8), t["net"], "track", t])
            for num, (px, py, g) in pads.items():
                cu.append([g, nets[num], "pad", (ref, num, px, py)])
            courts[ref] = court
            for v in add_vias:
                new_vias.append((v["x"], v["y"]))
                g = Point(v["x"], v["y"]).buffer(v["d"] / 2, 16)
                cu.append([g, "GND", "via", v])
                board.holes.append(Point(v["x"], v["y"]).buffer(v["drill"] / 2, 16))
            edits.append({"ref": ref, "from": [f["x"], f["y"], f["rot"]], "to": [x, y, rot], "anchor_distance": round(dist, 3), "add_vias": add_vias,
                          "remove_tracks": [{k: t[k] for k in ("x1", "y1", "x2", "y2", "w", "layer", "net")} for t in removed if not any(t is q for q in all_bridges)],
                          "add_tracks": [t for t in all_bridges if any(t is q for q in bridges)] + new_tracks})
            done = True
            break
        if not done:
            edits.append({"ref": ref, "error": "no placement/route found", "why": why,
                          "goals": {num: int(base[num][1].sum()) for num in base}, "nets": nets})
            tracks, cu, courts = snapshot
    return edits


def main():
    d = json.load(open(sys.argv[1]))
    b = Board(d)
    refs = b.violators()
    if len(sys.argv) > 3:
        refs = [r for r in refs if r in sys.argv[3].split(",")]
    edits = plan(b, refs)
    json.dump({"source": sys.argv[1], "parameters": {"housing_half": HOUSING_HALF, "housing_margin": HOUSING_MARGIN, "clearance": CLEARANCE,
                                                     "hole_clearance": HOLE_CLEARANCE, "edge_clearance": EDGE_CLEARANCE, "track_width": TRACK_W},
               "edits": edits}, open(sys.argv[2], "w"), indent=1)
    bad = [e["ref"] for e in edits if "error" in e]
    print(f"{len(edits)} parts planned, {len(bad)} failed: {bad}")
    if len(edits) > len(bad):
        ds = [e["anchor_distance"] for e in edits if "error" not in e]
        print("anchor distance min/median/max", min(ds), sorted(ds)[len(ds) // 2], max(ds))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
