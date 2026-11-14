#!/usr/bin/env python3
"""Connect relocated pads locally to surviving copper; native DRC is required.

This is an incremental plan, not a claim of whole-board connectivity. Existing
trace fragments across a new window may still need separate reconnection.
"""
import argparse
import json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
import local_router as LR
from plan_bottom_sites import snapshot, restore

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("geometry", type=Path)
ap.add_argument("design", type=Path)
ap.add_argument("output", type=Path)
a = ap.parse_args()
g = json.loads(a.geometry.read_text())
plan = json.loads((a.design/"bottom-assembly-plan.json").read_text())
refs = set(plan["relocate_top"]+plan["relocate_bottom"]) | {s["ref"] for s in plan["sites"]}
L = LR.Layout(g)
tracks, vias, report = [], [], []
tasks = [(f, pad) for f in g["fps"] if f["ref"] in refs for pad in f["pads"] if pad["num"] and not pad["net"].startswith("unconnected-")]
tasks.sort(key=lambda q: (q[1]["net"] != "GND", not q[1]["net"].startswith("+"), q[0]["ref"], q[1]["num"]))
def save():
    a.output.write_text(json.dumps({"status": "local routing plan; not whole-board acceptance",
                                   "ops": [{"op": "add_tracks", "tracks": tracks}, {"op": "add_vias", "vias": vias}],
                                   "report": report}, indent=2)+"\n")
for f, pad in tasks:
    net = pad["net"]
    start = (pad["x"], pad["y"])
    shape = unary_union([Polygon(o) for o in pad["poly"]])
    if any(c[1] == net and c[2] in ("track", "via") and c[0].intersects(shape) for c in L.cu["B.Cu"]):
        report.append({"ref": f["ref"], "pad": pad["num"], "at": start, "net": net, "status": "already-touches-copper"})
        continue
    width = .25 if net == "GND" or net.startswith(("+", "VBUS")) else .20
    def route():
        return L.route("B.Cu", start, net, width=width, half=8, grid=.10,
                       goal_filter=lambda c: c[2] == "via" if net == "GND" else c[2] in ("track", "via"))
    got = route()
    via = None
    if got is None:
        snap = snapshot(L)
        options = ([L.via_near(net, start, radii=(1.1, 1.4, 1.8, 2.2, 2.8, 3.5))] if net == "GND"
                   else L.via_candidates(net, "F.Cu", start, radius=8, limit=4, step=.3))
        for point in options:
            if point is None:
                continue
            v = L.add_via(*point, net)
            got = route()
            if got is not None:
                via = v
                break
            restore(L, snap)
    status = "routed" if got is not None else "needs-global-route"
    if got is not None:
        tracks += got
        if via:
            vias.append(via)
    report.append({"ref": f["ref"], "pad": pad["num"], "at": start, "net": net, "status": status})
    print(len(report), "/", len(tasks), f["ref"], pad["num"], net, status, flush=True)
    save()
save()
