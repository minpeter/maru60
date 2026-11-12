#!/usr/bin/env python3
"""Plan moving the remaining via holes out of SMD pads by rerouting, not by nudging.

usage: plan_via_relocate.py BOARD.json OPS.json [--skip x:y,x:y] [--radius MM]
                            [--step MM] [--pad-edge MM] [--clear MM] [--hole-clear MM] [--tries N]

The defaults keep a new via 0.20 mm from other copper and 0.36 mm (centre) from
every pad.  For the sites where that finds nothing, the search can be made
finer and brought down to what the rules need: --step 0.05 --pad-edge 0.33
--clear 0.16 --hole-clear 0.25 (0.33 leaves 0.2 mm between the hole and the
pad, so the hole stays under solder mask).

plan_via_out_of_pad.py moves a via up to 1.3 mm and drags the track ends with
it; that fails where the neighbourhood is full.  This planner takes the via
out, looks for a free via position up to RADIUS (default 4 mm) from the pad
that is at least 0.36 mm from every pad opening and passes the all-layer
clearance check, and routes to it:

  * on the pad's layer, from the new via to the pad;
  * on the other outer layer, from the new via to the track that ended on the
    old via (that track is shortened to the point where the new one joins it).

A GND pad whose via carries no track on the other layer and has no free
position is instead joined by a track to another GND via (one that is not in a
pad itself), and its own via is removed; both inner layers are GND planes.

Tracks of the pad's layer that ended on the old via stay: their end lies on the
pad.  KiCad DRC decides afterwards; rejected moves are listed with --skip.
"""
import json
import math
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from shapely.geometry import LineString, Point, Polygon  # noqa: E402

import local_router as LR  # noqa: E402
import plan_bottom_sites as PB  # noqa: E402

PAD_EDGE = 0.36          # via centre to the nearest pad opening: 0.25 mm via land radius + 0.11


def main():
    d = json.load(open(sys.argv[1]))
    skip = set()
    if "--skip" in sys.argv:
        skip = {tuple(round(float(v), 3) for v in s.split(":")) for s in sys.argv[sys.argv.index("--skip") + 1].split(",") if s}
    opt = lambda name, default: float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default
    radius, step, pad_edge = opt("--radius", 4.0), opt("--step", 0.1), opt("--pad-edge", PAD_EDGE)
    clear, hole_clear, tries = opt("--clear", 0.20), opt("--hole-clear", 0.35), int(opt("--tries", 40))
    L = LR.Layout(d)
    smd = [(Polygon(p["poly"][0]), f["ref"], p["num"], p["net"], "F.Cu" if "F.Cu" in p["layers"] else "B.Cu", p)
           for f in d["fps"] for p in f["pads"] if p["drill"][0] == 0 and p["poly"] and any(l in ("F.Cu", "B.Cu") for l in p["layers"])]
    ops_remove_t, ops_add_t, ops_remove_v, ops_add_v, report = [], [], [], [], []
    plain = lambda t: {k: t[k] for k in ("x1", "y1", "x2", "y2", "layer", "net")}
    for v in list(d["vias"]):
        pt = Point(v["x"], v["y"])
        hit = [s for s in smd if abs(s[5]["x"] - v["x"]) < 4 and abs(s[5]["y"] - v["y"]) < 4 and s[0].distance(pt) < v["drill"] / 2]
        if not hit:
            continue
        key = (round(v["x"], 3), round(v["y"], 3))
        g, ref, num, net, layer, p = hit[0]
        other = "F.Cu" if layer == "B.Cu" else "B.Cu"
        if key in skip or net != v["net"]:
            report.append({"via": key, "pad": f"{ref}.{num}", "moved": False, "why": "skipped"})
            continue
        at_via = lambda t: math.hypot(t["x1"] - v["x"], t["y1"] - v["y"]) < 1e-3 or math.hypot(t["x2"] - v["x"], t["y2"] - v["y"]) < 1e-3
        far_tracks = [c[3] for c in L.cu[other] if c[2] == "track" and c[1] == net and at_via(c[3])]
        if len(far_tracks) > 1:
            report.append({"via": key, "pad": f"{ref}.{num}", "moved": False, "why": f"{len(far_tracks)} tracks on {other} meet at the via"})
            continue
        base = PB.snapshot(L)
        for lay in LR.OUTER:
            L.cu[lay] = [c for c in L.cu[lay] if not (c[2] == "via" and c[3] is v)]
        L.via_holes = [h for h in L.via_holes if h.distance(pt) > 1e-6]
        mid = PB.snapshot(L)
        near_pads = [s[0] for s in smd if abs(s[5]["x"] - v["x"]) < radius + 2 and abs(s[5]["y"] - v["y"]) < radius + 2]
        n = int(radius / step)
        cands = sorted((math.hypot(ix * step, iy * step), round(v["x"] + ix * step, 4), round(v["y"] + iy * step, 4))
                       for ix in range(-n, n + 1) for iy in range(-n, n + 1) if 0.3 <= math.hypot(ix * step, iy * step) <= radius)
        done, tried = None, 0
        for dist, x, y in cands:
            q = Point(x, y)
            if any(s.distance(q) < pad_edge for s in near_pads) or not L.via_ok(x, y, net, clear=clear, hole_clear=hole_clear, own_ref=None):
                continue
            tried += 1
            if tried > tries:
                break
            L.add_via(x, y, net)
            w = 0.25 if net == "GND" else 0.2
            r1 = L.route(layer, (x, y), net, width=w, half=radius + 2, goal_filter=lambda c: c[2] == "pad" and c[3][0] == ref and c[3][1] == num)
            if r1 is None:
                PB.restore(L, mid)
                continue
            r2, shorten = [], None
            if far_tracks:
                t = far_tracks[0]
                r2 = L.route(other, (x, y), net, width=t["w"], half=radius + 2, goal_filter=lambda c: c[2] == "track" and c[3] is t)
                if r2 is None:
                    PB.restore(L, mid)
                    continue
                join = (r2[-1]["x2"], r2[-1]["y2"])
                a, b = (t["x1"], t["y1"]), (t["x2"], t["y2"])
                keep = b if math.hypot(a[0] - v["x"], a[1] - v["y"]) < 1e-3 else a      # the end that is not on the old via
                if math.hypot(join[0] - keep[0], join[1] - keep[1]) > 1e-3:
                    shorten = {"x1": keep[0], "y1": keep[1], "x2": round(join[0], 6), "y2": round(join[1], 6), "w": t["w"], "layer": other, "net": net}
            done = (x, y, r1, r2, shorten)
            break
        if not done and net == "GND" and not far_tracks:
            # A GND pad does not need its own via: join it to another GND via on its layer and drop this one.
            PB.restore(L, mid)
            for wd in (0.25, 0.2, 0.15):
                r = L.route(layer, (p["x"], p["y"]), net, width=wd, half=6.0,
                            goal_filter=lambda c: c[2] == "via" and not any(s.distance(Point(c[3]["x"], c[3]["y"])) < c[3]["drill"] / 2 for s in near_pads))
                if r:
                    break
            if r:
                ops_remove_v.append({"x": v["x"], "y": v["y"], "net": net})
                ops_add_t += r
                report.append({"via": key, "pad": f"{ref}.{num}", "moved": True, "to": [r[-1]["x2"], r[-1]["y2"]], "joined_existing_via": True,
                               "distance_mm": round(sum(math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"]) for t in r), 2)})
                continue
        if not done:
            PB.restore(L, base)
            report.append({"via": key, "pad": f"{ref}.{num}", "moved": False, "why": "no free position with a route"})
            continue
        x, y, r1, r2, shorten = done
        ops_remove_v.append({"x": v["x"], "y": v["y"], "net": net})
        ops_add_v.append({"x": x, "y": y, "net": net})
        ops_add_t += r1 + r2
        if far_tracks:
            t = far_tracks[0]
            ops_remove_t.append(plain(t))
            L.remove_track(t)
            if shorten:
                ops_add_t.append(shorten)
                L.add_track(shorten)
        report.append({"via": key, "pad": f"{ref}.{num}", "moved": True, "to": [x, y], "distance_mm": round(math.hypot(x - v["x"], y - v["y"]), 2)})
    json.dump({"note": "Via holes taken out of SMD pads and rerouted to a free position.", "report": report,
               "ops": [{"op": "remove_tracks", "tracks": ops_remove_t}, {"op": "remove_vias", "vias": ops_remove_v},
                       {"op": "add_vias", "vias": ops_add_v}, {"op": "add_tracks", "tracks": ops_add_t}]},
              open(sys.argv[2], "w"), indent=1)
    print(f"{len(report)} vias in pads: {sum(1 for r in report if r['moved'])} planned, {sum(1 for r in report if not r['moved'])} left")
    for r in report:
        print("  moved" if r["moved"] else "  left:", r["pad"], r["via"], r.get("to", r.get("why")), r.get("distance_mm", ""))


if __name__ == "__main__":
    main()
