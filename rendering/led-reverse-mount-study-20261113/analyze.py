#!/usr/bin/env python3
"""Read-only feasibility screen; this does not design or qualify LED cutouts."""
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SOURCE = ROOT / "pcb/experiments/resume-20261113-mcu-near-usb-zero-opens"


def polygons(rings):
    return unary_union([Polygon(r) for r in rings if len(r) >= 3])


def main():
    board = SOURCE / "pcb/maru60.kicad_pcb"
    board_hash = hashlib.sha256(board.read_bytes()).hexdigest()
    geometry_path = SOURCE / "qa/geometry.json.gz"
    g = json.loads(gzip.decompress(geometry_path.read_bytes()))
    fps = {f["ref"]: f for f in g["fps"]}
    with (SOURCE / "order/cpl-jlcpcb.csv").open() as stream:
        cpl = list(csv.DictReader(stream))
    with (SOURCE / "order/bom-full.csv").open() as stream:
        bom = {r["Reference"]: r for r in csv.DictReader(stream)}
    top = [r["Designator"] for r in cpl if r["Layer"] == "Top"]
    leds = [r for r in top if r.startswith("LED")]
    caps = [r for r in top if r.startswith("C") and bom[r]["Value"] == "100nF"]
    other = sorted(set(top) - set(leds) - set(caps))
    pads = [(f["ref"], p, polygons(p["poly"])) for f in fps.values() for p in f["pads"]]
    tracks = [(t, LineString([(t["x1"], t["y1"]), (t["x2"], t["y2"])]).buffer(t["w"] / 2, 16))
              for t in g["tracks"]]
    vias = [(v, Point(v["x"], v["y"]).buffer(v["d"] / 2, 32)) for v in g["vias"]]
    courts = [(f["ref"], polygons(f.get("courtyard", []))) for f in fps.values()
              if f["layer"] == "B.Cu"]
    windows = []
    for ref in sorted(leds, key=lambda r: int(r[3:])):
        f = fps[ref]
        # Deliberately hypothetical, fixed X/Y orientation at each existing anchor.
        w = box(f["x"] - 2, f["y"] - 1, f["x"] + 2, f["y"] + 1)
        ph = [{"ref": r, "pad": p["num"], "net": p["net"], "layers": p["layers"]}
              for r, p, geom in pads if r != ref and w.intersects(geom)]
        th = [t for t, geom in tracks if w.intersects(geom)]
        vh = [v for v, geom in vias if w.intersects(geom)]
        ch = [r for r, geom in courts if r != ref and w.intersects(geom)]
        windows.append({"ref": ref, "center_mm": [f["x"], f["y"]],
                        "other_pads": ph, "tracks": th, "vias": vh,
                        "bottom_courtyards": ch})
    data = {
        "source_board": str(board.relative_to(ROOT)), "source_sha256": board_hash,
        "geometry_sha256": hashlib.sha256(geometry_path.read_bytes()).hexdigest(),
        "scope": "Read-only hypothetical 4 x 2 mm sharp rectangular openings at the 61 automated top LED footprint anchors, long axis X. No new part selected, placement, rerouting, or DRC qualification.",
        "limitations": ["Only direct geometric intersections; no milling tolerance or copper-edge clearance added.",
                        "Zones/reference planes, switch bodies, stabilizer volumes, and alternate LED sites are not qualified by this screen.",
                        "Courtyard intersections flag placement conflicts; they do not prove component body collision.",
                        "Track counts are source records, which may include duplicate segments.",
                        "4 x 2 mm is the user's approximate reference observation, not a released machining dimension."],
        "assembly": {"current": dict(Counter(r["Layer"] for r in cpl)),
                     "top_leds": leds, "top_100nf_caps": caps,
                     "top_100nf_cap_nets": {r: sorted(set(p["net"] for p in fps[r]["pads"])) for r in caps},
                     "remaining_top": [{"ref": r, "value": bom[r]["Value"]} for r in other],
                     "after_led_cap_move_arithmetic_only": {"Top": len(other), "Bottom": len(cpl) - len(other)},
                     "all_bottom_target_unproven": {"Top": 0, "Bottom": len(cpl)}},
        "screen_counts": {"windows": len(windows),
                          "with_other_pad_intersections": sum(bool(w["other_pads"]) for w in windows),
                          "with_track_intersections": sum(bool(w["tracks"]) for w in windows),
                          "with_via_intersections": sum(bool(w["vias"]) for w in windows),
                          "with_bottom_courtyard_intersections": sum(bool(w["bottom_courtyards"]) for w in windows)},
        "windows": windows,
    }
    assert hashlib.sha256(board.read_bytes()).hexdigest() == board_hash
    (OUT / "findings.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k: v for k, v in data.items() if k in ("source_sha256", "screen_counts")}, indent=2))
    print("Remaining top:", data["assembly"]["remaining_top"])
    print("LED16:", json.dumps(next(w for w in windows if w["ref"] == "LED16"), indent=2))


if __name__ == "__main__":
    main()
