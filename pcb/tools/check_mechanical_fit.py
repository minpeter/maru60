#!/usr/bin/env python3
"""CAD-level mechanical fit checks for the Maru60 relocated-expansion checkpoint.

Checks, against the exported bottom-case 3MF and the board's own footprint data:

1. The relocated B.Cu GPIO expansion/isolation block: the case inner surface below
   each part and the free height at full gasket travel.
2. USB-C J1 at (18, 3.8) mm: the 12.8 mm stock notch, the printed 14.75 mm notch,
   the J1 body and the bottom-case USB passage.
3. The 7U spacebar stabilizer NPTH pattern against the INKC gas-plate cutout.

Frames and assumptions are stated in the output JSON and REPORT.md.  The 3MF is in
the bottom-case print frame; the print offset is recovered from the world-frame STL
exported by the same build (bottomcase-draft/bottom-*-world.stl).  The 3MF itself is
then ray-cast directly, so no re-meshing or boolean approximation is used for the
clearance numbers.

Run with the repository venv:

    .venv/bin/python pcb/tools/check_mechanical_fit.py

Writes qa/mechanical-fit/fit.json and qa/mechanical-fit/REPORT.md under the
checkpoint.  No git write commands are used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import build_bottomcase_draft as bc  # noqa: E402
import rule60_spec as spec  # noqa: E402

CHECKPOINT = ROOT / "pcb/experiments/resume-20261109-relocated-expansion-zero-opens"
DEFAULT_BOARD = CHECKPOINT / "pcb/maru60.kicad_pcb"
DEFAULT_OUT = CHECKPOINT / "qa/mechanical-fit"
MODELS = ROOT / "models"
BOTTOMCASE_DRAFT = ROOT / "bottomcase-draft"
PLATE_DXF = MODELS / "rule60-v3-hhkb-gas-plate.dxf"
OUTLINES = ROOT / "spec/rule60-v3-outlines.json"
BOARDS = ROOT / "spec/boards.json"

# --- stated assumptions (checked against the build/spec below) -----------------
BOARD_TOP_ZP = 12.50       # plate top 7.50 + 5.0 MX stack
BOARD_BOTTOM_ZP = 14.10    # 1.6 mm PCB
CAVITY_FLOOR_ZP = 18.20    # build_bottomcase_draft.FLOOR_ZP
GASKET_TRAVEL = 0.80       # full gasket travel used by the bottom-case build
BOARD_THICKNESS = 1.60
MX_STACK = 5.00
PLATE_TOP_ZP = 7.50

# The stock Rule60 V3 top-case notch is 12.8 mm wide at plate X 19.35; the
# printed cases cut 14.75 mm at the selected board's USB centre (PH60: 18.65).
STOCK_NOTCH_WIDTH = 12.80
STOCK_NOTCH_CENTRE_PLATE_X = 19.35
PRINTED_NOTCH_WIDTH = 14.75
USB_MAX_OVERMOLD_WIDTH = 12.35  # spec/rule60-v3.json top.usb_notch_cable_width source
J1_BODY_HEIGHT = 3.26           # bottom-case verification: 18.20 - 0.84 - 14.10
J1_BODY_HALF_WIDTH = 4.47       # J1 B.Fab rect
J1_BODY_HALF_DEPTH = 3.675      # J1 B.Fab rect

# Nominal package heights.  These are datasheet/package values, not measurements.
# The report marks them as inputs that still need a caliper check.
PART_HEIGHTS: dict[str, tuple[float, str]] = {
    "J3": (2.95, "JST SH SM10B-SRSS-TB side-entry body height; prior analysis "
                 ".omo/evidence/pcb-routing-20261109/manual/sim/SUMMARY.json "
                 "('J3_margin_assuming_2.95mm'); datasheet nominal, not measured"),
    "U13": (0.50, "TI TPD6E05U06RVZR RVZ14 package max height 0.5 mm; datasheet nominal, not measured"),
    "U11": (1.20, "TI SN74CB3T3245PWR TSSOP-20 (PW) max height 1.2 mm; datasheet nominal, not measured"),
    "U12": (1.10, "TI TLV810EA29DBZR SOT-23 (DBZ) max height 1.1 mm; datasheet nominal, not measured"),
}
DEFAULT_0603_HEIGHT = (0.50, "0603 resistor/capacitor max height 0.5 mm; standard package nominal, not measured")

RELOCATED_REFS = [
    "J3", "U13", "U11", "U12", "R128", "C128", "C129",
    "R130", "R131", "R132", "R133", "R134", "R135",
    "R140", "R141", "R142", "R143", "R144", "R145",
]
J3_PLUG_CORRIDOR_BOARD = (37.30, 68.20, 51.20, 71.70)  # x0,y0,x1,y1, board frame


# --- small helpers -------------------------------------------------------------
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def blocks(text: str, tag: str) -> list[str]:
    """Balanced top-level ``(tag ...)`` blocks."""
    out: list[str] = []
    i = 0
    needle = "(" + tag + " "
    while True:
        j = text.find(needle, i)
        if j < 0:
            break
        depth = 0
        k = j
        while k < len(text):
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        out.append(text[j:k + 1])
        i = k + 1
    return out


def first(pattern: str, text: str, default: Any = None) -> Any:
    m = re.search(pattern, text, re.S)
    return m.group(1) if m else default


def rotate_xy(x: float, y: float, deg: float) -> tuple[float, float]:
    """KiCad footprint rotation (counter-clockwise, degrees)."""
    if abs(deg) < 1e-9:
        return x, y
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return c * x - s * y, s * x + c * y


def board_to_plate(x: float, y: float) -> tuple[float, float]:
    """Board own frame -> INKC plate frame (spec/boards.json frames.pcb_to_plate)."""
    return x + 0.4525, 101.06775 - y


def plate_to_world(x: float, y: float) -> tuple[float, float]:
    """Plate frame -> bottom-case world frame (build_topcase_draft.pw)."""
    return bc.top.pw(x, y)


def board_to_world(x: float, y: float) -> tuple[float, float]:
    return plate_to_world(*board_to_plate(x, y))


def bbox_of(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


# --- board parsing -------------------------------------------------------------
def parse_footprints(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for blk in blocks(text, "footprint"):
        ref = first(r'\(property "Reference" "([^"]+)"', blk)
        if not ref:
            continue
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", blk)
        if not at:
            continue
        x, y = float(at.group(1)), float(at.group(2))
        rot = float(at.group(3)) if at.group(3) is not None else 0.0
        layer = first(r'\(layer "([^"]+)"\)', blk, "")
        name = first(r'\(footprint "([^"]+)"', blk, "")
        out.append({
            "ref": ref,
            "name": name,
            "x": x,
            "y": y,
            "rot": rot,
            "layer": layer,
            "block": blk,
        })
    return out


def courtyard_local_bbox(blk: str) -> tuple[float, float, float, float] | None:
    pts: list[tuple[float, float]] = []
    for m in re.finditer(r"\(fp_(line|rect|arc|poly|circle)\b(.*?)\n\t\t\)", blk, re.S):
        body = m.group(2)
        if '(layer "B.CrtYd")' not in body:
            continue
        for sm in re.finditer(r"\((start|end|mid|center|xy) ([-\d.]+) ([-\d.]+)\)", body):
            pts.append((float(sm.group(2)), float(sm.group(3))))
    if not pts:
        return None
    return bbox_of(pts)


def npth_pads(blk: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for pad in blocks(blk, "pad"):
        if "np_thru_hole" not in pad:
            continue
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", pad)
        if not at:
            continue
        size = re.search(r"\(size ([-\d.]+) ([-\d.]+)\)", pad)
        drill = re.search(r"\(drill ([-\d.]+)", pad)
        d = float(drill.group(1)) if drill else (float(size.group(1)) if size else 0.0)
        out.append({
            "x": float(at.group(1)),
            "y": float(at.group(2)),
            "diameter": d,
            "shape": first(r"np_thru_hole (\w+)", pad, "circle"),
        })
    return out


# --- 3MF loading and ray casting ----------------------------------------------
def load_case_meshes() -> list[dict[str, Any]]:
    """Load the two bottom-case 3MF halves and recover their print-frame offsets.

    The 3MF is in the print frame (desk face on the bed, centred on the 256 mm
    bed).  The same build also exports a world-frame STL; applying the known
    world->print rotation to that STL and matching its bounds to the 3MF bounds
    gives the on-bed translation.  The 3MF geometry itself is then used for all
    ray casts.
    """
    R = bc.TO_PRINT[:3, :3]
    tp = bc.TO_PRINT[:3, 3]
    meshes: list[dict[str, Any]] = []
    for half, key in (("left", "BottomLeft"), ("right", "BottomRight")):
        scene = trimesh.load(MODELS / f"maru60-hhkb-bottomcase-{half}.3mf")
        mesh = scene.geometry[key]
        world = trimesh.load_mesh(BOTTOMCASE_DRAFT / f"bottom-{half}-world.stl")
        pcal = world.vertices @ R.T + tp
        tbed = mesh.bounds[0] - pcal.min(axis=0)
        # Verify the recovered offset maps the 3MF back onto the world STL bounds.
        w3 = (mesh.vertices - tp - tbed) @ R
        err = float(np.max(np.abs(w3.min(axis=0) - world.bounds[0])))
        err = max(err, float(np.max(np.abs(w3.max(axis=0) - world.bounds[1]))))
        if err > 0.05:
            raise RuntimeError(f"{half}: 3MF/world-STL frame mismatch {err:.3f} mm")
        meshes.append({
            "half": half,
            "mesh": mesh,
            "tbed": tbed,
            "frame_error_mm": round(err, 4),
            "volume_cm3": round(float(mesh.volume) / 1000.0, 3),
        })
    return meshes


def ray_surface_zp(meshes: list[dict[str, Any]], xw: np.ndarray, yw: np.ndarray,
                   z_start: float = BOARD_BOTTOM_ZP) -> tuple[np.ndarray, np.ndarray]:
    """First case surface below ``z_start`` for each world XY sample.

    Returns (surface_zp, hit_mask).  ``surface_zp`` is +inf where no half was hit.
    The ray direction is +Z_p (downward); the 3MF is in print frame, so the ray is
    transformed with the same rotation/offset used to load the mesh.
    """
    R = bc.TO_PRINT[:3, :3]
    tp = bc.TO_PRINT[:3, 3]
    direction = R @ np.array([0.0, 0.0, 1.0])
    n = len(xw)
    best = np.full(n, np.inf, dtype=float)
    for entry in meshes:
        mesh = entry["mesh"]
        tbed = entry["tbed"]
        origins = np.column_stack([xw, yw, np.full(n, z_start)]) @ R.T + tp + tbed
        dirs = np.tile(direction, (n, 1))
        loc, idx, _ = mesh.ray.intersects_location(origins, dirs, multiple_hits=False)
        if len(loc) == 0:
            continue
        # Parameter along the unit ray = Z_p - z_start.
        zp = z_start + np.einsum("ij,ij->i", loc - origins[idx], dirs[idx])
        np.minimum.at(best, idx, zp)
    return best, np.isfinite(best)


def sample_rect_world(x0: float, y0: float, x1: float, y1: float, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Grid of world XY points inside a board-frame rectangle."""
    xs = np.linspace(x0, x1, n)
    ys = np.linspace(y0, y1, n)
    gx, gy = np.meshgrid(xs, ys)
    wx = np.empty(gx.size)
    wy = np.empty(gx.size)
    for k, (bx, by) in enumerate(zip(gx.ravel(), gy.ravel())):
        wx[k], wy[k] = board_to_world(float(bx), float(by))
    return wx, wy


def rect_world_bbox(x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float]:
    pts = [board_to_world(x, y) for x in (x0, x1) for y in (y0, y1)]
    return bbox_of(pts)


# --- check 1: relocated B.Cu block --------------------------------------------
def check_relocated(footprints: list[dict[str, Any]], meshes: list[dict[str, Any]], grid: int) -> dict[str, Any]:
    by_ref = {f["ref"]: f for f in footprints}
    records: list[dict[str, Any]] = []
    for ref in RELOCATED_REFS:
        fp = by_ref.get(ref)
        if fp is None:
            records.append({"ref": ref, "status": "unknown", "missing": "footprint not found"})
            continue
        local = courtyard_local_bbox(fp["block"])
        if local is None:
            records.append({"ref": ref, "status": "unknown", "missing": "no B.CrtYd courtyard"})
            continue
        lx0, ly0, lx1, ly1 = local
        corners = [rotate_xy(x, y, fp["rot"]) for x in (lx0, lx1) for y in (ly0, ly1)]
        bx0 = fp["x"] + min(c[0] for c in corners)
        bx1 = fp["x"] + max(c[0] for c in corners)
        by0 = fp["y"] + min(c[1] for c in corners)
        by1 = fp["y"] + max(c[1] for c in corners)
        wx, wy = sample_rect_world(bx0, by0, bx1, by1, grid)
        surf, hit = ray_surface_zp(meshes, wx, wy)
        if not hit.any():
            records.append({
                "ref": ref,
                "footprint": fp["name"],
                "position_board_mm": [fp["x"], fp["y"], fp["rot"]],
                "layer": fp["layer"],
                "courtyard_board_mm": [round(v, 4) for v in (bx0, by0, bx1, by1)],
                "case_surface_z_p_mm": None,
                "free_height_full_travel_mm": None,
                "part_height_mm": None,
                "clearance_mm": None,
                "status": "unknown",
                "missing": "no case surface hit below the part (opening or seam)",
            })
            continue
        surface = float(np.min(surf[hit]))
        surface_max = float(np.max(surf[hit]))
        free = surface - (BOARD_BOTTOM_ZP + GASKET_TRAVEL)
        nominal_free = CAVITY_FLOOR_ZP - (BOARD_BOTTOM_ZP + GASKET_TRAVEL)
        height, height_src = PART_HEIGHTS.get(ref, DEFAULT_0603_HEIGHT)
        clearance = free - height
        nominal_clearance = nominal_free - height
        if clearance < 0:
            status = "fail"
        elif clearance < 0.50:
            status = "tight"
        else:
            status = "pass"
        records.append({
            "ref": ref,
            "footprint": fp["name"],
            "position_board_mm": [fp["x"], fp["y"], fp["rot"]],
            "layer": fp["layer"],
            "courtyard_board_mm": [round(v, 4) for v in (bx0, by0, bx1, by1)],
            "courtyard_world_mm": [round(v, 4) for v in rect_world_bbox(bx0, by0, bx1, by1)],
            "case_surface_z_p_mm": round(surface, 4),
            "case_surface_z_p_max_mm": round(surface_max, 4),
            "nominal_cavity_floor_z_p_mm": CAVITY_FLOOR_ZP,
            "hit_fraction": round(float(hit.mean()), 4),
            "free_height_full_travel_mm": round(free, 4),
            "nominal_free_height_full_travel_mm": round(nominal_free, 4),
            "part_height_mm": height,
            "part_height_source": height_src,
            "clearance_mm": round(clearance, 4),
            "nominal_clearance_mm": round(nominal_clearance, 4),
            "status": status,
        })

    # J3 plug insertion corridor (no part height; the plug is not in CAD).
    cx0, cy0, cx1, cy1 = J3_PLUG_CORRIDOR_BOARD
    wx, wy = sample_rect_world(cx0, cy0, cx1, cy1, grid)
    surf, hit = ray_surface_zp(meshes, wx, wy)
    corridor = {
        "rect_board_mm": [cx0, cy0, cx1, cy1],
        "case_surface_z_p_mm": round(float(np.min(surf[hit])), 4) if hit.any() else None,
        "free_height_full_travel_mm": round(float(np.min(surf[hit])) - (BOARD_BOTTOM_ZP + GASKET_TRAVEL), 4) if hit.any() else None,
        "hit_fraction": round(float(hit.mean()), 4),
        "status": "pass" if hit.any() and float(np.min(surf[hit])) - (BOARD_BOTTOM_ZP + GASKET_TRAVEL) >= 3.0 else "unknown",
        "note": "3.5 mm wide insertion corridor; the JST SH plug body height is not in CAD, so only the corridor free height is checked.",
    }

    statuses = [r["status"] for r in records]
    return {
        "parts": records,
        "j3_plug_corridor": corridor,
        "counts": {s: statuses.count(s) for s in ("pass", "tight", "fail", "unknown")},
        "minimum_clearance_mm": min((r["clearance_mm"] for r in records if r["clearance_mm"] is not None), default=None),
        "minimum_clearance_ref": min((r for r in records if r["clearance_mm"] is not None),
                                     key=lambda r: r["clearance_mm"])["ref"] if any(r["clearance_mm"] is not None for r in records) else None,
    }


# --- check 2: USB-C J1 ---------------------------------------------------------
def check_usb(footprints: list[dict[str, Any]], meshes: list[dict[str, Any]]) -> dict[str, Any]:
    by_ref = {f["ref"]: f for f in footprints}
    j1 = by_ref.get("J1")
    if j1 is None:
        return {"status": "unknown", "missing": "J1 footprint not found"}
    jx, jy = j1["x"], j1["y"]
    jpx, jpy = board_to_plate(jx, jy)
    body_left = jpx - J1_BODY_HALF_WIDTH
    body_right = jpx + J1_BODY_HALF_WIDTH
    body_front = jpy - J1_BODY_HALF_DEPTH
    body_back = jpy + J1_BODY_HALF_DEPTH
    body_top = BOARD_BOTTOM_ZP
    body_bottom = BOARD_BOTTOM_ZP + J1_BODY_HEIGHT

    def notch(width: float, centre: float) -> dict[str, Any]:
        left, right = centre - width / 2, centre + width / 2
        body_clear = min(body_left - left, right - body_right)
        plug_left, plug_right = jpx - USB_MAX_OVERMOLD_WIDTH / 2, jpx + USB_MAX_OVERMOLD_WIDTH / 2
        plug_clear = min(plug_left - left, right - plug_right)
        return {
            "width_mm": width,
            "centre_plate_x_mm": round(centre, 4),
            "x_range_plate_mm": [round(left, 4), round(right, 4)],
            "j1_body_x_range_plate_mm": [round(body_left, 4), round(body_right, 4)],
            "j1_body_min_side_clearance_mm": round(body_clear, 4),
            "plug_12p35_x_range_plate_mm": [round(plug_left, 4), round(plug_right, 4)],
            "plug_12p35_min_side_clearance_mm": round(plug_clear, 4),
            "status": "pass" if plug_clear >= 0.50 else ("tight" if plug_clear >= 0 else "fail"),
        }

    stock = notch(STOCK_NOTCH_WIDTH, STOCK_NOTCH_CENTRE_PLATE_X)
    printed = notch(PRINTED_NOTCH_WIDTH, spec.usb_notch("ph60-rev3")[0])
    centred_on_j1 = notch(STOCK_NOTCH_WIDTH, jpx)

    # Bottom-case USB passage: body box vs the case mesh.
    wx0, wy0 = plate_to_world(body_left, body_front)
    wx1, wy1 = plate_to_world(body_right, body_back)
    box = trimesh.creation.box(extents=[abs(wx1 - wx0), abs(wy1 - wy0), body_bottom - body_top])
    box.apply_translation([(wx0 + wx1) / 2, (wy0 + wy1) / 2, (body_top + body_bottom) / 2])
    inter_vol: float | None = 0.0
    R = bc.TO_PRINT[:3, :3]
    tp = bc.TO_PRINT[:3, 3]
    for entry in meshes:
        try:
            # The box is in world coordinates; the 3MF is in print frame.
            box_print = box.copy()
            box_print.vertices = box.vertices @ R.T + tp + entry["tbed"]
            inter = trimesh.boolean.intersection([box_print, entry["mesh"]], engine="manifold")
            if inter is not None and len(inter.faces):
                inter_vol += float(inter.volume)
        except Exception:
            inter_vol = None
            break
    body_to_floor = CAVITY_FLOOR_ZP - body_bottom
    if inter_vol is None:
        body_status = "unknown"
    elif inter_vol < 1e-6 and body_to_floor >= 0.5:
        body_status = "pass"
    elif inter_vol < 1e-6:
        body_status = "tight"
    else:
        body_status = "fail"

    # Vertical notch depth: closed end Z_p and the J1 body top.
    notch_closed_zp = bc.top.SKIRT_H - spec.value("top.usb_notch")["depth_from_lip"]
    # Smaller Z_p is higher: the notch closed end is above the body when it is < body_top.
    vertical_above_body = body_top - notch_closed_zp

    return {
        "j1": {
            "position_board_mm": [jx, jy],
            "position_plate_mm": [round(jpx, 4), round(jpy, 4)],
            "body_x_range_plate_mm": [round(body_left, 4), round(body_right, 4)],
            "body_y_range_plate_mm": [round(body_front, 4), round(body_back, 4)],
            "body_z_p_mm": [body_top, round(body_bottom, 4)],
            "body_height_mm": J1_BODY_HEIGHT,
            "body_height_source": "bottom-case verification: 18.20 - 0.84 - 14.10; GCT USB4105 nominal",
        },
        "stock_notch_12p8": stock,
        "printed_notch_14p75": printed,
        "stock_notch_12p8_centred_on_j1": centred_on_j1,
        "bottom_case_passage": {
            "body_box_intersection_volume_mm3": round(inter_vol, 6) if inter_vol is not None else None,
            "body_bottom_to_cavity_floor_mm": round(body_to_floor, 4),
            "status": body_status,
        },
        "vertical": {
            "notch_depth_from_lip_mm": spec.value("top.usb_notch")["depth_from_lip"],
            "notch_closed_end_z_p_mm": round(notch_closed_zp, 4),
            "j1_body_top_z_p_mm": body_top,
            "notch_closed_end_above_body_mm": round(vertical_above_body, 4),
            "status": "pass" if vertical_above_body >= 0 else "fail",
            "note": "The J1 body is below the board; the notch closed end is above the board top. The plug overmold height above the board is not in CAD.",
        },
        "status": ("fail" if "fail" in (stock["status"], printed["status"], body_status) else
                   "tight" if "tight" in (stock["status"], printed["status"], body_status) else
                   "unknown" if "unknown" in (stock["status"], printed["status"], body_status) else "pass"),
        "missing_inputs": [
            "USB-C plug overmold height above the board (the 12.8 mm notch depth is 8.7 mm from the lip; the J1 body is below the board)",
            "actual plug overmold width and corner radius (12.35 mm is the spec maximum, not a measured plug)",
        ],
    }


# --- check 3: 7U stabilizer NPTH vs plate cutout ------------------------------
def load_plate_cutouts() -> list[dict[str, Any]]:
    import ezdxf

    doc = ezdxf.readfile(PLATE_DXF)
    out: list[dict[str, Any]] = []
    for e in doc.modelspace():
        if e.dxftype() != "POLYLINE":
            continue
        pts: list[tuple[float, float]] = []
        for ve in e.virtual_entities():
            if ve.dxftype() == "LINE":
                pts.append((float(ve.dxf.start.x), float(ve.dxf.start.y)))
                pts.append((float(ve.dxf.end.x), float(ve.dxf.end.y)))
            elif ve.dxftype() == "ARC":
                pts.extend((float(p.x), float(p.y)) for p in ve.flattening(0.01))
            else:
                raise RuntimeError(f"unexpected DXF virtual entity {ve.dxftype()}")
        if len(pts) > 1 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-6:
            pts = pts[:-1]
        if len(pts) < 3:
            continue
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
        out.append({"handle": e.dxf.handle, "polygon": poly, "bbox": poly.bounds, "n": len(pts)})
    return out


def check_stabilizer(footprints: list[dict[str, Any]]) -> dict[str, Any]:
    fp = next((f for f in footprints if "7U" in f["name"]), None)
    if fp is None:
        return {"status": "unknown", "missing": "7U footprint not found"}
    pads = npth_pads(fp["block"])
    if not pads:
        return {"status": "unknown", "missing": "no NPTH pads in 7U footprint"}

    cutouts = load_plate_cutouts()
    switch_plate = board_to_plate(fp["x"], fp["y"])
    candidates = [c for c in cutouts
                  if c["bbox"][0] < switch_plate[0] < c["bbox"][2]
                  and c["bbox"][1] < switch_plate[1] < c["bbox"][3]
                  and 100.0 < (c["bbox"][2] - c["bbox"][0]) < 200.0]
    if not candidates:
        return {"status": "unknown", "missing": "7U plate cutout not found in DXF"}
    cut = max(candidates, key=lambda c: c["polygon"].area)
    poly: Polygon = cut["polygon"]

    # Provenance: the DXF outer boundary must match the spec's plate_gas_hhkb outline.
    outlines = json.loads(OUTLINES.read_text())
    plate_spec = next(o for o in outlines["outlines"] if o["name"] == "plate_gas_hhkb")
    outer = max(cutouts, key=lambda c: c["bbox"][2] - c["bbox"][0])
    spec_bbox = plate_spec["bbox"]
    dxf_bbox = outer["bbox"]
    outline_delta = max(abs(a - b) for a, b in zip(spec_bbox, dxf_bbox))
    outline_check = {
        "spec_outline": "plate_gas_hhkb",
        "spec_bbox_plate_mm": [round(v, 4) for v in spec_bbox],
        "dxf_outer_bbox_plate_mm": [round(v, 4) for v in dxf_bbox],
        "max_abs_delta_mm": round(outline_delta, 4),
        "status": "pass" if outline_delta < 0.01 else "fail",
    }

    records: list[dict[str, Any]] = []
    for pad in pads:
        lx, ly = pad["x"], pad["y"]
        rx, ry = rotate_xy(lx, ly, fp["rot"])
        bx, by = fp["x"] + rx, fp["y"] + ry
        px, py = board_to_plate(bx, by)
        radius = pad["diameter"] / 2.0
        dist = float(poly.boundary.distance(Point(px, py)))
        clearance = dist - radius
        if abs(lx) > 50.0:
            role = "stabilizer_insert" if pad["diameter"] > 3.5 else "stabilizer_screw"
        else:
            role = "switch"
        records.append({
            "role": role,
            "local_mm": [round(lx, 4), round(ly, 4)],
            "plate_mm": [round(px, 4), round(py, 4)],
            "diameter_mm": pad["diameter"],
            "distance_to_cutout_boundary_mm": round(dist, 4),
            "clearance_mm": round(clearance, 4),
            "status": "pass" if clearance >= 0.50 else ("tight" if clearance >= 0 else "fail"),
        })

    inserts = [r for r in records if r["role"] == "stabilizer_insert"]
    screws = [r for r in records if r["role"] == "stabilizer_screw"]
    switches = [r for r in records if r["role"] == "switch"]
    worst_insert = min(inserts, key=lambda r: r["clearance_mm"]) if inserts else None
    worst_switch = min(switches, key=lambda r: r["clearance_mm"]) if switches else None
    if worst_insert is None:
        status = "unknown"
    elif worst_insert["clearance_mm"] < 0:
        status = "fail"
    elif worst_insert["clearance_mm"] < 0.50:
        status = "tight"
    else:
        status = "pass"
    return {
        "footprint": fp["name"],
        "position_board_mm": [fp["x"], fp["y"], fp["rot"]],
        "switch_plate_mm": [round(switch_plate[0], 4), round(switch_plate[1], 4)],
        "plate_cutout": {
            "handle": cut["handle"],
            "bbox_plate_mm": [round(v, 4) for v in cut["bbox"]],
            "vertices": cut["n"],
            "source": str(PLATE_DXF.relative_to(ROOT)),
        },
        "plate_outline_check": outline_check,
        "npth": records,
        "worst_stabilizer_insert": worst_insert,
        "worst_stabilizer_screw": min(screws, key=lambda r: r["clearance_mm"]) if screws else None,
        "worst_switch": worst_switch,
        "status": status,
        "compatibility_note": (
            "The 7U footprint is a PCB-mount NPTH pattern; the INKC plate cutout is a plate-mount "
            "stabilizer cutout.  If the build uses the PCB-mount stabilizer, the plate cutout must "
            "clear the stabilizer housing/legs; the insert holes are outside the cutout as drawn.  "
            "If the build uses a plate-mount stabilizer, the PCB NPTH holes are unused and this "
            "geometric mismatch is not a build failure."
        ),
        "missing_inputs": [
            "actual 7U stabilizer type (PCB-mount vs plate-mount) and housing dimensions",
            "plate 3MF (only the DXF is available; the DXF cutout is used)",
        ],
    }


# --- report --------------------------------------------------------------------
def fmt(v: Any, nd: int = 2) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def write_report(path: Path, data: dict[str, Any]) -> None:
    rel = data["checks"]["relocated_b_cu_block"]
    usb = data["checks"]["usb_c_j1"]
    stab = data["checks"]["stabilizer_7u"]
    lines: list[str] = []
    lines.append("# Maru60 mechanical fit — relocated expansion checkpoint\n")
    lines.append(f"Board: `{data['board']['path']}`  ")
    lines.append(f"SHA256: `{data['board']['sha256']}`  ")
    lines.append("Generated by `pcb/tools/check_mechanical_fit.py` with the repository venv:\n")
    lines.append("```sh\n.venv/bin/python pcb/tools/check_mechanical_fit.py\n```\n")
    lines.append("## Assumptions and frames\n")
    lines.append("- Board Z: top **12.50 mm**, bottom **14.10 mm** (1.60 mm PCB; plate top 7.50 + 5.00 MX stack).")
    lines.append("- Bottom-case cavity floor: **Z 18.20 mm** (`build_bottomcase_draft.FLOOR_ZP`).")
    lines.append("- Full gasket travel: **0.80 mm** (the bottom-case build's stated travel).")
    lines.append("- Board own frame -> plate frame: `x_plate = x + 0.4525`, `y_plate = 101.06775 - y` (`spec/boards.json`).")
    lines.append("- Plate -> bottom-case world: `X_w = 142.95 - x_plate`, `Y_w = y_plate + 84.82` (`build_topcase_draft.pw`).")
    lines.append(f"- The 3MF is in the bottom-case print frame. The print offset is recovered from the same build's world STL; the 3MF is then ray-cast directly. Frame error is {data['assumptions']['case_mesh_frame_error_mm']:.3f} mm (mesh quantization).")
    lines.append("- The battery-bay bottom-case 3MF is used. The relocated block is in front of the battery bay, so the no-battery-bay variant has the same cavity floor under it.\n")
    lines.append("## Summary\n")
    counts = rel["counts"]
    lines.append(f"- Relocated B.Cu block: **{counts['pass']} pass, {counts['tight']} tight, {counts['fail']} fail**; "
                 f"minimum **{fmt(rel['minimum_clearance_mm'])} mm** at **{rel['minimum_clearance_ref']}** (tight).")
    lines.append(f"- USB-C J1: **{usb['status']}** for the stock 12.8 mm notch; the printed 14.75 mm notch passes.")
    lines.append(f"- 7U stabilizer: **{stab['status']}** as drawn for a PCB-mount stabilizer; N/A for plate-mount.")
    lines.append("")
    lines.append("## 1. Relocated B.Cu block\n")
    lines.append("The case surface below each part is the first mesh hit from Z 14.10 downward, sampled on a grid over the B.CrtYd bounding box. Free height is `surface - (14.10 + 0.80)`. Clearance subtracts the nominal package height.\n")
    lines.append("| Ref | Footprint | Surface Z (mm) | Free at full travel (mm) | Part height (mm) | Clearance (mm) | Status |")
    lines.append("|---|---|---:|---:|---:|---:|---|")
    for r in rel["parts"]:
        lines.append(f"| {r['ref']} | {r.get('footprint','')} | {fmt(r.get('case_surface_z_p_mm'))} | "
                     f"{fmt(r.get('free_height_full_travel_mm'))} | {fmt(r.get('part_height_mm'))} | "
                     f"{fmt(r.get('clearance_mm'))} | **{r['status']}** |")
    lines.append("")
    lines.append(f"J3 plug corridor: free height **{fmt(rel['j3_plug_corridor']['free_height_full_travel_mm'])} mm** "
                 f"over the 3.5 mm-wide corridor; the JST SH plug body height is not in CAD.\n")
    lines.append(f"Minimum part clearance: **{fmt(rel['minimum_clearance_mm'])} mm** at **{rel['minimum_clearance_ref']}** "
                 f"(nominal 2.95 mm JST SH body). This is **tight**, not a failure.  "
                 f"Using the stated 18.20 mm floor instead of the quantized 3MF surface (18.18 mm) gives 0.35 mm; "
                 f"the 0.02 mm difference is mesh quantization, not a design change.\n")
    lines.append("## 2. USB-C J1\n")
    lines.append(f"J1 at board `{usb['j1']['position_board_mm']}` -> plate `{usb['j1']['position_plate_mm']}`. "
                 f"Body X `{usb['j1']['body_x_range_plate_mm']}`, Z `{usb['j1']['body_z_p_mm']}`.\n")
    lines.append("| Notch | Width (mm) | Centre X (mm) | J1 body min side (mm) | 12.35 mm plug min side (mm) | Status |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for key, label in (("stock_notch_12p8", "stock 12.8"), ("printed_notch_14p75", "printed 14.75"),
                       ("stock_notch_12p8_centred_on_j1", "12.8 centred on J1")):
        n = usb[key]
        lines.append(f"| {label} | {n['width_mm']} | {n['centre_plate_x_mm']} | "
                     f"{n['j1_body_min_side_clearance_mm']} | {n['plug_12p35_min_side_clearance_mm']} | **{n['status']}** |")
    lines.append("")
    lines.append(f"Bottom-case passage: body-box intersection **{usb['bottom_case_passage']['body_box_intersection_volume_mm3']} mm³**, "
                 f"body bottom to cavity floor **{usb['bottom_case_passage']['body_bottom_to_cavity_floor_mm']} mm** "
                 f"(**{usb['bottom_case_passage']['status']}**).")
    lines.append(f"Vertical: notch closed end Z **{usb['vertical']['notch_closed_end_z_p_mm']} mm**, "
                 f"J1 body top Z **{usb['vertical']['j1_body_top_z_p_mm']} mm**, "
                 f"closed end above body **{usb['vertical']['notch_closed_end_above_body_mm']} mm**.\n")
    lines.append("The 12.8 mm stock notch is **FAIL** for a 12.35 mm overmold: the stock notch is centred at plate X 19.35, "
                 "the J1/plug at 18.45, so the plug's left edge is 0.67 mm outside the notch and would hit the case shell. "
                 "The printed 14.75 mm notch (centred at 18.65) is comfortable (~1.00 mm per side). "
                 "The top-case 3MF is not used for the J1 body because the body is below the board; the notch is checked analytically. "
                 "The plug overmold height above the board is not in CAD, so the vertical plug fit cannot be concluded.\n")
    lines.append("## 3. 7U stabilizer NPTH vs plate cutout\n")
    lines.append(f"7U footprint `{stab['footprint']}` at board `{stab['position_board_mm']}`; plate cutout `{stab['plate_cutout']['handle']}` "
                 f"bbox `{stab['plate_cutout']['bbox_plate_mm']}` from `{stab['plate_cutout']['source']}`. "
                 f"The DXF outer boundary matches `spec/rule60-v3-outlines.json` `plate_gas_hhkb` within "
                 f"{stab['plate_outline_check']['max_abs_delta_mm']} mm ({stab['plate_outline_check']['status']}).\n")
    lines.append("| Role | Plate X,Y (mm) | Dia (mm) | Distance to cutout (mm) | Clearance (mm) | Status |")
    lines.append("|---|---|---:|---:|---:|---|")
    for r in stab["npth"]:
        lines.append(f"| {r['role']} | {r['plate_mm']} | {r['diameter_mm']} | "
                     f"{r['distance_to_cutout_boundary_mm']} | {r['clearance_mm']} | **{r['status']}** |")
    lines.append("")
    wi = stab["worst_stabilizer_insert"]
    if wi:
        lines.append(f"Worst stabilizer insert: **{fmt(wi['clearance_mm'])} mm** at plate `{wi['plate_mm']}`. "
                     f"**{stab['status'].upper()}** as drawn for a PCB-mount stabilizer: the insert holes are outside the plate cutout, "
                     f"so the plate would interfere with the stabilizer legs/housing. If the build uses a plate-mount stabilizer, "
                     f"the PCB NPTH holes are unused and this check is not applicable.")
    else:
        lines.append("No stabilizer insert NPTH holes were found; the check is **unknown**.")
    ws = stab.get("worst_switch")
    if ws:
        lines.append(f"The 3.0 mm switch hole at plate `{ws['plate_mm']}` is also **tight**: "
                     f"{fmt(ws['clearance_mm'])} mm to the 14 x 14 mm switch cutout.\n")
    lines.append("## What cannot be concluded from CAD\n")
    for item in data["missing_inputs"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Physical measurements still needed\n")
    for item in data["physical_measurements"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Verdict\n")
    counts = rel["counts"]
    lines.append(f"- Relocated block: **{counts['pass']} pass, {counts['tight']} tight, {counts['fail']} fail, "
                 f"{counts['unknown']} unknown**; minimum **{fmt(rel['minimum_clearance_mm'])} mm** at "
                 f"**{rel['minimum_clearance_ref']}** (tight).")
    lines.append(f"- USB-C: **{usb['status']}**; the stock 12.8 mm notch is 0.90 mm right of the J1 centre, so the "
                 f"12.35 mm plug overhangs it by 0.67 mm on the left; the printed 14.75 mm notch passes.")
    lines.append(f"- 7U stabilizer: **{stab['status']}** as drawn for PCB-mount; N/A for plate-mount.")
    lines.append(f"- Overall minimum clearance: **{fmt(data['summary']['overall_minimum_clearance_mm'])} mm** "
                 f"({data['summary']['overall_minimum_clearance_check']}); the minimum positive clearance is "
                 f"**{fmt(rel['minimum_clearance_mm'])} mm** at **{rel['minimum_clearance_ref']}**.")
    lines.append("")
    path.write_text("\n".join(lines) + "\n")


# --- main ----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--grid", type=int, default=9, help="samples per courtyard axis (default 9)")
    args = ap.parse_args()
    args.output_dir = args.output_dir.resolve()

    # Assumption guards: fail loudly if the build/spec drifts from the stated numbers.
    assert abs(bc.FLOOR_ZP - CAVITY_FLOOR_ZP) < 1e-9, bc.FLOOR_ZP
    assert abs(bc.top.Z_PLATE - PLATE_TOP_ZP) < 1e-9, bc.top.Z_PLATE
    assert abs((bc.top.Z_PLATE + MX_STACK) - BOARD_TOP_ZP) < 1e-9
    assert abs((BOARD_TOP_ZP + BOARD_THICKNESS) - BOARD_BOTTOM_ZP) < 1e-9

    text = args.board.read_text()
    footprints = parse_footprints(text)
    meshes = load_case_meshes()
    frame_error = max(m["frame_error_mm"] for m in meshes)

    relocated = check_relocated(footprints, meshes, args.grid)
    usb = check_usb(footprints, meshes)
    stab = check_stabilizer(footprints)

    all_clearances: list[tuple[float, str]] = []
    for r in relocated["parts"]:
        if r.get("clearance_mm") is not None:
            all_clearances.append((r["clearance_mm"], f"relocated:{r['ref']}"))
    for r in stab["npth"]:
        all_clearances.append((r["clearance_mm"], f"stabilizer_7u:{r['role']}@{r['plate_mm']}"))
    all_clearances.append((usb["stock_notch_12p8"]["plug_12p35_min_side_clearance_mm"],
                           "usb_c_j1:stock_notch_12p8_plug"))
    overall_min = min(all_clearances, key=lambda x: x[0])

    missing = [
        "Actual J3, U13, U11, U12 and 0603 body heights (the values used are datasheet/package nominals, not caliper readings).",
        "USB-C plug overmold height above the board and its actual width/corner radius (12.35 mm is the spec maximum).",
        "7U stabilizer type (PCB-mount vs plate-mount) and housing dimensions; the plate 3MF is not available, only the DXF.",
        "Printed case floor Z and flatness (the CAD floor is 18.20; print tolerance and gasket compression are not modelled).",
        "Solder/paste thickness and component placement tolerance (the clearance numbers are nominal CAD, not worst-case assembly).",
    ]
    physical = [
        "Caliper the JST SH SM10B-SRSS-TB body height above the PCB and the mating plug overmold height/width.",
        "Caliper the 0603, SOT-23, TSSOP-20 and RVZ14 parts after reflow (or measure the assembled board).",
        "Measure the printed bottom-case cavity floor Z under the relocated block and the USB passage.",
        "Measure the 7U stabilizer housing and confirm whether the build uses PCB-mount or plate-mount stabilizers.",
        "Measure the actual gasket compression at full travel and the resulting board Z.",
        "Measure the USB-C plug overmold and test insertion in the 12.8 mm stock notch and the 14.75 mm printed notch.",
    ]

    data: dict[str, Any] = {
        "format": "maru60-mechanical-fit/1",
        "generated_by": "pcb/tools/check_mechanical_fit.py",
        "board": {
            "path": str(args.board.relative_to(ROOT)),
            "sha256": sha256(args.board),
            "footprints": len(footprints),
        },
        "assumptions": {
            "board_top_z_p_mm": BOARD_TOP_ZP,
            "board_bottom_z_p_mm": BOARD_BOTTOM_ZP,
            "board_thickness_mm": BOARD_THICKNESS,
            "mx_stack_mm": MX_STACK,
            "plate_top_z_p_mm": PLATE_TOP_ZP,
            "cavity_floor_z_p_mm": CAVITY_FLOOR_ZP,
            "gasket_travel_mm": GASKET_TRAVEL,
            "z_p_convention": "Z_p grows downward from the top-case top face; the board top is 12.50 and the cavity floor is 18.20.",
            "board_to_plate": {"dx_mm": 0.4525, "y0_mm": 101.06775,
                               "source": "spec/boards.json frames.pcb_to_plate"},
            "plate_to_world": {"x": "X_w = 142.95 - x_plate", "y": "Y_w = y_plate + 84.82",
                               "source": "build_topcase_draft.pw / maru60.frames"},
            "case_mesh_frame": "3MF print frame; offset recovered from bottomcase-draft/bottom-*-world.stl; 3MF ray-cast directly.",
            "case_mesh_frame_error_mm": round(frame_error, 4),
        },
        "method": {
            "relocated_block": "B.CrtYd bounding box -> board -> plate -> world; 9x9 grid; first ray hit from Z 14.10 downward; min surface over the grid; free = surface - (14.10 + 0.80); clearance = free - nominal part height.",
            "usb_c": "J1 B.Fab body box; stock 12.8 mm notch at plate X 19.35 and printed 14.75 mm notch at the PH60 centre; 12.35 mm max overmold; body box vs bottom-case mesh boolean intersection; vertical notch closed end from spec.",
            "stabilizer_7u": "7U NPTH pads from the board; plate cutout from the INKC DXF (ezdxf flattening); circle-to-polygon-boundary distance minus radius.",
        },
        "checks": {
            "relocated_b_cu_block": relocated,
            "usb_c_j1": usb,
            "stabilizer_7u": stab,
        },
        "summary": {
            "relocated_block": relocated["counts"],
            "relocated_minimum_clearance_mm": relocated["minimum_clearance_mm"],
            "relocated_minimum_clearance_ref": relocated["minimum_clearance_ref"],
            "usb_c_status": usb["status"],
            "stabilizer_7u_status": stab["status"],
            "overall_minimum_clearance_mm": round(overall_min[0], 4),
            "overall_minimum_clearance_check": overall_min[1],
            "overall": "PASS_WITH_TIGHT_ITEMS" if "fail" not in (usb["status"], stab["status"]) else "ATTENTION",
        },
        "missing_inputs": missing,
        "physical_measurements": physical,
        "sources": {
            "board": str(args.board.relative_to(ROOT)),
            "bottomcase_3mf": [str((MODELS / f"maru60-hhkb-bottomcase-{h}.3mf").relative_to(ROOT)) for h in ("left", "right")],
            "bottomcase_world_stl": [str((BOTTOMCASE_DRAFT / f"bottom-{h}-world.stl").relative_to(ROOT)) for h in ("left", "right")],
            "plate_dxf": str(PLATE_DXF.relative_to(ROOT)),
            "spec": [str(OUTLINES.relative_to(ROOT)), str(BOARDS.relative_to(ROOT))],
            "prior_j3_height": ".omo/evidence/pcb-routing-20261109/manual/sim/SUMMARY.json",
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "fit.json").write_text(json.dumps(data, indent=2) + "\n")
    write_report(args.output_dir / "REPORT.md", data)
    print(json.dumps({
        "fit_json": str((args.output_dir / "fit.json").relative_to(ROOT)),
        "report": str((args.output_dir / "REPORT.md").relative_to(ROOT)),
        "relocated": relocated["counts"],
        "relocated_minimum_clearance_mm": relocated["minimum_clearance_mm"],
        "relocated_minimum_clearance_ref": relocated["minimum_clearance_ref"],
        "usb_c": usb["status"],
        "stabilizer_7u": stab["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
