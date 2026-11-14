#!/usr/bin/env python3
"""Plan reverse-LED mechanical sites without changing a PCB or accepting routing.

Uses the exact old geometry as input. Fixed switch/connector/drilled features
remain obstacles. Small existing bottom components are reported for relocation.
The scan is not an optical or manufacturing qualification.
"""
import argparse
import gzip
import json
import math
from pathlib import Path

from shapely.affinity import rotate, translate
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

# C5149201 / SK6812MINI-E-012: physical pin functions, not legacy MINI-E numbering.
PIN_FUNCTION = {"1": "GND", "2": "DIN", "3": "VDD", "4": "DOUT"}
OLD_TO_NEW = {"1": "2", "2": "3", "3": "4", "4": "1"}
CUTOUT_WIDTH, CUTOUT_HEIGHT, CORNER = 4.0, 3.6, 0.5
PAD_X, PAD_Y, PAD_W, PAD_H = 3.2, 0.75, 1.8, 0.9


def poly(rings):
    return unary_union([Polygon(p) for p in rings if len(p) >= 3])


def transform(g, x, y, angle):
    return translate(rotate(g, angle, origin=(0, 0)), x, y)


def package(x, y, angle):
    opening = box(-CUTOUT_WIDTH/2+CORNER, -CUTOUT_HEIGHT/2+CORNER,
                  CUTOUT_WIDTH/2-CORNER, CUTOUT_HEIGHT/2-CORNER).buffer(CORNER, 32)
    # Mechanical envelope includes land toes and the body; rounded cutout is separate.
    court = box(-4.25, -2.05, 4.25, 2.05)
    pads = [box(sx*PAD_X-PAD_W/2, sy*PAD_Y-PAD_H/2,
                sx*PAD_X+PAD_W/2, sy*PAD_Y+PAD_H/2)
            for sx in (-1, 1) for sy in (-1, 1)]
    return [transform(s, x, y, angle) for s in (opening, court, unary_union(pads))]


def old_sites(f):
    # Group old 1.5 mm four-land clusters using pad 1 as an anchor.
    remaining = list(f["pads"])
    sites = []
    while remaining:
        first = remaining[0]
        group = [p for p in remaining if p["layers"][0] == first["layers"][0]
                 and math.dist((p["x"], p["y"]), (first["x"], first["y"])) < 1.5]
        if len(group) != 4 or {p["num"] for p in group} != {"1", "2", "3", "4"}:
            raise ValueError((f["ref"], "unexpected old LED sites", group))
        sites.append({"x": sum(p["x"] for p in group)/4,
                      "y": sum(p["y"] for p in group)/4,
                      "side": first["layers"][0]})
        remaining = [p for p in remaining if p not in group]
    return sorted(sites, key=lambda s: math.dist((s["x"], s["y"]), (f["x"], f["y"])))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("geometry", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--max-shift", type=float, default=0.5)
    args = ap.parse_args()
    raw = args.geometry.read_bytes()
    g = json.loads(gzip.decompress(raw) if args.geometry.suffix == ".gz" else raw)
    key_leds = [f for f in g["fps"] if f["ref"].startswith("LED")
                and any(p["net"].startswith("KEY_RGB") for p in f["pads"])]
    key_refs = {f["ref"] for f in key_leds}
    # All top SMT is being moved; bottom passives can be relocated if necessary.
    movable = {f["ref"] for f in g["fps"] if f["layer"] == "F.Cu"
               and any(p["drill"][0] == 0 and p["num"] for p in f["pads"])} | key_refs
    small_bottom = {f["ref"] for f in g["fps"] if f["ref"].startswith(("C", "R", "D"))}
    obstacles, labels, fixed = [], [], []
    for f in g["fps"]:
        if f["ref"] in movable:
            continue
        # Holes and through lands cannot be sacrificed, even on movable parts.
        for p in f["pads"]:
            if p["drill"][0] or any(l.endswith(".Cu") for l in p["layers"]):
                shape = poly(p["poly"])
                if p["drill"][0]:
                    shape = shape.union(Point(p["x"], p["y"]).buffer(max(p["drill"])/2, 32))
                obstacles.append(shape); labels.append((f["ref"], "pad", p["num"]))
                fixed.append(f["ref"] not in small_bottom or bool(p["drill"][0]))
        if f["layer"] == "B.Cu" and f.get("courtyard"):
            obstacles.append(poly(f["courtyard"])); labels.append((f["ref"], "courtyard", ""))
            fixed.append(f["ref"] not in small_bottom)
    tree = STRtree(obstacles)
    xs = [e[k] for e in g["edges"] for k in ("x1", "x2")]
    ys = [e[k] for e in g["edges"] for k in ("y1", "y2")]
    outline = box(min(xs), min(ys), max(xs), max(ys))
    accepted = []
    results = []
    for f in sorted(key_leds, key=lambda f: int(f["ref"][3:])):
        for index, site in enumerate(old_sites(f)):
            # Bottom relay sites do not need a window; changing them needlessly
            # would create a new hole outside a switch's optical opening.
            if site["side"] == "B.Cu":
                results.append({"ref": f["ref"], "site_index": index,
                                "original": site, "status": "existing-bottom-relay"})
                continue
            candidates = []
            offsets = [n*0.25 for n in range(-int(args.max_shift/0.25), int(args.max_shift/0.25)+1)]
            for dx in offsets:
                for dy in offsets:
                    for angle in (0, 90, 45, 135):
                        x, y = site["x"]+dx, site["y"]+dy
                        opening, court, pads = package(x, y, angle)
                        hard, move = set(), set()
                        if not outline.buffer(-0.6).contains(court):
                            hard.add("board-edge")
                        region = court.buffer(0.15).union(opening.buffer(0.5))
                        for i in tree.query(region):
                            ref, kind, num = labels[i]
                            probe = court.buffer(0.15) if kind == "courtyard" else pads.buffer(0.18).union(opening.buffer(0.5))
                            if probe.intersects(obstacles[i]):
                                (hard if fixed[i] else move).add(ref)
                        for old_ref, old_court in accepted:
                            if court.buffer(0.15).intersects(old_court):
                                hard.add(old_ref)
                        candidates.append((len(hard), len(move), math.hypot(dx, dy), angle,
                                           x, y, sorted(hard), sorted(move), court))
            # Prefer the optical center over avoiding a movable passive.
            best = min(candidates, key=lambda c: (c[0], c[2], c[1], c[3]))
            nh, nm, offset, angle, x, y, hard, move, court = best
            row = {"ref": f["ref"], "site_index": index, "original": site,
                   "status": "placement-candidate" if not hard else "mechanically-blocked",
                   "center_mm": [x, y], "axis_degrees": angle,
                   "center_shift_mm": offset, "fixed_conflicts": hard,
                   "relocate_passives": move}
            results.append(row)
            if not hard:
                accepted.append((f["ref"]+":"+str(index), court))
    data = {"package": "SK6812MINI-E-012 / C5149201; procurement revision must match pinned datasheet",
            "cutout_mm": [CUTOUT_WIDTH, CUTOUT_HEIGHT], "corner_radius_mm": CORNER,
            "pads_mm": {"center_x": PAD_X, "center_y": PAD_Y, "width": PAD_W, "height": PAD_H},
            "limitations": ["Mechanical screening only, not a routed PCB or optical qualification.",
                            "Pad lands intentionally move outwards for 0.3 mm cutout clearance; assembly approval remains necessary.",
                            "Cutout machining profile tolerance and lead overlap need fabrication review.",
                            "Switch centers, drilled patterns, connectors and ICs are treated as fixed.",
                            f"Only +/-{args.max_shift} mm center offsets are searched; nonzero offsets require optical verification."],
            "sites": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2)+"\n")
    from collections import Counter
    print(Counter(r["status"] for r in results))
    for row in results:
        if row["status"] == "mechanically-blocked":
            print(row["ref"], row["site_index"], row["fixed_conflicts"])


if __name__ == "__main__":
    main()
