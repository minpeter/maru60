#!/usr/bin/env python3
"""Plan the replacement of U2 (MAX38902A, TDFN-8, no JLCPCB stock) by an AP2112K-3.3 in SOT-23-5.

usage: plan_ldo_swap.py BOARD.json OPS.json

The TDFN and its bypass capacitor C142, its minimum-load resistor R163 and its output-sense jumper (the
AP2112K has no BYP or sense pin and needs no minimum load) are removed
with the B.Cu tracks that only served them; a SOT-23-5 goes in the same place
with IN/GND/EN toward C100 and OUT toward C101, and is routed on B.Cu.
"""
import json
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from shapely.geometry import Polygon  # noqa: E402

import local_router as LR  # noqa: E402

X, Y = 142.0, 74.70      # 0.30 mm north of the TDFN centre: pad 3 clears the GND bar at y = 76.4, pad 1 the +3V3 track above
PADS = {"1": (1.1375, -0.95, "+4V_REG"), "2": (1.1375, 0.0, "GND"), "3": (1.1375, 0.95, "+4V_REG"), "5": (-1.1375, -0.95, "+3V3")}
NC = {"4": (-1.1375, 0.95)}
SX, SY = 1.325, 0.6
W = 0.3


def main():
    d = json.load(open(sys.argv[1]))
    L = LR.Layout(d)
    # U2: every track that ends in one of its pads goes.  The LDO_BYP net disappears altogether.
    old = [Polygon(pl) for p in L.fps["U2"]["pads"] for pl in p["poly"] if len(pl) >= 3]
    doomed = L.tracks_touching("B.Cu", old) + [c[3] for c in L.cu["B.Cu"] if c[2] == "track" and c[1] == "LDO_BYP"]
    doomed = [t for i, t in enumerate(doomed) if not any(t is u for u in doomed[:i])]
    seeds = []
    for t in doomed:
        L.remove_track(t)
        seeds += [(t["x1"], t["y1"]), (t["x2"], t["y2"])]
    # C142 / R163: their pads may be the only bridge between tracks that end inside them
    bridges = []
    for ref in ("C142", "R163"):
        for p in L.fps[ref]["pads"]:
            pg = Polygon(p["poly"][0])
            ends = sorted({(round(e[0], 4), round(e[1], 4)) for t in L.tracks_touching("B.Cu", [pg], nets=[p["net"]])
                           for e in ((t["x1"], t["y1"]), (t["x2"], t["y2"])) if pg.distance(LR.Point(e)) < 1e-3})
            seeds.append((p["x"], p["y"]))
            seeds += ends
            if len(ends) >= 2:
                for ex, ey in ends:
                    if abs(ex - p["x"]) + abs(ey - p["y"]) > 1e-4:
                        bt = {"x1": ex, "y1": ey, "x2": p["x"], "y2": p["y"], "w": 0.15, "layer": "B.Cu", "net": p["net"]}
                        bridges.append(bt)
                        L.add_track(bt)
    for ref in ("U2", "C142", "R163"):
        L.remove_ref(ref)
    # the MAX38902 OUTS Kelvin sense: C101.1 -> via -> In2.Cu -> via -> old pin 6
    sense_vias = [{"x": 138.3, "y": 74.45, "net": "+3V3"}, {"x": 140.25, "y": 76.05, "net": "+3V3"}]
    sense_tracks = [t for t in d["tracks"] if t["net"] == "+3V3" and (
        (t["layer"] == "In2.Cu" and min(t["x1"], t["x2"]) > 138.0 and max(t["x1"], t["x2"]) < 140.5 and min(t["y1"], t["y2"]) > 74.0 and max(t["y1"], t["y2"]) < 76.3)
        or (t["layer"] == "B.Cu" and abs(t["x1"] - 138.3) < 1e-3 and abs(t["x2"] - 138.3) < 1e-3 and {round(t["y1"], 2), round(t["y2"], 2)} == {74.45, 73.55}))]
    assert len(sense_tracks) == 3, sense_tracks
    for t in sense_tracks:
        if t["layer"] == "B.Cu":
            hit = [c[3] for c in L.cu["B.Cu"] if c[2] == "track" and c[3] == t]
            for h in hit:
                L.remove_track(h)
    for v in sense_vias:
        for layer in LR.OUTER:
            L.cu[layer] = [c for c in L.cu[layer] if not (c[2] == "via" and abs(c[3]["x"] - v["x"]) < 1e-3 and abs(c[3]["y"] - v["y"]) < 1e-3)]
    pruned = L.prune_stubs("B.Cu", seeds)
    bridges = [t for t in bridges if not any(t is u for u in pruned)]
    doomed += [t for t in pruned if not any(t is u for u in bridges) and "w" in t and t in d["tracks"]]
    geoms = {}
    for num, (dx, dy, net) in PADS.items():
        geoms[num] = L.add_pad("B.Cu", "U2", num, net, X + dx, Y + dy, SX, SY)
    nc = L.add_pad("B.Cu", "U2", "4", "", X + NC["4"][0], Y + NC["4"][1], SX, SY)
    tracks = []
    for num in ("1", "5", "3", "2"):     # EN first: it passes under the body to VIN; GND then leaves toward C100
        dx, dy, net = PADS[num]
        # leave from the inner end of the pad for EN so it can pass under the body
        start = (X + dx, Y + dy)
        r = L.route("B.Cu", start, net, width=W, half=8.0, goal_filter=lambda c, n=num: not (c[2] == "pad" and c[3][0] == "U2" and c[3][1] == n))
        if r is None:
            raise SystemExit(f"U2 pad {num} ({net}): no route")
        tracks += r
    ops = [
        {"op": "remove_tracks", "tracks": [{k: t[k] for k in ("x1", "y1", "x2", "y2", "layer", "net")} for t in doomed + sense_tracks]},
        {"op": "remove_vias", "vias": sense_vias},
        {"op": "remove_footprint", "ref": "C142"},
        {"op": "remove_footprint", "ref": "R163"},
        {"op": "replace_footprint", "ref": "U2", "lib_dir": "/workspace/pcb/experiments/resume-20261111-order-candidate/pcb/Maru60.pretty", "name": "SOT-23-5_TightCourtyard",
         "fpid": "Maru60:SOT-23-5_TightCourtyard", "side": "B.Cu", "x": X, "y": Y, "rot": 180, "value": "AP2112K-3.3TRG1",
         "pad_nets": {**{n: v[2] for n, v in PADS.items()}, "4": "unconnected-(U2-NC-Pad4)"},
         "expect_pads": {**{n: [X + v[0], Y + v[1]] for n, v in PADS.items()}, "4": [X + NC["4"][0], Y + NC["4"][1]]}},
        {"op": "add_tracks", "tracks": bridges + tracks},
    ]
    json.dump({"note": "U2 MAX38902AATA+T (TDFN-8) -> AP2112K-3.3TRG1 (SOT-23-5); C142, R163 and the OUTS sense jumper removed.", "ops": ops}, open(sys.argv[2], "w"), indent=1)
    print(f"removed {len(doomed)} tracks, added {len(tracks)}")


if __name__ == "__main__":
    main()
