#!/usr/bin/env python3
"""Plan an alternative land site for the option-position key LEDs.

The Caps Lock (normal / stepped) and right Shift (2.75U / 1.75U + 1U) positions
each have their own LED, and all of them are in series in the key LED chain, so
every one must be fitted for the chain to work.  But the LED of the option that
is *not* built lies under the housing of the switch (or stabilizer) that *is*
built.  This tool adds, for each such LED, a second set of four pads on the same
nets in the gap between housings.  The LED is soldered at exactly one of the two
sites: in its switch window when that option is built, at the alternative site
(where it only relays data) when it is not.  The chain order, and therefore the
firmware LED map, does not change.

usage: plan_led_alt_sites.py BOARD.json PLAN.json REF[,REF...]
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep

import itertools

import plan_topside_relocation as R

R.GRID = 0.1   # four pads and long signal runs: a coarser grid keeps the search fast

PAD = 0.55
PAD_OFF = 0.475
COURT_H = 1.0
TRIES = int(__import__("os").environ.get("ALT_TRIES", "60"))
ESCAPE = 0.7             # diagonal escape length (per axis) from each pad centre
SEARCH_R = float(__import__("os").environ.get("ALT_SEARCH_R", "13.0"))
ORDER = {"+4V_LED": 0, "GND": 9}


def plan_site(board: R.Board, ref, cu, courts, new_vias, pad_holes, centre=None):
    f = board.fps[ref]
    ax, ay = f["x"], f["y"]
    wx, wy = ax, ay
    if centre is not None:
        ax, ay = centre     # search (and route) around a hand-picked region instead of the LED itself
    rot = f["rot"]
    # pad offsets in board coordinates, taken from the placed footprint itself
    offs = {p["num"]: (round(p["x"] - wx, 6), round(p["y"] - wy, 6)) for p in f["pads"]}
    nets = {p["num"]: p["net"] for p in f["pads"]}
    keep = board.keepout.buffer(R.HOUSING_MARGIN)
    keep_p = prep(keep)
    edge_p = prep(board.outline.buffer(-R.EDGE_CLEARANCE))
    other_courts = unary_union(list(courts.values()))
    half = SEARCH_R + 2.5
    x0, y0 = ax - half, ay - half
    n = int(2 * half / R.GRID) + 1
    win = box(x0, y0, x0 + 2 * half, y0 + 2 * half)
    local = [c for c in cu if c[0].intersects(win)]
    holes = [h for h in pad_holes if h.intersects(win)]
    infl = R.CLEARANCE + R.TRACK_W / 2
    ex = board.outline.buffer(-(R.EDGE_CLEARANCE + R.TRACK_W / 2))
    yy, xx = np.mgrid[0:n, 0:n]
    gxx, gyy = x0 + xx * R.GRID, y0 + yy * R.GRID
    bx0, by0, bx1, by1 = ex.bounds
    edge_block = (gxx < bx0) | (gxx > bx1) | (gyy < by0) | (gyy > by1)
    hole_block = R.raster([h.buffer(R.HOLE_CLEARANCE + R.TRACK_W / 2, 6) for h in holes], x0, y0, n)

    def base_for(net):
        blocked = R.raster([c[0].buffer(infl, 4) for c in local if c[1] != net], x0, y0, n) | edge_block | hole_block
        inside = R.raster([g for g in (c[0].buffer(-(R.TRACK_W / 2 + 0.01), 4) for c in local if c[1] == net and c[2] != "zone") if not g.is_empty], x0, y0, n)
        blocked &= ~inside
        cell_anchor = {}
        for c in local:
            if c[1] != net:
                continue
            pts = []
            if c[2] == "track":
                t = c[3]
                L = math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"])
                k = max(1, int(L / (R.GRID / 2)))
                pts = [(t["x1"] + (t["x2"] - t["x1"]) * i / k, t["y1"] + (t["y2"] - t["y1"]) * i / k) for i in range(k + 1)]
            elif c[2] == "via":
                pts = [(c[3]["x"], c[3]["y"])]
            elif c[2] == "pad":
                pts = [(c[3][2], c[3][3])]
            for qx, qy in pts:
                cx, cy = int(round((qx - x0) / R.GRID)), int(round((qy - y0) / R.GRID))
                if 0 <= cx < n and 0 <= cy < n and not blocked[cy, cx]:
                    dd = math.hypot(x0 + cx * R.GRID - qx, y0 + cy * R.GRID - qy)
                    if (cy, cx) not in cell_anchor or dd < cell_anchor[(cy, cx)][0]:
                        cell_anchor[(cy, cx)] = (dd, qx, qy)
        goals = np.zeros((n, n), bool)
        for cy, cx in cell_anchor:
            goals[cy, cx] = True
        return blocked, goals, cell_anchor, R.flood(blocked, goals)

    base = {net: base_for(net) for net in set(nets.values())}

    def cell(px, py):
        return int(round((py - y0) / R.GRID)), int(round((px - x0) / R.GRID))

    cands = []
    steps = int(SEARCH_R / 0.25)
    for iy in range(-steps, steps + 1):
        for ix in range(-steps, steps + 1):
            x, y = round(ax + ix * 0.25, 4), round(ay + iy * 0.25, 4)
            d = math.hypot(x - ax, y - ay)
            if (2.5 < d or centre is not None) and d <= SEARCH_R:
                for turn in range(4):
                    cands.append((d + 0.001 * turn, x, y, turn))
    cands.sort()
    tried = 0
    why = {"keepout": 0, "courtyard": 0, "unreachable": 0, "pad_clearance": 0, "route": 0}

    def route_all(order, pads, geom, esc):
        new_tracks, add_vias = [], []
        # every pad first leaves its corner diagonally, so the four escapes can never block each other
        extra = [(LineString([pads[q], esc[q]]).buffer(R.TRACK_W / 2, 8), nets[q]) for q in pads]
        for q in pads:
            new_tracks.append({"x1": pads[q][0], "y1": pads[q][1], "x2": esc[q][0], "y2": esc[q][1], "w": R.TRACK_W, "layer": "F.Cu", "net": nets[q]})
        for num in order:
            net = nets[num]
            px, py = esc[num]
            blocked, goals, cell_anchor, _ = base[net]
            add = [geom[o].buffer(infl, 4) for o in pads if o != num and nets[o] != net] + [g.buffer(infl, 4) for g, nn in extra if nn != net]
            blocked = blocked | R.raster(add, x0, y0, n)
            cy_, cx_ = cell(px, py)
            blocked[max(0, cy_ - 1):cy_ + 2, max(0, cx_ - 1):cx_ + 2] = False
            path = None
            if net != "GND" or base[net][3][cy_, cx_] >= 0:
                dmap = R.flood(blocked, goals)
                path = R.descend(dmap, blocked, (cy_, cx_))
            if net == "GND" and (path is None or len(path) * R.GRID > R.GND_REUSE_MM):
                forbid = [gg for gg, nn in extra if nn != net] + [geom[o] for o in pads if o != num and nets[o] != net]
                v = R.find_gnd_via(board, px, py, ref, new_vias + [(q["x"], q["y"]) for q in add_vias], forbid, local, holes)
                if v is None:
                    return None
                add_vias.append({"x": v[0], "y": v[1], "d": R.VIA_D, "drill": R.VIA_DRILL, "net": "GND"})
                new_tracks.append({"x1": px, "y1": py, "x2": v[0], "y2": v[1], "w": R.TRACK_W, "layer": "F.Cu", "net": net})
                extra.append((LineString([(px, py), v]).buffer(R.TRACK_W / 2, 8), net))
                extra.append((Point(v).buffer(R.VIA_D / 2, 16), net))
                continue
            if path is None:
                return None
            pts = R.simplify(path) if len(path) > 1 else path
            coords = [(px, py)] + [(round(x0 + cx * R.GRID, 4), round(y0 + cy * R.GRID, 4)) for cy, cx in pts]
            _, qx, qy = cell_anchor[path[-1]]
            coords.append((round(qx, 6), round(qy, 6)))
            cc = [coords[0]]
            for q in coords[1:]:
                if math.hypot(q[0] - cc[-1][0], q[1] - cc[-1][1]) > 1e-6:
                    cc.append(q)
            if len(cc) > 1:
                g = LineString(cc).buffer(R.TRACK_W / 2, 8)
                if any(c[1] != net and c[0].distance(g) < R.MIN_CLEARANCE for c in local if R.near_box(c[0], (g.bounds[0] + g.bounds[2]) / 2, (g.bounds[1] + g.bounds[3]) / 2, max(g.bounds[2] - g.bounds[0], g.bounds[3] - g.bounds[1]) / 2 + 0.5)) \
                        or any(h.distance(g) < R.HOLE_CLEARANCE - 0.03 for h in holes) \
                        or any(nn != net and gg.distance(g) < R.MIN_CLEARANCE for gg, nn in extra) \
                        or any(nets[o] != net and geom[o].distance(g) < R.MIN_CLEARANCE for o in pads if o != num):
                    return None
                extra.append((g, net))
                for p1, p2 in zip(cc, cc[1:]):
                    new_tracks.append({"x1": p1[0], "y1": p1[1], "x2": p2[0], "y2": p2[1], "w": R.TRACK_W, "layer": "F.Cu", "net": net})
        return new_tracks, add_vias

    offs0 = offs
    for dist, x, y, turn in cands:
        # the alternative site may be turned in 90 degree steps; that changes which corner each net leaves from
        offs = dict(offs0)
        for _ in range(turn):
            offs = {q: (oy, -ox) for q, (ox, oy) in offs.items()}
        court = box(x - COURT_H, y - COURT_H, x + COURT_H, y + COURT_H)
        if keep_p.intersects(court) or not edge_p.contains(court):
            why["keepout"] += 1
            continue
        if court.distance(other_courts) < R.PART_CLEAR:
            why["courtyard"] += 1
            continue
        pads = {num: (round(x + ox, 6), round(y + oy, 6)) for num, (ox, oy) in offs.items()}
        geom = {num: box(px - PAD / 2, py - PAD / 2, px + PAD / 2, py + PAD / 2) for num, (px, py) in pads.items()}
        if any(base[nets[num]][3][cell(pads[num][0] + math.copysign(ESCAPE, offs[num][0]), pads[num][1] + math.copysign(ESCAPE, offs[num][1]))] < 0 for num in pads if nets[num] != "GND"):
            why["unreachable"] += 1
            continue
        near = [c for c in local if R.near_box(c[0], x, y, 3.0)]
        esc = {num: (round(pads[num][0] + math.copysign(ESCAPE, offs[num][0]), 6), round(pads[num][1] + math.copysign(ESCAPE, offs[num][1]), 6)) for num in pads}
        escg = {num: LineString([pads[num], esc[num]]).buffer(R.TRACK_W / 2, 8) for num in pads}
        if any(c[1] != nets[num] and c[0].distance(escg[num]) < R.CLEARANCE for num in pads for c in near) or \
                any(h.distance(escg[num]) < R.HOLE_CLEARANCE for num in pads for h in holes if R.near_box(h, x, y, 4.0)):
            why["pad_clearance"] += 1
            continue
        if any(c[1] != nets[num] and c[0].distance(geom[num]) < R.CLEARANCE for num in pads for c in near) or \
                any(h.distance(geom[num]) < R.HOLE_CLEARANCE for num in pads for h in holes if R.near_box(h, x, y, 4.0)):
            why["pad_clearance"] += 1
            continue
        tried += 1
        if tried > TRIES:
            break
        sig = [q for q in pads if nets[q] != "GND"]
        gnd = [q for q in pads if nets[q] == "GND"]
        result = None
        for perm in itertools.permutations(sig):
            result = route_all(list(perm) + gnd, pads, geom, esc)
            if result is not None:
                break
        if result is None:
            why["route"] += 1
            continue
        new_tracks, add_vias = result
        for t in new_tracks:
            cu.append([LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 8), t["net"], "track", t])
        for num, (px, py) in pads.items():
            cu.append([geom[num], nets[num], "pad", (ref, num, px, py)])
        for v in add_vias:
            new_vias.append((v["x"], v["y"]))
            cu.append([Point(v["x"], v["y"]).buffer(v["d"] / 2, 16), "GND", "via", v])
            board.holes.append(Point(v["x"], v["y"]).buffer(v["drill"] / 2, 16))
        courts[ref + "_ALT"] = court
        return {"ref": ref, "window_site": [wx, wy], "alt_site": [x, y], "alt_turns_ccw": turn, "distance": round(dist, 3),
                "alt_pads": {num: list(pads[num]) for num in pads}, "nets": nets, "add_tracks": new_tracks, "add_vias": add_vias}
    return {"ref": ref, "error": "no alternative site found", "why": why}


def main():
    d = json.load(open(sys.argv[1]))
    b = R.Board(d)
    cu = list(b.cu)
    courts = dict(b.courts)
    new_vias = []
    out = []
    for spec in sys.argv[3].split(","):
        # REF or REF@x:y (search around x,y)
        ref, _, at = spec.partition("@")
        centre = tuple(float(v) for v in at.split(":")) if at else None
        out.append(plan_site(b, ref, cu, courts, new_vias, b.pad_holes, centre))
        print(ref, out[-1].get("error") or (out[-1]["alt_site"], out[-1]["distance"], len(out[-1]["add_tracks"]), len(out[-1]["add_vias"])), out[-1].get("why", ""))
    json.dump({"source": sys.argv[1], "sites": out}, open(sys.argv[2], "w"), indent=1)
    return 1 if any("error" in o for o in out) else 0


if __name__ == "__main__":
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    sys.exit(main())
