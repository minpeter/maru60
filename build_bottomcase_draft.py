"""Maru60 HHKB bottom case (draft), for the Rule60 V3: a printable tray that takes the stock plate, silicone gasket
caps, ball catches, battery-bay filler and back decoration plate, and nests in the stock top case or the printed one
(build_topcase_draft.py).

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
  - Cavity floor under the MX stack (plate top 7.50, PCB top 12.50); 140 x 45 battery bay, 4.69 deep as the stock bay
    (owner caliper; published 4.5), at the back, back decoration plate recess (INKC drawing) on the underside, USB-C
    slot under the top-case notch.
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
# Two bodies (owner): a ㄷ tray (both rails + floor, rail outline, from the rail tops down to `TRAY_BOTTOM_ZP`) and a
# triangular base under it, inset from the tray on every side so the tray bottom shows as a step all round. Back: the
# base leaves `BACK_LEDGE_W`, then one straight slope `BACK_SLOPE_LEN` long runs to the desk face (owner caliper +
# IMG_0465 edge trace 5.0 / 14.5 mm at 47 deg; the desk-face inset then follows, ~15.3 mm; the owner's direct reading
# was 18.61). Front: a vertical face `FRONT_STEP_W` in (owner ~4.5). Ends: `END_STEP_W` in (IMG_0463: the
# desk face reads ~283 mm long against 292 mm rails). All approximate.
TRAY_BOTTOM_ZP = top.SKIRT_H  # ㄷ tray bottom at the back rail: 10.32 below the rail tops (owner 10.12 +-), at the lip
BACK_LEDGE_W = 5.2       # Tray bottom showing behind the base, from the back rail face
BACK_SLOPE_LEN = 14.59   # Straight slope from the step's inner edge to the desk face
FRONT_STEP_W = 4.5       # Tray bottom showing in front of the base, from the front rail face (owner, approximate)
END_STEP_W = 4.5         # Tray bottom showing past each end of the base, from the rail ends
DECO_CLEAR = 0.20        # Recess around the 3 mm steel weight / decoration plate outline (INKC drawing), per side
DECO_FROM_SLOPE = 6.5    # Plate straight edge from the slope's desk-face edge, along the desk face (owner)
DECO_RECESS = 2.3        # Recess depth: the 3 mm plate stands 0.7 proud of the desk face (1.3 under the bumpons'
                         # 2.0). The plate's centre bump lies over the front of the 4.69 deep battery bay: 2.3 leaves
                         # 1.03 mm of floor between them; 2.5 left 0.83 and a flush 3.0 would leave 0.33
DECO = spec.outline("back_deco_plate")
# ㄴㄱ split (owner): the seam runs through one back and one front ball catch, so each of those two stock catch bodies
# bridges it with one M2 screw in each half; between them it crosses the floor in front of the battery bay. Staggered
# against the top-case seams (back at its BL strike, front at X = 0). Hybrid joint as on the top case: the two catch
# bodies, line-to-line plan dovetails on the floor seam (the halves slide together along the print Z axis, normal to
# the desk face, and the tongues lock both in-plane directions), glue, and the steel weight plate under the back leg.
_STRIKES_W = {n: top.pw(x, y) for n, x, y in top.strike_centers_p()}
SEAM_BACK_CATCH = next(n for n, (x, y) in _STRIKES_W.items() if y > 150.0 and x < 0.0)
SEAM_FRONT_CATCH = next(n for n, (x, y) in _STRIKES_W.items() if y < 150.0 and x > 0.0)
SEAM_BACK_X, SEAM_FRONT_X = _STRIKES_W[SEAM_BACK_CATCH][0], _STRIKES_W[SEAM_FRONT_CATCH][0]
SEAM_CROSS_Y = 120.0     # World Y (desk face) of the floor crossing: 18 mm in front of the bay, floor ~6 mm thick
DOVETAIL = {"neck_half": 5.2, "head_half": 6.6, "proj": 6.0, "neck_taper": 0.55}  # top-case wrist-rest profile
SEAM_DOVETAILS = [("cross", -30.0, "left"), ("cross", 0.0, "right"), ("cross", 30.0, "left"),
                  ("back", 130.0, "left"), ("front", 106.0, "right")]
# ^ (seam leg, world X on the crossing / world Y on a leg, half carrying the tongue). Floor at the seam: crossing 6.2 mm,
#   front leg 3.2-6.2 mm (tongue in ~4.7), back leg ~7 mm at its tongue but only 1.8-4.3 mm where it runs under the
#   battery bay and the weight-plate recess: a plain glued butt there, which the taped steel plate spans.
JOINT_TEST_BOX = (-22.0, 104.0, 22.0, 136.0)  # World XY around the middle crossing tongue: the joint test pair
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


def tray_bottom_zp(y: float) -> float:
    """Z_p of the ㄷ tray bottom at world Y: `TRAY_BOTTOM_ZP` at the back rail face, tilted 0.2 deg so the front rail
    edge meets the desk plane. Level with the rail tops, the front edge would hang 0.42 mm over the bed when printed
    desk face down, with nothing under its first layers."""
    k = (TRAY_BOTTOM_ZP - desk_zp(Y_FRONT)) / (Y_BACK - Y_FRONT)
    return desk_zp(Y_FRONT) + k * (y - Y_FRONT)


def tray_bottom_plane() -> tuple[list[float], float]:
    """Plane (normal, offset) keeping Z_p <= `tray_bottom_zp(y)`."""
    k = (TRAY_BOTTOM_ZP - desk_zp(Y_FRONT)) / (Y_BACK - Y_FRONT)
    n = np.array([0.0, k, -1.0]) / math.hypot(k, 1.0)
    return n.tolist(), float(n[1] * Y_FRONT + n[2] * desk_zp(Y_FRONT))


def _back_slope_inset() -> float:
    """Desk-face back edge, horizontally in from the back rail face: the step plus the slope's horizontal run."""
    y0 = Y_BACK - BACK_LEDGE_W
    z0 = tray_bottom_zp(y0)
    lo, hi = 0.0, BACK_SLOPE_LEN
    for _ in range(60):  # run h with h^2 + (desk_zp(y0 - h) - z0)^2 = L^2; the left side grows with h
        h = (lo + hi) / 2
        lo, hi = (h, hi) if h * h + (desk_zp(y0 - h) - z0) ** 2 < BACK_SLOPE_LEN ** 2 else (lo, h)
    return round(BACK_LEDGE_W + (lo + hi) / 2, 3)


BACK_BEVEL_INSET = _back_slope_inset()
BUMPON_SITES = [(130.0, "front", round(FRONT_STEP_W + 8.5, 2)), (-130.0, "front", round(FRONT_STEP_W + 8.5, 2)),
                (130.0, "back", round(BACK_BEVEL_INSET + 8.5, 2)), (-130.0, "back", round(BACK_BEVEL_INSET + 8.5, 2))]
# ^ world X, edge, centre distance from that rail face; each row clears the base edge by a 1.2 mm wall + 0.5 mm. Four
#   corners only (owner): with the wrist rest's front row they make 8; the v0.8 centre pair at X +-15 carried nothing
#   in a rigid-body load share (self weight, two wrists, typing at the centre and the Esc corner).


def back_bevel() -> tuple[list[float], float]:
    """Plane (normal, offset) of the back slope: material keeps n . (x, y, z_p) >= offset. It runs from the step's
    inner edge at the lip level to the desk face `BACK_BEVEL_INSET` in from the rail face."""
    ya = Y_BACK - BACK_LEDGE_W
    za = tray_bottom_zp(ya)
    yb = Y_BACK - BACK_BEVEL_INSET
    zb = desk_zp(yb)
    n = np.array([0.0, -(zb - za), -(ya - yb)])  # perpendicular to (0, yb - ya, zb - za), toward the front/top
    n /= np.linalg.norm(n)
    return n.tolist(), float(n[1] * ya + n[2] * za)


def base_outline() -> Any:
    """Plan (world XY) of the triangular base at the tray bottom: the rail outline inset by the steps. The ends are
    clean square cuts (owner): vertical faces, sharp corners."""
    x1 = abs(top.pw(RIM_P[0], 0.0)[0]) - END_STEP_W
    return orient(sg.box(-x1, Y_FRONT + FRONT_STEP_W, x1, Y_BACK - BACK_LEDGE_W))


def base_body() -> md.Manifold:
    """The triangular base: the base outline from the tray bottom down, cut by the back slope (the desk plane trims
    it with the tray in `build`)."""
    deep = desk_zp(Y_BACK) + 2.0
    return prism(base_outline(), TRAY_BOTTOM_ZP - 1.0, deep).trim_by_plane(*back_bevel())


def underside_zp(y: float) -> float:
    """Z_p of the case underside at world Y away from the ends: tray bottom, desk face or back slope."""
    if y < Y_FRONT + FRONT_STEP_W or y >= Y_BACK - BACK_LEDGE_W:
        return tray_bottom_zp(y)
    if y <= Y_BACK - BACK_BEVEL_INSET:
        return desk_zp(y)
    y0, y1 = Y_BACK - BACK_BEVEL_INSET, Y_BACK - BACK_LEDGE_W
    return desk_zp(y0) + (y - y0) / (y1 - y0) * (tray_bottom_zp(y1) - desk_zp(y0))


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
    y_edge = print_y(Y_BACK - BACK_BEVEL_INSET) + DECO_FROM_SLOPE  # print Y' grows toward the front
    return orient(sg.Polygon([(x - w / 2, y_edge + (h - y)) for x, y in pts]))


def build(board: str) -> tuple[md.Manifold, dict[str, Any]]:
    # ㄷ tray (rail outline, rail tops to the tray bottom) + the inset triangular base, both cut by the desk plane.
    rim = plate_box(*RIM_P, r=RIM_CORNER_R)
    tray = prism(rim, Z_RIM_TOP, desk_zp(Y_FRONT) + 1.0).trim_by_plane(*tray_bottom_plane())
    body = tray + base_body()
    body = body.trim_by_plane([0.0, SIN, -COS], -DESK_A * COS)  # keep Z_p <= desk plane

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
    cuts.append(from_print(prism(deco_poly_print().buffer(DECO_CLEAR, quad_segs=8), -1.0, DECO_RECESS)))
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
        "deco_recess_print": {"outline_bounds": [round(v, 3) for v in deco_poly_print().bounds], "depth": DECO_RECESS,
                              "plate_thickness": DECO["thickness"], "from_slope_edge": DECO_FROM_SLOPE,
                              "clear": DECO_CLEAR},
        "rim_clear": RIM_CLEAR,
        "split": {"shape": "ㄴㄱ", "back_catch": SEAM_BACK_CATCH, "back_x_world": SEAM_BACK_X,
                  "front_catch": SEAM_FRONT_CATCH, "front_x_world": SEAM_FRONT_X, "cross_y_world": SEAM_CROSS_Y,
                  "dovetails": [{"leg": leg, "at": at, "male": male, **DOVETAIL} for leg, at, male in SEAM_DOVETAILS],
                  "clearance": top.JOINT_CLEAR, "insertion_axis_world": FROM_PRINT[:, 2].round(9).tolist()},
        "tray_and_base": {"tray_bottom_z_p_front_back": [round(tray_bottom_zp(Y_FRONT), 3), TRAY_BOTTOM_ZP],
                          "back_step": BACK_LEDGE_W, "back_slope_length": BACK_SLOPE_LEN,
                          "front_step": FRONT_STEP_W, "end_step": END_STEP_W,
                          "desk_face_back_inset": BACK_BEVEL_INSET,
                          "base_outline_world": [round(v, 3) for v in base_outline().bounds]},
    }
    return body, report


def left_region_print() -> Any:
    """Print-plane (X, Y') region of the left half (world +X, keyboard left): X > `SEAM_BACK_X` behind the crossing,
    X > `SEAM_FRONT_X` in front of it, with the dovetail tongues added (left male) or taken out (right male)."""
    yc = print_y(SEAM_CROSS_Y)  # Y' grows toward the front
    region = sg.Polygon([(SEAM_BACK_X, -1e3), (1e3, -1e3), (1e3, 1e3), (SEAM_FRONT_X, 1e3), (SEAM_FRONT_X, yc),
                         (SEAM_BACK_X, yc)])
    for leg, at, male in SEAM_DOVETAILS:
        into_right = male == "left"
        if leg == "cross":  # tongue along +-Y' from the crossing; the left half owns its back side
            tongue = top.dovetail_poly(at, clear=0.0, **DOVETAIL)
            m = [0.0, 1.0, 1.0 if into_right else -1.0, 0.0, 0.0, yc]
        else:  # tongue along +-X from a leg at X = x0; the left half owns X > x0
            x0 = SEAM_BACK_X if leg == "back" else SEAM_FRONT_X
            tongue = top.dovetail_poly(print_y(at), clear=0.0, **DOVETAIL)
            m = [-1.0 if into_right else 1.0, 0.0, 0.0, 1.0, x0, 0.0]
        tongue = sa.affine_transform(tongue, m)
        region = region.union(tongue) if into_right else region.difference(tongue)
    assert region.geom_type == "Polygon" and not region.interiors, region.geom_type
    return orient(region)


def split(body: md.Manifold) -> tuple[md.Manifold, md.Manifold]:
    """Left and right halves along the ㄴㄱ seam, line-to-line (`top.JOINT_CLEAR` = 0), cut normal to the desk face."""
    region = from_print(prism(left_region_print(), -20.0, 80.0))
    return body ^ region, body - region


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
    left, right = split(body)
    coupon = body ^ md.Manifold.cube([120.0, 21.0, 60.0]).translate([30.0, Y_FRONT - 1.0, -5.0])
    jx0, jy0, jx1, jy1 = JOINT_TEST_BOX
    jbox = md.Manifold.cube([jx1 - jx0, jy1 - jy0, 80.0]).translate([jx0, jy0, -10.0])
    world = {"bottom-left": left, "bottom-right": right, "coupon-front-left": coupon,
             "joint-test-left": left ^ jbox, "joint-test-right": right ^ jbox}
    for name, m in world.items():
        to_trimesh(m).export(OUT / f"{name}-world.stl")
    printed = {name: on_bed(m) for name, m in world.items()}
    for name, tm in printed.items():
        assert len(tm.split(only_watertight=False)) == 1, name
        tm.export(OUT / f"{name}-print.stl")
    lic = "CC BY-NC 4.0 (non-commercial use only)"
    top.write_3mf(OUT / "maru60-hhkb-bottomcase-left.3mf", f"Maru60 HHKB bottom case, for Rule60 V3 - left half ({lic})",
                  [("BottomLeft", printed["bottom-left"])], fine_layer_z=None)
    top.write_3mf(OUT / "maru60-hhkb-bottomcase-right.3mf", f"Maru60 HHKB bottom case, for Rule60 V3 - right half ({lic})",
                  [("BottomRight", printed["bottom-right"])], fine_layer_z=None)
    top.write_3mf(OUT / "maru60-hhkb-bottomcase-fit-coupon.3mf", f"Maru60 HHKB bottom case fit coupon ({lic})",
                  [("CouponFrontLeft", printed["coupon-front-left"])], fine_layer_z=None)
    pair = [printed["joint-test-left"].copy(), printed["joint-test-right"].copy()]
    pair[0].apply_translation([-25.0, 0.0, 0.0])
    pair[1].apply_translation([25.0, 0.0, 0.0])
    top.write_3mf(OUT / "maru60-hhkb-bottomcase-joint-test.3mf", f"Maru60 HHKB bottom case joint test ({lic})",
                  [("JointTestLeft", pair[0]), ("JointTestRight", pair[1])], fine_layer_z=None)
    report["parts"] = {name: {"print_extents": [round(v, 2) for v in tm.extents], "volume_cm3": round(tm.volume / 1e3, 1)}
                       for name, tm in printed.items()}
    (OUT / "draft-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["parts"], indent=2))


if __name__ == "__main__":
    main()
