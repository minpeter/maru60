#!/usr/bin/env python3
"""Plan a new 0402 two-pad part on the bottom side beside an existing part.

usage: plan_two_pad_part.py BOARD.json OPS.json REF VALUE NET1 NET2 NEAR_REF SHEET_PATH SHEETNAME SHEETFILE [RADIUS]

Used for C143, the feed-forward capacitor across the buck's top feedback
resistor R159 (+4V_REG to BUCK_FB).  Sites on a 0.125 mm grid within RADIUS
(default 3 mm) of NEAR_REF are tried nearest first, in four rotations; a site
must be clear of every bottom-side courtyard and copper (plan_bottom_sites),
and each pad must reach copper of its net on B.Cu.  The pad on a net other
than GND and the supply rails is routed first and kept short.  Output is an
operation list for apply_layout_ops.py; KiCad DRC is the judge.
"""
import json
import math
import sys
import uuid

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from shapely.geometry import box  # noqa: E402

import local_router as LR  # noqa: E402
import plan_bottom_sites as PB  # noqa: E402

OFFS = {0: {"1": (-0.48, 0.0), "2": (0.48, 0.0)}, 90: {"1": (0.0, 0.48), "2": (0.0, -0.48)},
        180: {"1": (0.48, 0.0), "2": (-0.48, 0.0)}, 270: {"1": (0.0, -0.48), "2": (0.0, 0.48)}}    # KiCad C_0402_1005Metric: pads 0.56 x 0.62 mm


def main():
    d = json.load(open(sys.argv[1]))
    ref, value, net1, net2, near_ref, sheet, sheetname, sheetfile = sys.argv[3:11]
    radius = float(sys.argv[11]) if len(sys.argv) > 11 else 3.0
    sym = str(uuid.uuid5(uuid.NAMESPACE_URL, f"maru60/order-candidate/{ref}"))
    L = LR.Layout(d)
    nf = L.fps[near_ref]
    nets = {"1": net1, "2": net2}
    n = int(radius / 0.125)
    cands = sorted((math.hypot(ix, iy) * 0.125 + rot * 1e-5, round(nf["x"] + ix * 0.125, 4), round(nf["y"] + iy * 0.125, 4), rot)
                   for ix in range(-n, n + 1) for iy in range(-n, n + 1) for rot in (0, 90, 180, 270) if math.hypot(ix, iy) * 0.125 <= radius)
    base = PB.snapshot(L)
    tried = 0
    for dist, x, y, rot in cands:
        sx, sy = (0.56, 0.62) if rot in (0, 180) else (0.62, 0.56)
        pads = {k: (round(x + v[0], 4), round(y + v[1], 4), sx, sy) for k, v in OFFS[rot].items()}
        court = box(x - 0.91, y - 0.46, x + 0.91, y + 0.46) if rot in (0, 180) else box(x - 0.46, y - 0.91, x + 0.46, y + 0.91)
        geom = [box(px - a / 2, py - b / 2, px + a / 2, py + b / 2) for px, py, a, b in pads.values()]
        if not PB.bottom_free(L, court, geom):
            continue
        tried += 1
        for k, (px, py, a, b) in pads.items():
            L.add_pad("B.Cu", ref, k, nets[k], px, py, a, b)
        order = sorted(pads, key=lambda k: nets[k] in ("GND",) or nets[k].startswith("+"))       # the signal pad first
        routes, ok = [], True
        for k in order:
            r = L.route("B.Cu", pads[k][:2], nets[k], width=0.2, half=5.0, goal_filter=lambda c: not (c[2] == "pad" and c[3][0] == ref))
            if r is None:
                ok = False
                break
            routes += r
        sig = sum(math.hypot(t["x2"] - t["x1"], t["y2"] - t["y1"]) for t in routes if t["net"] == nets[order[0]])
        if not ok or sig > 3.0:
            PB.restore(L, base)
            continue
        ops = [{"op": "add_footprint", "ref": ref, "lib_dir": "/usr/share/kicad/footprints/Capacitor_SMD.pretty", "name": "C_0402_1005Metric",
                "fpid": "Capacitor_SMD:C_0402_1005Metric", "side": "B.Cu", "x": x, "y": y, "rot": rot, "value": value, "pad_nets": nets,
                "path": f"{sheet}/{sym}", "sheetname": sheetname, "sheetfile": sheetfile, "expect_pads": {k: [v[0], v[1]] for k, v in pads.items()}},
               {"op": "add_tracks", "tracks": routes}]
        json.dump({"note": f"{ref} {value} between {net1} and {net2}, beside {near_ref}.", "symbol_uuid": sym, "ops": ops}, open(sys.argv[2], "w"), indent=1)
        print(f"{ref} at ({x}, {y}) rot {rot}, {round(dist, 2)} mm from {near_ref}; {len(routes)} tracks, {round(sig, 2)} mm on {nets[order[0]]}; {tried} sites tried")
        return 0
    print("no site found")
    return 1


if __name__ == "__main__":
    sys.exit(main())
