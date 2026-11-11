#!/usr/bin/env python3
"""Plan bottom-side land sites that are fed from top-side nets through new vias.

usage: plan_bottom_sites.py BOARD.json OPS.json led:REF[@x:y] ... cap:REF@x:y ...

  led:REF   add four B.Cu pads to a top-side key LED, as a second place to solder
            it (used when the LED's own switch window is covered by a stabilizer
            housing).  Each signal net gets a via on one of its existing F.Cu
            tracks and a B.Cu track to the new pad; GND gets a via into the planes.
  cap:REF   move a two-pad 0402 capacitor to B.Cu near x:y and connect it the same
            way.  The footprint is replaced by a bottom-side copy and populated.

The plan is a list of operations for apply_layout_ops.py.  Nothing is found by
luck: a site is accepted only when every pad has a route and every via passes the
all-layer clearance check; KiCad DRC is the acceptance test afterwards.
"""
from __future__ import annotations

import copy
import json
import math
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from shapely.geometry import Point, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import local_router as LR  # noqa: E402

W = 0.25
LED_PAD = 0.55
LED_OFF = 0.475
# pad pattern of a bottom-mounted SK6805-EC15 seen from the top (x right, y down), in its four rotations
LED_BASE = {"1": (1, 1), "2": (-1, 1), "3": (-1, -1), "4": (1, -1)}


def snapshot(L):
    return ({k: list(v) for k, v in L.cu.items()}, list(L.via_holes), list(L.inner), list(L.smd))


def restore(L, s):
    L.cu = {k: list(v) for k, v in s[0].items()}
    L.via_holes, L.inner, L.smd = list(s[1]), list(s[2]), list(s[3])


def bottom_free(L, court, pads_geom):
    for ref, c in L.courts["B.Cu"].items():
        if c.distance(court) < 0.15:
            return False
    near = [c for c in L.cu["B.Cu"] if LR.R.near_box(c[0], court.centroid.x, court.centroid.y, 3.0)]
    for g in pads_geom:
        if any(c[0].distance(g) < LR.CLEARANCE for c in near):
            return False
        if any(h.distance(g) < LR.HOLE_CLEARANCE for h in L.pad_holes + L.via_holes if LR.R.near_box(h, court.centroid.x, court.centroid.y, 4.0)):
            return False
    return L.outline.buffer(-LR.EDGE_CLEARANCE).contains(court)


def connect(L, ref, pads, nets, radius):
    """pads: {num: (x, y, sx, sy)}; returns (vias, tracks) or None."""
    vias, tracks = [], []
    geoms = {}
    for num, (x, y, sx, sy) in pads.items():
        geoms[num] = L.add_pad("B.Cu", ref, num, nets[num], x, y, sx, sy)
    order = sorted(pads, key=lambda q: (nets[q] == "GND", q))
    for num in order:
        net = nets[num]
        x, y = pads[num][0], pads[num][1]

        def run():
            return L.route("B.Cu", (x, y), net, width=W, half=radius + 3.0,
                           goal_filter=lambda c, n=num: not (c[2] == "pad" and c[3][0] == ref and c[3][1] == n))

        if net == "GND":
            v = L.via_near("GND", (x, y), radii=(0.9, 1.1, 1.3, 1.6, 2.0, 2.5), own_ref=ref)
            if v is None:
                return None
            vias.append(L.add_via(v[0], v[1], net))
            r = run()
        elif any(c[1] == net and c[2] in ("track", "via") and LR.R.near_box(c[0], x, y, radius) for c in L.cu["B.Cu"]):
            r = run()
        else:
            # a via on one of the net's F.Cu tracks; the nearest one may sit in a pocket on B.Cu, so try several
            r = None
            for v in L.via_candidates(net, "F.Cu", (x, y), radius=radius, own_ref=ref):
                keep = snapshot(L)
                rec = L.add_via(v[0], v[1], net)
                r = run()
                if r is not None:
                    vias.append(rec)
                    break
                restore(L, keep)
        if r is None:
            return None
        tracks += r
    return vias, tracks


def plan_led(L, ref, centre, search=9.0):
    f = L.fps[ref]
    nets = {p["num"]: p["net"] for p in f["pads"]}
    cx, cy = centre if centre else (f["x"], f["y"])
    cands = []
    steps = int(search / 0.5)
    for iy in range(-steps, steps + 1):
        for ix in range(-steps, steps + 1):
            x, y = round(cx + ix * 0.5, 4), round(cy + iy * 0.5, 4)
            d = math.hypot(x - cx, y - cy)
            if d <= search:
                for turn in range(4):
                    cands.append((d, x, y, turn))
    cands.sort()
    base = snapshot(L)
    tried = 0
    for d, x, y, turn in cands:
        offs = dict(LED_BASE)
        for _ in range(turn):
            offs = {k: (v[1], -v[0]) for k, v in offs.items()}
        pads = {k: (round(x + v[0] * LED_OFF, 4), round(y + v[1] * LED_OFF, 4), LED_PAD, LED_PAD) for k, v in offs.items()}
        court = box(x - 1.0, y - 1.0, x + 1.0, y + 1.0)
        geom = [box(px - sx / 2, py - sy / 2, px + sx / 2, py + sy / 2) for px, py, sx, sy in pads.values()]
        if not bottom_free(L, court, geom):
            continue
        tried += 1
        if tried > 60:
            break
        got = connect(L, ref, pads, nets, radius=9.0)
        if got is None:
            restore(L, base)
            continue
        L.courts["B.Cu"][ref + "_ALT"] = court
        vias, tracks = got
        return {"ref": ref, "site": [x, y], "turn": turn, "pads": pads, "vias": vias, "tracks": tracks}
    return None


def plan_cap(L, ref, centre, search=4.0):
    f = L.fps[ref]
    nets = {p["num"]: p["net"] for p in f["pads"]}
    cx, cy = centre
    cands = []
    steps = int(search / 0.25)
    for iy in range(-steps, steps + 1):
        for ix in range(-steps, steps + 1):
            x, y = round(cx + ix * 0.25, 4), round(cy + iy * 0.25, 4)
            d = math.hypot(x - cx, y - cy)
            if d <= search:
                for rot in (0, 90):
                    cands.append((d, x, y, rot))
    cands.sort()
    base = snapshot(L)
    tried = 0
    for d, x, y, rot in cands:
        # KiCad C_0402 flipped to the bottom, rotation 0: pad 1 at -x; rotation 90: pad 1 at +y
        o = {"1": (-0.48, 0.0), "2": (0.48, 0.0)} if rot == 0 else {"1": (0.0, 0.48), "2": (0.0, -0.48)}
        sx, sy = (0.56, 0.62) if rot == 0 else (0.62, 0.56)
        pads = {k: (round(x + v[0], 4), round(y + v[1], 4), sx, sy) for k, v in o.items()}
        court = box(x - 0.93, y - 0.47, x + 0.93, y + 0.47) if rot == 0 else box(x - 0.47, y - 0.93, x + 0.47, y + 0.93)
        geom = [box(px - a / 2, py - b / 2, px + a / 2, py + b / 2) for px, py, a, b in pads.values()]
        if not bottom_free(L, court, geom):
            continue
        tried += 1
        if tried > 60:
            break
        got = connect(L, ref, pads, nets, radius=6.0)
        if got is None:
            restore(L, base)
            continue
        L.courts["B.Cu"][ref] = court
        vias, tracks = got
        return {"ref": ref, "site": [x, y], "rot": rot, "pads": pads, "vias": vias, "tracks": tracks, "nets": nets}
    return None


def main():
    d = json.load(open(sys.argv[1]))
    L = LR.Layout(d)
    ops, report = [], []
    for spec in sys.argv[3:]:
        kind, rest = spec.split(":", 1)
        ref, _, at = rest.partition("@")
        centre = tuple(float(v) for v in at.split(":")) if at else None
        if kind == "led":
            r = plan_led(L, ref, centre)
            if r is None:
                report.append({"ref": ref, "error": "no bottom site found"})
                continue
            ops.append({"op": "add_vias", "vias": [{"x": v["x"], "y": v["y"], "net": v["net"]} for v in r["vias"]]})
            ops.append({"op": "add_pads", "ref": ref, "pads": [{"num": k, "like": k, "side": "B.Cu", "x": p[0], "y": p[1], "sx": p[2], "sy": p[3]} for k, p in sorted(r["pads"].items())]})
            ops.append({"op": "add_tracks", "tracks": r["tracks"]})
        else:
            L.remove_ref(ref)
            r = plan_cap(L, ref, centre)
            if r is None:
                report.append({"ref": ref, "error": "no bottom site found"})
                continue
            ops.append({"op": "add_vias", "vias": [{"x": v["x"], "y": v["y"], "net": v["net"]} for v in r["vias"]]})
            ops.append({"op": "replace_footprint", "ref": ref, "lib_dir": "/usr/share/kicad/footprints/Capacitor_SMD.pretty", "name": "C_0402_1005Metric",
                        "fpid": "Capacitor_SMD:C_0402_1005Metric", "side": "B.Cu", "x": r["site"][0], "y": r["site"][1], "rot": r["rot"], "value": L.fps[ref]["value"],
                        "pad_nets": r["nets"], "expect_pads": {k: [p[0], p[1]] for k, p in r["pads"].items()}})
            ops.append({"op": "set_dnp", "ref": ref, "dnp": False})
            ops.append({"op": "add_tracks", "tracks": r["tracks"]})
        report.append({"ref": ref, "site": r["site"], "vias": len(r["vias"]), "tracks": len(r["tracks"])})
        print(report[-1])
    json.dump({"report": report, "ops": ops}, open(sys.argv[2], "w"), indent=1)
    return 1 if any("error" in r for r in report) else 0


if __name__ == "__main__":
    sys.exit(main())
