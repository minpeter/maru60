#!/usr/bin/env python3
"""Plan a series damping resistor at the source of a long underglow LED data hop.

usage: plan_series_resistor.py BOARD.json OPS.json [REF LED NET]
       (default: R115 LED68 UG_LED_6; the second one is R116 LED71 UG_LED_9)

UG_LED_6 runs 276 mm from LED68 DOUT to LED69 DIN and UG_LED_9 105 mm from
LED71 DOUT to LED72 DIN.  If the SK6805 output is fast and strong (its data
sheet does not say), reflections on such an unterminated line re-cross the
input threshold.  A 100 ohm 0402 on B.Cu goes in series next to the driving
LED: its DOUT pad gets its own net NET_SRC, the rest of the hop keeps NET.
"""
import json
import math
import sys
import uuid

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from shapely.geometry import box  # noqa: E402

import local_router as LR  # noqa: E402
import plan_bottom_sites as PB  # noqa: E402

CORE_SHEET = "0940d797-79a6-569a-9535-d8f19961ba0b"
WIDTH = 0.15            # the hop's own track width


def main():
    d = json.load(open(sys.argv[1]))
    REF, LED, NET = sys.argv[3:6] if len(sys.argv) >= 6 else ("R115", "LED68", "UG_LED_6")
    SRC = NET + "_SRC"
    SYMBOL_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, f"maru60/order-candidate/{REF}"))
    L = LR.Layout(d)
    led = L.fps[LED]
    p3 = next(p for p in led["pads"] if p["num"] == "3")
    # the B.Cu tracks from the LED's DOUT pad up to the first via of the hop
    # the B.Cu route of the hop from the DOUT pad to its first via, in order
    tracks = [c[3] for c in L.cu["B.Cu"] if c[2] == "track" and c[1] == NET]
    ends = lambda t: ((t["x1"], t["y1"]), (t["x2"], t["y2"]))
    on_pad = lambda q: abs(q[0] - p3["x"]) <= p3["sx"] / 2 + 1e-3 and abs(q[1] - p3["y"]) <= p3["sy"] / 2 + 1e-3
    stubs = [t for t in tracks if all(on_pad(q) for q in ends(t))]          # short pieces that lie on the pad
    path, cur = [], None
    first = [t for t in tracks if t not in stubs and any(on_pad(q) or any(math.hypot(q[0] - e[0], q[1] - e[1]) < 2e-3 for u in stubs for e in ends(u)) for q in ends(t))]
    if len(first) != 1:
        print(f"{len(first)} tracks leave {LED}.3; expected one")
        return 1
    t = first[0]
    a, b = ends(t)
    cur = b if (on_pad(a) or any(math.hypot(a[0] - e[0], a[1] - e[1]) < 2e-3 for u in stubs for e in ends(u))) else a
    path.append((t, cur))
    is_via = lambda q: any(c[2] == "via" and c[1] == NET and math.hypot(c[3]["x"] - q[0], c[3]["y"] - q[1]) < 0.06 for c in L.cu["B.Cu"])
    while not is_via(cur):
        nxt = [u for u in tracks if u not in stubs and all(u is not v for v, _ in path) and any(math.hypot(q[0] - cur[0], q[1] - cur[1]) < 2e-3 for q in ends(u))]
        if len(nxt) != 1:
            break
        u = nxt[0]
        a, b = ends(u)
        cur = b if math.hypot(a[0] - cur[0], a[1] - cur[1]) < 2e-3 else a
        path.append((u, cur))
    for c in L.cu["B.Cu"]:
        if c[2] == "pad" and c[3][0] == LED and c[3][1] == "3":
            c[1] = SRC
    nets = {"1": SRC, "2": NET}
    offs = {0: {"1": (-0.51, 0.0), "2": (0.51, 0.0)}, 90: {"1": (0.0, 0.51), "2": (0.0, -0.51)},
            180: {"1": (0.51, 0.0), "2": (-0.51, 0.0)}, 270: {"1": (0.0, -0.51), "2": (0.0, 0.51)}}
    # Cut the route after its k-th segment: the first k segments (and the pieces on the pad) are removed,
    # the rest keeps NET.  The resistor goes within 2.5 mm of the cut.
    for k in range(1, len(path) + 1):
        removed = stubs + [t for t, _ in path[:k]]
        cut = path[k - 1][1]
        base = PB.snapshot(L)
        for t in removed:
            L.remove_track(t)
        mid = PB.snapshot(L)
        cands = sorted((math.hypot(ix * 0.125, iy * 0.125) + rot * 1e-5, round(round((cut[0] + ix * 0.125) / 0.0125) * 0.0125, 4), round(round((cut[1] + iy * 0.125) / 0.0125) * 0.0125, 4), rot)
                       for ix in range(-20, 21) for iy in range(-20, 21) for rot in (0, 90, 180, 270))
        for dist, x, y, rot in cands:
            # KiCad R_0402_1005Metric: pads 0.54 x 0.64 mm at +/-0.51 mm
            o = offs[rot]
            sx, sy = (0.54, 0.64) if rot in (0, 180) else (0.64, 0.54)
            pads = {n: (round(x + v[0], 4), round(y + v[1], 4), sx, sy) for n, v in o.items()}
            court = box(x - 0.93, y - 0.47, x + 0.93, y + 0.47) if rot in (0, 180) else box(x - 0.47, y - 0.93, x + 0.47, y + 0.93)
            geom = [box(px - a / 2, py - b / 2, px + a / 2, py + b / 2) for px, py, a, b in pads.values()]
            if not PB.bottom_free(L, court, geom):
                continue
            for n, (px, py, a, b) in pads.items():
                L.add_pad("B.Cu", REF, n, nets[n], px, py, a, b)
            r1 = L.route("B.Cu", pads["1"][:2], SRC, width=WIDTH, half=5.0, goal_filter=lambda c: c[2] == "pad" and c[3][0] == LED)
            r2 = L.route("B.Cu", pads["2"][:2], NET, width=WIDTH, half=5.0, goal_filter=lambda c: not (c[2] == "pad" and c[3][0] == REF)) if r1 is not None else None
            if r1 is None or r2 is None:
                PB.restore(L, mid)
                continue
            # what is left of the old route between the cut and the point where the new track joins it would dangle
            joins = [q for t in r2 for q in ((t["x1"], t["y1"]), (t["x2"], t["y2"]))]
            start = cut
            for t, end in path[k:]:
                if any(math.hypot(q[0] - start[0], q[1] - start[1]) < 2e-3 for q in joins):
                    break
                removed.append(t)
                start = end
            ops = [
                {"op": "remove_tracks", "tracks": [{f: t[f] for f in ("x1", "y1", "x2", "y2", "layer", "net")} for t in removed]},
                {"op": "set_pad_net", "ref": LED, "pad": "3", "net": SRC},
                {"op": "add_footprint", "ref": REF, "lib_dir": "/usr/share/kicad/footprints/Resistor_SMD.pretty", "name": "R_0402_1005Metric",
                 "fpid": "Resistor_SMD:R_0402_1005Metric", "side": "B.Cu", "x": x, "y": y, "rot": rot, "value": "100 1%", "pad_nets": nets,
                 "path": f"/{CORE_SHEET}/{SYMBOL_UUID}", "sheetname": "/Core/", "sheetfile": "maru60-core.kicad_sch",
                 "expect_pads": {n: [v[0], v[1]] for n, v in pads.items()}},
                {"op": "add_tracks", "tracks": r1 + r2},
            ]
            json.dump({"note": f"{REF} 100 ohm in series at the source of the underglow data hop {NET} ({LED} DOUT).", "symbol_uuid": SYMBOL_UUID, "ops": ops},
                      open(sys.argv[2], "w"), indent=1)
            print(f"{REF} at ({x}, {y}) rot {rot}; removed {len(removed)} tracks, added {len(r1) + len(r2)}")
            return 0
        PB.restore(L, base)
    print("no site found")
    return 1


if __name__ == "__main__":
    sys.exit(main())
