#!/usr/bin/env python3
"""Independent GEOS + exact rational Q^2 inner-plane witness replay (matching header6-orthogonal methodology).

Run from the repository root with the repository virtual environment (shapely is already installed):

    .venv/bin/python pcb/tools/geos_witness_zero_opens.py --qa-dir <audit-output-dir>

``--qa-dir`` must contain ``exact-native-plane-inputs.json`` produced by
``pcb/tools/audit_relocated_zero_opens.py``. The script writes ``geos-audit.json`` and
``geos-rational-witnesses.json`` into that same directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from fractions import Fraction as F
from pathlib import Path
import shapely
from shapely import wkt
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union


def geometry(rows):
    parts = [Polygon(row["outer"], row["holes"]) for row in rows]
    bad = sum(not x.is_valid for x in parts)
    fixed = [shapely.make_valid(x) if not x.is_valid else x for x in parts]
    return unary_union(fixed), bad


def subtract_holes(shape, holes):
    relevant = [hole for hole in holes if shape.intersects(hole)]
    return shape.difference(unary_union(relevant)) if relevant else shape


def inside_q2(ring, point):
    x, y = point
    v = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < F(a[0]) + F(y - a[1], b[1] - a[1]) * (b[0] - a[0]):
            v = not v
    return v


def boundary_q2(ring, p):
    x, y = p
    return any(
        min(a[0], b[0]) <= x <= max(a[0], b[0])
        and min(a[1], b[1]) <= y <= max(a[1], b[1])
        and (x - a[0]) * (b[1] - a[1]) == (y - a[1]) * (b[0] - a[0])
        for a, b in zip(ring, ring[1:] + ring[:1])
    )


def index_ring_q2(ring):
    rx0 = min(pt[0] for pt in ring)
    rx1 = max(pt[0] for pt in ring)
    ry0 = min(pt[1] for pt in ring)
    ry1 = max(pt[1] for pt in ring)
    buckets: dict[int, list[tuple[list[int], list[int]]]] = {}
    for a, b in zip(ring, ring[1:] + ring[:1]):
        y0, y1 = (a[1], b[1]) if a[1] <= b[1] else (b[1], a[1])
        for bk in range(y0 >> 20, (y1 >> 20) + 1):
            buckets.setdefault(bk, []).append((a, b))
    return (rx0, rx1, ry0, ry1, buckets)


def inside_indexed_ring_q2(idx_ring, point):
    rx0, rx1, ry0, ry1, buckets = idx_ring
    x, y = point
    if x < rx0 or x > rx1 or y < ry0 or y > ry1:
        return False
    bk = int(y) >> 20
    v = False
    for a, b in buckets.get(bk, ()):
        if (a[1] > y) != (b[1] > y) and x < F(a[0]) + F(y - a[1], b[1] - a[1]) * (b[0] - a[0]):
            v = not v
    return v


def boundary_indexed_ring_q2(idx_ring, point):
    rx0, rx1, ry0, ry1, buckets = idx_ring
    x, y = point
    if x < rx0 or x > rx1 or y < ry0 or y > ry1:
        return False
    for bk in {int(y) >> 20, (int(y) + 1) >> 20}:
        for a, b in buckets.get(bk, ()):
            if (
                min(a[0], b[0]) <= x <= max(a[0], b[0])
                and min(a[1], b[1]) <= y <= max(a[1], b[1])
                and (x - a[0]) * (b[1] - a[1]) == (y - a[1]) * (b[0] - a[0])
            ):
                return True
    return False


def index_polys_q2(polys):
    return [(index_ring_q2(q["outer"]), [index_ring_q2(h) for h in q["holes"]]) for q in polys]


def covered_q2(indexed_polys, p):
    for outer, holes in indexed_polys:
        if inside_indexed_ring_q2(outer, p) and not any(inside_indexed_ring_q2(h, p) for h in holes):
            return True
    return False


def on_boundary_q2(indexed_polys, p):
    for outer, holes in indexed_polys:
        if boundary_indexed_ring_q2(outer, p) or any(boundary_indexed_ring_q2(h, p) for h in holes):
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa-dir", type=Path, required=True)
    args = ap.parse_args()
    qa = args.qa_dir

    data = json.loads((qa / "exact-native-plane-inputs.json").read_text())
    planes = {}
    invalid = {}
    for side in ("source", "candidate"):
        for layer, parts in data[side]["planes"].items():
            planes[side, layer], invalid[f"{side}:{layer}"] = geometry(parts)

    # Inscribed 1024-gon windows (conservative subset of exact disks!)
    windows = unary_union([Point(w["xy_nm"]).buffer(w["radius_nm"] * math.cos(math.pi / 1024), quad_segs=256) for w in data["windows"]]) if data["windows"] else Polygon()
    oldholes = [geometry(h["polygons"])[0] for h in data["source"]["holes"]]
    newholes = [geometry(h["polygons"])[0] for h in data["candidate"]["holes"]]

    plane_rows = []
    for layer in data["source"]["planes"]:
        raw = planes["source", layer].difference(planes["candidate", layer])
        outside = subtract_holes(raw.difference(windows) if data["windows"] else raw, oldholes)
        plane_rows.append({
            "layer": layer,
            "outside_window_area_nm2": outside.area,
            "outside_window_area_mm2": outside.area / 1e12,
            "outside_empty": outside.is_empty,
            "raw_loss_area_nm2": raw.area,
            "outside_wkt": outside.wkt,
        })

    oldsh = {x["uuid"]: x for x in data["source"]["flagged_retained_shadows"]}
    ref = []
    for item in data["candidate"]["flagged_retained_shadows"]:
        old, _ = geometry(oldsh[item["uuid"]]["polygons"])
        new, _ = geometry(item["polygons"])
        old = subtract_holes(old, oldholes)
        new = subtract_holes(new, newholes)
        for layer in data["source"]["planes"]:
            supported_old = old.intersection(planes["source", layer])
            supported_new = new.intersection(planes["candidate", layer])
            loss = supported_old.difference(supported_new)
            loss_outside = loss.difference(windows) if data["windows"] else loss
            ref.append({
                "uuid": item["uuid"],
                "net": item["net"],
                "layer": layer,
                "lost_support_area_nm2": loss.area,
                "lost_support_outside_windows_area_nm2": loss_outside.area,
                "empty_outside_windows": loss_outside.is_empty,
            })

    input_path = qa / "exact-native-plane-inputs.json"
    geos_out = {
        "producer": {
            "script": "pcb/tools/geos_witness_zero_opens.py",
            "argv": [Path(sys.argv[0]).as_posix(), *sys.argv[1:]],
            "cwd": str(Path.cwd()),
            "input": "exact-native-plane-inputs.json",
            "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        },
        "engine": "GEOS " + shapely.geos_version_string,
        "shapely": shapely.__version__,
        "coordinate_units": "nanometres, original integer vertices; no precision grid or tolerance snapping",
        "invalid_input_polygons": invalid,
        "allowed_window_approximation": "1024-sided INSCRIBED circles (strictly inside exact declared window disks).",
        "retained_reference_lost_support_max_nm2": max((r["lost_support_area_nm2"] for r in ref), default=0.0),
        "retained_reference_lost_support_outside_windows_max_nm2": max((r["lost_support_outside_windows_area_nm2"] for r in ref), default=0.0),
        "planes": [{k: v for k, v in r.items() if k != "outside_wkt"} for r in plane_rows],
        "retained_reference": ref,
    }
    (qa / "geos-audit.json").write_text(json.dumps(geos_out, indent=2) + "\n")

    # Exact rational Q^2 witness classification on every GEOS outside part
    indexed_holes = [index_polys_q2(q["polygons"]) for q in data["source"]["holes"]]
    witness_rows = []
    for plane in plane_rows:
        geom = wkt.loads(plane["outside_wkt"])
        if geom.is_empty:
            continue
        parts = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
        layer = plane["layer"]
        a = index_polys_q2(data["source"]["planes"][layer])
        b = index_polys_q2(data["candidate"]["planes"][layer])
        for i, part in enumerate(parts):
            pt = part.representative_point()
            pq = (F(str(pt.x)), F(str(pt.y)))
            inwindow = any(
                (pq[0] - q["xy_nm"][0]) ** 2 + (pq[1] - q["xy_nm"][1]) ** 2 <= q["radius_nm"] ** 2
                for q in data["windows"]
            )
            inhole = any(covered_q2(ih, pq) for ih in indexed_holes)
            truth = (
                covered_q2(a, pq)
                and not covered_q2(b, pq)
                and not on_boundary_q2(a, pq)
                and not on_boundary_q2(b, pq)
                and not inwindow
                and not inhole
            )
            witness_rows.append({
                "layer": layer,
                "index": i,
                "point_nm": [str(x) for x in pq],
                "geos_area_nm2": part.area,
                "strict_native_domain_loss_witness": truth,
                "inside_exact_window": inwindow,
            })

    witness_summary = {
        "geos_parts_total": len(witness_rows),
        "strict_q2_interior_witnesses": sum(r["strict_native_domain_loss_witness"] for r in witness_rows),
        "strict_q2_witness_total_geos_area_nm2": sum(r["geos_area_nm2"] for r in witness_rows if r["strict_native_domain_loss_witness"]),
        "strict_q2_witness_total_geos_area_mm2": sum(r["geos_area_nm2"] for r in witness_rows if r["strict_native_domain_loss_witness"]) / 1e12,
        "note": "Clipper2 integer keyhole fracture-line reshuffling on In1.Cu/In2.Cu when new via holes alter single-outline keyhole topology; native KiCad SHAPE_POLY_SET BooleanSubtract outside declared windows is 0, while exact Q^2 polygon-ring replay detects shifted 1nm integer keyhole chords. Explicitly recorded without tolerance waiver; strict_baseline is NOT promoted.",
        "witnesses": witness_rows,
    }
    (qa / "geos-rational-witnesses.json").write_text(json.dumps(witness_summary, indent=2) + "\n")
    print(json.dumps({
        "planes": geos_out["planes"],
        "retained_max_lost_nm2": geos_out["retained_reference_lost_support_max_nm2"],
        "geos_parts_total": witness_summary["geos_parts_total"],
        "strict_q2_interior_witnesses": witness_summary["strict_q2_interior_witnesses"],
        "strict_q2_area_mm2": witness_summary["strict_q2_witness_total_geos_area_mm2"],
    }, indent=2))


if __name__ == "__main__":
    main()
