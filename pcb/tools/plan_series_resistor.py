#!/usr/bin/env python3
"""Plan a series damping resistor at the source of the long underglow LED data hop.

usage: plan_series_resistor.py BOARD.json OPS.json

UG_LED_6 runs 276 mm from LED68 DOUT to LED69 DIN.  If the SK6805 output is fast
and strong (its data sheet does not say), reflections on that unterminated line
re-cross the input threshold.  R115 (100 ohm, 0402, B.Cu) goes in series next to
LED68: LED68.3 gets its own net UG_LED_6_SRC, the rest of the hop keeps UG_LED_6.
"""
import json
import math
import sys
import uuid

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from shapely.geometry import box  # noqa: E402

import local_router as LR  # noqa: E402
import plan_bottom_sites as PB  # noqa: E402

SYMBOL_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, "maru60/order-candidate/R115"))
CORE_SHEET = "0940d797-79a6-569a-9535-d8f19961ba0b"


def main():
    d = json.load(open(sys.argv[1]))
    L = LR.Layout(d)
    led = L.fps["LED68"]
    p3 = next(p for p in led["pads"] if p["num"] == "3")
    # the B.Cu tracks from LED68.3 up to the first via of the hop
    chain, cur = [], (p3["x"], p3["y"])
    tracks = [c[3] for c in L.cu["B.Cu"] if c[2] == "track" and c[1] == "UG_LED_6"]
    while True:
        nxt = [t for t in tracks if t not in chain and (math.hypot(t["x1"] - cur[0], t["y1"] - cur[1]) < 2e-3 or math.hypot(t["x2"] - cur[0], t["y2"] - cur[1]) < 2e-3)]
        if len(nxt) != 1:
            break
        t = nxt[0]
        chain.append(t)
        cur = (t["x2"], t["y2"]) if math.hypot(t["x1"] - cur[0], t["y1"] - cur[1]) < 2e-3 else (t["x1"], t["y1"])
        if any(c[2] == "via" and c[1] == "UG_LED_6" and math.hypot(c[3]["x"] - cur[0], c[3]["y"] - cur[1]) < 0.06 for c in L.cu["B.Cu"]):
            break
    for t in chain:
        L.remove_track(t)
    for c in L.cu["B.Cu"]:
        if c[2] == "pad" and c[3][0] == "LED68" and c[3][1] == "3":
            c[1] = "UG_LED_6_SRC"
    nets = {"1": "UG_LED_6_SRC", "2": "UG_LED_6"}
    cx, cy = (p3["x"] + cur[0]) / 2, (p3["y"] + cur[1]) / 2
    cands = sorted((math.hypot(ix * 0.25, iy * 0.25) + (0.01 if rot else 0), round(cx + ix * 0.25, 4), round(cy + iy * 0.25, 4), rot)
                   for ix in range(-12, 13) for iy in range(-12, 13) for rot in (0, 90))
    base = PB.snapshot(L)
    for dist, x, y, rot in cands:
        # KiCad R_0402_1005Metric: pads 0.54 x 0.64 mm at +/-0.51 mm
        o = {"1": (-0.51, 0.0), "2": (0.51, 0.0)} if rot == 0 else {"1": (0.0, 0.51), "2": (0.0, -0.51)}
        sx, sy = (0.54, 0.64) if rot == 0 else (0.64, 0.54)
        pads = {k: (round(x + v[0], 4), round(y + v[1], 4), sx, sy) for k, v in o.items()}
        court = box(x - 0.93, y - 0.47, x + 0.93, y + 0.47) if rot == 0 else box(x - 0.47, y - 0.93, x + 0.47, y + 0.93)
        geom = [box(px - a / 2, py - b / 2, px + a / 2, py + b / 2) for px, py, a, b in pads.values()]
        if not PB.bottom_free(L, court, geom):
            continue
        for k, (px, py, a, b) in pads.items():
            L.add_pad("B.Cu", "R115", k, nets[k], px, py, a, b)
        r1 = L.route("B.Cu", pads["1"][:2], "UG_LED_6_SRC", width=0.2, half=6.0, goal_filter=lambda c: c[2] == "pad" and c[3][0] == "LED68")
        r2 = L.route("B.Cu", pads["2"][:2], "UG_LED_6", width=0.2, half=6.0, goal_filter=lambda c: not (c[2] == "pad" and c[3][0] == "R115")) if r1 is not None else None
        if r1 is None or r2 is None:
            PB.restore(L, base)
            continue
        ops = [
            {"op": "remove_tracks", "tracks": [{k: t[k] for k in ("x1", "y1", "x2", "y2", "layer", "net")} for t in chain]},
            {"op": "set_pad_net", "ref": "LED68", "pad": "3", "net": "UG_LED_6_SRC"},
            {"op": "add_footprint", "ref": "R115", "lib_dir": "/usr/share/kicad/footprints/Resistor_SMD.pretty", "name": "R_0402_1005Metric",
             "fpid": "Resistor_SMD:R_0402_1005Metric", "side": "B.Cu", "x": x, "y": y, "rot": rot, "value": "100 1%", "pad_nets": nets,
             "path": f"/{CORE_SHEET}/{SYMBOL_UUID}", "sheetname": "/Core/", "sheetfile": "maru60-core.kicad_sch",
             "expect_pads": {k: [v[0], v[1]] for k, v in pads.items()}},
            {"op": "add_tracks", "tracks": r1 + r2},
        ]
        json.dump({"note": "R115 100 ohm in series at the source of the 276 mm underglow data hop (LED68 DOUT -> LED69 DIN).", "symbol_uuid": SYMBOL_UUID, "ops": ops},
                  open(sys.argv[2], "w"), indent=1)
        print(f"R115 at ({x}, {y}) rot {rot}; removed {len(chain)} tracks, added {len(r1) + len(r2)}")
        return 0
    print("no site found")
    return 1


if __name__ == "__main__":
    sys.exit(main())
