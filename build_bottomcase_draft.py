"""Rule 60 V3 HHKB bottom case (draft): a printable tray that takes the stock plate, silicone gasket caps, ball catches,
battery-bay filler and back decoration plate, and nests in the stock top case or the printed one (build_topcase_draft.py).

No caliper reading of the stock bottom case exists yet (the caliper displays in IMG_0462-0465 are out of frame), so the
geometry comes from the parts it mates with, plus the owner's photos IMG_0462-0474 for layout:
  - Outline: the top-case base pocket (caliper) less `RIM_CLEAR` per side, R2.7 corners (the stock rim held off an R5.0
    pocket by ~2.3 mm at the corners), from the rail tops at the 9.69 pocket floor they bear on straight down to the
    desk face: no step at the top-case lip, so the top-case skirt wraps the case from outside (owner, IMG_0463-0465).
  - Desk face on the plane the wrist rest stands on (6 deg): the floor is a wedge, ~0.4 mm below the lip at the front
    rail and ~12 mm at the back, so keyboard and wrist rest share one plane and the same SJ5012 bumpons (1.5 deep pockets).
  - Open ends, as the stock part (IMG_0462, 0472, 0473): only the front and back rails rise to the rim, full length;
    between them the cavity runs out through both short ends, closed there by the top-case side skirts.
  - The long rails carry the 6 gasket tabs: one open recess per tab whose floor holds the cap bottom flanges at
    `CAP_SEAT_ZP` (6.30 top-case seat + compressed caps + 1.5 plate), and a through notch per ball catch below the
    top-case strike pocket. The catch barrels rise past the rim top into that pocket: with the catch flush the balls
    would sit below the 12.7 strike-tongue tip; the stock pocket's end walls and screw-head lobes fit a raised catch.
  - Cavity floor under the MX stack (plate top 7.50, PCB top 12.50); 140 x 45 x 4.5 battery bay (published) at the
    back, back decoration plate recess (INKC drawing) on the underside, USB-C slot under the top-case notch.
  - Split at X = 0 into two halves for a 256 mm bed, each printed desk face down without supports.

Frames: the top-case print frame (`world`: X mirrored from the plate frame, Y from the wrist-rest front, Z_p down from the
top face) and each part's print frame (desk face on the bed). Usage: uv run build_bottomcase_draft.py [--board BOARD]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import manifold3d as md
import numpy as np
import shapely.affinity as sa
import shapely.geometry as sg
from shapely.geometry.polygon import orient
import trimesh

import build_topcase_draft as top
import rule60_spec as spec

OUT = Path(__file__).resolve().parent / "bottomcase-draft"
OUT.mkdir(exist_ok=True)

RIM_CLEAR = 0.15         # Rim to top-case pocket wall, per side
RIM_CORNER_R = 2.70      # Stock bottom-case rim corner radius (v6.2 fit: held ~2.3 mm off an R5.0 pocket)
Z_RIM_TOP = top.Z_FLOOR  # Rim top bears on the top-case pocket floor (9.69)
# No outer step (owner): below the top-case lip the case stays inside the top-case skirt; the rail faces run straight
# down to the desk face, and the floor between them is a 6-deg wedge, thin at the front and thick at the back.
PLATE_EDGE_CLEAR = 0.50  # Rail inner faces from the INKC 6095(gas) plate body edge (body Y)
# Gasket caps: top flange on the 6.30 top-case seat, PC plate, bottom flange on this seat (both flanges compressed alike).
CAP_SEAT_ZP = round(top.Z_PLATE + spec.value("plate.thickness") + spec.value("gasket.top_flange_compressed"), 2)  # 10.20
CAP_REACH = round(top.CAP_FOOT_L / 2 + top.CAP_CLEAR - top.CAP_INSET, 3)  # Recess end past the tab end (1.55), as top
CAP_SIDE = round(top.CAP_FOOT_W / 2 + top.CAP_CLEAR, 3)  # Recess skirt side from the cap centreline (2.65), as top
_CATCH = spec.value("ball_catch.catch_body")
CATCH_TOP_ZP = 7.60      # Catch barrel top: 0.60 under the strike plate (Z_p 5.55 + 1.45); the tongue tip is at 12.70
CATCH_FLOOR_ZP = round(CATCH_TOP_ZP + _CATCH["height"], 2)  # Notch floor the catch stands on (15.30)
CATCH_NOTCH_HALF_L = round(_CATCH["length"] / 2 + 0.30, 2)  # 0.30 mm room at each catch end
CATCH_SCREW_DX = round(top.STRIKE_PLATE_HALF_LEN + top.STRIKE_LOBE_REACH - top.STRIKE_LOBE_R, 3)  # 12.75 (lobe centre)
CATCH_SCREW_DY = round(top.STRIKE_POCKET_HALF_W - top.STRIKE_LOBE_R, 3)  # 1.575 toward the skirt (lobe centre)
PILOT_D, PILOT_MAX, PILOT_SKIN = 1.70, 4.00, 0.80  # M2 self-tapping pilots in PETG: depth up to 4.0, 0.8 skin left
FLOOR_ZP = 18.20         # Cavity floor: PCB 12.50-14.10 (1.6 mm), bottom USB-C body to ~17.36, ~0.8 mm gasket travel
_BAY = spec.value("bottom.battery_bay")
BAY_BACK_GAP = 4.0       # Battery bay from the back ledge face (IMG_0474: filler block against the back, centred in X)
# Back face (owner caliper + IMG_0465 edge trace, both approximate): vertical from the rail up to the top-case lip
# (A 10.12 measured, 10.32 kept), then a flat step `BACK_LEDGE_W` inward at the lip level, then one straight slope
# `BACK_SLOPE_LEN` long down to the desk face. The photo trace gives 5.0 / 14.5 mm and a 47 deg slope, matching both
# lengths; the desk-face inset then follows from the case height (~15.3 mm; the owner's direct B reading was 18.61).
BACK_BEVEL_START_ZP = top.SKIRT_H  # Step level on the back rail face (Z_p 20.01, the top-case lip)
BACK_LEDGE_W = 5.2       # Flat step inward from the back rail face at the lip level
BACK_SLOPE_LEN = 14.59   # Straight slope from the step's inner edge to the desk face
DECO_CLEAR = 0.20        # Recess around the 3 mm decoration plate outline, per side
DECO_BACK_D = 16.5       # Plate straight edge from the back rail face (IMG_0463: ~16): 1.2 mm in from the slope edge;
                         # further forward its centre bump leaves less than 1 mm over the battery bay
DECO = spec.outline("back_deco_plate")
SPLIT_GAP = 0.10         # Gap between the halves at X = 0
BED = 256.0

COS, SIN, TAN = math.cos(top.TILT_RAD), math.sin(top.TILT_RAD), math.tan(top.TILT_RAD)
DESK_A = top.z_desk_in_print_frame(0.0)  # Desk plane: Z_p = DESK_A + Y * TAN (the wrist-rest pad faces)
Y_FRONT = round(top.INNER_P[1] + RIM_CLEAR + top.DY_PW, 3)  # Front rail outer face (world Y)
Y_BACK = round(top.INNER_P[3] - RIM_CLEAR + top.DY_PW, 3)   # Back rail outer face (world Y)
# World -> print frame: desk face on the bed (Z' = height above it), X kept, Y' = -(Y cos + Z_p sin); a proper rotation.
TO_PRINT = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, -COS, -SIN, 0.0], [0.0, SIN, -COS, DESK_A * COS]])
FROM_PRINT = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, -COS, SIN, -DESK_A * COS * SIN], [0.0, -SIN, -COS, DESK_A * COS * COS]])


def desk_zp(y: float) -> float:
    return DESK_A + y * TAN


def _back_slope_inset() -> float:
    """Desk-face back edge, horizontally in from the back rail face: the step plus the slope's horizontal run."""
    y0, z0 = Y_BACK - BACK_LEDGE_W, BACK_BEVEL_START_ZP
    lo, hi = 0.0, BACK_SLOPE_LEN
    for _ in range(60):  # run h with h^2 + (desk_zp(y0 - h) - z0)^2 = L^2; the left side grows with h
        h = (lo + hi) / 2
        lo, hi = (h, hi) if h * h + (desk_zp(y0 - h) - z0) ** 2 < BACK_SLOPE_LEN ** 2 else (lo, h)
    return round(BACK_LEDGE_W + (lo + hi) / 2, 3)


BACK_BEVEL_INSET = _back_slope_inset()
BUMPON_SITES = [(130.0, "front", 11.0), (-130.0, "front", 11.0), (130.0, "back", round(BACK_BEVEL_INSET + 8.5, 2)),
                (-130.0, "back", round(BACK_BEVEL_INSET + 8.5, 2)), (15.0, "front", 11.0), (-15.0, "front", 11.0)]
# ^ world X, edge, centre distance from that rail face; the back row clears the slope by a 1.2 mm wall + 0.5 mm.


def back_bevel() -> tuple[list[float], float]:
    """Plane (normal, offset) of the back slope: material keeps n . (x, y, z_p) >= offset. It runs from the step's
    inner edge at the lip level to the desk face `BACK_BEVEL_INSET` in from the rail face."""
    ya, za = Y_BACK - BACK_LEDGE_W, BACK_BEVEL_START_ZP
    yb = Y_BACK - BACK_BEVEL_INSET
    zb = desk_zp(yb)
    n = np.array([0.0, -(zb - za), -(ya - yb)])  # perpendicular to (0, yb - ya, zb - za), toward the front/top
    n /= np.linalg.norm(n)
    return n.tolist(), float(n[1] * ya + n[2] * za)


def back_cut() -> md.Manifold:
    """Everything removed behind the back face below the lip level: the step and the slope."""
    deep = desk_zp(Y_BACK) + 2.0
    z0 = BACK_BEVEL_START_ZP
    behind_slope = md.Manifold.cube([400.0, BACK_BEVEL_INSET + 6.0, deep - z0]).translate(
        [-200.0, Y_BACK - BACK_BEVEL_INSET - 1.0, z0])
    n, off = back_bevel()
    behind_slope = behind_slope.trim_by_plane([-v for v in n], -off)
    step = md.Manifold.cube([400.0, BACK_LEDGE_W + 5.0, deep - z0]).translate([-200.0, Y_BACK - BACK_LEDGE_W, z0])
    return behind_slope + step


def underside_zp(y: float) -> float:
    """Z_p of the case underside at world Y: the desk face, the back slope, or the step at the lip level."""
    if y <= Y_BACK - BACK_BEVEL_INSET:
        return desk_zp(y)
    if y >= Y_BACK - BACK_LEDGE_W:
        return BACK_BEVEL_START_ZP
    t = (y - (Y_BACK - BACK_BEVEL_INSET)) / (BACK_BEVEL_INSET - BACK_LEDGE_W)
    return desk_zp(Y_BACK - BACK_BEVEL_INSET) + t * (BACK_BEVEL_START_ZP - desk_zp(Y_BACK - BACK_BEVEL_INSET))


def print_y(y: float) -> float:
    """Print-frame Y' of the desk-face point at world Y."""
    return -(y * COS + desk_zp(y) * SIN)


def plate_to_world(g: Any) -> Any:
    return orient(sa.affine_transform(g, [top.PW_SX, 0.0, 0.0, 1.0, top.PW_SX * top.DX_PW, top.DY_PW]))


def plate_box(x0: float, y0: float, x1: float, y1: float, r: float = 0.0) -> Any:
    b = sg.box(x0, y0, x1, y1)
    return plate_to_world(b.buffer(-r).buffer(r, quad_segs=16) if r else b)


def prism(poly: Any, z0: float, z1: float) -> md.Manifold:
    pts = np.asarray(orient(poly).exterior.coords[:-1], dtype=np.float64)
    return md.CrossSection([pts]).extrude(z1 - z0).translate([0.0, 0.0, z0])


def from_print(m: md.Manifold) -> md.Manifold:
    return m.transform(FROM_PRINT)


# Plate-frame inner faces of the front and back rails, from the 6095(gas) plate body (Y 5.57..101.916).
_BODY_Y = spec.value("plate.body_y")
LEDGE_FRONT_P = round(_BODY_Y[0] - PLATE_EDGE_CLEAR, 3)
LEDGE_BACK_P = round(_BODY_Y[1] + PLATE_EDGE_CLEAR, 3)
RIM_P = tuple(round(v + d, 3) for v, d in zip(top.INNER_P, (RIM_CLEAR, RIM_CLEAR, -RIM_CLEAR, -RIM_CLEAR)))


def cap_recesses_p() -> list[Any]:
    """Open gasket-cap recesses in the long ledges (plate frame): the top-case cap pocket plan (cap footprints + 0.65),
    run through the ledge into the cavity, R1.8 on the skirt-side corners."""
    polys = []
    for tabs, y_mid, sign, y_open in ((top.FRONT_TABS_P, top.WING_MID_Y_P[0], -1.0, LEDGE_FRONT_P + 1.0),
                                      (top.BACK_TABS_P, top.WING_MID_Y_P[1], 1.0, LEDGE_BACK_P - 1.0)):
        y_skirt = y_mid + sign * CAP_SIDE
        for xl, xr in tabs:
            x0, x1 = xl - CAP_REACH, xr + CAP_REACH
            box = sg.box(x0, min(y_skirt, y_open), x1, max(y_skirt, y_open))
            sharp = sg.box(x0, min(y_skirt - sign * top.CAP_POCKET_R, y_open), x1,
                           max(y_skirt - sign * top.CAP_POCKET_R, y_open))
            polys.append(box.buffer(-top.CAP_POCKET_R).buffer(top.CAP_POCKET_R, quad_segs=16).union(sharp).simplify(1e-4))
    return polys


def catch_sites_p() -> list[dict[str, Any]]:
    """Each strike (plate frame) with its catch notch and screw pilots; `skirt` is +1 when the outer wall is at +Y."""
    sites = []
    for name, sx, sy in top.strike_centers_p():
        skirt = 1.0 if sy > 50.0 else -1.0
        y_out = RIM_P[3] + 1.0 if skirt > 0 else RIM_P[1] - 1.0
        y_in = LEDGE_BACK_P - 1.0 if skirt > 0 else LEDGE_FRONT_P + 1.0
        sites.append({"name": name, "strike_p": [sx, sy], "skirt": skirt,
                      "notch_p": [sx - CATCH_NOTCH_HALF_L, min(y_out, y_in), sx + CATCH_NOTCH_HALF_L, max(y_out, y_in)],
                      "screws_p": [[round(sx + dx, 3), round(sy + skirt * CATCH_SCREW_DY, 3)]
                                   for dx in (-CATCH_SCREW_DX, CATCH_SCREW_DX)]})
    return sites


def bumpon_centres_world() -> list[tuple[float, float]]:
    return [(x, Y_FRONT + d if edge == "front" else Y_BACK - d) for x, edge, d in BUMPON_SITES]


def deco_poly_print() -> Any:
    """Back decoration plate outline (INKC drawing) in the print frame, true size on the desk face."""
    pts = spec.outline_points("back_deco_plate")
    w, h = DECO["bbox"][2], DECO["bbox"][3]
    y_edge = print_y(Y_BACK) + DECO_BACK_D  # print Y' grows toward the front
    return orient(sg.Polygon([(x - w / 2, y_edge + (h - y)) for x, y in pts]))


def build(board: str) -> tuple[md.Manifold, dict[str, Any]]:
    # One outline from the rail tops to the desk face: no step at the top-case lip, the skirt wraps it from outside.
    rim = plate_box(*RIM_P, r=RIM_CORNER_R)
    deep = desk_zp(Y_BACK) + 1.0
    body = prism(rim, Z_RIM_TOP, deep)
    body = body.trim_by_plane([0.0, SIN, -COS], -DESK_A * COS)  # keep Z_p <= desk plane
    body = body - back_cut()  # back face: step inward at the lip level, then a straight slope to the desk face

    # Cavity between the rails, through both short ends (no end walls).
    cuts = [prism(plate_box(RIM_P[0] - 1.0, LEDGE_FRONT_P, RIM_P[2] + 1.0, LEDGE_BACK_P), Z_RIM_TOP - 1.0, FLOOR_ZP)]
    cuts += [prism(plate_to_world(p), Z_RIM_TOP - 1.0, CAP_SEAT_ZP) for p in cap_recesses_p()]
    sites = catch_sites_p()
    pilots = []
    for s in sites:
        cuts.append(prism(plate_box(*s["notch_p"]), Z_RIM_TOP - 1.0, CATCH_FLOOR_ZP))
        for xp, yp in s["screws_p"]:
            xw, yw = top.pw(xp, yp)
            depth = round(min(PILOT_MAX, underside_zp(yw) - CATCH_FLOOR_ZP - PILOT_SKIN), 2)
            pilots.append({"world": [xw, yw], "depth": depth})
            cuts.append(md.Manifold.cylinder(depth + 0.5, PILOT_D / 2, PILOT_D / 2, 24).translate(
                [xw, yw, CATCH_FLOOR_ZP - 0.5]))
    usb_x, usb_w = top.usb_notch_print(board)
    usb_y0, usb_y1 = top.pw(0.0, LEDGE_BACK_P - 1.0)[1], top.pw(0.0, RIM_P[3] + 1.0)[1]
    cuts.append(prism(sg.box(usb_x - usb_w / 2, usb_y0, usb_x + usb_w / 2, usb_y1), Z_RIM_TOP - 1.0, top.SKIRT_H))
    bay_y1 = LEDGE_BACK_P - BAY_BACK_GAP
    bay_cx = -top.DX_PW  # plate X of the case centre line (world X = 0)
    bay_p = (bay_cx - _BAY["length"] / 2, bay_y1 - _BAY["width"], bay_cx + _BAY["length"] / 2, bay_y1)
    cuts.append(prism(plate_box(*bay_p, r=_BAY["corner_r"]), FLOOR_ZP - 1.0, FLOOR_ZP + _BAY["height"]))
    # Underside features, square to the desk face (print frame), mapped back to the world frame.
    pocket_r = top.POCKET_D / 2
    for xw, yw in bumpon_centres_world():
        cuts.append(from_print(md.Manifold.cylinder(top.POCKET_DEPTH + 1.0, pocket_r, pocket_r, 64).translate(
            [xw, print_y(yw), -1.0])))
    deco_t = DECO["thickness"]
    cuts.append(from_print(prism(deco_poly_print().buffer(DECO_CLEAR, quad_segs=8), -1.0, deco_t)))
    body = body - md.Manifold.batch_boolean(cuts, md.OpType.Add)

    report = {
        "board": board,
        "frames": {"world": "top-case print frame (topcase-draft): X_w = -(X_plate + DX_PW), Y_w = Y_plate + DY_PW, Z_p",
                   "to_print_3x4": TO_PRINT.round(9).tolist()},
        "z_p": {"rim_top": Z_RIM_TOP, "cap_seat": CAP_SEAT_ZP, "catch_top": CATCH_TOP_ZP, "catch_floor": CATCH_FLOOR_ZP,
                "cavity_floor": FLOOR_ZP, "bay_floor": round(FLOOR_ZP + _BAY["height"], 2), "lip": top.SKIRT_H,
                "desk_at_y0": round(DESK_A, 6), "desk_tan": round(TAN, 9)},
        "plate_frame": {"rim": RIM_P, "rim_corner_r": RIM_CORNER_R, "ledge_front_y": LEDGE_FRONT_P,
                        "ledge_back_y": LEDGE_BACK_P, "open_ends": "no short walls: the cavity runs through both ends",
                        "battery_bay": [round(v, 3) for v in bay_p], "cap_recesses": [[round(v, 3) for v in p.bounds]
                                                                                      for p in cap_recesses_p()]},
        "catches": [{**s, "pilots": pilots[2 * k:2 * k + 2]} for k, s in enumerate(sites)],
        "usb_slot_world": {"x": usb_x, "width": usb_w, "y": [usb_y0, usb_y1], "z_p": [Z_RIM_TOP, top.SKIRT_H]},
        "bumpons_world": [[x, round(y, 3)] for x, y in bumpon_centres_world()],
        "bumpon_pocket": {"d": top.POCKET_D, "depth": top.POCKET_DEPTH},
        "deco_recess_print": {"outline_bounds": [round(v, 3) for v in deco_poly_print().bounds], "depth": deco_t,
                              "clear": DECO_CLEAR},
        "split_x_world": 0.0, "split_gap": SPLIT_GAP, "rim_clear": RIM_CLEAR,
        "back_bevel": {"step_z_p": BACK_BEVEL_START_ZP, "step_width": BACK_LEDGE_W, "slope_length": BACK_SLOPE_LEN,
                       "inset_at_desk_face": BACK_BEVEL_INSET,
                       "desk_face_back_edge_world_y": round(Y_BACK - BACK_BEVEL_INSET, 3)},
    }
    return body, report


def to_trimesh(m: md.Manifold) -> trimesh.Trimesh:
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=True)
    assert tm.is_watertight and tm.is_winding_consistent, "non-manifold export"
    return tm


def on_bed(m: md.Manifold) -> trimesh.Trimesh:
    tm = to_trimesh(m.transform(TO_PRINT))
    (x0, y0, z0), (x1, y1, _) = tm.bounds
    assert x1 - x0 <= BED and y1 - y0 <= BED, (x1 - x0, y1 - y0)
    tm.apply_translation([BED / 2 - (x0 + x1) / 2, BED / 2 - (y0 + y1) / 2, -z0])
    return tm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", choices=spec.board_ids(), default=spec.default_board(),
                    help="PCB whose USB-C position sets the slot (spec/boards.json); default: %(default)s")
    args = ap.parse_args()
    body, report = build(args.board)
    halves = {"left": body.trim_by_plane([1.0, 0.0, 0.0], SPLIT_GAP / 2),     # world +X: keyboard left, USB side
              "right": body.trim_by_plane([-1.0, 0.0, 0.0], SPLIT_GAP / 2)}
    coupon = body ^ md.Manifold.cube([120.0, 21.0, 60.0]).translate([30.0, Y_FRONT - 1.0, -5.0])
    world = {"bottom-left": halves["left"], "bottom-right": halves["right"], "coupon-front-left": coupon}
    for name, m in world.items():
        to_trimesh(m).export(OUT / f"{name}-world.stl")
    printed = {name: on_bed(m) for name, m in world.items()}
    for name, tm in printed.items():
        assert len(tm.split(only_watertight=False)) == 1, name
        tm.export(OUT / f"{name}-print.stl")
    lic = "CC BY-NC 4.0 (non-commercial use only)"
    top.write_3mf(OUT / "rule60-hhkb-bottomcase-left.3mf", f"Rule 60 V3 HHKB bottom case, left half ({lic})",
                  [("BottomLeft", printed["bottom-left"])], fine_layer_z=None)
    top.write_3mf(OUT / "rule60-hhkb-bottomcase-right.3mf", f"Rule 60 V3 HHKB bottom case, right half ({lic})",
                  [("BottomRight", printed["bottom-right"])], fine_layer_z=None)
    top.write_3mf(OUT / "rule60-hhkb-bottomcase-fit-coupon.3mf", f"Rule 60 V3 bottom case fit coupon ({lic})",
                  [("CouponFrontLeft", printed["coupon-front-left"])], fine_layer_z=None)
    report["parts"] = {name: {"print_extents": [round(v, 2) for v in tm.extents], "volume_cm3": round(tm.volume / 1e3, 1)}
                       for name, tm in printed.items()}
    (OUT / "draft-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["parts"], indent=2))


if __name__ == "__main__":
    main()
