#!/usr/bin/env python3
"""Plan a series damping resistor at the source of a long LED data hop.

usage: plan_series_resistor.py BOARD.json OPS.json REF LED NET [MAX_MM [MIN_MM]]
       e.g. R116 LED71 UG_LED_9, R117 LED58 KEY_RGB_CHAIN_60

A hop runs from one LED's DOUT (pad 3) to the next LED's DIN.  If the SK6805
output is fast and strong (its data sheet does not say), reflections on a long
unterminated hop re-cross the input threshold.  A 100 ohm 0402 goes in series
near the driving LED: DOUT and the copper up to the resistor get the net
NET_SRC, the rest of the hop keeps NET.

The route is followed from the DOUT pad through tracks and vias.  The resistor
may start at the pad or at any via within MAX_MM (default 12) of it; from that
point the next k track segments are removed and the part is placed beside the
gap, on the layer the removed segments were on.  With MIN_MM given, the end of
every track segment between MIN_MM and MAX_MM from the pad is a start point
too: that is for hops that run under switch housings without a via, where the
first free place for a top-side part is the gap between two housings.  The
part goes:

  B.Cu  clear of every bottom-side courtyard and copper (plan_bottom_sites);
  F.Cu  additionally outside every switch housing and stabilizer zone by
        0.35 mm (plan_topside_relocation), because MX housings sit on the PCB.

Output is an operation list for apply_layout_ops.py; KiCad DRC is the judge.
The schematic change (symbol REF on the core sheet, label NET_SRC on the LED's
DOUT) is made separately.
"""
import json
import math
import sys
import uuid

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from shapely.geometry import box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import local_router as LR  # noqa: E402
import plan_bottom_sites as PB  # noqa: E402
import plan_topside_relocation as TR  # noqa: E402

CORE_SHEET = "0940d797-79a6-569a-9535-d8f19961ba0b"
LIB_DIR = "pcb/experiments/resume-20261111-order-candidate/pcb/Maru60.pretty"     # the stock 0402 land without its silkscreen
OFFS = {0: {"1": (-0.51, 0.0), "2": (0.51, 0.0)}, 90: {"1": (0.0, 0.51), "2": (0.0, -0.51)},
        180: {"1": (0.51, 0.0), "2": (-0.51, 0.0)}, 270: {"1": (0.0, -0.51), "2": (0.0, 0.51)}}


def ends(t):
    return ((t["x1"], t["y1"]), (t["x2"], t["y2"]))


def near(a, b, tol=2e-3):
    return math.hypot(a[0] - b[0], a[1] - b[1]) < tol


def trace(L, led, net, p3):
    """The hop from the DOUT pad: [("track", t, end_point) | ("via", v, point)], plus the tracks lying on the pad."""
    layer = "F.Cu" if "F.Cu" in p3["layers"] else "B.Cu"
    tracks = {lay: [c[3] for c in L.cu[lay] if c[2] == "track" and c[1] == net] for lay in LR.OUTER}
    vias = [c[3] for c in L.cu["B.Cu"] if c[2] == "via" and c[1] == net]
    on_pad = lambda q: abs(q[0] - p3["x"]) <= p3["sx"] / 2 + 1e-3 and abs(q[1] - p3["y"]) <= p3["sy"] / 2 + 1e-3
    stubs = [t for t in tracks[layer] if all(on_pad(q) for q in ends(t))]
    touches_start = lambda q: on_pad(q) or any(near(q, e) for u in stubs for e in ends(u))
    first = [t for t in tracks[layer] if t not in stubs and any(touches_start(q) for q in ends(t))]
    if len(first) != 1:
        raise SystemExit(f"{len(first)} tracks leave {led}.3; expected one")
    path, seen = [], set()
    t = first[0]
    a, b = ends(t)
    cur = b if touches_start(a) else a
    path.append(("track", t, cur, layer))
    seen.add(id(t))
    while True:
        nxt = [u for u in tracks[layer] if id(u) not in seen and u not in stubs and any(near(q, cur) for q in ends(u))]
        if len(nxt) == 1:
            u = nxt[0]
            a, b = ends(u)
            cur = b if near(a, cur) else a
            path.append(("track", u, cur, layer))
            seen.add(id(u))
            continue
        v = [v for v in vias if near((v["x"], v["y"]), cur, 0.06) and id(v) not in seen]
        if len(nxt) == 0 and len(v) == 1:
            layer = "B.Cu" if layer == "F.Cu" else "F.Cu"
            cur = (v[0]["x"], v[0]["y"])
            path.append(("via", v[0], cur, layer))
            seen.add(id(v[0]))
            continue
        return path, stubs


def main():
    d = json.load(open(sys.argv[1]))
    REF, LED, NET = sys.argv[3:6]
    MAX_MM = float(sys.argv[6]) if len(sys.argv) > 6 else 12.0
    MIN_MM = float(sys.argv[7]) if len(sys.argv) > 7 else None
    SRC = NET + "_SRC"
    SYMBOL_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"maru60/order-candidate/{REF}"))
    L = LR.Layout(d)
    keepout = unary_union([box(x - TR.HOUSING_HALF, y - TR.HOUSING_HALF, x + TR.HOUSING_HALF, y + TR.HOUSING_HALF) for _, x, y in TR.switch_centers(d["fps"])]
                          + TR.stab_zones(d["fps"])).buffer(TR.HOUSING_MARGIN)
    p3 = next(p for p in L.fps[LED]["pads"] if p["num"] == "3" and p["net"] == NET)
    path, stubs = trace(L, LED, NET, p3)
    width = path[0][1]["w"]

    def free(layer, court, geom):
        if layer == "B.Cu":
            return PB.bottom_free(L, court, geom)
        if court.intersects(keepout) or not L.outline.buffer(-LR.EDGE_CLEARANCE).contains(court):
            return False
        if any(c.distance(court) < 0.15 for ref, c in L.courts["F.Cu"].items() if not ref.startswith(("SW", "STAB"))):
            return False
        local = [c for c in L.cu["F.Cu"] if LR.R.near_box(c[0], court.centroid.x, court.centroid.y, 3.0)]
        for g in geom:
            if any(c[0].distance(g) < LR.CLEARANCE for c in local):
                return False
            if any(h.distance(g) < LR.HOLE_CLEARANCE for h in L.pad_holes + L.via_holes if LR.R.near_box(h, court.centroid.x, court.centroid.y, 4.0)):
                return False
        return True

    # start points: the pad itself, then every via of the hop within MAX_MM of the pad
    starts, run = [(-1, 0.0)], 0.0
    for i, (kind, item, pt, layer) in enumerate(path):
        if kind == "track":
            run += math.hypot(item["x2"] - item["x1"], item["y2"] - item["y1"])
            if MIN_MM is not None and MIN_MM <= run <= MAX_MM:
                starts.append((i, run))
        elif run <= MAX_MM:
            starts.append((i, run))
    if MIN_MM is not None:
        starts = [q for q in starts if q[1] >= MIN_MM]
    entries = {lay: {id(c[3]): c for c in L.cu[lay] if c[2] in ("track", "via")} for lay in LR.OUTER}
    pad_entries = [c for lay in LR.OUTER for c in L.cu[lay] if c[2] == "pad" and c[3][0] == LED and c[3][1] == "3" and near((c[3][2], c[3][3]), (p3["x"], p3["y"]))]

    for s, run0 in starts:
        upstream = path[:s + 1]                          # copper that becomes NET_SRC
        layer = path[s][3] if s >= 0 else path[0][3]
        root = path[s][2] if s >= 0 else (p3["x"], p3["y"])
        after = []
        for kind, item, pt, lay in path[s + 1:]:
            if kind != "track":
                break
            after.append((item, pt))
        # rename the upstream copper in the model
        for c in pad_entries:
            c[1] = SRC
        renamed = []
        for kind, item, pt, lay in upstream:
            for lay2 in LR.OUTER:
                c = entries[lay2].get(id(item))
                if c is not None:
                    c[1] = SRC
                    renamed.append(c)
        up_stubs = stubs if s >= 0 else []
        for t in up_stubs:
            entries[layer if s < 0 else path[0][3]][id(t)][1] = SRC
            renamed.append(entries[path[0][3]][id(t)])
        try:
            removed_len = 0.0
            for k in range(1, len(after) + 1):
                removed = ([] if s >= 0 else list(stubs)) + [t for t, _ in after[:k]]
                removed_len += math.hypot(after[k - 1][0]["x2"] - after[k - 1][0]["x1"], after[k - 1][0]["y2"] - after[k - 1][0]["y1"])
                if run0 + removed_len > MAX_MM + 6:
                    break
                cut = after[k - 1][1]
                base = PB.snapshot(L)
                for t in removed:
                    L.remove_track(t)
                first_removed = list(removed)
                mid = PB.snapshot(L)
                anchors = [root, cut, ((root[0] + cut[0]) / 2, (root[1] + cut[1]) / 2)]
                seen, cands = set(), []
                for ax, ay in anchors:
                    for ix in range(-20, 21):
                        for iy in range(-20, 21):
                            x, y = round(round((ax + ix * 0.125) / 0.0125) * 0.0125, 4), round(round((ay + iy * 0.125) / 0.0125) * 0.0125, 4)
                            if (x, y) in seen:
                                continue
                            seen.add((x, y))
                            for rot in (0, 90, 180, 270):
                                cands.append((math.hypot(x - root[0], y - root[1]) + math.hypot(x - cut[0], y - cut[1]) + rot * 1e-5, x, y, rot))
                cands.sort()
                tried = 0
                for dist, x, y, rot in cands:
                    sx, sy = (0.54, 0.64) if rot in (0, 180) else (0.64, 0.54)      # KiCad R_0402_1005Metric pads at +/-0.51 mm
                    pads = {n: (round(x + v[0], 4), round(y + v[1], 4), sx, sy) for n, v in OFFS[rot].items()}
                    court = box(x - 0.93, y - 0.47, x + 0.93, y + 0.47) if rot in (0, 180) else box(x - 0.47, y - 0.93, x + 0.47, y + 0.93)
                    geom = [box(px - a / 2, py - b / 2, px + a / 2, py + b / 2) for px, py, a, b in pads.values()]
                    if not free(layer, court, geom):
                        continue
                    tried += 1
                    if tried > 60:
                        break
                    nets = {"1": SRC, "2": NET}
                    for n, (px, py, a, b) in pads.items():
                        L.add_pad(layer, REF, n, nets[n], px, py, a, b)
                    if s < 0:
                        is_root = lambda c: c[2] == "pad" and c[3][0] == LED
                    elif path[s][0] == "via":
                        is_root = lambda c: c[2] == "via" and near((c[3]["x"], c[3]["y"]), root, 0.06)
                    else:
                        is_root = lambda c: c[2] == "track" and c[3] is path[s][1]
                    r1 = L.route(layer, pads["1"][:2], SRC, width=width, half=8.0, goal_filter=is_root)
                    if r1 and s >= 0 and path[s][0] == "track" and not near((r1[-1]["x2"], r1[-1]["y2"]), root, 0.08):
                        r1 = None                       # joined the upstream track away from its end: that would leave a stub
                    r2 = L.route(layer, pads["2"][:2], NET, width=width, half=8.0, goal_filter=lambda c: not (c[2] == "pad" and c[3][0] == REF)) if r1 is not None else None
                    if r1 is None or r2 is None:
                        PB.restore(L, mid)
                        continue
                    # what is left of the old route between the cut and the point where the new track joins it would dangle
                    joins = [q for t in r2 for q in ends(t)]
                    start = cut
                    removed = list(first_removed)
                    for t, end in after[k:]:
                        if any(near(q, start) for q in joins):
                            break
                        removed.append(t)
                        start = end
                    if not any(near(q, start) for q in joins):
                        PB.restore(L, mid)             # the new track joined the old route in the middle of a segment
                        continue
                    up_tracks = [item for kind, item, pt, lay in upstream if kind == "track"] + list(up_stubs)
                    up_vias = [item for kind, item, pt, lay in upstream if kind == "via"]
                    plain = lambda t, net: {"x1": t["x1"], "y1": t["y1"], "x2": t["x2"], "y2": t["y2"], "layer": t["layer"], "net": net}
                    ops = [
                        {"op": "remove_tracks", "tracks": [plain(t, NET) for t in removed + up_tracks]},
                        {"op": "remove_vias", "vias": [{"x": v["x"], "y": v["y"], "net": NET} for v in up_vias]},
                        {"op": "set_pad_net", "ref": LED, "pad": "3", "net": SRC},
                        {"op": "add_footprint", "ref": REF, "lib_dir": LIB_DIR, "name": "R_0402_1005Metric",
                         "fpid": "Maru60:R_0402_1005Metric", "side": layer, "x": x, "y": y, "rot": rot, "value": "100 1%", "pad_nets": nets,
                         "path": f"/{CORE_SHEET}/{SYMBOL_UUID}", "sheetname": "/Core/", "sheetfile": "maru60-core.kicad_sch",
                         "expect_pads": {n: [v[0], v[1]] for n, v in pads.items()}},
                        {"op": "add_vias", "vias": [{"x": v["x"], "y": v["y"], "net": SRC} for v in up_vias]},
                        {"op": "add_tracks", "tracks": [dict(plain(t, SRC), w=t["w"]) for t in up_tracks] + r1 + r2},
                    ]
                    ops = [o for o in ops if o.get("tracks", o.get("vias", True))]
                    json.dump({"note": f"{REF} 100 ohm in series at the source of the LED data hop {NET} ({LED} DOUT), {round(run0, 1)} mm of copper before it.",
                               "symbol_uuid": SYMBOL_UUID, "ops": ops}, open(sys.argv[2], "w"), indent=1)
                    print(f"{REF} on {layer} at ({x}, {y}) rot {rot}; {round(run0, 1)} mm from {LED}.3; removed {len(removed)} tracks, renamed {len(up_tracks)} tracks and {len(up_vias)} vias, added {len(r1) + len(r2)}")
                    return 0
                PB.restore(L, base)
        finally:
            for c in renamed:
                c[1] = NET
    print("no site found")
    return 1


if __name__ == "__main__":
    sys.exit(main())
