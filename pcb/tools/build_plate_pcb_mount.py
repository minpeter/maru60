#!/usr/bin/env python3
"""Build the PCB-mount 7U variant of the INKC Rule60 V3 HHKB gas plate.

The stock plate DXF (`models/rule60-v3-hhkb-gas-plate.dxf`) carries the INKC
plate-mount 7U stabilizer cutout.  The Maru60 PCB uses the PCB-mount
`Maru60_Candidates:MX-Hotswap-7U-4L-NPTH-StabRot180` footprint, whose four NPTH
holes sit outside that cutout (worst insert clearance -1.71 mm).  This script
reuses `build_plate.py` geometry and `spec/rule60-v3-outlines.json`, replaces
only the 7U cutout with the union of the stock cutout and the four NPTH
clearance circles, and writes a new DXF (and Gerber zip) without touching the
stock files.

The clearance circles use `NPTH_MARGIN` (default 0.40 mm) so the measured
polygon-to-hole-edge clearance stays above the required 0.30 mm after the DXF
4-decimal rounding and the 48-chord arc flattening used by the fit checker.

Usage:
    .venv/bin/python pcb/tools/build_plate_pcb_mount.py
    .venv/bin/python pcb/tools/build_plate_pcb_mount.py --margin 0.40
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import build_plate as bp  # noqa: E402
import rule60_spec as spec  # noqa: E402

NAME = "rule60-v3-hhkb-gas-plate-pcb-mount"
OUT = ROOT / "pcb/experiments/resume-20261109-relocated-expansion-zero-opens/qa/mechanical-fit"
# 7U PCB-mount NPTH pattern, plate frame: (x, y, diameter).  These are the four
# holes reported by check_mechanical_fit.py for the 7U footprint.
NPTH = [
    (85.8, 8.684, 3.048),    # stabilizer screw, left
    (85.8, 23.924, 3.9878),  # stabilizer insert, left
    (200.1, 8.684, 3.048),   # stabilizer screw, right
    (200.1, 23.924, 3.9878), # stabilizer insert, right
]
SEVEN_U_INDEX = 3  # spec/rule60-v3-outlines.json plate_gas_hhkb cutout 3 (bbox 81.5551..204.5051)


def pcb_mount_7u(cutout_verts: list[list[float]], margin: float) -> list[list[float]]:
    """Stock 7U cutout unioned with the four NPTH clearance circles, as [x, y, 0] verts."""
    stock = Polygon(spec.verts_points(cutout_verts, 48))
    circles = [Point(x, y).buffer(d / 2.0 + margin, quad_segs=64) for x, y, d in NPTH]
    merged = stock.union(unary_union(circles))
    if merged.geom_type != "Polygon":
        raise RuntimeError(f"7U union is {merged.geom_type}, expected Polygon")
    if not merged.is_valid:
        raise RuntimeError("7U union is not a valid polygon")
    return [[x, y, 0.0] for x, y in merged.exterior.coords[:-1]]


def npth_clearances(cutout: Polygon) -> list[dict[str, Any]]:
    out = []
    for x, y, d in NPTH:
        dist = float(cutout.boundary.distance(Point(x, y)))
        out.append({
            "plate_mm": [x, y],
            "diameter_mm": d,
            "distance_to_cutout_boundary_mm": round(dist, 4),
            "clearance_mm": round(dist - d / 2.0, 4),
            "status": "pass" if dist - d / 2.0 >= 0.30 else "fail",
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--margin", type=float, default=0.40,
                    help="radial clearance around each NPTH hole (default 0.40 mm; required >= 0.30)")
    ap.add_argument("--no-gerber", action="store_true", help="write only the DXF")
    args = ap.parse_args()
    if args.margin < 0.30:
        ap.error("--margin must be >= 0.30 mm")

    rec = spec.outline("plate_gas_hhkb")
    stock_cutouts = [list(c) for c in rec["cutouts"]]
    if len(stock_cutouts) != 62:
        raise RuntimeError(f"expected 62 cutouts, got {len(stock_cutouts)}")
    stock_7u = Polygon(spec.verts_points(stock_cutouts[SEVEN_U_INDEX], 48))
    if not (stock_7u.bounds[0] < 82 and stock_7u.bounds[2] > 204):
        raise RuntimeError(f"cutout {SEVEN_U_INDEX} is not the 7U cutout: {stock_7u.bounds}")

    cutouts_verts = [list(c) for c in stock_cutouts]
    cutouts_verts[SEVEN_U_INDEX] = pcb_mount_7u(stock_cutouts[SEVEN_U_INDEX], args.margin)
    loops = [rec["verts"]] + cutouts_verts

    outer = Polygon(spec.verts_points(rec["verts"], 48))
    cutouts = [Polygon(spec.verts_points(c, 48)) for c in cutouts_verts]
    plate = outer.difference(unary_union(cutouts))
    copper = plate.buffer(-bp.COPPER_PULLBACK, quad_segs=16)

    # Reuse the stock builder's assertions: outline identity, 60 HHKB keys,
    # 2.25u/7u stabilizer housings, router reach, copper pullback.
    report = bp.check(outer, cutouts, plate, copper)

    # Only the 7U cutout may change; every other cutout must be bit-identical.
    changed = [i for i, (a, b) in enumerate(zip(stock_cutouts, cutouts_verts)) if a != b]
    if changed != [SEVEN_U_INDEX]:
        raise RuntimeError(f"unexpected changed cutouts: {changed}")
    for i, (a, b) in enumerate(zip(stock_cutouts, cutouts_verts)):
        if i == SEVEN_U_INDEX:
            continue
        if Polygon(spec.verts_points(a, 48)).symmetric_difference(Polygon(spec.verts_points(b, 48))).area > 1e-9:
            raise RuntimeError(f"cutout {i} changed")

    new_7u = cutouts[SEVEN_U_INDEX]
    clearances = npth_clearances(new_7u)
    if any(c["status"] != "pass" for c in clearances):
        raise RuntimeError(f"NPTH clearance below 0.30 mm: {clearances}")

    report.update({
        "variant": "pcb-mount-7u",
        "source_plate": "models/rule60-v3-hhkb-gas-plate.dxf (unchanged)",
        "npth_margin_mm": args.margin,
        "npth_clearances": clearances,
        "seven_u_cutout": {
            "index": SEVEN_U_INDEX,
            "stock_bbox_plate_mm": [round(v, 4) for v in stock_7u.bounds],
            "new_bbox_plate_mm": [round(v, 4) for v in new_7u.bounds],
            "stock_area_mm2": round(stock_7u.area, 3),
            "new_area_mm2": round(new_7u.area, 3),
            "area_delta_mm2": round(new_7u.area - stock_7u.area, 3),
            "bbox_delta_mm": [round(b - a, 4) for a, b in zip(stock_7u.bounds, new_7u.bounds)],
        },
        "unchanged_cutouts": len(stock_cutouts) - 1,
        "changed_cutouts": changed,
        "files": [f"models/{NAME}.dxf"],
    })

    (bp.MODELS / f"{NAME}.dxf").write_text(bp.dxf(loops))
    if not args.no_gerber:
        files = {
            f"{NAME}.GKO": bp.gerber("Profile,NP", bp.outline_strokes(loops)),
            f"{NAME}.GTL": bp.gerber("Copper,L1,Top", bp.regions(copper)),
            f"{NAME}.GBL": bp.gerber("Copper,L2,Bot", bp.regions(copper)),
            f"{NAME}.GTS": bp.gerber("Soldermask,Top", []),
            f"{NAME}.GBS": bp.gerber("Soldermask,Bot", []),
        }
        with zipfile.ZipFile(bp.MODELS / f"{NAME}-fr4-gerber.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for name, text in files.items():
                z.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), text)
        report["files"].append(f"models/{NAME}-fr4-gerber.zip: " + ", ".join(sorted(files)))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "plate-pcb-mount-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "dxf": f"models/{NAME}.dxf",
        "gerber": None if args.no_gerber else f"models/{NAME}-fr4-gerber.zip",
        "npth_margin_mm": args.margin,
        "npth_clearances": clearances,
        "seven_u_cutout": report["seven_u_cutout"],
        "max_uncut_void_mm2": report["max_uncut_void_mm2"],
        "cutouts": report["cutouts"],
        "hhkb_keys": report["hhkb_keys"],
    }, indent=2))


if __name__ == "__main__":
    main()
