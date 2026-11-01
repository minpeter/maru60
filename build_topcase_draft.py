"""Maru60 HHKB top case + integrated honeycomb wrist rest, for the Rule60 V3 (stock bottom case, plate, gaskets, catches).

Built from caliper measurements of the owner's stock top case plus photo metrology of the silicone gasket caps and
ball-catch pockets (IMG_0201..IMG_0222, 28 px/mm rectified):
  - Silicone gasket cap ("gasket bean/sock", 12 installed = 2 per 41 mm tab): the Keebox 8.0 x 5.0 x 5.0 mm U-sock with a
    rounded end and a 6.5 x 2.8 x 1.2 mm slot (`gasket.cap_free`), 1.9 mm flanges either side of the 1.5 mm PC tab.
    Pockets are sized from the stock underside photo (`gasket.pocket_footprint`, 43.00 mm outer span per tab).
  - CNC order as on the stock part (caliper; top face down = `Z_p 0`, `Z_p` grows toward the skirt lip):
      1. Block with the 6-deg top face + 0.70 mm 45-deg outer chamfer, skirt lip at `Z_p = 20.01 mm` (IMG_0333)
      2. Base pocket from the lip down to the `Z_p = 9.69 mm` floor (IMG_0334) inside the skirt (`2.85 mm` sides and back,
         `2.80 mm` front; `R4.85` outer / `R2.0` inner corners); the stock bottom case nests in this 10.32 mm pocket.
         Outline from the caliper-measured top-face bezels: 5.65 sides, 10.90 back, 11.02 front -> 298.10 x 117.37 mm
      3. HHKB keycap opening through the floor
      4. Plate-body relief + 6 open rounded-rectangle silicone-cap pockets, one level `Z_p = 6.30 mm` (caliper), cut
         straight from the floor inside a `2.05 mm` floor ledge along the skirt (short side: ledge 2.85..4.90 mm and the
         6.30 strip 4.90..5.66 mm from the outer edge, caliper). One pocket per DWG `6095(gas)` tab: the photo-read cap
         footprint (`8.2 x 4.0 mm`, two per tab) plus `0.65 mm` room per side (front: up to the ledge), `R1.8` skirt-side
         corners, no wall toward the plate. `R1.0` where a pocket meets the relief, `R0.5` on the relief corners
      5. 4 ball-catch strike pockets cut from the floor to `Z_p = 5.55 mm` (IMG_0337): `7.25 mm` wide for the ~20.5 x
         6.55 mm strike, stock CNC "mushroom" end reliefs (`4.1 mm` semicircular lobe on the skirt half `4.55 mm` past each
         plate end, interior-half end wall `2.15 mm` past it, `R0.85` shoulder; two-view fit of IMG_0218/0222), with
         `3.55 mm` deep M2 strike screw pilots; each keeps its fitted distance to the inner skirt wall it faces
      6. USB-C notch (12.8 wide, 8.7 deep from the lip, R1.5 closed-end corners). Gasket mount only: no top-mount screws.
  - Staggered split into two X2D halves: X = 0 through the wrist rest and front bezel (3 dovetails); the back bezel runs
    on in the LeftHalf to the back-left (BL) strike centre, where the stock strike plate (one M2 per half) and a wedge key
    join the back seam. Each male part keeps its 45-deg print ramp and the female side fills under it, so every joint
    closes over all faces with a 0.20 mm glue line and nothing needs support.

Interface values (stock top case, INKC plate, gasket caps, ball catches, bumpons) come from `spec/` via rule60_spec.py;
`--board` picks the PCB whose USB-C position sets the notch (spec/boards.json, or `universal` for all known boards).

Usage:
    uv run build_topcase_draft.py [--board BOARD]
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from typing import Any
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import manifold3d as md
import numpy as np
from shapely.ops import unary_union
import shapely.geometry as sg
import trimesh

import rule60_spec as spec

SOLIDCRAFT_CLI = Path.home() / ".local/bin/solidcraft-cli"
OUT = Path(__file__).resolve().parent / "topcase-draft"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Plate frame = DWG `6095(gas)` plate / HHKB keycap layout seen from the top (X right, Y back); the keycap opening is
# fixed in it. The outer case follows the caliper-measured top-face bezels (owner, +-1 mm). The print frame is the
# part upside down on the bed (top face at Z_p 0) seen from above, i.e. the underside: centred on X = 0, front at
# Y = WRIST_D, and X mirrored: X_world = -(X_plate + DX_PW), Y_world = Y_plate + DY_PW. v6.2 and earlier skipped the
# mirror and printed the mirror image (USB on the wrong side, back gasket pockets 10 mm off the tabs).
# ---------------------------------------------------------------------------
OPENING_P = tuple(spec.value("top.keycap_opening_hhkb"))  # HHKB keycap opening bounds (plate frame); front edge = bottom-row middle
BEZEL_SIDE, BEZEL_BACK, BEZEL_FRONT = (spec.value("top.bezel")[k] for k in ("side", "back", "front"))  # Top-face bezel
SKIRT_WALL = spec.value("top.skirt_wall")["side_back"]  # Skirt wall thickness, sides and back (caliper, flipped)
FRONT_WALL = spec.value("top.skirt_wall")["front"]      # Skirt wall thickness, front (caliper, flipped)
RIM_SEAT_W = spec.value("top.rim_seat_w")  # Floor ledge (bottom-case rim seat) inside the skirt: short side 4.90 - 2.85 mm
OUTER_P = (round(OPENING_P[0] - BEZEL_SIDE, 3), round(OPENING_P[1] - BEZEL_FRONT, 3),
           round(OPENING_P[2] + BEZEL_SIDE, 3), round(OPENING_P[3] + BEZEL_BACK, 3))  # (-6.10, -4.82, 292.00, 112.55)
INNER_P = (round(OUTER_P[0] + SKIRT_WALL, 3), round(OUTER_P[1] + FRONT_WALL, 3),
           round(OUTER_P[2] - SKIRT_WALL, 3), round(OUTER_P[3] - SKIRT_WALL, 3))  # Inner skirt faces
LEDGE_P = (round(INNER_P[0] + RIM_SEAT_W, 3), round(INNER_P[1] + RIM_SEAT_W, 3),
           round(INNER_P[2] - RIM_SEAT_W, 3), round(INNER_P[3] - RIM_SEAT_W, 3))  # Inner edge of the floor ledge
CASE_W = round(OUTER_P[2] - OUTER_P[0], 3)  # 298.10
CASE_D = round(OUTER_P[3] - OUTER_P[1], 3)  # 117.37
WRIST_D = 80.00         # Integrated honeycomb wrist-rest depth
DX_PW = round(-(OUTER_P[0] + OUTER_P[2]) / 2, 3)  # -142.95
DY_PW = round(WRIST_D - OUTER_P[1], 3)            # 84.82
PW_SX = -1.0            # Plate X -> print X sign (underside view)


def pw(xp: float, yp: float) -> tuple[float, float]:
    return round(PW_SX * (xp + DX_PW), 4), round(yp + DY_PW, 4)


TILT_DEG = spec.value("top.tilt_deg")  # IC spec: 6.0 deg typing angle
JUNC_H = spec.value("top.height")      # Installed height of the top face at the Y=80 junction = stock top-case height

SKIRT_H = spec.value("top.height")    # Caliper-measured total stock top-case height (IMG_0333: 20.01 mm)
Z_FLOOR = spec.value("top.bottom_seat_z")    # Base pocket floor: pocketed 10.32 mm deep from the lip inside the skirt
Z_GASKET = spec.value("top.gasket_seat_z")   # 6 silicone-cap pockets, 3.39 mm below the floor (caliper)
Z_STRIKE = spec.value("top.strike_floor_z")  # 4 ball-catch strike pockets, 4.14 mm below the floor (caliper, IMG_0337)
FRONT_TABS_P = [tuple(t) for t in spec.value("plate.front_tabs_x")]  # DWG `6095(gas)` front tab X spans (plate frame)
BACK_TABS_P = [tuple(t) for t in spec.value("plate.back_tabs_x")]    # DWG `6095(gas)` back tab X spans (plate frame)
WING_MID_Y_P = tuple(spec.value("plate.tab_mid_y"))  # Front / back cap centerline Y (plate frame) on the DWG tabs
CAP_FOOT_L, CAP_FOOT_W = spec.value("gasket.pocket_footprint")  # Photo-read cap footprint the pockets are sized from
CAP_INSET = spec.value("gasket.pocket_inset")  # Pocket centre inset from each tab end (2 caps per 41.00 mm tab)
_CAP = spec.value("gasket.cap_free")  # The part (Keebox drawing), reported only
CAP_CLEAR = 0.65        # Pocket room per side around the cap footprint for the compressed silicone to bulge
CAP_POCKET_R = 1.80     # Pocket skirt-side corner radius; every cap footprint must stay >= 0.03 mm inside its pocket
PLATE_RELIEF_CLEAR = 0.30  # Plate-body travel relief past the DWG plate body, front and back
RELIEF_Y_P = tuple(round(y + d, 2) for y, d in zip(spec.value("plate.body_y"), (-PLATE_RELIEF_CLEAR, PLATE_RELIEF_CLEAR)))
RELIEF_X_P = (LEDGE_P[0], LEDGE_P[2])  # Relief X span: from the floor ledge, a 0.76 mm strip beside the opening (caliper)
JUNCTION_R = 1.00       # Where a cap pocket end meets the relief edge
RELIEF_CORNER_R = 0.50  # Relief outer corners (0.35 mm from the plate edge)
CAP_TOP_COMPRESSED = spec.value("gasket.top_flange_compressed")  # Cap top flange: 1.9 free, 1.20 seated (derived)
Z_PLATE = round(Z_GASKET + CAP_TOP_COMPRESSED, 2)  # Seated gasket-plate top face (7.50 mm)
Z_RELIEF = Z_GASKET     # Plate-body travel relief: same level as the cap pockets (owner), 1.20 mm plate travel
KERNEL_WORKAROUND_W = (30.257, 87.070)  # Temporary bore site in the RightHalf front floor face (print frame), step 10b
# Ball-catch strikes: (name, X_plate, inner skirt wall faced, center distance from that wall). Back pair: the distance
# fitted to IMG_0218/0222 (kept when the measured outline moves the wall). Front pair: the measured front bezel narrows
# the band between the inner wall and the gasket-plate edge to 7.6 mm, so they sit centred in it (0.63 mm pocket-to-wall
# and tongue-to-plate); the fitted 4.65 mm would leave the tongue 0.24 mm from the plate.
STRIKE_SITES = [tuple(s) for s in spec.value("ball_catch.strike_sites")]
JOINT_YC = {  # Dovetail centers (world Y): wrist / front wall joints across X = 0
    "WristFrontJoint": 23.50,
    "WristMidJoint": 50.00,
    "FrontBezelWallJoint": 75.50,
}
JOINTS_SPEC = [
    # (name, yc, nh, hh, proj, z_stop, z_top, z_sock_top, rib_top, neck_taper)
    # 6 mm joints: the 45-deg print ramp leaves tongue material at the rib apex only above `z_stop + 2.2`,
    # so their ribs reach `z_stop + 4.8` for ~2.3 mm of contact while staying clear for `dz >= 3.2`.
    ("WristFrontJoint",      JOINT_YC["WristFrontJoint"], 5.20, 6.60, 6.0, 4.0, 13.0, 22.0, 4.8, 0.55),
    ("WristMidJoint",        JOINT_YC["WristMidJoint"], 5.20, 6.60, 6.0, 4.0, 15.7, 22.0, 4.8, 0.55),
    ("FrontBezelWallJoint",  JOINT_YC["FrontBezelWallJoint"], 5.00, 6.40, 6.0, 4.0, 17.6, 22.0, 4.8, 0.55),
]
# Staggered split: the wrist rest, front bezel and keycap opening split at X = 0 (the 3 dovetails above); the back bezel
# runs on in the LeftHalf to the centre of the back strike on the +X side (the stock back-left, BL, in the underside
# view), so the stock strike plate (2 x M2 at 13.0 mm pitch) bridges the back seam with one screw in each half, and the
# back-centre cap pocket stays in one piece. The step from X = 0 to the back seam runs at `SPLIT_STEP_Y` through the
# keycap opening, where there is no material.
BACK_SEAM_STRIKE = next(n for n, x, wall, _ in STRIKE_SITES if wall == "back" and pw(x, 0.0)[0] > 0.0)
BACK_SEAM_X = round(pw(next(x for n, x, *_ in STRIKE_SITES if n == BACK_SEAM_STRIKE), 0.0)[0], 3)  # world X (53.10)
BACK_SEAM_GAP = 0.0     # End gap across the back seam: line-to-line, like every side face of the X = 0 dovetails (owner)
SPLIT_STEP_Y = round((OPENING_P[1] + OPENING_P[3]) / 2 + DY_PW, 3)  # Mid keycap opening, world Y
BACK_KEY_HW = 1.50      # Back-seam key half width (Y): a 45-deg wedge on the LeftHalf below the seam strike pocket floor
BACK_KEY_Z0 = 2.00      # Key underside at the seam face (Z_p); it rises at 45 deg to the strike pocket floor
BACK_KEY_CLR_Y = 0.0    # Notch clearance per side (Y): line-to-line (owner); under the wedge the notch keeps
                        # `JOINT_Z_CLEAR` (vertical), like the dovetail landings and print ramps
STRIKE_PILOT_DEPTH = 3.55  # Blind M2 pilot depth past the strike pocket floor (2.00 mm top skin left); a pilot deeper
                           # than the screw costs nothing, a shallower one stops a long screw before it clamps


def strike_centers_p() -> list[tuple[str, float, float]]:
    return [(n, x, round(INNER_P[3] - d if wall == "back" else INNER_P[1] + d, 3)) for n, x, wall, d in STRIKE_SITES]


def back_seam_key() -> dict[str, Any]:
    """World X/Y, Z_p of the back-seam wedge key (LeftHalf) and its notch (RightHalf), centred on the seam strike. The
    notch is the wedge lowered by `JOINT_Z_CLEAR`: a uniform glue line under the slope, no void (`notch_xz`: X, Z_p)."""
    _, _, by_p = next(s for s in strike_centers_p() if s[0] == BACK_SEAM_STRIKE)
    key_y = round(by_p + DY_PW, 3)
    key_x0 = round(BACK_SEAM_X - BACK_SEAM_GAP / 2, 3)  # LeftHalf seam face
    key_tip_x = round(key_x0 + Z_STRIKE - BACK_KEY_Z0, 3)
    notch_x0 = round(BACK_SEAM_X + BACK_SEAM_GAP / 2 - 0.3, 3)
    notch_top = round(Z_STRIKE + 0.5, 3)  # into the open strike pocket
    return {
        "key_y": key_y,
        "key_x0": key_x0,
        "key_tip_x": key_tip_x,
        "notch_y0": round(key_y - BACK_KEY_HW - BACK_KEY_CLR_Y, 3),
        "notch_y1": round(key_y + BACK_KEY_HW + BACK_KEY_CLR_Y, 3),
        "notch_xz": [[notch_x0, round(BACK_KEY_Z0 - JOINT_Z_CLEAR + notch_x0 - key_x0, 3)],
                     [round(key_x0 + notch_top - BACK_KEY_Z0 + JOINT_Z_CLEAR, 3), notch_top],
                     [notch_x0, notch_top]],
    }


def cap_pocket_polys_p() -> list[Any]:
    """Open silicone-cap pockets (plate frame): cap footprints + `CAP_CLEAR`, from the skirt side (clipped at the floor
    ledge) to 0.5 mm into the plate relief (no plate-side wall). The two skirt-side corners take `CAP_POCKET_R`."""
    reach = CAP_FOOT_L / 2 + CAP_CLEAR - CAP_INSET           # pocket end past the tab end (1.55 mm)
    side = CAP_FOOT_W / 2 + CAP_CLEAR                        # pocket skirt side from the cap centerline (2.65 mm)
    polys = []
    for tabs, y_mid, sign, y_open, y_ledge in ((FRONT_TABS_P, WING_MID_Y_P[0], -1.0, RELIEF_Y_P[0] + 0.5, LEDGE_P[1]),
                                               (BACK_TABS_P, WING_MID_Y_P[1], 1.0, RELIEF_Y_P[1] - 0.5, LEDGE_P[3])):
        y_skirt = round(max(y_mid - side, y_ledge) if sign < 0 else min(y_mid + side, y_ledge), 3)
        for xl, xr in tabs:
            x0, x1 = round(xl - reach, 3), round(xr + reach, 3)
            box = sg.box(x0, min(y_skirt, y_open), x1, max(y_skirt, y_open))
            sharp = sg.box(x0, min(y_skirt - sign * CAP_POCKET_R, y_open), x1, max(y_skirt - sign * CAP_POCKET_R, y_open))
            rounded = box.buffer(-CAP_POCKET_R).buffer(CAP_POCKET_R, quad_segs=16)
            pocket = rounded.union(sharp).simplify(1e-4)
            for cx in (xl + CAP_INSET, xr - CAP_INSET):
                cap = sg.box(cx - CAP_FOOT_L / 2, y_mid - CAP_FOOT_W / 2, cx + CAP_FOOT_L / 2, y_mid + CAP_FOOT_W / 2)
                assert pocket.buffer(-0.03).contains(cap), f"cap footprint at X_plate {cx} touches its pocket wall"
            polys.append(pocket)
    return polys


def orange_cut_poly_p() -> Any:
    """Everything cut to `z_gasket` (plate frame): plate-body relief + the 6 cap pockets as one polygon, `JUNCTION_R`
    where a pocket end meets the relief edge, `RELIEF_CORNER_R` on the relief's outer corners, and `RELIEF_CORNER_R`
    where a (deeper) strike pocket crosses the relief edge: those slivers are cut to this level too."""
    relief = sg.box(RELIEF_X_P[0], RELIEF_Y_P[0], RELIEF_X_P[1], RELIEF_Y_P[1])
    cut = unary_union([relief, *cap_pocket_polys_p()])
    cut = cut.buffer(JUNCTION_R, quad_segs=8).buffer(-JUNCTION_R, quad_segs=8)
    cut = cut.buffer(-RELIEF_CORNER_R, quad_segs=8).buffer(RELIEF_CORNER_R, quad_segs=8)
    strikes = unary_union([strike_pocket_poly(x, y, 1.0 if y > 50.0 else -1.0) for _, x, y in strike_centers_p()])
    with_strikes = cut.union(strikes)
    slivers = with_strikes.buffer(RELIEF_CORNER_R, quad_segs=8).buffer(-RELIEF_CORNER_R, quad_segs=8).difference(with_strikes)
    cut = cut.union(slivers.buffer(0.01).intersection(cut.buffer(RELIEF_CORNER_R))).simplify(0.005)
    assert cut.geom_type == "Polygon" and not cut.interiors, cut.geom_type
    return cut


FINE_LAYER_Z = (5.40, 10.00)  # Print Z band sliced at `FINE_LAYER_H` (layer_config_ranges.xml in every print 3MF)
FINE_LAYER_H = 0.10
SKIN_T = 2.20           # Honeycomb wrist-rest top skin thickness
WRIST_WALL = 2.20       # Wrist-rest outer perimeter wall thickness
CORNER_R = 4.85         # Outer vertical corner radius: concentric with the R2.0 inner skirt corner (+ 2.85 mm wall)
INNER_SKIRT_R = spec.value("top.inner_corner_r")  # Inner skirt (bottom-case pocket) vertical corner radius: the R5.0 of
                        # v6.2 held the stock bottom case ~2.3 mm off its seat at the corners (owner, printed part): its
                        # corners are about R2.7, so the pocket takes R2.0 to clear them with the straight walls line-to-line.
RIB = 2.40              # Honeycomb rib width (matches v9)
# Bumpon pads: 4 sites along the wrist-rest front edge, each with a pocket for a 3M Bumpon Protective Products SJ5012
# (cylindrical, flat top, Ø12.7 x 3.5 mm, +-0.5 mm; same shape as SJ5312 transparent and SJ5412 true white). The bumpons
# fill the gap the stock bottom-case feet leave under the wrist rest; the pocket sets how far they stand proud of the pad
# face (`DESK_GAP`) and holds them against sideways shear. Each pad runs `PAD_D` in from the front face: full height
# near the wall, then a 45-deg corbel that prints without support. v7.4 had 6 mm deep flat pads, v7.5 11 mm deep flat
# pads for the hemispherical Ø7.9 x 2.2 mm SJ5302. v7.10 drops the back row along the junction (owner): the printed
# bottom case's front bumpons stand 24 mm behind it, so with it the assembly stood on 14 bumpons where 8 carry every
# load case.
BUMPON_D = spec.value("bumpon.sj5012")["diameter"]  # 3M SJ5012 diameter (datasheet nominal)
BUMPON_D_MAX = BUMPON_D + spec.value("bumpon.sj5012")["tolerance"]  # Diameter at the +0.5 mm datasheet tolerance
BUMPON_H = spec.value("bumpon.sj5012")["height"]  # 3M SJ5012 height (datasheet nominal)
DESK_GAP = spec.value("desk.gap")  # Pad face to desk with the keyboard on its stock feet: estimated, not measured
POCKET_DEPTH = round(BUMPON_H - DESK_GAP, 3)  # Pocket depth along the desk-plane normal (1.50 mm)
POCKET_D = round(BUMPON_D_MAX + 0.4, 3)       # Pocket diameter (13.60 mm): 0.2 mm per side at the largest bumpon
PAD_X = (30.0, 119.0)   # Pad centres, |X| (print frame)
PAD_W = 16.0            # Pad width (X): 1.2 mm wall each side of the pocket
PAD_D = 16.0            # Pad depth (Y) from the outer face: 1.2 mm wall each side of the pocket
PAD_COLUMN_D = 6.0      # Full-height part of the pad at least, wall included
PAD_TIP_T = round(POCKET_DEPTH + 1.0, 3)      # Vertical land at the pad's inner edge, under the pad face


def pad_centres() -> list[tuple[float, float]]:
    """Print-frame X, Y of the 4 bumpon pad centres along the front edge."""
    return [(s * c, PAD_D / 2) for c in PAD_X for s in (-1.0, 1.0)]


def usb_notch_print(board_id: str) -> tuple[float, float]:
    """Print X of the USB-C notch centre and its width for a board (spec/boards.json). The stock top-case notch sits at
    plate X 19.35; the default board, the 6095 tri-mode kit PCB, measures 18.45 in public photos."""
    centre_p, width = spec.usb_notch(board_id)
    return pw(centre_p, 0.0)[0], width


# Width and corner shape from the stock notch measured against the v6.2 print (owner photos IMG_0378/0379, scaled from
# the printed 14.2 mm notch): 12.6 / 12.75 wide, rounded closed-end corners (CNC endmill); 0.1-0.2 mm generous. Depth
# from the v7.3 full-print fit: the photo-estimated 5.7 mm hit the USB-C connector until the owner cut the notch ~3 mm
# deeper by hand, so it is 8.7 mm (closed end 1.62 mm above the 9.69 floor).
USB_TOP_ZP = round(SKIRT_H - spec.value("top.usb_notch")["depth_from_lip"], 2)  # Notch closed end (Z_p 11.31)
USB_DEPTH = round(SKIRT_H - USB_TOP_ZP, 2)  # USB-C notch depth from skirt lip
USB_END_R = spec.value("top.usb_notch")["end_r"]  # Closed-end corner radius (3 mm endmill); the lip-side corners stay sharp

JOINT_CLEAR = 0.0       # Base dovetail socket clearance per face: line-to-line, as in the published v9 tight fit
JOINT_Z_CLEAR = 0.20    # Vertical gap between each tongue landing and its socket roof, so both halves rest on the desk
COMP_INTERF = 0.08      # Local interference per flank on chevron compression ribs

TILT_RAD = math.radians(TILT_DEG)


def z_desk_in_print_frame(y: float) -> float:
    """Desk plane Z_p below the top-face point at print Y=y (measured along the top-face normal, Z_p down from the top)."""
    h_inst = JUNC_H - (WRIST_D - y) * math.sin(TILT_RAD)
    return h_inst / math.cos(TILT_RAD)


def poly_to_pts(poly: Any) -> list[list[float]]:
    coords = list(poly.exterior.coords)
    pts = [[round(float(x), 4), round(float(y), 4)] for x, y in coords[:-1]]
    pts.append(pts[0])
    return pts


# Stock ball-catch strike pocket, fitted to IMG_0218 + IMG_0222 (iPhone Ultra Wide 13 mm eq., f = 1485 px) by
# two-view ray-cast silhouette matching; scale from the 13.0 mm strike screw pitch (plate-frame mm).
# The strike plate measures ~20.5 x 6.55 mm; its 7.25 mm wide pocket ends in the CNC "mushroom" relief —
# a 4.1 mm semicircular lobe tangent to the skirt-side wall reaching 4.55 mm past the plate end, beside an
# interior-half end wall 2.15 mm past the plate end, joined by an R0.85 shoulder. Pocket depth is not re-fitted.
_STRIKE_PLATE, _STRIKE_POCKET = spec.value("ball_catch.strike_plate"), spec.value("ball_catch.strike_pocket")
STRIKE_PLATE_HALF_LEN = _STRIKE_PLATE["length"] / 2
STRIKE_PLATE_HALF_W = _STRIKE_PLATE["width"] / 2
STRIKE_POCKET_HALF_W = _STRIKE_POCKET["half_w"]
STRIKE_END_WALL_GAP = _STRIKE_POCKET["end_wall_gap"]
STRIKE_LOBE_REACH = _STRIKE_POCKET["lobe_reach"]
STRIKE_LOBE_R = _STRIKE_POCKET["lobe_r"]
STRIKE_SHOULDER_R = _STRIKE_POCKET["shoulder_r"]
STRIKE_TOOL_R = _STRIKE_POCKET["tool_r"]


def strike_pocket_poly(sx_p: float, sy_p: float, skirt_sign: float) -> sg.Polygon:
    """Plan outline of one strike pocket in plate coordinates; `skirt_sign` is +1 when the outer wall is at +Y."""
    x_end = STRIKE_PLATE_HALF_LEN + STRIKE_END_WALL_GAP
    lobe_cx = STRIKE_PLATE_HALF_LEN + STRIKE_LOBE_REACH - STRIKE_LOBE_R
    lobe_cy = skirt_sign * (STRIKE_POCKET_HALF_W - STRIKE_LOBE_R)
    shape = sg.box(-x_end, -STRIKE_POCKET_HALF_W, x_end, STRIKE_POCKET_HALF_W)
    for end in (-1.0, 1.0):
        lobe = sg.LineString([(end * x_end, lobe_cy), (end * lobe_cx, lobe_cy)]).buffer(STRIKE_LOBE_R, quad_segs=24)
        shape = shape.union(lobe)
    shape = shape.buffer(STRIKE_SHOULDER_R, quad_segs=12).buffer(-STRIKE_SHOULDER_R, quad_segs=12)
    shape = shape.buffer(-STRIKE_TOOL_R, quad_segs=12).buffer(STRIKE_TOOL_R, quad_segs=12)
    shape = shape.simplify(0.01)
    assert shape.geom_type == "Polygon" and not shape.interiors, shape.geom_type
    return sg.Polygon([(x + sx_p, y + sy_p) for x, y in shape.exterior.coords[:-1]])



def tongue_ramp_z(x: float, z_tongue: float, proj: float) -> float:
    """Z_p of the self-supporting print ramp under a tongue at X: (0.8, z_tongue - 0.5) to (proj + 0.6, z_tongue + proj - 0.2).
    The tongue keeps the material above it; the socket fill (step 15b) rises to it less `JOINT_Z_CLEAR`."""
    return z_tongue - 0.5 + (x - 0.8) * (proj + 0.3) / (proj - 0.2)


def dovetail_poly(
    yc: float,
    neck_half: float,
    head_half: float,
    proj: float,
    clear: float = 0.0,
    neck_taper: float = 0.55,
) -> sg.Polygon:
    """Planar 2D Polygon of a plain dovetail tongue, or its socket when `clear` > 0."""
    poly = sg.Polygon([
        (-2.0, yc - neck_half),
        (0.0, yc - neck_half),
        (1.4, yc - (neck_half - neck_taper)),
        (proj, yc - head_half),
        (proj, yc + head_half),
        (1.4, yc + (neck_half - neck_taper)),
        (0.0, yc + neck_half),
        (-2.0, yc + neck_half),
    ])
    if clear != 0.0:
        poly = poly.buffer(clear, join_style="mitre", mitre_limit=4.0)
    return poly


def socket_rib_polys(yc: float, neck_half: float, head_half: float, proj: float, neck_taper: float) -> list[sg.Polygon]:
    """Chevron compression ribs standing proud of both cleared socket flanks.

    Each triangle is rooted 0.05 mm inside the socket wall; its apex reaches `COMP_INTERF`
    past the plain tongue flank, so the seated tongue bites only on these ribs.
    """
    p_a = np.array([1.4, yc - neck_half + neck_taper])
    p_b = np.array([proj, yc - head_half])
    tang = p_b - p_a
    u_out = np.array([tang[1], -tang[0]]) / float(np.linalg.norm(tang))
    if u_out[1] > 0:
        u_out = -u_out
    root = JOINT_CLEAR + 0.05
    lower = [
        p_a + 0.35 * tang + u_out * root,
        p_a + 0.52 * tang - u_out * COMP_INTERF,
        p_a + 0.69 * tang + u_out * root,
    ]
    return [
        sg.Polygon([(float(p[0]), float(yc + sign * (p[1] - yc))) for p in lower])
        for sign in (1.0, -1.0)
    ]


def build_solidcraft_commands(board_id: str) -> list[dict[str, Any]]:
    cmds: list[dict[str, Any]] = []
    usb_x, usb_w = usb_notch_print(board_id)

    def add_param(name: str, expr: str, comment: str = "") -> None:
        p: dict[str, Any] = {"name": name, "expression": expr}
        if comment:
            p["comment"] = comment
        cmds.append({"command": "parameters.add", "params": p})

    # 1. Editable User Parameters in SolidCraft Timeline (19 parameters)
    add_param("case_w", f"{CASE_W} mm", f"Top-case outer width ({CASE_W:.2f} mm, from caliper bezels)")
    add_param("case_d", f"{CASE_D} mm", f"Top-case outer depth ({CASE_D:.2f} mm, from caliper bezels)")
    add_param("wrist_d", f"{WRIST_D} mm", "Integrated palm-rest depth (80.00 mm)")
    add_param("tilt_deg", f"{TILT_DEG} deg", "Keyboard & top-deck angle (6.0 deg)")
    add_param("junc_h", f"{JUNC_H} mm", f"Installed top-face height at Y=wrist_d junction ({JUNC_H:.2f} mm)")
    add_param("skirt_h", f"{SKIRT_H} mm", f"Top-case total height ({SKIRT_H:.2f} mm, caliper)")
    add_param("z_floor", f"{Z_FLOOR} mm", f"Base pocket floor ({Z_FLOOR:.2f} mm, caliper)")
    add_param("z_gasket", f"{Z_GASKET} mm", f"6 open silicone-cap pocket floor ({Z_GASKET:.2f} mm, caliper)")
    add_param("z_strike", f"{Z_STRIKE} mm", f"4 ball-catch strike pocket floor ({Z_STRIKE:.2f} mm, caliper)")
    add_param("skin_t", f"{SKIN_T} mm", "Wrist-rest honeycomb top skin thickness")
    add_param("skirt_wall", f"{SKIRT_WALL} mm", f"Skirt wall thickness, sides and back ({SKIRT_WALL:.2f} mm, caliper)")
    add_param("front_wall", f"{FRONT_WALL} mm", f"Skirt wall thickness, front ({FRONT_WALL:.2f} mm, caliper)")
    add_param("wrist_wall", f"{WRIST_WALL} mm", "Wrist-rest perimeter wall thickness")
    add_param("corner_r", f"{CORNER_R} mm", f"Outer vertical corner fillet radius ({CORNER_R:.2f} mm)")
    add_param("usb_x", f"{usb_x} mm", f"USB-C center X ({usb_x:.2f} mm)")
    add_param("usb_w", f"{usb_w} mm", f"USB-C opening width ({usb_w:.2f} mm)")
    add_param("usb_depth", f"{USB_DEPTH} mm", f"USB-C notch depth from skirt lip ({USB_DEPTH:.2f} mm, top at Z_p {USB_TOP_ZP:.2f})")
    add_param("joint_clear", f"{JOINT_CLEAR} mm", "Base dovetail clearance per face")
    add_param("joint_z_clear", f"{JOINT_Z_CLEAR} mm", "Vertical tongue-landing to socket-roof clearance")

    # 2. Main Unibody Envelope + `CORNER_R` Outer Corner Fillets (wrist-rest front and case back corners)
    cmds.extend([
        {
            "command": "solid.box",
            "params": {
                "length": "case_w",
                "width": "wrist_d + case_d",
                "height": 24,
                "center": [0, "(wrist_d + case_d)/2", 12],
                "body_name": "Unibody",
                "name": "UnibodyBlock",
            },
        },
        {
            "command": "solid.fillet",
            "params": {
                "edges": [
                    [-CASE_W / 2, 0, 12],
                    [CASE_W / 2, 0, 12],
                    [-CASE_W / 2, WRIST_D + CASE_D, 12],
                    [CASE_W / 2, WRIST_D + CASE_D, 12],
                ],
                "radius": "corner_r",
                "name": "OuterCornerFillets",
            },
        },
    ])

    # 3. Single Side-Profile Cut on YZ Plane (6-deg wrist desk plane + 20.01 mm case skirt lip)
    z_m2 = round(z_desk_in_print_frame(-2.0), 4)
    z_w = round(z_desk_in_print_frame(WRIST_D), 4)
    cmds.extend([
        {"command": "sketch.create", "params": {"plane": "YZ", "offset": "-160", "name": "SideProfileSk"}},
        {
            "command": "sketch.line",
            "params": {
                "points": [
                    [-2.0, z_m2],
                    [WRIST_D, z_w],
                    [WRIST_D, SKIRT_H],
                    [WRIST_D + CASE_D + 2.0, SKIRT_H],
                    [WRIST_D + CASE_D + 2.0, 26.0],
                    [-2.0, 26.0],
                    [-2.0, z_m2],
                ]
            },
        },
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {
                "sketch": "SideProfileSk",
                "distance": 320,
                "operation": "cut",
                "targets": ["Unibody"],
                "name": "DeskAndSkirtProfileCut",
            },
        },
    ])

    # 4. Base Pocket from the skirt lip down to the floor (`z_floor = 9.69 mm`), leaving the outer skirt wall (`2.85 mm`
    #    sides and back, `2.80 mm` front) with R = 5.0 mm inner corners. Every later interior feature is cut into this floor.
    cx_in = round(CASE_W / 2 - SKIRT_WALL, 3)
    cy0_in = round(WRIST_D + FRONT_WALL, 3)
    cy1_in = round(WRIST_D + CASE_D - SKIRT_WALL, 3)
    cmds.extend([
        {
            "command": "solid.box",
            "params": {
                "length": "case_w - 2*skirt_wall",
                "width": "case_d - skirt_wall - front_wall",
                "height": 20,
                "center": [0, "wrist_d + front_wall + (case_d - skirt_wall - front_wall)/2", "z_floor + 10 mm"],
                "operation": "cut",
                "targets": ["Unibody"],
                "name": "BasePocketToFloor",
            },
        },
        {
            "command": "solid.fillet",
            "params": {
                "edges": [
                    [-cx_in, cy0_in, 12.0],
                    [cx_in, cy0_in, 12.0],
                    [-cx_in, cy1_in, 12.0],
                    [cx_in, cy1_in, 12.0],
                ],
                "radius": INNER_SKIRT_R,
                "name": "CavityInnerCornerFillets",
            },
        },
    ])

    # 6. Punch Exact HHKB 7U Keycap Opening (`Z_p = -1 .. 15 mm`) + CNC R=1.2 mm Corner Fillets on 6 vertices;
    #    the two bottom-row outer corners next to the blockers keep only 0.50/0.34 mm keycap clearance, so they take R=0.5.
    hhkb_world_pts = [
        list(pw(OPENING_P[0], 25.20)),
        list(pw(28.55, 25.20)),
        list(pw(28.55, OPENING_P[1])),
        list(pw(257.35, OPENING_P[1])),
        list(pw(257.35, 25.20)),
        list(pw(OPENING_P[2], 25.20)),
        list(pw(OPENING_P[2], OPENING_P[3])),
        list(pw(OPENING_P[0], OPENING_P[3])),
        list(pw(OPENING_P[0], 25.20)),
    ]
    bottom_row_corners = {2, 3}
    hhkb_corner_edges = [[pt[0], pt[1], 3.0] for i, pt in enumerate(hhkb_world_pts[:-1]) if i not in bottom_row_corners]
    bottom_row_corner_edges = [[hhkb_world_pts[i][0], hhkb_world_pts[i][1], 3.0] for i in sorted(bottom_row_corners)]
    cmds.extend([
        {"command": "sketch.create", "params": {"plane": "XY", "offset": -1.0, "name": "HHKBOpeningSk"}},
        {"command": "sketch.line", "params": {"points": hhkb_world_pts}},
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {
                "sketch": "HHKBOpeningSk",
                "distance": 15.0,
                "operation": "cut",
                "targets": ["Unibody"],
                "name": "HHKBKeycapCutout",
            },
        },
        {
            "command": "solid.fillet",
            "params": {
                "edges": hhkb_corner_edges,
                "radius": 1.2,
                "name": "HHKBOpeningCornerFillets",
            },
        },
        {
            "command": "solid.fillet",
            "params": {
                "edges": bottom_row_corner_edges,
                "radius": 0.5,
                "name": "HHKBBottomRowCornerFillets",
            },
        },
    ])

    # 7. Plate-body relief + 6 open silicone-cap pockets cut in one go to `z_gasket = 6.30 mm` (one level, owner), straight
    #    from the floor (`orange_cut_poly_p`). The seated gasket plate occupies `Z_p = 7.50..9.00`.
    orange_w = sg.Polygon([pw(x, y) for x, y in orange_cut_poly_p().exterior.coords[:-1]])
    orange_pick = orange_w.representative_point()
    cmds.extend([
        {"command": "sketch.create", "params": {"plane": "XY", "offset": "z_gasket", "name": "CapPocketsAndReliefSk"}},
        {"command": "sketch.line", "params": {"points": poly_to_pts(orange_w)}},
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {
                "sketch": "CapPocketsAndReliefSk",
                "profiles": [{"point": [round(orange_pick.x, 3), round(orange_pick.y, 3)]}],
                "distance": "z_floor - z_gasket + 1 mm",
                "operation": "cut",
                "targets": ["Unibody"],
                "name": "CapPocketsAndPlateRelief",
            },
        },
    ])

    # 8. Four Ball-Catch Strike Pockets with stock CNC mushroom end reliefs (`strike_pocket_poly`), floor at `z_strike`.
    #    Lobes sit on the skirt half: +Y for the back pair, -Y for the front pair.
    strike_sites_p = strike_centers_p()
    cmds.append({"command": "sketch.create", "params": {"plane": "XY", "offset": "z_strike", "name": "StrikePocketsSk"}})
    strike_picks: list[dict[str, list[float]]] = []
    for _, sx_p, sy_p in strike_sites_p:
        pocket_p = strike_pocket_poly(sx_p, sy_p, skirt_sign=1.0 if sy_p > 50.0 else -1.0)
        pocket_w = sg.Polygon([pw(x, y) for x, y in pocket_p.exterior.coords[:-1]])
        cmds.append({"command": "sketch.line", "params": {"points": poly_to_pts(pocket_w)}})
        cxw, cyw = pw(sx_p, sy_p)
        strike_picks.append({"point": [cxw, cyw]})
    cmds.append({"command": "sketch.finish", "params": {}})
    cmds.append({
        "command": "solid.extrude",
        "params": {
            "sketch": "StrikePocketsSk",
            "profiles": strike_picks,
            "distance": 5.0,
            "operation": "cut",
            "targets": ["Unibody"],
            "name": "BallCatchStrikePockets",
        },
    })

    # 9. Blind M2 strike-screw pilot holes (Ø1.8 mm, `STRIKE_PILOT_DEPTH` past each strike pocket floor)
    pilot_sets = [
        ("StrikePilotsSk", f"z_strike - {STRIKE_PILOT_DEPTH} mm", [(round(pw(sx_p, sy_p)[0] + dx_s, 4), pw(sx_p, sy_p)[1], 0.90)
                                                                  for _, sx_p, sy_p in strike_sites_p for dx_s in (-6.5, 6.5)]),
    ]
    for sk_name, sk_offset, holes in pilot_sets:
        cmds.append({"command": "sketch.create", "params": {"plane": "XY", "offset": sk_offset, "name": sk_name}})
        for hx, hy, hr in holes:
            cmds.append({"command": "sketch.circle.center", "params": {"center": [hx, hy], "radius": hr}})
        cmds.append({"command": "sketch.finish", "params": {}})
        cmds.append({
            "command": "solid.extrude",
            "params": {
                "sketch": sk_name,
                "profiles": [{"point": [hx, hy]} for hx, hy, _ in holes],
                "distance": round(STRIKE_PILOT_DEPTH + 1.45, 2),
                "operation": "cut",
                "targets": ["Unibody"],
                "name": sk_name.replace("Sk", "Holes"),
            },
        })

    # 10b. SolidCraft v0.22.0 boolean workaround, part 1: with no inner loop in the front-right floor face, the first
    #      RightHalf joint-socket cut leaves a zero-width slit at X = 25.965, drops the front top chamfer up to that slit
    #      and loses ~38 mm^3 of wrist material. A temporary bore here avoids it; part 2 refills it after the joints.
    wa_x, wa_y = KERNEL_WORKAROUND_W
    cmds.extend([
        {"command": "sketch.create", "params": {"plane": "XY", "offset": "z_floor - 3.8 mm", "name": "KernelWorkaroundBoreSk"}},
        {"command": "sketch.circle.center", "params": {"center": [wa_x, wa_y], "radius": 1.00}},
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {
                "sketch": "KernelWorkaroundBoreSk",
                "profiles": [{"point": [wa_x, wa_y]}],
                "distance": 4.5,
                "operation": "cut",
                "targets": ["Unibody"],
                "name": "KernelWorkaroundBore",
            },
        },
    ])

    # 11. USB-C notch through the back skirt wall: open at the lip, `USB_END_R` corners at its closed end (Z_p
    #     `USB_TOP_ZP`). XZ sketch coordinates are (X, -Z_p); the profile runs 1 mm past the lip and is cut through the wall.
    usb_xz = sg.box(usb_x - usb_w / 2, USB_TOP_ZP, usb_x + usb_w / 2, SKIRT_H + 1.0)
    usb_xz = usb_xz.buffer(-USB_END_R).buffer(USB_END_R, quad_segs=12).union(
        sg.box(usb_x - usb_w / 2, USB_TOP_ZP + USB_END_R, usb_x + usb_w / 2, SKIRT_H + 1.0)).simplify(1e-4)
    usb_sk = sg.Polygon([(x, -z) for x, z in usb_xz.exterior.coords[:-1]])
    back_inner_y = round(WRIST_D + CASE_D - SKIRT_WALL, 3)
    cmds.extend([
        {"command": "sketch.create", "params": {"plane": "XZ", "offset": str(round(back_inner_y - 1.0, 3)), "name": "USBNotchSk"}},
        {"command": "sketch.line", "params": {"points": poly_to_pts(usb_sk)}},
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {"sketch": "USBNotchSk", "distance": round(SKIRT_WALL + 2.0, 3), "operation": "cut",
                       "targets": ["Unibody"], "name": "USBCutout"},
        },
    ])

    # 12. Wrist-Rest Symmetric Interior Hollows (contoured around the 4 front bumpon pads) + Right-Side Undercut Boss
    #     Strip + 45-deg pad undercuts
    assert (PAD_D - BUMPON_D_MAX) / 2 >= 1.0 and PAD_W >= BUMPON_D_MAX + 2.0, "bumpon pad too small"
    w_in_x = round(CASE_W / 2 - WRIST_WALL, 3)
    front_notches: list[list[float]] = []
    for c in sorted(PAD_X, reverse=True):  # left half, outer pad first along the front (X rising)
        x0, x1 = -(c + PAD_W / 2), -(c - PAD_W / 2)
        front_notches += [[x0, WRIST_WALL], [x0, PAD_D], [x1, PAD_D], [x1, WRIST_WALL]]
    left_hollow_pts = [
        [-w_in_x + 5.5, 2.2],
        *front_notches,
        [-4.0, 2.2],
        [-4.0, 77.8],
        [-w_in_x, 77.8],
        [-w_in_x, 7.7],
        [-w_in_x + 5.5, 2.2],
    ]
    right_hollow_pts = [[-x, y] for x, y in reversed(left_hollow_pts)]

    cmds.extend([
        {"command": "sketch.create", "params": {"plane": "XY", "offset": "skin_t", "name": "WristHollowSk"}},
        {"command": "sketch.line", "params": {"points": left_hollow_pts}},
        {"command": "sketch.line", "params": {"points": right_hollow_pts}},
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {
                "sketch": "WristHollowSk",
                "profiles": [{"point": [-75.0, 40.0]}, {"point": [75.0, 40.0]}],
                "distance": 24,
                "operation": "cut",
                "targets": ["Unibody"],
                "name": "WristBayHollows",
            },
        },
        # Socket boss strip (X 3.5..9.8) carrying the right-half dovetail sockets. It stands on the wrist skin (bottom
        # 0.2 mm into it): v5.7 started it at Z_p 4.5, a 5.6 mm wide flat overhang with nothing under it in print.
        {"command": "sketch.create", "params": {"plane": "YZ", "offset": "3.5", "name": "RightBossSideSk"}},
        {
            "command": "sketch.line",
            "params": {
                "points": [
                    [14.0, round(SKIN_T - 0.2, 3)],
                    [79.0, round(SKIN_T - 0.2, 3)],
                    [79.0, 17.5],
                    [14.0, round(z_desk_in_print_frame(14.0) - 0.5, 3)],
                    [14.0, round(SKIN_T - 0.2, 3)],
                ]
            },
        },
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {
                "sketch": "RightBossSideSk",
                "distance": 6.3,
                "operation": "join",
                "targets": ["Unibody"],
                "name": "RightSocketBossStrip",
            },
        },
    ])

    # Pad undercuts: each pad's underside rises at 45 deg to a `PAD_TIP_T` vertical land at its inner edge, so it prints
    # without support; the pad stays full height where that slope meets the skin, at least `PAD_COLUMN_D` from the wall.
    # Only cuts: the pad face stays the step-3 desk plane and the pad sides the hollow notch, and the cut reaches 1 mm
    # into the empty bay past the pad's sides and inner edge (no coincident faces).
    z_tip = z_desk_in_print_frame(PAD_D) - PAD_TIP_T  # underside at the pad's inner edge
    y_out = PAD_D + 1.0
    below_slope = sg.Polygon([(y_out, z_tip + 1.0), (PAD_D - 100.0, z_tip - 100.0), (y_out, z_tip - 100.0)])
    cut = sg.box(PAD_COLUMN_D, SKIN_T, y_out, z_tip + 1.0).intersection(below_slope)
    assert cut.geom_type == "Polygon" and cut.area > 1.0, cut
    undercut = sg.Polygon([(round(y, 4), round(z, 4)) for y, z in cut.exterior.coords[:-1]])
    for i, x0 in enumerate(sorted(s * c - PAD_W / 2 for c in PAD_X for s in (-1.0, 1.0))):
        cmds.extend([
            {"command": "sketch.create", "params": {"plane": "YZ", "offset": str(x0 - 1.0), "name": f"PadUndercutSk{i}"}},
            {"command": "sketch.line", "params": {"points": poly_to_pts(undercut)}},
            {"command": "sketch.finish", "params": {}},
            {
                "command": "solid.extrude",
                "params": {
                    "sketch": f"PadUndercutSk{i}",
                    "profiles": [{"point": [round(undercut.centroid.x, 4), round(undercut.centroid.y, 4)]}],
                    "distance": PAD_W + 2.0,
                    "operation": "cut",
                    "targets": ["Unibody"],
                    "name": f"PadUndercut{i}",
                },
            },
        ])

    # Bumpon pockets: one sketch on the desk plane (x along X, v up the 6-deg slope, normal out of the pad faces), a
    # 72-gon circumscribing `POCKET_D` centred on each pad, cut `POCKET_DEPTH` into the pad and 1 mm out past its face.
    # Flat facets keep the two halves exact mirrors; a true circle is faceted differently in each exported half.
    cos_t, sin_t = math.cos(TILT_RAD), math.sin(TILT_RAD)
    r_poly = POCKET_D / 2 / math.cos(math.pi / 72)
    cmds.append({"command": "sketch.create", "params": {
        "plane": {"origin": [0.0, 0.0, z_desk_in_print_frame(0.0)], "x_dir": [1.0, 0.0, 0.0], "y_dir": [0.0, cos_t, sin_t]},
        "name": "BumponPocketSk"}})
    for x, y in pad_centres():
        v = y / cos_t
        pts = [[round(x + r_poly * math.cos(2 * math.pi * k / 72), 4), round(v + r_poly * math.sin(2 * math.pi * k / 72), 4)]
               for k in range(72)]
        cmds.append({"command": "sketch.line", "params": {"points": [*pts, pts[0]]}})
    cmds.extend([
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {"sketch": "BumponPocketSk", "distance": POCKET_DEPTH, "direction": "negative", "distance2": 1.0,
                       "operation": "cut", "targets": ["Unibody"], "name": "BumponPockets"},
        },
    ])

    # 13. Symmetric Honeycomb Lattice Cutout through Wrist-Rest Top Skin (Z_p = 0 .. skin_t)
    hex_r = round(4.5 - RIB / math.sqrt(3), 4)
    left_bay = sg.Polygon([(-w_in_x + 5.5, 2.2), (-4.0, 2.2), (-4.0, 77.8), (-w_in_x, 77.8), (-w_in_x, 7.7)]).buffer(-1.0)
    right_bay = sg.Polygon([(4.0, 2.2), (w_in_x - 5.5, 2.2), (w_in_x, 7.7), (w_in_x, 77.8), (4.0, 77.8)]).buffer(-1.0)

    cmds.append({"command": "sketch.create", "params": {"plane": "XY", "offset": -0.5, "name": "HoneycombSk"}})
    hex_picks = []
    for col in range(-22, 23):
        hx = round(col * 6.75, 4)
        for row in range(-6, 7):
            hy = round(40.0 + (row + (col % 2) * 0.5) * 4.5 * math.sqrt(3), 4)
            cell = sg.Point(hx, hy).buffer(hex_r)
            if left_bay.contains(cell) or right_bay.contains(cell):
                cmds.append({
                    "command": "sketch.polygon.inscribed",
                    "params": {"center": [hx, hy], "radius": hex_r, "sides": 6, "connect": False},
                })
                hex_picks.append({"point": [hx, hy]})
    cmds.append({"command": "sketch.finish", "params": {}})
    cmds.append({
        "command": "solid.extrude",
        "params": {
            "sketch": "HoneycombSk",
            "profiles": hex_picks,
            "distance": "skin_t + 1 mm",
            "operation": "cut",
            "targets": ["Unibody"],
            "name": "HoneycombSkinCutout",
        },
    })

    # 14. Split Unibody on YZ Symmetry Plane (X = 0) -> `RightHalf` & `LeftHalf` (the back strip moves over in 15a)
    cmds.extend([
        {"command": "solid.split_body", "params": {"body": "Unibody", "plane": "YZ", "name": "CenterYZSplit"}},
        {"command": "body.rename", "params": {"body": "Unibody", "name": "RightHalf"}},
        {"command": "body.rename", "params": {"body": "Unibody (1)", "name": "LeftHalf"}},
    ])

    # 15. Screwless 3-dovetail system across X = 0 (with planar chevron compression ribs):
    #     - Plain tongue meets the plain socket line-to-line (0 mm) in plan; each tongue starts `JOINT_Z_CLEAR` below the
    #       socket roof (`z_tongue = z_stop + 0.20`), the only vertical contact between the halves.
    #     - Chevron ribs stand in the socket band `[z_tongue + 0.3, z_tongue + rib_top]` (fixed in the RightHalf),
    #       so the tongue bites only once its ramped underside reaches that band (final 2.2 mm of travel).
    #     - The tongue's 45-deg print ramp is matched by a socket fill (15b), so tongue and socket meet over every face.
    for jname, yc, nh, hh, proj, z_stop, z_top, z_sock_top, rib_top, taper in JOINTS_SPEC:
        z_tongue = round(z_stop + JOINT_Z_CLEAR, 3)
        assert nh - taper > 0.0, f"{jname}: neck half-width at X=1.4 must stay positive"
        z_limit = SKIRT_H if yc - hh > WRIST_D else z_desk_in_print_frame(yc - hh)
        assert z_top <= z_limit - 0.4, f"{jname}: tongue top {z_top} breaks the desk/skirt plane {z_limit:.3f}"
        sock_poly = dovetail_poly(yc, nh, hh, proj, clear=JOINT_CLEAR, neck_taper=taper)
        male_poly = dovetail_poly(yc, nh, hh, proj, neck_taper=taper)
        rib_polys = socket_rib_polys(yc, nh, hh, proj, taper)
        assert sock_poly.is_valid and male_poly.is_valid and all(p.is_valid for p in rib_polys), jname

        cmds.extend([
            {"command": "sketch.create", "params": {"plane": "XY", "offset": z_stop, "name": f"{jname}SockSk"}},
            {"command": "sketch.line", "params": {"points": poly_to_pts(sock_poly)}},
            {"command": "sketch.finish", "params": {}},
            {
                "command": "solid.extrude",
                "params": {
                    "sketch": f"{jname}SockSk",
                    "profiles": [{"point": [round(proj / 2, 2), yc]}],
                    "distance": round(z_sock_top - z_stop, 3),
                    "operation": "cut",
                    "targets": ["RightHalf"],
                    "name": f"{jname}Socket",
                },
            },
            {"command": "sketch.create", "params": {"plane": "XY", "offset": round(z_tongue + 0.3, 3), "name": f"{jname}SockRibSk"}},
            *({"command": "sketch.line", "params": {"points": poly_to_pts(p)}} for p in rib_polys),
            {"command": "sketch.finish", "params": {}},
            {
                "command": "solid.extrude",
                "params": {
                    "sketch": f"{jname}SockRibSk",
                    "profiles": [
                        {"point": [round(p.representative_point().x, 4), round(p.representative_point().y, 4)]}
                        for p in rib_polys
                    ],
                    "distance": round(rib_top - 0.3, 3),
                    "operation": "join",
                    "targets": ["RightHalf"],
                    "name": f"{jname}SocketRibs",
                },
            },
            {"command": "sketch.create", "params": {"plane": "XY", "offset": z_tongue, "name": f"{jname}TongueSk"}},
            {"command": "sketch.line", "params": {"points": poly_to_pts(male_poly)}},
            {"command": "sketch.finish", "params": {}},
            {
                "command": "solid.extrude",
                "params": {
                    "sketch": f"{jname}TongueSk",
                    "profiles": [{"point": [round(proj / 2, 2), yc]}],
                    "distance": round(z_top - z_tongue, 3),
                    "operation": "join",
                    "targets": ["LeftHalf"],
                    "name": f"{jname}Tongue",
                },
            },
            # 45-deg self-supporting print ramp under the overhanging tongue
            {
                "command": "sketch.create",
                "params": {"plane": "XZ", "offset": str(round(yc - hh - 1.2, 3)), "name": f"{jname}RampSk"},
            },
            {
                "command": "sketch.line",
                "params": {
                    "points": [
                        [0.8, round(-tongue_ramp_z(0.8, z_tongue, proj), 3)],
                        [round(proj + 0.6, 3), round(-tongue_ramp_z(0.8, z_tongue, proj), 3)],
                        [round(proj + 0.6, 3), round(-tongue_ramp_z(proj + 0.6, z_tongue, proj), 3)],
                        [0.8, round(-tongue_ramp_z(0.8, z_tongue, proj), 3)],
                    ]
                },
            },
            {"command": "sketch.finish", "params": {}},
            {
                "command": "solid.extrude",
                "params": {
                    "sketch": f"{jname}RampSk",
                    "distance": round(2 * hh + 2.4, 3),
                    "operation": "cut",
                    "targets": ["LeftHalf"],
                    "name": f"{jname}PrintChamfer",
                },
            },
        ])

    # 15a. Stagger: the back strip of the RightHalf from X = 0 to `BACK_SEAM_X - gap/2` (above `SPLIT_STEP_Y`, so only
    #      back bezel and skirt) joins the LeftHalf; the RightHalf loses it up to `BACK_SEAM_X + gap/2` (gap 0: one
    #      plane). It runs after the dovetails on purpose: a tongue joined to a LeftHalf that has been through
    #      `solid.combine` came out shifted by 0.4 um (SolidCraft v0.22.0), enough to drag along its line-to-line socket.
    half_gap = round(BACK_SEAM_GAP / 2, 3)

    def strip_sketch(name: str, x0: float, x1: float) -> list[dict[str, Any]]:
        pts = [[x0, SPLIT_STEP_Y], [x1, SPLIT_STEP_Y], [x1, 205.0], [x0, 205.0], [x0, SPLIT_STEP_Y]]
        return [{"command": "sketch.create", "params": {"plane": "XY", "offset": -5.0, "name": name}},
                {"command": "sketch.line", "params": {"points": pts}},
                {"command": "sketch.finish", "params": {}}]

    cmds.extend([
        *strip_sketch("BackStripSk", 0.0, round(BACK_SEAM_X - half_gap, 3)),
        {"command": "solid.extrude", "params": {"sketch": "BackStripSk", "distance": 40.0, "operation": "new",
                                                "body_name": "BackStrip", "name": "BackStripRegion"}},
        {"command": "solid.combine",
         "params": {"target": "BackStrip", "tools": ["RightHalf"], "operation": "intersect", "keep_tools": True}},
        *strip_sketch("BackStripCutSk", -1.0, round(BACK_SEAM_X + half_gap, 3)),
        {"command": "solid.extrude", "params": {"sketch": "BackStripCutSk", "distance": 40.0, "operation": "cut",
                                                "targets": ["RightHalf"], "name": "BackStripCut"}},
        {"command": "solid.combine", "params": {"target": "LeftHalf", "tools": ["BackStrip"], "operation": "join"}},
    ])

    # 15b. Socket fills: the RightHalf fills the space under each tongue's print ramp up to the ramp lowered by
    #      `JOINT_Z_CLEAR`, inside the socket outline, so the ramp is a glue face with the same 0.20 mm (vertical) line as
    #      the tongue landing, not a 3 mm void. Fill = socket prism intersected with the lowered-ramp profile, joined
    #      after the dovetails (see 15a). Printed on the socket floor, its top is the 45-deg slope: no support.
    for jname, yc, nh, hh, proj, z_stop, *_, taper in JOINTS_SPEC:
        z_tongue = round(z_stop + JOINT_Z_CLEAR, 3)
        z_base = round(z_stop - 0.3, 3)
        x_end = round(proj + 0.5, 3)
        k = (proj + 0.3) / (proj - 0.2)
        x_start = round(0.8 + (z_base + JOINT_Z_CLEAR - tongue_ramp_z(0.8, z_tongue, proj)) / k, 4)
        z_end = round(tongue_ramp_z(x_end, z_tongue, proj) - JOINT_Z_CLEAR, 4)
        cmds.extend([
            {"command": "sketch.create", "params": {"plane": "XY", "offset": z_base, "name": f"{jname}FillPlanSk"}},
            {"command": "sketch.line",
             "params": {"points": poly_to_pts(dovetail_poly(yc, nh, hh, proj, clear=JOINT_CLEAR, neck_taper=taper))}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude",
             "params": {"sketch": f"{jname}FillPlanSk", "profiles": [{"point": [round(proj / 2, 2), yc]}],
                        "distance": round(z_end - z_base + 0.5, 3), "operation": "new",
                        "body_name": f"{jname}SocketFill", "name": f"{jname}FillPlan"}},
            {"command": "sketch.create",
             "params": {"plane": "XZ", "offset": str(round(yc - hh - 1.0, 3)), "name": f"{jname}FillRampSk"}},
            {"command": "sketch.line",
             "params": {"points": [[x_start, -z_base], [x_end, -z_base], [x_end, -z_end], [x_start, -z_base]]}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.extrude",
             "params": {"sketch": f"{jname}FillRampSk", "distance": round(2 * hh + 2.0, 3), "operation": "intersect",
                        "targets": [f"{jname}SocketFill"], "name": f"{jname}FillRamp"}},
            {"command": "solid.combine",
             "params": {"target": "RightHalf", "tools": [f"{jname}SocketFill"], "operation": "join"}},
        ])

    # 15c. Back seam: Y alignment from a 45-deg wedge key on the LeftHalf under the seam strike pocket floor, sliding down
    #      with the dovetails into a matching notch in the RightHalf (the wedge lowered by `JOINT_Z_CLEAR`) that opens
    #      into the strike pocket. X and Z across the seam come from the stock strike plate screwed into both halves.
    #      The key root sinks 0.3 mm into the LeftHalf.
    bk = back_seam_key()
    root_x, root_z = round(bk["key_x0"] - 0.3, 3), round(BACK_KEY_Z0 - 0.3, 3)
    notch_pts = [[x, -z] for x, z in bk["notch_xz"]] + [[bk["notch_xz"][0][0], -bk["notch_xz"][0][1]]]
    cmds.extend([
        {"command": "sketch.create",
         "params": {"plane": "XZ", "offset": str(round(bk["key_y"] - BACK_KEY_HW, 3)), "name": "BackSeamKeySk"}},
        {"command": "sketch.line",
         "params": {"points": [[root_x, -root_z], [root_x, -Z_STRIKE], [bk["key_tip_x"], -Z_STRIKE], [root_x, -root_z]]}},
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {"sketch": "BackSeamKeySk", "distance": round(2 * BACK_KEY_HW, 3), "operation": "join",
                       "targets": ["LeftHalf"], "name": "BackSeamKey"},
        },
        {"command": "sketch.create", "params": {"plane": "XZ", "offset": str(bk["notch_y0"]), "name": "BackSeamNotchSk"}},
        {"command": "sketch.line", "params": {"points": notch_pts}},
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {"sketch": "BackSeamNotchSk", "distance": round(bk["notch_y1"] - bk["notch_y0"], 3),
                       "operation": "cut", "targets": ["RightHalf"], "name": "BackSeamNotch"},
        },
    ])

    # 15d. SolidCraft boolean workaround, part 2: refill the temporary bore (r + 0.05 mm, floor down past its bottom), so
    #      the floor is solid there again. Net geometry: no hole. (v5.7: an r1.6/1.65 pair left a non-manifold seam.)
    cmds.extend([
        {"command": "sketch.create", "params": {"plane": "XY", "offset": "z_floor - 3.9 mm", "name": "KernelWorkaroundFillSk"}},
        {"command": "sketch.circle.center", "params": {"center": [wa_x, wa_y], "radius": 1.05}},
        {"command": "sketch.finish", "params": {}},
        {
            "command": "solid.extrude",
            "params": {
                "sketch": "KernelWorkaroundFillSk",
                "profiles": [{"point": [wa_x, wa_y]}],
                "distance": 3.9,
                "operation": "join",
                "targets": ["RightHalf"],
                "name": "KernelWorkaroundFill",
            },
        },
    ])

    # 16. Final Crisp CNC 45-deg Outer Top Perimeter Chamfers (`0.70 mm`)
    cmds.extend([
        {
            "command": "solid.chamfer",
            "params": {
                "body": "LeftHalf",
                "edges": [[-75.0, 0.0, 0.0]],
                "distance": 0.70,
                "name": "LeftOuterTopChamfer",
            },
        },
        {
            "command": "solid.chamfer",
            "params": {
                "body": "RightHalf",
                "edges": [[75.0, 0.0, 0.0]],
                "distance": 0.70,
                "name": "RightOuterTopChamfer",
            },
        },
    ])

    return cmds


def write_3mf(path: Path, title: str, named_meshes: list[tuple[str, trimesh.Trimesh]],
              fine_layer_z: tuple[float, float] | None = FINE_LAYER_Z) -> None:
    model = ET.Element("model", {"unit": "millimeter", "xmlns": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"})
    ET.SubElement(model, "metadata", {"name": "Title"}).text = title
    ET.SubElement(model, "metadata", {"name": "Designer"}).text = "minpeter"
    ET.SubElement(model, "metadata", {"name": "License"}).text = "CC BY-NC 4.0 (non-commercial use only) — https://creativecommons.org/licenses/by-nc/4.0/"
    resources, build = ET.SubElement(model, "resources"), ET.SubElement(model, "build")
    for idx, (name, m) in enumerate(named_meshes, 1):
        obj = ET.SubElement(resources, "object", {"id": str(idx), "type": "model", "name": name})
        mesh_el = ET.SubElement(obj, "mesh")
        vs, ts = ET.SubElement(mesh_el, "vertices"), ET.SubElement(mesh_el, "triangles")
        for v in m.vertices:
            _ = ET.SubElement(vs, "vertex", dict(zip(("x", "y", "z"), (f"{float(val):.6f}" for val in v))))
        for f in m.faces:
            _ = ET.SubElement(ts, "triangle", dict(zip(("v1", "v2", "v3"), map(str, f))))
        _ = ET.SubElement(build, "item", {"objectid": str(idx)})
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("3D/3dmodel.model", ET.tostring(model, encoding="utf-8", xml_declaration=True))
        zf.writestr(
            "[Content_Types].xml",
            (
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
                "</Types>"
            ),
        )
        zf.writestr(
            "_rels/.rels",
            (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
                "</Relationships>"
            ),
        )
        if fine_layer_z is None:
            return
        # Bambu Studio / Orca height-range modifier on every object: 0.10 mm layers across the strike, cap-pocket and
        # base-pocket floors. With 0.20 mm layers the 6.30 cap floor prints at 6.4 and the 9.69 rim floor at 9.6, so the
        # silicone caps sit 0.19 mm tighter between top and bottom case; at 0.10 mm they print at 6.3 / 9.7 (sliced).
        zf.writestr(
            "Metadata/layer_config_ranges.xml",
            '<?xml version="1.0" encoding="utf-8"?>\n<objects>\n'
            + "".join(
                f' <object id="{idx}">\n  <range min_z="{fine_layer_z[0]}" max_z="{fine_layer_z[1]}">\n'
                '   <option opt_key="extruder">0</option>\n'
                f'   <option opt_key="layer_height">{FINE_LAYER_H}</option>\n  </range>\n </object>\n'
                for idx in range(1, len(named_meshes) + 1)
            )
            + "</objects>\n",
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse-solidcraft", action="store_true", help="Reuse existing .solidcraft/.step/.3mf if present")
    ap.add_argument("--board", choices=spec.board_ids(), default=spec.default_board(),
                    help="PCB whose USB-C position sets the notch (spec/boards.json); default: %(default)s")
    args = ap.parse_args()

    cmds = build_solidcraft_commands(args.board)
    usb_x, usb_w = usb_notch_print(args.board)
    script_path = OUT / "maru60-hhkb-unibody-draft.script.json"
    design_path = OUT / "maru60-hhkb-unibody-draft.solidcraft"
    step_path = OUT / "maru60-hhkb-unibody-draft.step"
    threemf_raw = OUT / "solidcraft-export.3mf"
    eval_path = OUT / "solidcraft-eval.json"

    script_path.write_text(json.dumps({"commands": cmds}, indent=2) + "\n")

    if not (args.reuse_solidcraft and design_path.exists() and step_path.exists() and threemf_raw.exists() and eval_path.exists()):
        print(f"Running SolidCraft headless engine ({len(cmds)} commands) -> {design_path.name}")
        subprocess.run(
            [
                str(SOLIDCRAFT_CLI),
                "run",
                str(script_path),
                "--save",
                str(design_path),
                "--out",
                str(step_path),
                "--out",
                str(threemf_raw),
                "--timings",
                "--json-out",
                str(OUT / "solidcraft-timings.json"),
            ],
            check=True,
        )
        subprocess.run(
            [str(SOLIDCRAFT_CLI), "eval", "--in", str(design_path), "--json-out", str(eval_path)],
            check=True,
        )
    sc_eval = json.loads(eval_path.read_text())
    print("SolidCraft B-rep bodies:", [(b["name"], round(b["volume_mm3"], 1), b["faces"]) for b in sc_eval["bodies"]])

    scene = trimesh.load(threemf_raw, force="scene")
    assert isinstance(scene, trimesh.Scene)
    raw_meshes = list(scene.dump(concatenate=False))
    raw_tms = [m for m in raw_meshes if isinstance(m, trimesh.Trimesh)]
    assert len(raw_tms) == 2, f"Expected 2 bodies, got {len(raw_tms)}"

    def to_manifold(tm: trimesh.Trimesh) -> md.Manifold:
        tm = tm.copy()
        tm.merge_vertices(digits_vertex=5)
        mf = md.Manifold(md.Mesh64(np.asarray(tm.vertices, dtype=np.float64), np.asarray(tm.faces, dtype=np.uint64)))
        assert mf.status() == md.Error.NoError, mf.status()
        return mf

    def to_trimesh(mf: md.Manifold) -> trimesh.Trimesh:
        # Welding on a 1e-5 grid also exposes zero-width slits (pinched surfaces) as open edges.
        d = mf.simplify(1e-5).to_mesh64()
        tm = trimesh.Trimesh(d.vert_properties[:, :3], d.tri_verts)
        tm.merge_vertices(digits_vertex=5)
        assert tm.is_watertight and tm.is_winding_consistent, (tm.is_watertight, tm.is_winding_consistent)
        return tm

    raw_tms.sort(key=lambda m: float(m.bounds[0][0]))
    left_mf = to_manifold(raw_tms[0])
    right_mf = to_manifold(raw_tms[1])

    seated_interference = float((left_mf ^ right_mf).volume())
    disengaged_overlap = float((left_mf.translate([0.0, 0.0, 17.5]) ^ right_mf).volume())
    blocked_x = float((left_mf.translate([-1.0, 0.0, 0.0]) ^ right_mf).volume())
    blocked_z_stop = float((left_mf.translate([0.0, 0.0, -(JOINT_Z_CLEAR + 0.3)]) ^ right_mf).volume())
    assert 0.05 < seated_interference < 30.0, f"Unexpected compression-rib interference: {seated_interference}"
    assert disengaged_overlap < 0.001, f"Disengaged overlap at dz=17.5: {disengaged_overlap}"
    assert blocked_x > 5.0 and blocked_z_stop > 1.0, (blocked_x, blocked_z_stop)

    def place_on_x2d(mf: md.Manifold) -> trimesh.Trimesh:
        tm = to_trimesh(mf)
        cx, cy = (tm.bounds[0][0] + tm.bounds[1][0]) / 2.0, (tm.bounds[0][1] + tm.bounds[1][1]) / 2.0
        z0 = tm.bounds[0][2]
        tm.apply_translation([128.0 - cx, 128.0 - cy, -z0])
        assert np.all(tm.bounds[0] >= -1e-3) and np.all(tm.bounds[1] <= [256.0, 256.0, 260.0]), tm.bounds.tolist()
        return tm

    left_plate_tm = place_on_x2d(left_mf)
    right_plate_tm = place_on_x2d(right_mf)
    left_plate_tm.export(OUT / "left-half-print.stl")
    right_plate_tm.export(OUT / "right-half-print.stl")
    write_3mf(OUT / "maru60-hhkb-left-plate.3mf", "Maru60 HHKB top case + wrist rest, for Rule60 V3 - Left half (X2D)", [("LeftHalf", left_plate_tm)])
    write_3mf(OUT / "maru60-hhkb-right-plate.3mf", "Maru60 HHKB top case + wrist rest, for Rule60 V3 - Right half (X2D)", [("RightHalf", right_plate_tm)])

    rot_deg = 180.0 - TILT_DEG
    left_inst_tm = to_trimesh(left_mf.rotate([rot_deg, 0.0, 0.0]))
    right_inst_tm = to_trimesh(right_mf.rotate([rot_deg, 0.0, 0.0]))
    z_desk_min = min(float(left_inst_tm.bounds[0][2]), float(right_inst_tm.bounds[0][2]))
    x_shift = CASE_W / 2.0
    y_shift = -min(float(left_inst_tm.bounds[0][1]), float(right_inst_tm.bounds[0][1]))
    for tm_i in (left_inst_tm, right_inst_tm):
        tm_i.apply_translation([x_shift, y_shift, -z_desk_min])
    trimesh.Scene([left_inst_tm, right_inst_tm]).export(OUT / "assembly-installed.glb")
    (OUT / "render-meshes.json").write_text(
        json.dumps(
            [
                {"name": "LeftHalf", "vertices": left_inst_tm.vertices.tolist(), "faces": left_inst_tm.faces.tolist()},
                {"name": "RightHalf", "vertices": right_inst_tm.vertices.tolist(), "faces": right_inst_tm.faces.tolist()},
            ]
        )
    )

    # Corner coupon starts at the wrist junction (Y = wrist_d) so it carries no loose strip of palm rest.
    catch_coupon_mf = left_mf ^ md.Manifold.cube([115.0, 42.0, 25.0]).translate([-149.5, WRIST_D, -0.5])
    # Back-seam pair: the split seam strike pocket with one pilot per half, the wedge key and its notch (fits the strike).
    back_sL_mf = left_mf ^ md.Manifold.cube([24.0, 16.0, 25.0]).translate([BACK_SEAM_X - 19.0, 184.0, -0.5])
    back_sR_mf = right_mf ^ md.Manifold.cube([20.0, 16.0, 25.0]).translate([BACK_SEAM_X - 1.0, 184.0, -0.5])
    front_jL_mf = left_mf ^ md.Manifold.cube([30.0, 66.0, 25.0]).translate([-15.0, 18.0, -0.5])
    front_jR_mf = right_mf ^ md.Manifold.cube([30.0, 66.0, 25.0]).translate([-15.0, 18.0, -0.5])

    def place_at(mf: md.Manifold, x0: float, y0: float) -> trimesh.Trimesh:
        tm = to_trimesh(mf)
        tm.apply_translation([x0 - tm.bounds[0][0], y0 - tm.bounds[0][1], -tm.bounds[0][2]])
        return tm

    catch_tm = place_at(catch_coupon_mf, 25.0, 25.0)
    fL_tm = place_at(front_jL_mf, 25.0, 80.0)
    fR_tm = place_at(front_jR_mf, 75.0, 80.0)
    bL_tm = place_at(back_sL_mf, 130.0, 80.0)
    bR_tm = place_at(back_sR_mf, 130.0, 105.0)

    catch_tm.export(OUT / "coupon-ballcatch-gasket-left.stl")
    write_3mf(
        OUT / "maru60-fit-test-coupons.3mf",
        "Maru60 HHKB top case + wrist rest, for Rule60 V3 - fit-test coupons",
        [
            ("CornerCatchBossCoupon", catch_tm),
            ("FrontJointLeft", fL_tm),
            ("FrontJointRight", fR_tm),
            ("BackSeamLeft", bL_tm),
            ("BackSeamRight", bR_tm),
        ],
    )

    report = {
        "version": "v7.10-front-row-bumpons",
        "generator": "SolidCraft v0.22.0 parametric timeline + 28px/mm gasket metrology",
        "solidcraft_design": str(design_path.relative_to(Path(__file__).resolve().parent)),
        "step_export": str(step_path.relative_to(Path(__file__).resolve().parent)),
        "strike_pocket_spec_mm": {
            "pocket_width": 2 * STRIKE_POCKET_HALF_W,
            "strike_plate_length": 2 * STRIKE_PLATE_HALF_LEN,
            "strike_plate_width": 2 * STRIKE_PLATE_HALF_W,
            "interior_end_wall_past_plate_end": STRIKE_END_WALL_GAP,
            "skirt_side_lobe_reach_past_plate_end": STRIKE_LOBE_REACH,
            "lobe_diameter": 2 * STRIKE_LOBE_R,
            "shoulder_radius": STRIKE_SHOULDER_R,
            "concave_corner_tool_radius": STRIKE_TOOL_R,
        },
        "silicone_gasket_cap_spec_mm": {
            "count_installed": 12,
            "arrangement": "2 end-caps per 41.00 mm PC tab (26.2 mm bare tab between caps)",
            "cap_length_x_width_x_height": [_CAP["length"], _CAP["width"], _CAP["height"]],
            "cap_slot_depth_x_width_x_thickness": [_CAP["slot_depth"], _CAP["slot_width"], _CAP["slot_thickness"]],
            "top_flange_pc_tab_bottom_flange_free": [round((_CAP["height"] - _CAP["slot_thickness"]) / 2, 2),
                                                    spec.value("plate.thickness"),
                                                    round((_CAP["height"] - _CAP["slot_thickness"]) / 2, 2)],
            "flange_compressed": CAP_TOP_COMPRESSED,
            "outer_span_across_pair": 43.0,
            "cap_pocket_clearance_per_side": CAP_CLEAR,
            "cap_pocket_corner_radius": CAP_POCKET_R,
        },
        "calibrated_z_stack_mm": {
            "Z_top_surface": 0.0,
            "Z_strike_pocket_floor": Z_STRIKE,
            "Z_gasket_trough_floor": Z_GASKET,
            "cap_pocket_polys_plate_frame": [[[round(x, 4), round(y, 4)] for x, y in p.exterior.coords[:-1]]
                                             for p in cap_pocket_polys_p()],
            "plate_relief_box_plate_frame": [RELIEF_X_P[0], RELIEF_Y_P[0], RELIEF_X_P[1], RELIEF_Y_P[1]],
            "orange_cut_poly_plate_frame": [[round(x, 4), round(y, 4)] for x, y in orange_cut_poly_p().exterior.coords[:-1]],
            "Z_plate_relief_floor": Z_RELIEF,
            "Z_seated_gasket_plate_top": Z_PLATE,
            "Z_base_pocket_floor": Z_FLOOR,
            "Z_outer_skirt_lip": SKIRT_H,
        },
        "geometry_mm": {
            "plate_to_world_offset": [DX_PW, DY_PW],
            "plate_to_world_x_sign": PW_SX,
            "outer_plate_frame": list(OUTER_P),
            "inner_skirt_world": [round(-(INNER_P[2] - INNER_P[0]) / 2, 3), round(INNER_P[1] + DY_PW, 3),
                                  round((INNER_P[2] - INNER_P[0]) / 2, 3), round(INNER_P[3] + DY_PW, 3)],
            "back_seam_strike": BACK_SEAM_STRIKE,
            "usb_notch": {"board": args.board, "x_world": usb_x, "width": usb_w, "closed_end_zp": USB_TOP_ZP,
                          "depth_from_lip": USB_DEPTH, "closed_end_corner_r": USB_END_R},
            "inner_skirt_corner_r": INNER_SKIRT_R,
            "outer_corner_r": CORNER_R,
            "floor_ledge_width": RIM_SEAT_W,
            "strike_centers_plate_frame": [[x, y] for _, x, y in strike_centers_p()],
            "joint_yc_world": JOINT_YC,
            "back_seam": {
                "x_world": BACK_SEAM_X,
                "gap": BACK_SEAM_GAP,
                "split_step_y_world": SPLIT_STEP_Y,
                "key_half_width": BACK_KEY_HW,
                "key_underside_z_at_seam": BACK_KEY_Z0,
                "notch_clearance_y_per_side": BACK_KEY_CLR_Y,
                "notch_clearance_under_wedge_vertical": JOINT_Z_CLEAR,
                **back_seam_key(),
            },
            "strike_pilot_depth": STRIKE_PILOT_DEPTH,
            "dovetails": [{"name": n, "yc": yc, "proj": proj, "z_stop": z_stop, "z_top": z_top}
                          for n, yc, _, _, proj, z_stop, z_top, *_ in JOINTS_SPEC],
            "bumpon_pads": {
                "bumpon": "3M Bumpon Protective Products SJ5012 (same shape: SJ5312 transparent, SJ5412 true white)",
                "bumpon_diameter": BUMPON_D,
                "bumpon_diameter_max": BUMPON_D_MAX,
                "bumpon_height": BUMPON_H,
                "desk_gap": DESK_GAP,
                "pocket_d": POCKET_D,
                "pocket_depth": POCKET_DEPTH,
                "pad_w": PAD_W,
                "pad_d": PAD_D,
                "column_d": PAD_COLUMN_D,
                "tip_land": PAD_TIP_T,
                "centres_world": [list(p) for p in pad_centres()],
                "desk_plane_zp_at_y0": z_desk_in_print_frame(0.0),
                "desk_plane_tilt_deg": TILT_DEG,
            },
        },
        "bodies": [
            {
                "name": b["name"],
                "volume_mm3": round(float(b["volume_mm3"]), 2),
                "mass_petg_g": round(float(b["volume_mm3"]) * 1.27e-3, 1),
                "faces": b["faces"],
                "print_plate_bounds_mm": np.round(
                    (left_plate_tm if b["name"] == "LeftHalf" else right_plate_tm).bounds, 2
                ).tolist(),
            }
            for b in sc_eval["bodies"]
        ],
        "installed_assembly_extents_mm": np.round(
            trimesh.util.concatenate([left_inst_tm, right_inst_tm]).extents, 2
        ).tolist(),
        "verification": {
            "watertight": bool(left_plate_tm.is_watertight and right_plate_tm.is_watertight),
            "compression_rib_intentional_interference_mm3": round(seated_interference, 3),
            "disengaged_overlap_mm3": round(disengaged_overlap, 6),
            "blocked_x_separation_1mm_overlap_mm3": round(blocked_x, 3),
            "blocked_z_overtravel_0p3mm_past_clearance_overlap_mm3": round(blocked_z_stop, 3),
            "dovetail_z_stop_clearance_mm": JOINT_Z_CLEAR,
            "fits_bambu_x2d_256x256": True,
            "supports_required": False,
        },
    }
    (OUT / "draft-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
