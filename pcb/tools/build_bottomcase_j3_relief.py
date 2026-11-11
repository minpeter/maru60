#!/usr/bin/env python3
"""Build a bottom-case variant with a local relief pocket under J3.

The relocated JST SH 10-pin connector J3 (board 44.25, 75.0) has a 2.95 mm
nominal body and only 3.28 mm free height at full 0.80 mm gasket travel, i.e.
0.33 mm clearance.  This script reuses `build_bottomcase_draft.build()` and
cuts a 0.50 mm deep pocket under the J3 courtyard (plus 0.50 mm margin), so the
local floor drops from Z_p 18.20 to 18.70 and the nominal clearance rises to
0.85 mm (0.83 mm on the quantized 3MF surface).  The pocket is in the left half
only; the right half is unchanged.

The new 3MFs and world STLs are written under `models/` and `build/`; the stock
`models/maru60-hhkb-bottomcase-*.3mf` files are not touched.

Usage:
    .venv/bin/python pcb/tools/build_bottomcase_j3_relief.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import build_bottomcase_draft as bc  # noqa: E402

BUILD_DIR = ROOT / "build/j3-relief"
QA = ROOT / "pcb/experiments/resume-20261109-relocated-expansion-zero-opens/qa/mechanical-fit"
LEFT_NAME = "maru60-hhkb-bottomcase-j3-relief-left.3mf"
RIGHT_NAME = "maru60-hhkb-bottomcase-j3-relief-right.3mf"

# J3 courtyard in the plate frame: board (44.25, 75.0) +- (6.9, 3.28), then
# x_plate = x + 0.4525, y_plate = 101.06775 - y.
J3_PLATE_BBOX = (37.8025, 22.78775, 51.6025, 29.34775)
POCKET_MARGIN = 0.50
POCKET_DEPTH = 0.50
POCKET_CORNER_R = 0.50
J3_BODY_HEIGHT = 2.95
BOARD_BOTTOM_ZP = 14.10
GASKET_TRAVEL = 0.80


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", default="ph60-rev3", help="board id (default: ph60-rev3)")
    ap.add_argument("--no-battery-bay", action="store_true", help="build the wired (no battery bay) variant")
    args = ap.parse_args()

    body, report = bc.build(args.board, battery_bay=not args.no_battery_bay)
    x0, y0, x1, y1 = J3_PLATE_BBOX
    pocket_plate = box(x0 - POCKET_MARGIN, y0 - POCKET_MARGIN,
                       x1 + POCKET_MARGIN, y1 + POCKET_MARGIN)
    pocket_plate = pocket_plate.buffer(-POCKET_CORNER_R).buffer(POCKET_CORNER_R, quad_segs=16)
    pocket_world = bc.plate_to_world(pocket_plate)
    pocket = bc.prism(pocket_world, bc.FLOOR_ZP - 0.01, bc.FLOOR_ZP + POCKET_DEPTH)
    body = body - pocket

    left, right = bc.split(body)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    world = {"bottom-left": left, "bottom-right": right}
    for name, m in world.items():
        bc.to_trimesh(m).export(BUILD_DIR / f"{name}-world.stl")
    printed = {name: bc.on_bed(m) for name, m in world.items()}
    for name, tm in printed.items():
        assert len(tm.split(only_watertight=False)) == 1, name
        tm.export(BUILD_DIR / f"{name}-print.stl")

    bc.write_3mf(ROOT / "models" / LEFT_NAME,
                 "Maru60 HHKB bottom case, for Rule60 V3 - left half, J3 0.50 mm relief (CC BY-NC 4.0)",
                 [("BottomLeft", printed["bottom-left"])], fine_layer_z=None)
    bc.write_3mf(ROOT / "models" / RIGHT_NAME,
                 "Maru60 HHKB bottom case, for Rule60 V3 - right half, J3 relief variant (CC BY-NC 4.0)",
                 [("BottomRight", printed["bottom-right"])], fine_layer_z=None)

    new_floor = bc.FLOOR_ZP + POCKET_DEPTH
    free = new_floor - (BOARD_BOTTOM_ZP + GASKET_TRAVEL)
    out = {
        "variant": "j3-relief",
        "board": args.board,
        "battery_bay": not args.no_battery_bay,
        "j3_plate_bbox_mm": [round(v, 4) for v in J3_PLATE_BBOX],
        "pocket_plate_bbox_mm": [round(v, 4) for v in pocket_plate.bounds],
        "pocket_world_bbox_mm": [round(v, 4) for v in pocket_world.bounds],
        "pocket_margin_mm": POCKET_MARGIN,
        "pocket_depth_mm": POCKET_DEPTH,
        "pocket_corner_r_mm": POCKET_CORNER_R,
        "floor_before_z_p_mm": bc.FLOOR_ZP,
        "floor_after_z_p_mm": round(new_floor, 4),
        "tray_bottom_z_p_mm": bc.TRAY_BOTTOM_ZP,
        "remaining_floor_slab_mm": round(bc.TRAY_BOTTOM_ZP - new_floor, 4),
        "j3_body_height_mm": J3_BODY_HEIGHT,
        "board_bottom_z_p_mm": BOARD_BOTTOM_ZP,
        "gasket_travel_mm": GASKET_TRAVEL,
        "free_height_before_mm": round(bc.FLOOR_ZP - (BOARD_BOTTOM_ZP + GASKET_TRAVEL), 4),
        "free_height_after_mm": round(free, 4),
        "clearance_before_mm": round(bc.FLOOR_ZP - (BOARD_BOTTOM_ZP + GASKET_TRAVEL) - J3_BODY_HEIGHT, 4),
        "clearance_after_mm": round(free - J3_BODY_HEIGHT, 4),
        "expected_mesh_surface_z_p_mm": round(new_floor - 0.02, 4),
        "expected_mesh_clearance_mm": round(new_floor - 0.02 - (BOARD_BOTTOM_ZP + GASKET_TRAVEL) - J3_BODY_HEIGHT, 4),
        "files": [f"models/{LEFT_NAME}", f"models/{RIGHT_NAME}"],
        "world_stl_dir": str(BUILD_DIR.relative_to(ROOT)),
        "note": "The pocket is in the left half only; the right half is unchanged. The 3MFs are in the X2D print frame.",
    }
    QA.mkdir(parents=True, exist_ok=True)
    (QA / "bottomcase-j3-relief-report.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
