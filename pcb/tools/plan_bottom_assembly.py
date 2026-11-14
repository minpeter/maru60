#!/usr/bin/env python3
"""Mechanical placement for the reverse-LED experiment; no routing acceptance.

Preserves every switch, stabilizer, connector and IC location. Off-window LEDs
are explicitly identified. Run with the repository virtualenv (Shapely 2).
"""
import argparse
import gzip
import json
import math
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Point, box
from shapely.strtree import STRtree

from plan_reverse_led_placement import old_sites, package, poly


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("geometry", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    raw = args.geometry.read_bytes()
    g = json.loads(gzip.decompress(raw) if args.geometry.suffix == ".gz" else raw)
    leds = [f for f in g["fps"] if f["ref"].startswith("LED")
            and any(p["net"].startswith("KEY_RGB") for p in f["pads"])]
    keyrefs = {f["ref"] for f in leds}
    top = {f["ref"] for f in g["fps"] if f["layer"] == "F.Cu"
           and f["attr"] & 2 and f["pads"]}
    # Keep regulator/MCU/crystal decoupling and feedback parts fixed. Moving an
    # LED a little is preferable to invalidating those tightly coupled loops.
    small = {f["ref"] for f in g["fps"]
             if (f["ref"].startswith("C") and f["value"].startswith("100nF")
                 and any(p["net"] == "+4V_LED" for p in f["pads"]))
             or (f["ref"].startswith("R") and any("RGB" in p["net"] or p["net"].startswith("UG_LED") for p in f["pads"]))
             or (f["ref"].startswith("D") and any(p["net"].startswith("KEY_") for p in f["pads"]))}
    shapes, meta = [], []
    for f in g["fps"]:
        if f["ref"] in keyrefs | top:
            continue
        for p in f["pads"]:
            if not p["drill"][0] and "B.Cu" not in p["layers"]:
                continue
            shape = poly(p["poly"])
            if p["drill"][0]:
                shape = shape.union(Point(p["x"], p["y"]).buffer(max(p["drill"])/2, 32))
            shapes.append(shape)
            meta.append((f["ref"], "pad", f["ref"] not in small or bool(p["drill"][0])))
        if f["layer"] == "B.Cu" and f.get("courtyard"):
            shapes.append(poly(f["courtyard"]))
            meta.append((f["ref"], "court", f["ref"] not in small))
    tree = STRtree(shapes)
    xs = [e[k] for e in g["edges"] for k in ("x1", "x2")]
    ys = [e[k] for e in g["edges"] for k in ("y1", "y2")]
    outline = box(min(xs), min(ys), max(xs), max(ys)).buffer(-0.6)
    templates = {}
    for angle in (0, 90, 45, 135):
        opening, court, pads = package(0, 0, angle)
        templates[angle] = (opening, court, court.buffer(.15),
                            pads.buffer(.18).union(opening.buffer(.5)))
    sites = []
    for f in sorted(leds, key=lambda f: int(f["ref"][3:])):
        originals = old_sites(f)
        # A single peripheral emitter replaces the old mutually-exclusive
        # normal/stepped window + relay sites. Both chain references stay fitted.
        if f["ref"] in ("LED30", "LED54", "LED75"):
            originals = [originals[0]]
        for i, s in enumerate(originals):
            sites.append((f, i, s))
    # Keep unconstrained sites at the original optical centers first.
    difficult = {"LED1", "LED15", "LED16", "LED17", "LED30", "LED44", "LED49", "LED54", "LED59", "LED75", "LED76"}
    sites.sort(key=lambda q: (q[0]["ref"] in difficult, int(q[0]["ref"][3:]), q[1]))
    placed, report = [], []
    for f, index, s in sites:
        maxshift = 12 if f["ref"] in difficult else 1.5
        candidates = sorted((math.hypot(i*.25, j*.25), i*.25, j*.25, angle)
                            for i in range(-int(maxshift*4), int(maxshift*4)+1)
                            for j in range(-int(maxshift*4), int(maxshift*4)+1)
                            if math.hypot(i*.25, j*.25) <= maxshift
                            for angle in templates)
        best = None
        for offset, dx, dy, angle in candidates:
            if best and offset > best[0] + 1e-8:
                break
            x, y = s["x"]+dx, s["y"]+dy
            opening, court, court_probe, pad_probe = [translate(a, x, y) for a in templates[angle]]
            if not outline.contains(court):
                continue
            if any(court_probe.intersects(c) for c in placed):
                continue
            move, blocked = set(), False
            for k in tree.query(court_probe.union(pad_probe)):
                ref, kind, fixed = meta[k]
                if (court_probe if kind == "court" else pad_probe).intersects(shapes[k]):
                    if fixed:
                        blocked = True
                        break
                    move.add(ref)
            if blocked:
                continue
            choice = (offset, len(move), angle, x, y, move, court, opening)
            if best is None or choice[:3] < best[:3]:
                best = choice
        if best is None:
            raise RuntimeError(f"No physical site for {f['ref']}:{index}; keep board untouched")
        offset, _, angle, x, y, move, court, opening = best
        placed.append(court)
        report.append({"ref": f["ref"], "site_index": index, "original": s,
                       "center_mm": [round(x, 6), round(y, 6)], "axis_degrees": angle,
                       "center_shift_mm": round(offset, 6),
                       "optical_status": "original-window-center" if offset < 1e-6 and s["side"] == "F.Cu" else "offset-or-peripheral; optical-fit-unqualified",
                       "relocate_passives": sorted(move), "cutout_polygon": list(opening.exterior.coords)})
        print(f["ref"], index, (round(x, 4), round(y, 4)), angle, "shift", round(offset, 3), "move", sorted(move), flush=True)
    args.output.write_text(json.dumps({"status": "mechanical placement only; no routing or fabrication qualification",
                                       "layout_policy": "all baseline switch/stabilizer options preserved",
                                       "key_led_refs": len(keyrefs), "window_count": len(report),
                                       "backspace_population": "LED14 and LED15 retain two mutually-exclusive sites each; fit exactly one per reference",
                                       "relocate_top": sorted(top-keyrefs),
                                       "relocate_bottom": sorted({r for s in report for r in s["relocate_passives"]}),
                                       "sites": sorted(report, key=lambda r: (int(r["ref"][3:]), r["site_index"]))}, indent=2)+"\n")


if __name__ == "__main__":
    main()
