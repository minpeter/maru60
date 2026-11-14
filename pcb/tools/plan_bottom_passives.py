#!/usr/bin/env python3
"""Place moved SMT parts on B.Cu while preserving fixed pads and LED apertures.

Produces placement operations only. Tracks are intentionally not treated as
fixed placements: intersecting copper is explicitly removed/rerouted later.
"""
import argparse
import json
import math
from pathlib import Path
from shapely.affinity import rotate, scale, translate
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree


def poly(rings):
    return unary_union([Polygon(r) for r in rings if len(r) >= 3])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("geometry", type=Path)
    ap.add_argument("plan", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    g, plan = json.loads(args.geometry.read_text()), json.loads(args.plan.read_text())
    fps = {f["ref"]: f for f in g["fps"]}
    refs = set(plan["relocate_top"]+plan["relocate_bottom"])
    material = unary_union([Polygon(o[0], o[1:]) for o in g["board_material"]])
    copper_region = material.buffer(-.52)
    courts, pads, holes = [], [], []
    for f in g["fps"]:
        if f["ref"] in refs:
            continue
        if f["layer"] == "B.Cu" and f["courtyard"]:
            courts.append(poly(f["courtyard"]))
        for p in f["pads"]:
            if "B.Cu" in p["layers"]:
                pads.append(poly(p["poly"]))
            if p["drill"][0]:
                holes.append(Point(p["x"], p["y"]).buffer(max(p["drill"])/2, 32))
    court_tree, pad_tree, hole_tree = STRtree(courts), STRtree(pads), STRtree(holes)
    critical = lambda n: n.startswith(("USB_", "QSPI_", "VREG_")) or n in ("XIN", "XOUT", "XTAL_OUT", "+1V1")
    protected = [(LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"]/2, 24), t["net"])
                 for t in g["tracks"] if t["layer"] == "B.Cu" and critical(t["net"])]
    protected += [(Point(v["x"], v["y"]).buffer(v["d"]/2, 32), v["net"]) for v in g["vias"] if critical(v["net"])]
    protected_tree = STRtree([q[0] for q in protected])
    added_courts, added_pads = [], []
    ops, report = [], []
    def ledcap(ref):
        return (ref.startswith("C") and 200 <= int(ref[1:]) <= 275
                and "LED"+str(int(ref[1:])-199) in fps)
    # Power / signal passives first; per-LED bypass parts use the remaining local space.
    order = sorted(refs, key=lambda r: (ledcap(r), -poly(fps[r]["courtyard"]).area, r))
    for ref in order:
        f = fps[ref]
        def canonical(g):
            g = translate(rotate(g, f["rot"], origin=(f["x"], f["y"])), -f["x"], -f["y"])
            return scale(g, yfact=-1, origin=(0, 0)) if f["layer"] == "F.Cu" else g
        localcourt = canonical(poly(f["courtyard"]))
        localpads = [canonical(poly(p["poly"])) for p in f["pads"]]
        anchors = [(f["x"], f["y"])]
        if ledcap(ref):
            ledref = "LED"+str(int(ref[1:])-199)
            led = fps[ledref]
            vdd = next(p for p in led["pads"] if p["num"] == "3")
            # Centroid of the current package may include an alternate site;
            # explicitly use the default site's VDD pad from the CAD plan.
            anchors = [(vdd["x"], vdd["y"]+2), (vdd["x"], vdd["y"]-2)]
        found = None
        options = {}
        radius = 24 if ref == "F1" else 12 if ref in ("C144", "R187") else 8
        step = .5 if radius > 8 else .25
        limit = round(radius/step)
        for ai, (cx, cy) in enumerate(anchors):
            for i in range(-limit, limit+1):
                for j in range(-limit, limit+1):
                    dist = math.hypot(i*step, j*step)
                    if dist <= radius:
                        x, y = round(cx+i*step, 6), round(cy+j*step, 6)
                        for angle in sorted({0, 90, 180, -90, f["rot"]}):
                            options[(x, y, angle)] = min(options.get((x, y, angle), (1e9,)), (dist, ai, abs(angle-f["rot"])))
        for (x, y, angle), score in sorted(options.items(), key=lambda q: q[1]):
            court = translate(rotate(localcourt, -angle, origin=(0, 0)), x, y)
            cp = court.buffer(.15)
            if any(cp.intersects(courts[i]) for i in court_tree.query(cp)) or any(cp.intersects(c) for c in added_courts):
                continue
            pp = [translate(rotate(g, -angle, origin=(0, 0)), x, y) for g in localpads]
            if not all(copper_region.contains(q) for q in pp):
                continue
            if any(q.buffer(.18).intersects(pads[i]) for q in pp for i in pad_tree.query(q.buffer(.18))):
                continue
            if any(q.buffer(.25).intersects(holes[i]) for q in pp for i in hole_tree.query(q.buffer(.25))):
                continue
            if any(q.distance(other) < .18 for q in pp for other in added_pads):
                continue
            if any(q.distance(protected[i][0]) < .18 for p, q in zip(f["pads"], pp)
                   for i in protected_tree.query(q.buffer(.18)) if p["net"] != protected[i][1]):
                continue
            found = (x, y, angle, court, pp)
            break
        if found is None:
            raise RuntimeError(f"No B.Cu site for {ref}; no CAD mutations have occurred")
        x, y, angle, court, pp = found
        added_courts.append(court)
        added_pads.extend(pp)
        ops.append({"op": "move_footprint", "ref": ref, "side": "B.Cu", "x": x, "y": y, "rot": angle})
        report.append({"ref": ref, "from": [f["x"], f["y"], f["layer"]], "to": [x, y, "B.Cu"], "rot": angle,
                       "pad_centers": [[p["num"], q.centroid.x, q.centroid.y] for p, q in zip(f["pads"], pp)]})
        print(ref, (round(x, 3), round(y, 3)), angle, flush=True)
    args.output.write_text(json.dumps({"status": "placement only; tracks must be repaired", "ops": ops, "report": report}, indent=2)+"\n")


if __name__ == "__main__":
    main()
