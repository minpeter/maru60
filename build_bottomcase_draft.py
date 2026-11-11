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
    (owner caliper; published 4.5), at the back, back decoration plate recess (INKC drawing) on the underside with four
    counterbored M2 holes from the cavity to screw the steel plate on as the stock case does, USB-C slot under the
    top-case notch, with a separate lower-case bridge over the USB passage (floor at the tray bottom, back slope uncut). The battery bay can be omitted
    with --no-battery-bay for a wired build; all other cuts, including the underside weight-plate recess, remain.
  - Split at X = 0 into two halves for a 256 mm bed, printed desk face down with support under the USB bridge.

Frames: the top-case print frame (`world`: X mirrored from the plate frame, Y from the wrist-rest front, Z_p down from the
top face) and each part's print frame (desk face on the bed).
Usage: uv run build_bottomcase_draft.py [--board BOARD] [--catches {stock,luban32}] [--inserts | --no-inserts] [--battery-bay | --no-battery-bay]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

import manifold3d as md
import numpy as np
import shapely.affinity as sa
import shapely.geometry as sg
from shapely.geometry.polygon import orient
import trimesh

import build_topcase_draft as top
import rule60_spec as spec
from maru60.mesh_io import to_trimesh, write_3mf
from maru60.paths import bottomcase_dir
from maru60.frames import DX_PW, DY_PW, PW_SX, pw

OUT = bottomcase_dir()

RIM_CLEAR = 0.15         # Rim to the caliper inner skirt, per side (printed 111.46 wide; stock 111.63); the printed top
                         # case adds `POCKET_GROW` on top
RIM_CORNER_R = 2.70      # Stock bottom-case rim corner radius (v6.2 fit: held ~2.3 mm off an R5.0 pocket)
Z_RIM_TOP = top.Z_FLOOR  # Rim top bears on the top-case pocket floor (9.69)
# No outer step (owner): below the top-case lip the case stays inside the top-case skirt; the rail faces run straight
# down to the desk face, and the floor between them is a 6-deg wedge, thin at the front and thick at the back.
PLATE_EDGE_CLEAR = 0.50  # Rail inner faces from the INKC 6095(gas) plate body edge (body Y)
# Gasket caps: top flange on the 6.30 top-case seat, PC plate, bottom flange on this seat. A seat 0.51 below the rim
# (3.90 seat gap) printed 0.7-0.9 deep and over-squeezed the caps, pushing the assembled case open against the stock
# catches; the stock case reads 1.2-1.5 (owner caliper, 2026-11-10). `CAP_SEAT_RELIEF` sets the seat 1.05 below the rim
# (4.44 gap), which should print about 1.3 deep, inside the stock range.
CAP_SEAT_RELIEF = 0.54
CAP_SEAT_ZP = round(top.Z_PLATE + spec.value("plate.thickness") + spec.value("gasket.top_flange_compressed")
                    + CAP_SEAT_RELIEF, 2)  # 10.74
CAP_REACH = round(top.CAP_FOOT_L / 2 + top.CAP_CLEAR - top.CAP_INSET, 3)  # Recess end past the tab end (1.55), as top
CAP_SIDE = round(top.CAP_FOOT_W / 2 + top.CAP_CLEAR, 3)  # Recess skirt side from the cap centreline (2.65), as top
CAP_MOUTH_R = 0.50      # Round the closed end of the USB-side cap entry, preserving the flat bearing seat and its height
_CATCH = spec.value("ball_catch.catch_body")
CATCH_TOP_ZP = 7.60      # Catch barrel top: 0.60 under the strike plate (Z_p 5.55 + 1.45); the tongue tip is at 12.70
CATCH_FLOOR_ZP = round(CATCH_TOP_ZP + _CATCH["height"], 2)  # Notch floor the catch stands on (15.30)
CATCH_NOTCH_HALF_L = round(_CATCH["length"] / 2 + 0.60, 2)  # 0.60 mm room at each catch end (length photo-read +-0.5)
PILOT_D, PILOT_MAX, PILOT_SKIN = 1.70, 4.00, 0.80  # M2 self-tapping pilots in PETG: depth up to 4.0, 0.8 skin left
STOCK_INSERT_DEPTH = 3.55  # CANOT OD3.5/L3 blind bore depth on the stock catch seat (15.30..18.85, >= 1.16 skin left)
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
SLOT_MIN_WALL = 0.8      # Rail left between the USB-C slot and a cap recess: anything thinner (under two 0.4 mm
                         # perimeters) is cut away, so the slot opens into the recess instead of leaving a fin
USB_BRIDGE_BOTTOM_ZP = 11.90  # Roof underside; its top is flush with the surrounding rim, not a separate recessed beam
# The passage floor stops at the tray bottom (owner, IMG_0795-0800): it leaves over the open back step and the back
# slope under it stays whole, instead of a slot cut down through the slope that printed as a stair-stepped groove.
# 0.05 under the tray bottom so no film is left; the 12.35 x 6.5 plug gauge with 0.8 mm gasket travel reaches 19.78.
USB_TUNNEL_FLOOR_ZP = round(TRAY_BOTTOM_ZP + 0.05, 2)  # 20.06
USB_PORT_POCKET_DEPTH = 2.44  # Bounded recess in front of the port: stock depth below the cavity floor (owner
                              # caliper 2026-11-10, 2.44; a first reading gave 2.9)
USB_PORT_POCKET_W = 15.5     # Across X, centred on the port (owner caliper, long side)
USB_PORT_POCKET_L = 11.4     # Front edge to the back of the rail notch, notch included (owner caliper, short side)
USB_PORT_POCKET_R = 2.0      # Front corners; the back end opens square into the passage (radius not measured)
USB_RAIL_NOTCH_D = 2.0       # Stock: the pocket's end-mill pass also shaves the rail's inner wall face, full height,
                             # to the pocket width with the same R2 corners (owner: ~1.5-2 mm deep, same curvature as the
                             # pocket). Depth = R keeps both quarter arcs whole and tangent to the pocket sides
DECO_CLEAR = 0.20        # Recess around the steel weight / decoration plate outline (INKC drawing), per side
DECO_FROM_SLOPE = 6.5    # Plate straight edge from the slope's desk-face edge, along the desk face (owner)
DECO_RECESS = 2.3        # Recess depth: the 2.88 mm plate stands 0.58 proud of the desk face (1.42 under the bumpons'
                         # 2.0). The plate's centre bump lies over the front of the 4.69 deep battery bay: 2.3 leaves
                         # 1.03 mm of floor between them; 2.5 left 0.83 and a flush 3.0 would leave 0.33
DECO = spec.outline("back_deco_plate")
DECO_T = spec.value("bottom.weight_plate_thickness")  # Caliper; the drawing label says 3 mm
DECO_SCREWS = spec.value("bottom.weight_plate_holes")  # Tapped holes of the stock plate, plate-outline frame (photo)
DECO_SCREW_HOLE_D = 3.0  # Through the floor for the M2 shank: 0.5 mm float per side covers the photo-read positions
DECO_SCREW_CBORE_D = 5.4  # Counterbore from the cavity side for an M2 head up to 4.0 (socket cap 3.8, pan 4.0), same float
DECO_SCREW_CLAMP = 2.5  # Floor under each head: an M2 x 4 screw reaches 1.5 mm into the 2.88 mm plate, its tip 1.38 short
DECO_SCREW_LEN = 4.0    # of the outer face (the stock holes are blind); the head sits 2.2-4.3 mm below the cavity floor
# ㄴㄱ split (owner): the seam runs through one back and one front ball catch, so each of those two stock catch bodies
# bridges it with one M2 screw in each half; between them it crosses the floor in front of the battery bay. Staggered
# against the top-case seams (back at its BL strike, front at X = 0). Hybrid joint matching the top case: the two catch
# bodies, five ramped sliding dovetails with chevron compression ribs and a 0.20 mm vertical glue line above a blind
# desk-face roof (LeftHalf carries all five tongues and slides down normal to the desk face into RightHalf's sockets),
# glue, and the steel weight plate under the back leg, screwed to each half with two of its four M2 screws.
_STRIKES_W = {n: pw(x, y) for n, x, y in top.strike_centers_p()}
SEAM_BACK_CATCH = next(n for n, (x, y) in _STRIKES_W.items() if y > 150.0 and x < 0.0)
SEAM_FRONT_CATCH = next(n for n, (x, y) in _STRIKES_W.items() if y < 150.0 and x > 0.0)
SEAM_BACK_X, SEAM_FRONT_X = _STRIKES_W[SEAM_BACK_CATCH][0], _STRIKES_W[SEAM_FRONT_CATCH][0]
SEAM_CROSS_Y = 120.0     # World Y (desk face) of the floor crossing: 18 mm in front of the bay, floor ~6 mm thick
SEAM_Z_STOP = 0.80       # Blind socket floor on the desk face (4 x 0.20 mm layers): straight seam on the underside
SEAM_Z_TONGUE = round(SEAM_Z_STOP + top.JOINT_Z_CLEAR, 3)  # Tongue landing (1.00 mm): 0.20 mm vertical glue gap
SEAM_LAND = 0.80         # Flat horizontal landing before the print ramp (two 0.4 mm perimeters; < 2 mm, no support)
SEAM_RAMP_SLOPE = 1.05   # Self-supporting print ramp slope dz'/du (46.4 deg above horizontal); socket fill matches it
SEAM_RIB_TOP = 3.30      # Chevron compression ribs reach SEAM_Z_TONGUE + SEAM_RIB_TOP (4.30 mm), below the cavity floor
DOVETAIL = {"neck_half": 5.0, "head_half": 6.2, "proj": 3.8, "neck_taper": 0.55}
SEAM_DOVETAILS = [("cross", -30.0, "left"), ("cross", 0.0, "left"), ("cross", 30.0, "left"),
                  ("back", 128.5, "left"), ("front", 111.0, "left")]
# ^ (seam leg, world X on the crossing / world Y on a leg, half carrying the tongue). Floor at the seam: crossing 6.2 mm,
#   front leg 4.6-6.0 mm across the tongue, back leg ~7 mm at its tongue and 1.6-4.6 mm where it runs under the battery
#   bay and the weight-plate recess: a straight glued butt there, which the screwed steel plate spans.
JOINT_TEST_BOX = (-22.0, 104.0, 22.0, 136.0)  # World XY around the middle crossing tongue: the joint test pair
BED = 256.0

COS, SIN, TAN = math.cos(top.TILT_RAD), math.sin(top.TILT_RAD), math.tan(top.TILT_RAD)
DESK_A = top.z_desk_in_print_frame(0.0)  # Desk plane: Z_p = DESK_A + Y * TAN (the wrist-rest pad faces)
Y_FRONT = round(top.STOCK_INNER_P[1] + RIM_CLEAR + DY_PW, 3)  # Front rail outer face (world Y)
Y_BACK = round(top.STOCK_INNER_P[3] - RIM_CLEAR + DY_PW, 3)   # Back rail outer face (world Y)
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
#   corners only (owner): with the wrist rest's front row they make 7 (8 before top case v7.13); the v0.8 centre pair
#   at X +-15 carried nothing in a rigid-body load share (self weight, two wrists, typing at the centre and the Esc
#   corner).


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
    x1 = abs(pw(RIM_P[0], 0.0)[0]) - END_STEP_W
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
    return orient(sa.affine_transform(g, [PW_SX, 0.0, 0.0, 1.0, PW_SX * DX_PW, DY_PW]))


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
RIM_P = tuple(round(v + d, 3) for v, d in zip(top.STOCK_INNER_P, (RIM_CLEAR, RIM_CLEAR, -RIM_CLEAR, -RIM_CLEAR)))


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


def catch_sites_p(*, purchased: bool = False, luban: bool = False) -> list[dict[str, Any]]:
    """Each strike (plate frame) with its catch notch and screw pilots; `skirt` is +1 when the outer wall is at +Y."""
    sites = []
    half_l = round(top.LUBAN["catch"]["length"] / 2 + 0.30, 2) if luban else CATCH_NOTCH_HALF_L
    for name, sx, sy in top.strike_centers_p(purchased=purchased, luban=luban):
        skirt = 1.0 if sy > 50.0 else -1.0
        y_out = RIM_P[3] + 1.0 if skirt > 0 else RIM_P[1] - 1.0
        y_in = LEDGE_BACK_P - 1.0 if skirt > 0 else LEDGE_FRONT_P + 1.0
        notch = [sx-16.1, sy-4.3, sx+16.1, sy+4.3] if purchased else [
            sx - half_l, min(y_out, y_in), sx + half_l, max(y_out, y_in)]
        sites.append({"name": name, "strike_p": [sx, sy], "skirt": skirt,
                      "notch_p": notch,
                      "screws_p": [list(axis) for axis in top.catch_screw_axes_p(sx, sy, purchased=purchased, luban=luban)]})
    return sites


def bumpon_centres_world() -> list[tuple[float, float]]:
    return [(x, Y_FRONT + d if edge == "front" else Y_BACK - d) for x, edge, d in BUMPON_SITES]


def deco_to_print(x: float, y: float) -> tuple[float, float]:
    """Weight-plate outline frame (X along its length, Y 0 at the bump tip) -> print frame (X, Y'): centred on X = 0, its
    straight back edge `DECO_FROM_SLOPE` in front of the slope's desk-face edge (print Y' grows toward the front)."""
    y_edge = print_y(Y_BACK - BACK_BEVEL_INSET) + DECO_FROM_SLOPE
    return x - DECO["bbox"][2] / 2, y_edge + DECO["bbox"][3] - y


def deco_poly_print() -> Any:
    """Back decoration plate outline (INKC drawing) in the print frame, true size on the desk face."""
    return orient(sg.Polygon([deco_to_print(x, y) for x, y in spec.outline_points("back_deco_plate")]))


def cavity_floor_print_z(y_p: float) -> float:
    """Print Z' of the cavity floor (Z_p = `FLOOR_ZP`) above print Y'."""
    y = -(y_p + FLOOR_ZP * SIN) / COS
    return SIN * y - COS * FLOOR_ZP + DESK_A * COS


def deco_screws_print(holes: list[list[float]] | None = None) -> list[dict[str, Any]]:
    """Weight-plate screw axes, normal to the desk face like the plate's tapped holes: print (X, Y'), the counterbore
    floor `DECO_SCREW_CLAMP` above the recess roof, and the cavity floor Z' on the axis."""
    sites = []
    for x, y in DECO_SCREWS["holes"] if holes is None else holes:
        px, py = deco_to_print(x, y)
        sites.append({"plate": [x, y], "print": [px, py], "cbore_floor_z": DECO_RECESS + DECO_SCREW_CLAMP,
                      "cavity_floor_z": cavity_floor_print_z(py)})
    return sites


def build(board: str, *, battery_bay: bool = True, inserts: bool = False, catch_inserts: bool = False,
          purchased_catches: bool = False, insert_hole_d: float = 3.2,
          weight_holes: list[list[float]] | None = None,
          sculpted_catches: bool = False, luban_catches: bool = False) -> tuple[md.Manifold, dict[str, Any]]:
    if (inserts or luban_catches) and (catch_inserts or purchased_catches or sculpted_catches):
        raise ValueError("Published catch/insert options cannot be combined with the separate local catch studies")
    purchased_catches = purchased_catches or sculpted_catches
    catch_inserts = catch_inserts or purchased_catches
    insert = dict(top.PURCHASED_INSERT if purchased_catches else top.CATCH_INSERT)
    if sculpted_catches:
        insert["depth"] = top.SCULPTED_CATCH["depth"]
    catch_floor = (top.LUBAN_CATCH_Z if luban_catches else top.SCULPTED_CATCH["catch_z"] if sculpted_catches
                   else top.PURCHASED_CATCH_Z if purchased_catches else CATCH_FLOOR_ZP)
    # ㄷ tray (rail outline, rail tops to the tray bottom) + the inset triangular base, both cut by the desk plane.
    rim = plate_box(*RIM_P, r=RIM_CORNER_R)
    tray = prism(rim, Z_RIM_TOP, desk_zp(Y_FRONT) + 1.0).trim_by_plane(*tray_bottom_plane())
    body = tray + base_body()
    body = body.trim_by_plane([0.0, SIN, -COS], -DESK_A * COS)  # keep Z_p <= desk plane

    # Cavity between the rails, through both short ends (no end walls).
    cuts = [prism(plate_box(RIM_P[0] - 1.0, LEDGE_FRONT_P, RIM_P[2] + 1.0, LEDGE_BACK_P), Z_RIM_TOP - 1.0, FLOOR_ZP)]
    cuts += [prism(plate_to_world(p), Z_RIM_TOP - 1.0, CAP_SEAT_ZP) for p in cap_recesses_p()]
    sites = catch_sites_p(purchased=purchased_catches, luban=luban_catches)
    pilots = []
    for s in sites:
        if sculpted_catches:
            sx, sy = s["strike_p"]
            hl, hw = top.SCULPTED_CATCH["length"] / 2, top.SCULPTED_CATCH["width"] / 2
            s["notch_p"] = [sx-hl, sy-hw, sx+hl, sy+hw]
        cuts.append(prism(plate_box(*s["notch_p"]), Z_RIM_TOP - 1.0, catch_floor))
        for xp, yp in s["screws_p"]:
            xw, yw = pw(xp, yp)
            if catch_inserts:
                depth, diameter = insert["depth"], insert_hole_d if purchased_catches else insert["hole_d"]
                # Local round bosses sit inside matching upper-skirt scallops. The rear pads also thicken the skin;
                # trimming to the existing desk plane prevents the front pads from becoming unintended feet.
                pad_bottom = catch_floor + depth + 1.3
                pad = md.Manifold.cylinder(pad_bottom - catch_floor, insert["boss_d"] / 2,
                                          circular_segments=96).translate([xw, yw, catch_floor])
                body += pad.trim_by_plane([0.0, SIN, -COS], -DESK_A * COS)
            elif inserts:  # CANOT OD3.5/L3 bores on the original underside: no pads, >= 0.8 mm skin left across bore
                depth = top.LUBAN_BORE_DEPTH if luban_catches else STOCK_INSERT_DEPTH
                diameter = top.CANOT_INSERT["hole_d"]
                min_under = min(underside_zp(yw), underside_zp(yw - diameter / 2), underside_zp(yw + diameter / 2))
                assert min_under - catch_floor - depth >= PILOT_SKIN, (s["name"], min_under)
            else:
                depth = round(min(PILOT_MAX, underside_zp(yw) - catch_floor - PILOT_SKIN), 2)
                diameter = PILOT_D
            pilots.append({"world": [xw, yw], "depth": depth, "diameter": diameter})
            cuts.append(md.Manifold.cylinder(depth + 0.5, diameter / 2, diameter / 2, 96 if catch_inserts or inserts else 24).translate(
                [xw, yw, catch_floor - 0.5]))
    usb_x, usb_w = top.usb_notch_print(board)
    usb_y0, usb_y1 = pw(0.0, LEDGE_BACK_P - 1.0)[1], pw(0.0, RIM_P[3] + 1.0)[1]
    slot = sg.box(usb_x - usb_w / 2, usb_y0, usb_x + usb_w / 2, usb_y1)
    # A passage with a distinct lower-case bridge above it (the upper case has its own bridge): its floor stops at
    # `USB_TUNNEL_FLOOR_ZP`, flush with the tray bottom, so it leaves over the open back step without cutting the back
    # slope. The port pocket in front runs straight into it: no raised end or deeper strip between them (owner).
    usb_open_y = usb_y0 + 1.0
    px0, px1 = usb_x - USB_PORT_POCKET_W / 2, usb_x + USB_PORT_POCKET_W / 2
    py0 = usb_open_y + USB_RAIL_NOTCH_D - USB_PORT_POCKET_L  # the measured length includes the rail notch
    inner_relief = sg.box(px0, py0, px1, usb_open_y).buffer(-USB_PORT_POCKET_R).buffer(USB_PORT_POCKET_R, quad_segs=16)
    inner_relief = inner_relief.union(sg.box(px0, py0 + USB_PORT_POCKET_R, px1, usb_open_y))
    cuts.append(prism(inner_relief, FLOOR_ZP - 0.01, FLOOR_ZP + USB_PORT_POCKET_DEPTH))
    # The R2 tool's last pass along the pocket's back edge runs USB_RAIL_NOTCH_D into the wall, from above the rim down
    # to the passage floor (not the pocket floor, so the back slope stays whole): a shallow notch with tool-radius ends.
    tool_y = usb_open_y + USB_RAIL_NOTCH_D - USB_PORT_POCKET_R
    rail_notch = sg.LineString([(px0 + USB_PORT_POCKET_R, tool_y), (px1 - USB_PORT_POCKET_R, tool_y)]).buffer(
        USB_PORT_POCKET_R, quad_segs=16)
    cuts.append(prism(rail_notch, Z_RIM_TOP - 1.0, USB_TUNNEL_FLOOR_ZP))
    # Overlap the deeper pocket (which contains this section) so no zero-thickness membrane is left at usb_open_y.
    cuts.append(prism(sg.box(usb_x - usb_w / 2, usb_open_y - 0.1, usb_x + usb_w / 2, usb_y1),
                      Z_RIM_TOP - 1.0, USB_TUNNEL_FLOOR_ZP))
    # Same X/Z_p lip contour as the top case on the free rail ends over the step, so square lower-case tips do not
    # show behind its rounds; kept off the base so the slope stays whole.
    cuts.append(top.prism_xz(top.usb_lip_round_xz(usb_x, usb_w, TRAY_BOTTOM_ZP + 1.0),
                             Y_BACK - BACK_LEDGE_W + 0.3, usb_y1))  # 0.3 clear of the base edge: no shared edge
    # Continue the rim plane over the port, preserving its existing cap recesses and fin relief.
    # Match the top-case opening's upper corner curves without lowering the central ceiling.
    arch_box = sg.box(usb_x - usb_w / 2, USB_BRIDGE_BOTTOM_ZP, usb_x + usb_w / 2, USB_TUNNEL_FLOOR_ZP)
    arch_opening = arch_box.buffer(-top.USB_END_R).buffer(top.USB_END_R, quad_segs=12).union(
        sg.box(usb_x - usb_w / 2, USB_BRIDGE_BOTTOM_ZP + top.USB_END_R,
               usb_x + usb_w / 2, USB_TUNNEL_FLOOR_ZP)).simplify(1e-4)
    # Overlap the side walls beyond the arc tangency so the STL has no zero-width junction there.
    # Its front edge follows the rail notch's R2 outline, which the stock CNC pass leaves open over the full height,
    # so from above the notch reads as round instead of showing the passage's square corners below it.
    bridge = prism(sg.box(usb_x - usb_w / 2 - 0.8, usb_open_y, usb_x + usb_w / 2 + 0.8, Y_BACK).difference(rail_notch),
                   Z_RIM_TOP, USB_BRIDGE_BOTTOM_ZP + top.USB_END_R + 0.1)
    bridge -= top.prism_xz(arch_opening, usb_open_y - 0.1, Y_BACK + 0.1)
    # A cap recess may reach into the slot (PH60 Rev.3: 0.06 mm with the 14.75 mm notch); the recess wins there.
    for recess in cap_recesses_p():
        bridge -= prism(plate_to_world(recess), Z_RIM_TOP - 1.0, CAP_SEAT_ZP)
    slot_fins = []
    for recess in (plate_to_world(p) for p in cap_recesses_p()):
        wall = slot.distance(recess)
        if 0.0 < wall < SLOT_MIN_WALL:  # join them down to the recess floor, its rounded corner included
            (sx0, sy0, sx1, sy1), (rx0, ry0, rx1, ry1) = slot.bounds, recess.bounds
            xa, xb = (sx1 - 0.01, rx0 + top.CAP_POCKET_R) if rx0 >= sx1 else (rx1 - top.CAP_POCKET_R, sx0 + 0.01)
            fin_plan = sg.box(xa, max(sy0, ry0), xb, min(sy1, ry1))
            # Keep this USB-side mouth open, but do not let its rectangular relief erase the skirt-side round.
            # Round the closed end, not the flat bearing floor; the cavity-side open end remains square.
            x_tip, inward = (xa, 1.0) if rx0 >= sx1 else (xb, -1.0)
            y_tip = min(sy1, ry1)
            cx, cy = x_tip + inward * CAP_MOUTH_R, y_tip - CAP_MOUTH_R
            corner = sg.box(min(x_tip, cx), cy, max(x_tip, cx), y_tip)
            fin_plan = fin_plan.difference(corner.difference(sg.Point(cx, cy).buffer(CAP_MOUTH_R, quad_segs=16)))
            fin_cut = prism(fin_plan, Z_RIM_TOP - 1.0, CAP_SEAT_ZP)
            cuts.append(fin_cut)
            bridge -= fin_cut
            slot_fins.append(round(wall, 3))
    bay_y1 = LEDGE_BACK_P - BAY_BACK_GAP
    bay_cx = -DX_PW  # plate X of the case centre line (world X = 0)
    bay_p = (bay_cx - _BAY["length"] / 2, bay_y1 - _BAY["width"], bay_cx + _BAY["length"] / 2, bay_y1)
    if battery_bay:
        cuts.append(prism(plate_box(*bay_p, r=_BAY["corner_r"]), FLOOR_ZP - 1.0, FLOOR_ZP + _BAY["height"]))
    # Underside features, square to the desk face (print frame), mapped back to the world frame.
    pocket_r = top.POCKET_D / 2
    for xw, yw in bumpon_centres_world():
        cuts.append(from_print(md.Manifold.cylinder(top.POCKET_DEPTH + 1.0, pocket_r, pocket_r, 64).translate(
            [xw, print_y(yw), -1.0])))
    cuts.append(from_print(prism(deco_poly_print().buffer(DECO_CLEAR, quad_segs=8), -1.0, DECO_RECESS)))
    # Weight-plate screws from inside: a through hole from the recess roof and a counterbore down from the cavity floor.
    hole_r, cbore_r = DECO_SCREW_HOLE_D / 2, DECO_SCREW_CBORE_D / 2
    for s in deco_screws_print(weight_holes):
        (px, py), z0 = s["print"], s["cbore_floor_z"]
        cuts.append(from_print(md.Manifold.cylinder(DECO_SCREW_CLAMP + 2.0, hole_r, hole_r, 32).translate(
            [px, py, DECO_RECESS - 1.0])))
        cuts.append(from_print(md.Manifold.cylinder(s["cavity_floor_z"] + 1.0 - z0, cbore_r, cbore_r, 48).translate(
            [px, py, z0])))
    body = body - md.Manifold.batch_boolean(cuts, md.OpType.Add)
    body += bridge

    report = {
        "board": board,
        "battery_bay": battery_bay,
        "frames": {"world": "top-case print frame (topcase-draft): X_w = -(X_plate + DX_PW), Y_w = Y_plate + DY_PW, Z_p",
                   "to_print_3x4": TO_PRINT.round(9).tolist()},
        "z_p": {"rim_top": Z_RIM_TOP, "cap_seat": CAP_SEAT_ZP,
                "catch_top": catch_floor - 9.0 if purchased_catches or luban_catches else CATCH_TOP_ZP, "catch_floor": catch_floor,
                "cavity_floor": FLOOR_ZP, "bay_floor": round(FLOOR_ZP + _BAY["height"], 2) if battery_bay else None,
                "lip": top.SKIRT_H,
                "desk_at_y0": round(DESK_A, 6), "desk_tan": round(TAN, 9)},
        "plate_frame": {"rim": RIM_P, "rim_corner_r": RIM_CORNER_R, "ledge_front_y": LEDGE_FRONT_P,
                        "ledge_back_y": LEDGE_BACK_P, "open_ends": "no short walls: the cavity runs through both ends",
                        "battery_bay": [round(v, 3) for v in bay_p] if battery_bay else None,
                        "cap_mouth_radius": CAP_MOUTH_R,
                        "cap_recesses": [[round(v, 3) for v in p.bounds] for p in cap_recesses_p()]},
        "catches": [{**s, "pilots": pilots[2 * k:2 * k + 2]} for k, s in enumerate(sites)],
        "usb_slot_world": {"x": usb_x, "width": usb_w, "y": [usb_y0, usb_y1], "z_p": [Z_RIM_TOP, USB_TUNNEL_FLOOR_ZP],
                           "tunnel_y": [usb_open_y, usb_y1], "exit_over_open_step_y": [Y_BACK - BACK_LEDGE_W, Y_BACK],
                           "open_lip_corner_r": top.USB_LIP_R,
                           "inner_connector_pocket": {"bounds_xy": list(inner_relief.bounds), "corner_r": USB_PORT_POCKET_R, "size": [USB_PORT_POCKET_W, USB_PORT_POCKET_L],
                                                      "rail_notch_depth": USB_RAIL_NOTCH_D,
                                                      "floor_z_p": FLOOR_ZP + USB_PORT_POCKET_DEPTH,
                                                      "end_land_mm": 0.0},
                           "bridge_z_p": [Z_RIM_TOP, USB_BRIDGE_BOTTOM_ZP],
                           "bridge_corner_r": top.USB_END_R,
                           "bridge_y": [usb_open_y, Y_BACK], "bridge_requires_print_support": True,
                           "cap_recess_walls_removed_mm": slot_fins, "min_wall": SLOT_MIN_WALL},
        "bumpons_world": [[x, round(y, 3)] for x, y in bumpon_centres_world()],
        "bumpon_pocket": {"d": top.POCKET_D, "depth": top.POCKET_DEPTH},
        "deco_recess_print": {"outline_bounds": [round(v, 3) for v in deco_poly_print().bounds], "depth": DECO_RECESS,
                              "plate_thickness": DECO_T, "from_slope_edge": DECO_FROM_SLOPE,
                              "clear": DECO_CLEAR},
        "deco_screws": {"thread": DECO_SCREWS["thread"], "length": DECO_SCREW_LEN, "hole_d": DECO_SCREW_HOLE_D,
                        "cbore_d": DECO_SCREW_CBORE_D, "clamp": DECO_SCREW_CLAMP,
                        "sites": [{"plate": s["plate"], "print": [round(v, 3) for v in s["print"]],
                                   "world_x": round(s["print"][0], 3), "cbore_floor_print_z": s["cbore_floor_z"],
                                   "cavity_floor_print_z": round(s["cavity_floor_z"], 3)} for s in deco_screws_print(weight_holes)],
                        "positions_status": "user override; measure purchased A plate" if weight_holes is not None else "photo estimate; unverified on purchased A plate"},
        "rim_clear": RIM_CLEAR,
        "split": {"shape": "ㄴㄱ", "back_catch": SEAM_BACK_CATCH, "back_x_world": SEAM_BACK_X,
                  "front_catch": SEAM_FRONT_CATCH, "front_x_world": SEAM_FRONT_X, "cross_y_world": SEAM_CROSS_Y,
                  "z_stop": SEAM_Z_STOP, "z_clear": top.JOINT_Z_CLEAR, "land": SEAM_LAND,
                  "ramp_slope": SEAM_RAMP_SLOPE, "rib_top": SEAM_RIB_TOP, "comp_interf": top.COMP_INTERF,
                  "dovetails": [{"leg": leg, "at": at, "male": male, **DOVETAIL} for leg, at, male in SEAM_DOVETAILS],
                  "clearance": top.JOINT_CLEAR, "insertion_axis_world": FROM_PRINT[:, 2].round(9).tolist()},
        "tray_and_base": {"tray_bottom_z_p_front_back": [round(tray_bottom_zp(Y_FRONT), 3), TRAY_BOTTOM_ZP],
                          "back_step": BACK_LEDGE_W, "back_slope_length": BACK_SLOPE_LEN,
                          "front_step": FRONT_STEP_W, "end_step": END_STEP_W,
                          "desk_face_back_inset": BACK_BEVEL_INSET,
                          "base_outline_world": [round(v, 3) for v in base_outline().bounds]},
    }
    report["inserts"] = inserts
    report["catch_hardware"] = "luban32" if luban_catches else "stock"
    report["catch_insert_trial"] = (
        {
            "hole_d": top.CANOT_INSERT["hole_d"],
            "outer_d": top.CANOT_INSERT["outer_d"],
            "length": top.CANOT_INSERT["length"],
            "depth": top.LUBAN_BORE_DEPTH if luban_catches else STOCK_INSERT_DEPTH,
            "min_wall_from_hole_mm": 1.30 if luban_catches else 0.80,
            "tool_tip_max_d": 4.0,
            "coupon_required": True,
        }
        if inserts
        else None
    )
    if luban_catches:
        report["luban32"] = {"hardware_assumed": top.LUBAN, "catch_seat_zp": catch_floor, "inserts": inserts,
                             "bore_depth": top.LUBAN_BORE_DEPTH if inserts else None,
                             "bore_d": top.CANOT_INSERT["hole_d"] if inserts else PILOT_D,
                             "insert": "CANOT M2 OD3.5 x L3" if inserts else None,
                             "status": "widths assumed (spec ball_catch.luban32); caliper the purchased parts before printing"}
    if catch_inserts:
        report["experimental_catch_inserts"] = {**insert, "hole_d": diameter, "rear_pad_bottom_z_p": pad_bottom,
                                                 "purchased_32mm": purchased_catches,
                                                 "hardware_dimensions_unconfirmed": True}
    return body, report


def seam_ramp_z(u: float) -> float:
    """Print-frame Z' of the self-supporting print ramp under a male tongue at local distance u >= 0 from the seam."""
    return SEAM_Z_TONGUE + SEAM_RAMP_SLOPE * max(0.0, u - SEAM_LAND)


def dovetail_local_matrix(leg: str, at: float) -> np.ndarray:
    """Rigid right-handed 3x4 transform from a dovetail's local frame (u into RightHalf, v along seam, z = Z') to print."""
    yc = print_y(SEAM_CROSS_Y)
    if leg == "cross":  # seam at Y' = yc; u along +Y' (into RightHalf), v along -X centred at X = at (det +1)
        return np.array([[0.0, -1.0, 0.0, at],
                         [1.0,  0.0, 0.0, yc],
                         [0.0,  0.0, 1.0, 0.0]])
    x0 = SEAM_BACK_X if leg == "back" else SEAM_FRONT_X
    yp = print_y(at)
    return np.array([[-1.0,  0.0, 0.0, x0],
                     [ 0.0, -1.0, 0.0, yp],
                     [ 0.0,  0.0, 1.0, 0.0]])


def straight_left_region_print() -> Any:
    """Straight ㄴㄱ region of the left half on the desk face (Z' = 0 .. SEAM_Z_STOP), without dovetail cutouts."""
    yc = print_y(SEAM_CROSS_Y)  # Y' grows toward the front
    return orient(sg.Polygon([(SEAM_BACK_X, -1e3), (1e3, -1e3), (1e3, 1e3), (SEAM_FRONT_X, 1e3), (SEAM_FRONT_X, yc),
                              (SEAM_BACK_X, yc)]))


def left_region_print() -> Any:
    """Print-plane (X, Y') region of the left half above `SEAM_Z_STOP`, including all five male dovetail tongues."""
    region = straight_left_region_print()
    tongue = top.dovetail_poly(0.0, clear=0.0, **DOVETAIL)
    for leg, at, male in SEAM_DOVETAILS:
        assert male == "left", (leg, at, male)
        m = dovetail_local_matrix(leg, at)
        aff = [m[0, 0], m[0, 1], m[1, 0], m[1, 1], m[0, 3], m[1, 3]]
        region = region.union(orient(sa.affine_transform(tongue, aff)))
    assert region.geom_type == "Polygon" and not region.interiors, region.geom_type
    return orient(region)


def dovetail_landing_polys_print() -> list[Any]:
    """Print-plane (X, Y') outlines of the 0.80 mm horizontal landing strips under the five male tongues."""
    nh = DOVETAIL["neck_half"]
    land_box = sg.box(0.0, -nh, SEAM_LAND, nh)
    polys = []
    for leg, at, _ in SEAM_DOVETAILS:
        m = dovetail_local_matrix(leg, at)
        aff = [m[0, 0], m[0, 1], m[1, 0], m[1, 1], m[0, 3], m[1, 3]]
        polys.append(orient(sa.affine_transform(land_box, aff)))
    return polys


def seam_rib_zones_world() -> md.Manifold:
    """World-frame bounding boxes around the chevron compression-rib bands of all five dovetails."""
    hh, proj = DOVETAIL["head_half"], DOVETAIL["proj"]
    zone_loc = md.Manifold.cube([proj + 0.2, 2.0 * (hh + 0.4), SEAM_RIB_TOP + top.JOINT_Z_CLEAR]).translate(
        [0.5, -hh - 0.4, SEAM_Z_STOP])
    zones_p = md.Manifold.batch_boolean(
        [zone_loc.transform(dovetail_local_matrix(leg, at)) for leg, at, _ in SEAM_DOVETAILS], md.OpType.Add)
    return from_print(zones_p)


def split(body: md.Manifold) -> tuple[md.Manifold, md.Manifold]:
    """Split into LeftHalf (male) and RightHalf (female) along the ㄴㄱ seam, matching the top-case dovetail system:
    straight seam on the desk face (0 .. SEAM_Z_STOP), 0.20 mm vertical glue line under each landing and print ramp,
    and chevron compression ribs in RightHalf's sockets."""
    body_p = body.transform(TO_PRINT)
    left_p = body_p ^ prism(left_region_print(), -20.0, 80.0)
    right_p = body_p - prism(straight_left_region_print(), -20.0, 80.0)

    nh, hh, proj, taper = DOVETAIL["neck_half"], DOVETAIL["head_half"], DOVETAIL["proj"], DOVETAIL["neck_taper"]
    sock_poly = top.dovetail_poly(0.0, nh, hh, proj, clear=top.JOINT_CLEAR, neck_taper=taper)
    rib_polys = top.socket_rib_polys(0.0, nh, hh, proj, taper)

    under_tongue_xz = sg.Polygon([
        (0.0, -1.0), (proj + 0.6, -1.0), (proj + 0.6, seam_ramp_z(proj + 0.6)),
        (SEAM_LAND, SEAM_Z_TONGUE), (0.0, SEAM_Z_TONGUE),
    ])
    under_cut_loc = top.prism_xz(under_tongue_xz, -hh - 1.2, hh + 1.2)

    z_base, u_end = SEAM_Z_STOP - 0.3, proj + 0.5
    u_start = SEAM_LAND - 0.3 / SEAM_RAMP_SLOPE
    z_end = SEAM_Z_STOP + SEAM_RAMP_SLOPE * (u_end - SEAM_LAND)
    fill_loc = top.prism_xz(sg.Polygon([(u_start, z_base), (u_end, z_base), (u_end, z_end)]), -hh - 1.0, hh + 1.0)
    socket_loc = top.prism_xy(sock_poly, SEAM_Z_STOP, 30.0)
    ribs_loc = top.prism_xy(sg.MultiPolygon(rib_polys), SEAM_Z_TONGUE + 0.3, SEAM_Z_TONGUE + SEAM_RIB_TOP)

    for leg, at, _ in SEAM_DOVETAILS:
        mat = dovetail_local_matrix(leg, at)
        left_p -= under_cut_loc.transform(mat)
        sock_p = socket_loc.transform(mat)
        fill_p = fill_loc.transform(mat)
        assert ((sock_p ^ fill_p) - right_p).volume() < 1e-6, f"{leg}@{at}: socket fill outside RightHalf"
        right_p -= sock_p - fill_p
        right_p += ribs_loc.transform(mat) ^ body_p

    return from_print(left_p), from_print(right_p)


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
    ap.add_argument("--battery-bay", action=argparse.BooleanOptionalAction, default=True,
                    help="cut the stock battery bay; use --no-battery-bay for a wired case (default: enabled)")
    ap.add_argument("--catches", choices=["stock", "luban32"], default="stock",
                    help="Ball-catch hardware, matching the top case build; default: %(default)s")
    ap.add_argument("--inserts", action=argparse.BooleanOptionalAction, default=False,
                    help="CANOT M2 OD3.5/L3 heat-set insert bores instead of self-tapping pilots; default: self-tapping")
    ap.add_argument("--strike-inserts", action=argparse.BooleanOptionalAction, default=None,
                    help="Alias for --inserts / --no-inserts")
    args = ap.parse_args()
    use_inserts = args.strike_inserts if args.strike_inserts is not None else bool(args.inserts)
    if args.battery_bay:
        print("WARNING: the battery-bay bottom case is on hold and not reviewed for printing; "
              "--no-battery-bay builds the current wired bottom case.", file=sys.stderr)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "verification.json").unlink(missing_ok=True)
    body, report = build(args.board, battery_bay=args.battery_bay, inserts=use_inserts,
                         luban_catches=args.catches == "luban32")
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
    write_3mf(OUT / "maru60-hhkb-bottomcase-left.3mf", f"Maru60 HHKB bottom case, for Rule60 V3 - left half ({lic})",
                  [("BottomLeft", printed["bottom-left"])], fine_layer_z=None)
    write_3mf(OUT / "maru60-hhkb-bottomcase-right.3mf", f"Maru60 HHKB bottom case, for Rule60 V3 - right half ({lic})",
                  [("BottomRight", printed["bottom-right"])], fine_layer_z=None)
    write_3mf(OUT / "maru60-hhkb-bottomcase-fit-coupon.3mf", f"Maru60 HHKB bottom case fit coupon ({lic})",
                  [("CouponFrontLeft", printed["coupon-front-left"])], fine_layer_z=None)
    pair = [printed["joint-test-left"].copy(), printed["joint-test-right"].copy()]
    pair[0].apply_translation([-25.0, 0.0, 0.0])
    pair[1].apply_translation([25.0, 0.0, 0.0])
    write_3mf(OUT / "maru60-hhkb-bottomcase-joint-test.3mf", f"Maru60 HHKB bottom case joint test ({lic})",
                  [("JointTestLeft", pair[0]), ("JointTestRight", pair[1])], fine_layer_z=None)
    report["parts"] = {name: {"print_extents": [round(v, 2) for v in tm.extents], "volume_cm3": round(tm.volume / 1e3, 1)}
                       for name, tm in printed.items()}
    (OUT / "draft-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["parts"], indent=2))


if __name__ == "__main__":
    main()
