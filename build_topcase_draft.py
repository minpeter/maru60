"""Maru60 HHKB top case + integrated honeycomb wrist rest, for the Rule60 V3 (stock bottom case, plate, gaskets, catches).

Built in pure Python (manifold3d mesh CSG, a few seconds) from caliper measurements of the owner's stock top case plus
photo metrology of the silicone gasket caps and ball-catch pockets (IMG_0201..IMG_0222, 28 px/mm rectified):
  - Silicone gasket cap ("gasket bean/sock", 12 installed = 2 per 41 mm tab): the Keebox 8.0 x 5.0 x 5.0 mm U-sock with a
    rounded end and a 6.5 x 2.8 x 1.2 mm slot (`gasket.cap_free`), 1.9 mm flanges either side of the 1.5 mm PC tab.
    Pockets are sized from the stock underside photo (`gasket.pocket_footprint`, 43.00 mm outer span per tab).
  - CNC order as on the stock part (caliper; top face down = `Z_p 0`, `Z_p` grows toward the skirt lip):
      1. Block with the 6-deg top face + 0.70 mm 45-deg outer chamfer, skirt lip at `Z_p = 20.01 mm` (IMG_0333)
      2. Base pocket from the lip down to the `Z_p = 9.69 mm` floor (IMG_0334) inside the skirt (`2.85 mm` sides and back,
         `2.80 mm` front; `R4.85` outer / `R2.0` inner corners); the stock bottom case nests in this 10.32 mm pocket.
         Outline from the caliper-measured top-face bezels: 5.65 sides, 10.90 back, 11.02 front -> 298.10 x 117.37 mm,
         then 0.20 mm out on every side (`POCKET_GROW`, maru60/frames.py) for play: 298.50 x 117.77 mm
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
      6. USB-C notch (14.75 wide for cable plugs, stock 12.8 selectable in spec/, 8.7 deep from the lip, R1.5 closed-end
         corners and convex R0.5 rounds at the open lip ends). Gasket mount only: no top-mount screws.
  - Staggered split into two X2D halves: X = 0 through the wrist rest and front bezel (3 dovetails); the back bezel runs
    on in the LeftHalf to the back-left (BL) strike centre, where the stock strike plate (one M2 per half) and a wedge key
    join the back seam. Each male part keeps its 45-deg print ramp and the female side fills under it, so every joint
    closes over all faces with a 0.20 mm glue line and nothing needs support.

Interface values (stock top case, INKC plate, gasket caps, ball catches, bumpons) come from `spec/` via rule60_spec.py;
`--board` picks the PCB whose USB-C position sets the notch (spec/boards.json, or `universal` for all known boards).

Usage:
    uv run build_topcase_draft.py [--board BOARD] [--strike-inserts | --no-strike-inserts]
"""
from __future__ import annotations

import argparse
import json
import math
from typing import Any

import manifold3d as md
import numpy as np
from shapely.ops import unary_union
import shapely.affinity as sa
import shapely.geometry as sg
from shapely.geometry.polygon import orient
import trimesh

import rule60_spec as spec
from maru60.mesh_io import FINE_LAYER_Z as FINE_LAYER_Z, FINE_LAYER_H as FINE_LAYER_H, to_trimesh, write_3mf
from maru60.paths import topcase_dir
from maru60.frames import (OPENING_P, BEZEL_SIDE as BEZEL_SIDE, BEZEL_BACK as BEZEL_BACK, BEZEL_FRONT as BEZEL_FRONT, SKIRT_WALL, FRONT_WALL,
                           RIM_SEAT_W, OUTER_P, INNER_P, LEDGE_P, CASE_W, CASE_D, WRIST_D, DX_PW, DY_PW, PW_SX, pw,
                           STOCK_INNER_P, POCKET_GROW)

OUT = topcase_dir()

# ---------------------------------------------------------------------------
# Plate frame = DWG `6095(gas)` plate / HHKB keycap layout seen from the top (X right, Y back); the keycap opening is
# fixed in it. The outer case follows the caliper-measured top-face bezels (owner, +-1 mm). The print frame is the
# part upside down on the bed (top face at Z_p 0) seen from above, i.e. the underside: centred on X = 0, front at
# Y = WRIST_D, and X mirrored: X_world = -(X_plate + DX_PW), Y_world = Y_plate + DY_PW. v6.2 and earlier skipped the
# mirror and printed the mirror image (USB on the wrong side, back gasket pockets 10 mm off the tabs).
# ---------------------------------------------------------------------------


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
    # (name, yc, nh, hh, proj, z_stop, z_sock_top, rib_top, neck_taper)
    # 6 mm joints: the 45-deg print ramp leaves tongue material at the rib apex only above `z_stop + 2.2`,
    # so their ribs reach `z_stop + 4.8` for ~2.3 mm of contact while staying clear for `dz >= 3.2`.
    # Every tongue runs down to the case's underside plane (`underside_keep`), flush with the centre rib and socket boss.
    ("WristFrontJoint",      JOINT_YC["WristFrontJoint"], 5.20, 6.60, 6.0, 4.0, 22.0, 4.8, 0.55),
    ("WristMidJoint",        JOINT_YC["WristMidJoint"], 5.20, 6.60, 6.0, 4.0, 22.0, 4.8, 0.55),
    ("FrontBezelWallJoint",  JOINT_YC["FrontBezelWallJoint"], 5.00, 6.40, 6.0, 4.0, 22.0, 4.8, 0.55),
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
# Original-contour upper-only CANOT trial: coupon dimensions, not a manufacturer hole recommendation.
CANOT_INSERT = {"hole_d": 3.2, "outer_d": 3.5, "length": 3.0, "bl2_recess": 0.35}
# Experimental TC-M2x3.0 layout, exercised separately by tools/study_catch_inserts.py, not the published print files.
# CNC Kitchen: D1 3.6, D2 3.2, L 3.0, blind hole >= L+1, W >= 1.3 measured from D2 (boss diameter >= 5.8).
CATCH_INSERT = {"hole_d": 3.2, "depth": 4.0, "outer_d": 3.6, "length": 3.0,
                "wall": 1.3, "boss_d": 6.2, "case_clearance": 0.2}
# Purchased CANOT insert / LUBAN 32 mm catch trial. Pilot and bottom relief are coupon candidates,
# NOT a CANOT installation recommendation. The stock and TC studies remain reproducible.
PURCHASED_INSERT = {**CATCH_INSERT, "outer_d": 3.5, "depth": 3.7}
PURCHASED_STRIKE_Z = 4.7
PURCHASED_CATCH_Z = 15.7  # 11 mm assembled height from seller drawing, not the old photo estimate
# Separate C-derived trial: retain the original sculpted strike seat and open only the body-height band.
# 33.06 is the photographed recess span, NOT a screw pitch; 8.6 clears the seller's 8 mm envelope.
# Neither the 11 mm engagement nor the CANOT bore/depth is established by the new photographs.
SCULPTED_CATCH = {"length": 33.06, "width": 8.6, "body_relief_z": 7.4,
                  "strike_z": 5.55, "catch_z": 16.55, "depth": 3.2, "key_z0": 3.35}
# `--catches luban32`: the purchased LUBAN 32 mm catch with CANOT OD3.5/L3 inserts in both cases, on the original
# pocket contours. Only faces hidden inside the assembled housing change (verify_bottomcase.py proves the exterior).
# The hardware widths are assumed (`ball_catch.luban32`): caliper the parts before printing.
LUBAN = spec.value("ball_catch.luban32")
LUBAN_STRIKE_Z = 5.00   # Strike seat 0.55 above Z_STRIKE: the lower seat (+ the 11.0 engaged height) then leaves
                        # 0.8 mm of bottom-case skin under its 3.2 mm bores at the back rail
LUBAN_CATCH_Z = round(LUBAN_STRIKE_Z + LUBAN["assembled_height"], 3)
LUBAN_BORE_DEPTH = 3.20  # CANOT L3 + 0.2 well, both cases (1.80 mm top skin left over the upper bores)
LUBAN_WALL_OFFSET = round(0.17 + LUBAN["catch"]["width"] / 2, 3)  # Hardware centre line from the inner skirt wall:
                        # its outer side 0.02 inside the bottom-case rail face, its inner side clear of the plate edge
LUBAN_POCKET_HALF_W = LUBAN_WALL_OFFSET  # The pocket widens inward only; its skirt side runs on the inner skirt wall
LUBAN_KEY_Z0 = 2.80      # Back-seam key underside: 0.8 shorter, keeping 1.3 mm round the U-BL.2 insert past its notch


def strike_centers_p(*, purchased: bool = False, luban: bool = False) -> list[tuple[str, float, float]]:
    if luban:
        return [(n, x, round(STOCK_INNER_P[3] - LUBAN_WALL_OFFSET if wall == "back" else STOCK_INNER_P[1] + LUBAN_WALL_OFFSET, 3))
                for n, x, wall, _ in STRIKE_SITES]
    return [(n, x, round((STOCK_INNER_P[3] - d + (1.0 if purchased else 0.0)) if wall == "back"
                        else (1.0 if purchased else STOCK_INNER_P[1] + d), 3)) for n, x, wall, d in STRIKE_SITES]


def catch_screw_axes_p(sx: float, sy: float, *, purchased: bool = False, luban: bool = False) -> list[tuple[float, float]]:
    """Lower catch ears align with the skirt-side lobes of the upper strike pocket, not its 13 mm screw pitch."""
    dx = LUBAN["catch"]["screw_pitch"] / 2 if luban else 12.5 if purchased else STRIKE_PLATE_HALF_LEN + STRIKE_LOBE_REACH - STRIKE_LOBE_R
    dy = 0.0 if purchased or luban else (1.0 if sy > 50.0 else -1.0) * (STRIKE_POCKET_HALF_W - STRIKE_LOBE_R)
    return [(round(sx + sign * dx, 3), round(sy + dy, 3)) for sign in (-1.0, 1.0)]


def back_seam_key(*, z0: float = BACK_KEY_Z0, purchased: bool = False, luban: bool = False) -> dict[str, Any]:
    """World X/Y, Z_p of the back-seam wedge key (LeftHalf) and its notch (RightHalf), centred on the seam strike. The
    notch is the wedge lowered by `JOINT_Z_CLEAR`: a uniform glue line under the slope, no void (`notch_xz`: X, Z_p)."""
    _, _, by_p = next(s for s in strike_centers_p(purchased=purchased, luban=luban) if s[0] == BACK_SEAM_STRIKE)
    seat = LUBAN_STRIKE_Z if luban else PURCHASED_STRIKE_Z if purchased else Z_STRIKE
    key_y = round(by_p + DY_PW, 3)
    key_x0 = round(BACK_SEAM_X - BACK_SEAM_GAP / 2, 3)  # LeftHalf seam face
    key_tip_x = round(key_x0 + seat - z0, 3)
    notch_x0 = round(BACK_SEAM_X + BACK_SEAM_GAP / 2 - 0.3, 3)
    notch_top = round(seat + 0.5, 3)  # into the open strike pocket
    return {
        "key_y": key_y,
        "key_x0": key_x0,
        "key_tip_x": key_tip_x,
        "notch_y0": round(key_y - BACK_KEY_HW - BACK_KEY_CLR_Y, 3),
        "notch_y1": round(key_y + BACK_KEY_HW + BACK_KEY_CLR_Y, 3),
        "notch_xz": [[notch_x0, round(z0 - JOINT_Z_CLEAR + notch_x0 - key_x0, 3)],
                     [round(key_x0 + notch_top - z0 + JOINT_Z_CLEAR, 3), notch_top],
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
# Plan outline: straight sides from the wall, then a half-round inner end concentric with the pocket (owner: round, not
# square), so the pocket wall is the same 1.2 mm all round.


def pad_centres() -> list[tuple[float, float]]:
    """Print-frame X, Y of the 4 bumpon pad centres along the front edge."""
    return [(s * c, PAD_D / 2) for c in PAD_X for s in (-1.0, 1.0)]


def usb_notch_print(board_id: str) -> tuple[float, float]:
    """Print X of the USB-C notch centre and its width for a board (spec/boards.json). The stock top-case notch sits at
    plate X 19.35; the default board, the PH60 Rev.3 Multi PCB, has its USB-C at 18.65 in its design files."""
    centre_p, width = spec.usb_notch(board_id)
    return pw(centre_p, 0.0)[0], width


def usb_lip_round_xz(usb_x: float, usb_w: float, z1: float) -> Any:
    """Shared X/Z_p corner cuts at the open lip: remove tips in both cases without closing the passage."""
    rounds = []
    for edge, side in ((usb_x - usb_w / 2, -1.0), (usb_x + usb_w / 2, 1.0)):
        cx, cz = edge + side * USB_LIP_R, SKIRT_H - USB_LIP_R
        rounds.append(sg.box(min(edge, cx), cz, max(edge, cx), z1).difference(
            sg.Point(cx, cz).buffer(USB_LIP_R, quad_segs=12)))
    return unary_union(rounds)


# Width and corner shape from the stock notch measured against the v6.2 print (owner photos IMG_0378/0379, scaled from
# the printed 14.2 mm notch): 12.6 / 12.75 wide, rounded closed-end corners (CNC endmill); 0.1-0.2 mm generous. v7.11
# cuts it 14.75 wide (`top.usb_notch_cable_width`): the stock width left 0.22 mm per side for a 12.35 mm plug. Depth
# from the v7.3 full-print fit: the photo-estimated 5.7 mm hit the USB-C connector until the owner cut the notch ~3 mm
# deeper by hand, so it is 8.7 mm (closed end 1.62 mm above the 9.69 floor).
USB_TOP_ZP = round(SKIRT_H - spec.value("top.usb_notch")["depth_from_lip"], 2)  # Notch closed end (Z_p 11.31)
USB_DEPTH = round(SKIRT_H - USB_TOP_ZP, 2)  # USB-C notch depth from skirt lip
USB_END_R = spec.value("top.usb_notch")["end_r"]  # Closed-end arch radius; unchanged
USB_LIP_R = 0.50  # Small matching free-end rounds on both cases, reduced from the R1.5 preview

JOINT_CLEAR = 0.0       # Base dovetail socket clearance per face: line-to-line, as in the published v9 tight fit
JOINT_Z_CLEAR = 0.20    # Vertical gap between each tongue landing and its socket roof, so both halves rest on the desk
COMP_INTERF = 0.08      # Local interference per flank on chevron compression ribs

TILT_RAD = math.radians(TILT_DEG)


def z_desk_in_print_frame(y: float) -> float:
    """Desk plane Z_p below the top-face point at print Y=y (measured along the top-face normal, Z_p down from the top)."""
    h_inst = JUNC_H - (WRIST_D - y) * math.sin(TILT_RAD)
    return h_inst / math.cos(TILT_RAD)


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


def strike_pocket_poly(sx_p: float, sy_p: float, skirt_sign: float,
                       *, half_width: float = STRIKE_POCKET_HALF_W) -> sg.Polygon:
    """Plan outline of one strike pocket in plate coordinates; `skirt_sign` is +1 when the outer wall is at +Y."""
    x_end = STRIKE_PLATE_HALF_LEN + STRIKE_END_WALL_GAP
    lobe_cx = STRIKE_PLATE_HALF_LEN + STRIKE_LOBE_REACH - STRIKE_LOBE_R
    lobe_cy = skirt_sign * (half_width - STRIKE_LOBE_R)
    shape = sg.box(-x_end, -half_width, x_end, half_width)
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


# ---------------------------------------------------------------------------
# Geometry kernel: manifold3d mesh CSG in the print frame. Sketched outlines are the same shapely polylines throughout;
# true arcs (outer and inner skirt corners, keycap-opening corners, strike-screw pilots) are tessellated to `ARC_TOL`.
# Sketch planes: XY (X, Y) extruded along +Z_p; YZ (Y, Z_p) along +X; XZ (X, Z_p) along +Y.
# ---------------------------------------------------------------------------
ARC_TOL = 0.002  # Max chord error of tessellated arcs (mm)


def arc_steps(r: float, sweep: float) -> int:
    return max(2, math.ceil(sweep / (2.0 * math.acos(1.0 - ARC_TOL / r))))


def round_vertices(pts: list[tuple[float, float]], radii: list[float]) -> sg.Polygon:
    """Polygon with vertex i replaced by the tangent arc of radius `radii[i]` (0: sharp); a convex vertex loses area,
    a reflex vertex gains it (the fillet of a solid's concave or convex vertical edge seen from either side)."""
    p = np.asarray(pts, dtype=float)
    out: list[tuple[float, float]] = []
    for i, r in enumerate(radii):
        b = p[i]
        if r <= 0.0:
            out.append((float(b[0]), float(b[1])))
            continue
        u1 = (p[i - 1] - b) / np.linalg.norm(p[i - 1] - b)
        u2 = (p[(i + 1) % len(p)] - b) / np.linalg.norm(p[(i + 1) % len(p)] - b)
        theta = math.acos(float(np.clip(u1 @ u2, -1.0, 1.0)))
        centre = b + (u1 + u2) / np.linalg.norm(u1 + u2) * r / math.sin(theta / 2.0)
        p1, p2 = b + u1 * r / math.tan(theta / 2.0), b + u2 * r / math.tan(theta / 2.0)
        a1 = math.atan2(p1[1] - centre[1], p1[0] - centre[0])
        sweep = (math.atan2(p2[1] - centre[1], p2[0] - centre[0]) - a1 + math.pi) % (2.0 * math.pi) - math.pi
        k = arc_steps(r, abs(sweep))
        out.extend((float(centre[0] + r * math.cos(a1 + sweep * j / k)), float(centre[1] + r * math.sin(a1 + sweep * j / k)))
                   for j in range(k + 1))
    poly = sg.Polygon(out)
    assert poly.is_valid, "self-intersecting fillet"
    return poly


def circle(cx: float, cy: float, r: float) -> sg.Polygon:
    n = arc_steps(r, 2.0 * math.pi)
    return sg.Polygon([(cx + r * math.cos(2.0 * math.pi * k / n), cy + r * math.sin(2.0 * math.pi * k / n)) for k in range(n)])


def xsec(shape: Any) -> md.CrossSection:
    rings: list[np.ndarray] = []
    for g in getattr(shape, "geoms", [shape]):
        g = orient(g)
        rings.append(np.asarray(g.exterior.coords[:-1], dtype=np.float64))
        rings.extend(np.asarray(h.coords[:-1], dtype=np.float64) for h in g.interiors)
    return md.CrossSection(rings)


def prism_xy(shape: Any, z0: float, z1: float) -> md.Manifold:
    return xsec(shape).extrude(z1 - z0).translate([0.0, 0.0, z0])


def prism_yz(shape_yz: Any, x0: float, x1: float) -> md.Manifold:
    """(Y, Z_p) outline swept along +X from x0 to x1."""
    return xsec(shape_yz).extrude(x1 - x0).transform(np.array([[0.0, 0.0, 1.0, x0], [1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]]))


def prism_xz(shape_xz: Any, y0: float, y1: float) -> md.Manifold:
    """(X, Z_p) outline swept along +Y from y0 to y1 (built in (X, -Z_p), a right-handed sketch frame)."""
    flipped = sa.affine_transform(shape_xz, [1.0, 0.0, 0.0, -1.0, 0.0, 0.0])
    return xsec(flipped).extrude(y1 - y0).transform(np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 1.0, y0], [0.0, -1.0, 0.0, 0.0]]))


def build_halves(board_id: str, *, strike_inserts: bool = False, catch_inserts: bool = False, purchased_catches: bool = False,
                 insert_hole_d: float = 3.2, sculpted_catches: bool = False,
                 luban_catches: bool = False) -> tuple[md.Manifold, md.Manifold]:
    """LeftHalf (X <= 0 plus the back strip) and RightHalf in the print frame, in the CNC order of the docstring."""
    if strike_inserts and (catch_inserts or purchased_catches or sculpted_catches):
        raise ValueError("Original-contour strike inserts cannot be combined with the earlier catch-layout studies")
    if luban_catches and (strike_inserts or catch_inserts or purchased_catches or sculpted_catches):
        raise ValueError("The LUBAN catch layout already carries its CANOT bores; it combines with no other catch option")
    purchased_catches = purchased_catches or sculpted_catches
    catch_inserts = catch_inserts or purchased_catches
    insert = dict(PURCHASED_INSERT if purchased_catches else CATCH_INSERT)
    if sculpted_catches:
        insert["depth"] = SCULPTED_CATCH["depth"]
    strike_z = (LUBAN_STRIKE_Z if luban_catches else SCULPTED_CATCH["strike_z"] if sculpted_catches
                else PURCHASED_STRIKE_Z if purchased_catches else Z_STRIKE)
    usb_x, usb_w = usb_notch_print(board_id)
    total_d = WRIST_D + CASE_D

    # 1. Block (Z_p 0..24) with the `CORNER_R` outer vertical corners.
    outer = round_vertices([(-CASE_W / 2, 0.0), (CASE_W / 2, 0.0), (CASE_W / 2, total_d), (-CASE_W / 2, total_d)], [CORNER_R] * 4)
    body = prism_xy(outer, 0.0, 24.0)

    # 2. Side profile: the 6-deg desk plane under the wrist rest, the 20.01 mm skirt lip under the case.
    profile = sg.Polygon([(-2.0, round(z_desk_in_print_frame(-2.0), 4)), (WRIST_D, round(z_desk_in_print_frame(WRIST_D), 4)),
                          (WRIST_D, SKIRT_H), (total_d + 2.0, SKIRT_H), (total_d + 2.0, 26.0), (-2.0, 26.0)])
    body -= prism_yz(profile, -160.0, 160.0)

    # 3. Base pocket from the lip down to the floor (`z_floor`), `INNER_SKIRT_R` inner corners, inside the skirt walls.
    cx_in, cy0_in, cy1_in = CASE_W / 2 - SKIRT_WALL, WRIST_D + FRONT_WALL, WRIST_D + CASE_D - SKIRT_WALL
    pocket = round_vertices([(-cx_in, cy0_in), (cx_in, cy0_in), (cx_in, cy1_in), (-cx_in, cy1_in)], [INNER_SKIRT_R] * 4)
    body -= prism_xy(pocket, Z_FLOOR, Z_FLOOR + 20.0)

    # 4. HHKB keycap opening (`Z_p -1 .. 14`): R1.2 corners, R0.5 at the two bottom-row outer corners next to the
    #    blockers (0.50/0.34 mm keycap clearance there).
    opening = [pw(OPENING_P[0], 25.20), pw(28.55, 25.20), pw(28.55, OPENING_P[1]), pw(257.35, OPENING_P[1]),
               pw(257.35, 25.20), pw(OPENING_P[2], 25.20), pw(OPENING_P[2], OPENING_P[3]), pw(OPENING_P[0], OPENING_P[3])]
    body -= prism_xy(round_vertices(opening, [1.2, 1.2, 0.5, 0.5, 1.2, 1.2, 1.2, 1.2]), -1.0, 14.0)

    # 5. Plate-body relief + 6 open silicone-cap pockets, one cut to `z_gasket` (`orange_cut_poly_p`); the seated gasket
    #    plate occupies `Z_p = 7.50..9.00`.
    orange_w = sg.Polygon([pw(x, y) for x, y in orange_cut_poly_p().exterior.coords[:-1]])
    body -= prism_xy(orange_w, Z_GASKET, Z_FLOOR + 1.0)

    # 6. Four strike pockets (`strike_pocket_poly`, lobes on the skirt half), floor at `z_strike`, and the blind M2
    #    pilots (Ø1.8 mm, `STRIKE_PILOT_DEPTH` past the pocket floor).
    strikes = strike_centers_p(purchased=purchased_catches, luban=luban_catches)
    pockets = unary_union([sg.Polygon([pw(x, y) for x, y in
                           (strike_pocket_poly(sx, sy, 1.0 if sy > 50.0 else -1.0, half_width=LUBAN_POCKET_HALF_W) if luban_catches else
                            strike_pocket_poly(sx, sy, 1.0 if sy > 50.0 else -1.0, half_width=4.3) if sculpted_catches else
                            sg.box(sx-16.1, sy-4.3, sx+16.1, sy+4.3) if purchased_catches else
                            strike_pocket_poly(sx, sy, 1.0 if sy > 50.0 else -1.0)).exterior.coords[:-1]])
                           for _, sx, sy in strikes])
    body -= prism_xy(pockets, strike_z, Z_STRIKE + 5.0 if sculpted_catches or not purchased_catches else 24.1)
    if sculpted_catches:
        hl, hw = SCULPTED_CATCH["length"] / 2, SCULPTED_CATCH["width"] / 2
        body_clearance = unary_union([sg.box(*pw(sx+hl, sy-hw), *pw(sx-hl, sy+hw)) for _, sx, sy in strikes])
        # Continue to the open lip: stopping at the seated catch floor traps its mounting feet on disassembly.
        # The original sculpted shallow seat below this band remains, unlike the full-depth boxed prototype.
        body -= prism_xy(body_clearance, SCULPTED_CATCH["body_relief_z"], SKIRT_H + 0.1)
    pilot_r = (insert_hole_d / 2 if purchased_catches else insert["hole_d"] / 2) if catch_inserts else 0.90
    pilot_depth = insert["depth"] if catch_inserts else STRIKE_PILOT_DEPTH
    pitch_half = 5.5 if purchased_catches else 6.5
    pilots = unary_union([circle(pw(sx, sy)[0] + dx, pw(sx, sy)[1], pilot_r)
                          for _, sx, sy in strikes for dx in (-pitch_half, pitch_half)])
    if not luban_catches:  # its insert bores are cut after the seam key, below
        body -= prism_xy(pilots, strike_z - pilot_depth, strike_z + 2.0)
    if catch_inserts:
        # Keep the original latch axes and plate travel. Hide the lower bosses in local internal skirt scallops,
        # instead of moving the hardware toward the PCB or changing the outside silhouette.
        catch_floor = SCULPTED_CATCH["catch_z"] if sculpted_catches else PURCHASED_CATCH_Z if purchased_catches else 7.60 + spec.value("ball_catch.catch_body")["height"]
        reliefs = unary_union([circle(pw(x, y)[0], pw(x, y)[1], insert["boss_d"] / 2 + insert["case_clearance"])
                              for _, sx, sy in strikes for x, y in catch_screw_axes_p(sx, sy, purchased=purchased_catches)])
        body -= prism_xy(reliefs, catch_floor - 0.1, SKIRT_H + 0.1)

    # 7. USB-C notch through the back skirt wall: open at the lip, `USB_END_R` corners at its closed end (`USB_TOP_ZP`).
    usb_xz = sg.box(usb_x - usb_w / 2, USB_TOP_ZP, usb_x + usb_w / 2, SKIRT_H + 1.0)
    usb_xz = usb_xz.buffer(-USB_END_R).buffer(USB_END_R, quad_segs=12).union(
        sg.box(usb_x - usb_w / 2, USB_TOP_ZP + USB_END_R, usb_x + usb_w / 2, SKIRT_H + 1.0)).simplify(1e-4)
    # Round away the two pointed lip tips, flaring outward rather than adding a bottom bar across the notch.
    usb_xz = usb_xz.union(usb_lip_round_xz(usb_x, usb_w, SKIRT_H + 1.0))
    back_inner_y = WRIST_D + CASE_D - SKIRT_WALL
    body -= prism_xz(usb_xz, back_inner_y - 1.0, back_inner_y + SKIRT_WALL + 1.0)

    # 8. Wrist rest: the two interior hollows under the skin (contoured around the 4 front bumpon pads), the
    #    right-side socket boss strip (X 3.5..9.8, standing 0.2 mm into the skin: a flat overhang otherwise, and down to
    #    the desk plane, flush with the centre rib and the dovetail tongues), the
    #    45-deg pad undercuts and the bumpon pockets.
    assert (PAD_D - BUMPON_D_MAX) / 2 >= 1.0 and PAD_W >= BUMPON_D_MAX + 2.0, "bumpon pad too small"
    w_in_x = round(CASE_W / 2 - WRIST_WALL, 3)
    left_pads = [sg.box(-(c + PAD_W / 2), -10.0, -(c - PAD_W / 2), PAD_D / 2).union(
        sg.Point(-c, PAD_D / 2).buffer(PAD_W / 2, quad_segs=32)) for c in PAD_X]
    left_hollow = sg.Polygon([(-w_in_x + 5.5, 2.2), (-4.0, 2.2), (-4.0, 77.8), (-w_in_x, 77.8), (-w_in_x, 7.7)]).difference(
        unary_union(left_pads))
    assert left_hollow.geom_type == "Polygon", left_hollow.geom_type
    right_hollow = sa.scale(left_hollow, xfact=-1.0, origin=(0.0, 0.0))
    body -= prism_xy(sg.MultiPolygon([left_hollow, right_hollow]), SKIN_T, SKIN_T + 24.0)
    boss = sg.Polygon([(14.0, SKIN_T - 0.2), (79.0, SKIN_T - 0.2), (79.0, z_desk_in_print_frame(79.0)),
                       (14.0, z_desk_in_print_frame(14.0))])
    body += prism_yz(boss, 3.5, 9.8)

    # Pad undercuts: each pad's underside rises at 45 deg to a `PAD_TIP_T` vertical land at its inner edge, so it prints
    # without support; the pad stays full height where that slope meets the skin, at least `PAD_COLUMN_D` from the wall.
    # Only cuts: the pad face stays the desk plane and the pad sides the hollow notch, and the cut reaches 1 mm into the
    # empty bay past the pad's sides and inner edge (no coincident faces).
    z_tip = z_desk_in_print_frame(PAD_D) - PAD_TIP_T  # underside at the pad's inner edge
    y_out = PAD_D + 1.0
    below_slope = sg.Polygon([(y_out, z_tip + 1.0), (PAD_D - 100.0, z_tip - 100.0), (y_out, z_tip - 100.0)])
    undercut = sg.box(PAD_COLUMN_D, SKIN_T, y_out, z_tip + 1.0).intersection(below_slope)
    assert undercut.geom_type == "Polygon" and undercut.area > 1.0, undercut
    for x0 in sorted(s * c - PAD_W / 2 for c in PAD_X for s in (-1.0, 1.0)):
        body -= prism_yz(undercut, x0 - 1.0, x0 + PAD_W + 1.0)

    # Bumpon pockets: on the desk plane (x along X, v up the 6-deg slope, normal out of the pad faces), a 72-gon
    # circumscribing `POCKET_D` centred on each pad, `POCKET_DEPTH` into the pad and 1 mm out past its face. Flat facets
    # keep the two halves exact mirrors.
    cos_t, sin_t = math.cos(TILT_RAD), math.sin(TILT_RAD)
    r_poly = POCKET_D / 2 / math.cos(math.pi / 72)
    rings = [sg.Polygon([(x + r_poly * math.cos(2 * math.pi * k / 72), y / cos_t + r_poly * math.sin(2 * math.pi * k / 72))
                         for k in range(72)]) for x, y in pad_centres()]
    to_desk_plane = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, cos_t, -sin_t, 0.0], [0.0, sin_t, cos_t, z_desk_in_print_frame(0.0)]])
    body -= xsec(sg.MultiPolygon(rings)).extrude(POCKET_DEPTH + 1.0).translate([0.0, 0.0, -POCKET_DEPTH]).transform(to_desk_plane)

    # 9. Honeycomb through the wrist-rest skin (`Z_p -0.5 .. skin_t + 0.5`): hexagons with a vertex at 90 deg, each
    #    circumcircle 1 mm inside a bay.
    hex_r = round(4.5 - RIB / math.sqrt(3), 4)
    left_bay = sg.Polygon([(-w_in_x + 5.5, 2.2), (-4.0, 2.2), (-4.0, 77.8), (-w_in_x, 77.8), (-w_in_x, 7.7)]).buffer(-1.0)
    right_bay = sg.Polygon([(4.0, 2.2), (w_in_x - 5.5, 2.2), (w_in_x, 7.7), (w_in_x, 77.8), (4.0, 77.8)]).buffer(-1.0)
    cells = []
    for col in range(-22, 23):
        hx = round(col * 6.75, 4)
        for row in range(-6, 7):
            hy = round(40.0 + (row + (col % 2) * 0.5) * 4.5 * math.sqrt(3), 4)
            if left_bay.contains(sg.Point(hx, hy).buffer(hex_r)) or right_bay.contains(sg.Point(hx, hy).buffer(hex_r)):
                cells.append(sg.Polygon([(hx + hex_r * math.cos(math.pi / 6 + math.pi * k / 3),
                                          hy + hex_r * math.sin(math.pi / 6 + math.pi * k / 3)) for k in range(6)]))
    body -= prism_xy(sg.MultiPolygon(cells), -0.5, SKIN_T + 0.5)

    # 10. Split at X = 0: LeftHalf X <= 0, RightHalf X >= 0 (the back strip moves over in 12).
    left, right = body.trim_by_plane([-1.0, 0.0, 0.0], 0.0), body.trim_by_plane([1.0, 0.0, 0.0], 0.0)

    # 11. Three dovetails across X = 0 (with planar chevron compression ribs):
    #     - Plain tongue meets the plain socket line-to-line (0 mm) in plan; each tongue starts `JOINT_Z_CLEAR` below the
    #       socket roof (`z_tongue = z_stop + 0.20`), the only vertical contact between the halves.
    #     - Chevron ribs stand in the socket band `[z_tongue + 0.3, z_tongue + rib_top]` (fixed in the RightHalf),
    #       so the tongue bites only once its ramped underside reaches that band (final 2.2 mm of travel).
    #     - Socket fill: the RightHalf keeps the space under the tongue's 45-deg print ramp up to the ramp lowered by
    #       `JOINT_Z_CLEAR`, so the ramp is a glue face with the same 0.20 mm (vertical) line as the tongue landing, not a
    #       3 mm void. Printed on the socket floor, its top is the 45-deg slope: no support. It is left uncut (socket
    #       minus the fill wedge) rather than cut and joined back, which would leave the fill's flanks coplanar with the
    #       socket walls.
    #     - Each tongue reaches the case underside (desk plane, capped at the skirt lip) less 0.02 mm, flush with the
    #       centre rib and the socket boss to well under a layer: exactly coplanar, the union with the centre rib
    #       leaves zero-volume slivers.
    y_lip = (SKIRT_H - z_desk_in_print_frame(0.0)) / (z_desk_in_print_frame(1.0) - z_desk_in_print_frame(0.0))
    underside_keep = prism_yz(sg.Polygon([(-5.0, -5.0), (95.0, -5.0), (95.0, SKIRT_H), (y_lip, SKIRT_H),
                                          (-5.0, z_desk_in_print_frame(-5.0))]), -5.0, 15.0).translate([0.0, 0.0, -0.02])
    for jname, yc, nh, hh, proj, z_stop, z_sock_top, rib_top, taper in JOINTS_SPEC:
        z_tongue = round(z_stop + JOINT_Z_CLEAR, 3)
        assert nh - taper > 0.0, f"{jname}: neck half-width at X=1.4 must stay positive"
        assert z_sock_top > SKIRT_H, f"{jname}: socket must open through the underside"
        sock_poly = dovetail_poly(yc, nh, hh, proj, clear=JOINT_CLEAR, neck_taper=taper)
        male_poly = dovetail_poly(yc, nh, hh, proj, neck_taper=taper)
        rib_polys = socket_rib_polys(yc, nh, hh, proj, taper)
        assert sock_poly.is_valid and male_poly.is_valid and all(p.is_valid for p in rib_polys), jname
        z_base, x_end = round(z_stop - 0.3, 3), round(proj + 0.5, 3)
        x_start = 0.8 + (z_base + JOINT_Z_CLEAR - tongue_ramp_z(0.8, z_tongue, proj)) / ((proj + 0.3) / (proj - 0.2))
        z_end = tongue_ramp_z(x_end, z_tongue, proj) - JOINT_Z_CLEAR
        fill = prism_xz(sg.Polygon([(x_start, z_base), (x_end, z_base), (x_end, z_end)]), yc - hh - 1.0, yc + hh + 1.0)
        socket = prism_xy(sock_poly, z_stop, z_sock_top)
        assert ((socket ^ fill) - right).volume() < 1e-6, f"{jname}: fill outside the RightHalf"
        right -= socket - fill
        right += prism_xy(sg.MultiPolygon(rib_polys), z_tongue + 0.3, z_tongue + rib_top)
        left += prism_xy(male_poly, z_tongue, z_sock_top) ^ underside_keep
        ramp = sg.Polygon([(0.8, tongue_ramp_z(0.8, z_tongue, proj)), (proj + 0.6, tongue_ramp_z(0.8, z_tongue, proj)),
                           (proj + 0.6, tongue_ramp_z(proj + 0.6, z_tongue, proj))])
        left -= prism_xz(ramp, yc - hh - 1.2, yc + hh + 1.2)  # 45-deg self-supporting print ramp under the tongue

    # 12. Stagger: the back strip of the RightHalf from X = 0 to `BACK_SEAM_X - gap/2` (above `SPLIT_STEP_Y`, so only
    #     back bezel and skirt) joins the LeftHalf; the RightHalf loses it up to `BACK_SEAM_X + gap/2` (gap 0: one plane).
    half_gap = BACK_SEAM_GAP / 2
    strip = right ^ prism_xy(sg.box(0.0, SPLIT_STEP_Y, BACK_SEAM_X - half_gap, 205.0), -5.0, 35.0)
    right -= prism_xy(sg.box(-1.0, SPLIT_STEP_Y, BACK_SEAM_X + half_gap, 205.0), -5.0, 35.0)
    left += strip

    # 13. Back seam: Y alignment from a 45-deg wedge key on the LeftHalf under the seam strike pocket floor, sliding down
    #     with the dovetails into a matching notch in the RightHalf (the wedge lowered by `JOINT_Z_CLEAR`) that opens
    #     into the strike pocket. X and Z across the seam come from the stock strike plate screwed into both halves.
    #     The key root sinks 0.3 mm into the LeftHalf.
    # The larger insert bore needs 0.15 mm more wall beside the wedge notch at the strike seat. Shorten both
    # matching wedge profiles by 0.20 mm, keeping the seat, alignment axis and uniform 0.20 mm glue line unchanged.
    # The 11 mm strike pitch brings U-BL.2 toward this notch. Shorten the matched wedge/notch locally,
    # retaining its original Y axis and 45-degree bearing instead of leaving a 0.2 mm insert web.
    key_z0 = (LUBAN_KEY_Z0 if luban_catches else SCULPTED_CATCH["key_z0"] if sculpted_catches
              else 2.6 if purchased_catches else BACK_KEY_Z0 + (0.20 if catch_inserts else 0.0))
    bk = back_seam_key(z0=key_z0, purchased=purchased_catches and not sculpted_catches, luban=luban_catches)
    root_x, root_z = bk["key_x0"] - 0.3, key_z0 - 0.3
    left += prism_xz(sg.Polygon([(root_x, root_z), (root_x, strike_z), (bk["key_tip_x"], strike_z)]),
                     bk["key_y"] - BACK_KEY_HW, bk["key_y"] + BACK_KEY_HW)
    right -= prism_xz(sg.Polygon(bk["notch_xz"]), bk["notch_y0"], bk["notch_y1"])

    # 14. 45-deg `0.70 mm` chamfer round the outer top perimeter (the top face meets the outer walls; the split faces
    #     and every opening keep sharp edges): keep what lies inside the top outline inset by `0.70 - Z_p`.
    chamfer_keep = md.Manifold.hull(
        prism_xy(outer.buffer(-0.701, quad_segs=arc_steps(CORNER_R, math.pi / 2)), -0.001, 0.0)
        + prism_xy(outer, 0.70, 0.701)) + prism_xy(outer.buffer(5.0), 0.70, 40.0)
    left, right = left ^ chamfer_keep, right ^ chamfer_keep
    if strike_inserts:
        # Cut after the seam key is built: change only the eight bores, never the key or pocket outline.
        bores = md.Manifold()
        for _, sx, sy in strike_centers_p():
            x, y = pw(sx, sy)
            for dx in (-6.5, 6.5):
                bores += md.Manifold.cylinder(STRIKE_PILOT_DEPTH + 0.02, CANOT_INSERT["hole_d"] / 2,
                                              circular_segments=96).translate([x + dx, y, Z_STRIKE - STRIKE_PILOT_DEPTH])
        left, right = left - bores, right - bores
    if luban_catches:
        bores = md.Manifold()
        for _, sx, sy in strikes:
            x, y = pw(sx, sy)
            for dx in (-LUBAN["strike"]["screw_pitch"] / 2, LUBAN["strike"]["screw_pitch"] / 2):
                bores += md.Manifold.cylinder(LUBAN_BORE_DEPTH + 0.02, CANOT_INSERT["hole_d"] / 2,
                                              circular_segments=96).translate([x + dx, y, strike_z - LUBAN_BORE_DEPTH])
        left, right = left - bores, right - bores
    return left, right


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", choices=spec.board_ids(), default=spec.default_board(),
                    help="PCB whose USB-C position sets the notch (spec/boards.json); default: %(default)s")
    ap.add_argument("--strike-inserts", action=argparse.BooleanOptionalAction, default=False,
                    help="Upper-only CANOT OD3.5/L3 trial bores, preserving original pockets/axes; default: no inserts")
    ap.add_argument("--catches", choices=["stock", "luban32"], default="stock",
                    help="Ball-catch hardware: stock, or the purchased LUBAN 32 mm catch with CANOT inserts "
                         "(assumed widths, spec ball_catch.luban32); default: %(default)s")
    args = ap.parse_args()
    luban = args.catches == "luban32"
    if luban and args.strike_inserts:
        ap.error("--catches luban32 already cuts CANOT insert bores; drop --strike-inserts")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "verification.json").unlink(missing_ok=True)

    usb_x, usb_w = usb_notch_print(args.board)
    left_mf, right_mf = build_halves(args.board, strike_inserts=args.strike_inserts, luban_catches=luban)
    strike_z = LUBAN_STRIKE_Z if luban else Z_STRIKE
    key_z0 = LUBAN_KEY_Z0 if luban else BACK_KEY_Z0
    strike_hw = LUBAN["strike"] if luban else spec.value("ball_catch.strike_plate")
    for name, mf in (("LeftHalf", left_mf), ("RightHalf", right_mf)):
        assert mf.status() == md.Error.NoError and len(mf.decompose()) == 1, (name, mf.status(), len(mf.decompose()))

    # Both halves in the print frame, as built: the mating gauge for verify_topcase.py and verify_bottomcase.py.
    write_3mf(OUT / "halves-world.3mf", "Maru60 HHKB top case halves, print frame (as built)",
              [("LeftHalf", to_trimesh(left_mf, single_shell=True)), ("RightHalf", to_trimesh(right_mf, single_shell=True))], fine_layer_z=None)

    seated_interference = float((left_mf ^ right_mf).volume())
    disengaged_overlap = float((left_mf.translate([0.0, 0.0, 17.5]) ^ right_mf).volume())
    blocked_x = float((left_mf.translate([-1.0, 0.0, 0.0]) ^ right_mf).volume())
    blocked_z_stop = float((left_mf.translate([0.0, 0.0, -(JOINT_Z_CLEAR + 0.3)]) ^ right_mf).volume())
    assert 0.05 < seated_interference < 30.0, f"Unexpected compression-rib interference: {seated_interference}"
    assert disengaged_overlap < 0.001, f"Disengaged overlap at dz=17.5: {disengaged_overlap}"
    assert blocked_x > 5.0 and blocked_z_stop > 1.0, (blocked_x, blocked_z_stop)

    def place_on_x2d(mf: md.Manifold) -> trimesh.Trimesh:
        tm = to_trimesh(mf, single_shell=True)
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
    left_inst_tm = to_trimesh(left_mf.rotate([rot_deg, 0.0, 0.0]), single_shell=True)
    right_inst_tm = to_trimesh(right_mf.rotate([rot_deg, 0.0, 0.0]), single_shell=True)
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
        tm = to_trimesh(mf, single_shell=True)
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
        "version": "v7.12-ph60-rev3-default",
        "generator": "manifold3d mesh CSG (build_topcase_draft.py) + 28px/mm gasket metrology",
        "strike_inserts": args.strike_inserts,
        "catch_hardware": args.catches,
        "luban32": {
            "hardware_assumed": LUBAN,
            "strike_seat_zp": LUBAN_STRIKE_Z,
            "catch_seat_zp": LUBAN_CATCH_Z,
            "bore_depth": LUBAN_BORE_DEPTH,
            "centre_from_inner_skirt_wall": LUBAN_WALL_OFFSET,
            "pocket_half_width": LUBAN_POCKET_HALF_W,
            "back_key_underside_zp": LUBAN_KEY_Z0,
            "status": "widths assumed (spec ball_catch.luban32); caliper the purchased parts before printing",
        } if luban else None,
        "strike_insert_trial": {
            **CANOT_INSERT,
            "bl2_recess": 0.0,
            "depth": LUBAN_BORE_DEPTH,
            "installation_recess_by_hole_mm": {f"U-{name}.{i}": 0.0 for name, *_ in strike_centers_p() for i in (1, 2)},
            "tool_tip_max_d": 3.0,
            "tool_tip_min_reach": 0.40,
            "coupon_required": True,
            "purchased_32mm_catch_compatible": True,
        } if luban else {
            **CANOT_INSERT,
            "depth": STRIKE_PILOT_DEPTH,
            "installation_recess_by_hole_mm": {
                f"U-{name}.{i}": CANOT_INSERT["bl2_recess"] if name == "BL" and i == 2 else 0.0
                for name, *_ in strike_centers_p() for i in (1, 2)
            },
            "tool_tip_max_d": 3.0,
            "tool_tip_min_reach": 0.40,
            "coupon_required": True,
            "purchased_32mm_catch_compatible": False,
        } if args.strike_inserts else None,
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
            "Z_strike_pocket_floor": strike_z,
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
            "pocket_grow": POCKET_GROW,
            "inner_skirt_world": [round(-(INNER_P[2] - INNER_P[0]) / 2, 3), round(INNER_P[1] + DY_PW, 3),
                                  round((INNER_P[2] - INNER_P[0]) / 2, 3), round(INNER_P[3] + DY_PW, 3)],
            "back_seam_strike": BACK_SEAM_STRIKE,
            "usb_notch": {"board": args.board, "x_world": usb_x, "width": usb_w, "closed_end_zp": USB_TOP_ZP,
                          "depth_from_lip": USB_DEPTH, "closed_end_corner_r": USB_END_R, "open_lip_corner_r": USB_LIP_R},
            "inner_skirt_corner_r": INNER_SKIRT_R,
            "outer_corner_r": CORNER_R,
            "floor_ledge_width": RIM_SEAT_W,
            "strike_centers_plate_frame": [[x, y] for _, x, y in strike_centers_p(luban=luban)],
            "strike_pocket_half_w": LUBAN_POCKET_HALF_W if luban else STRIKE_POCKET_HALF_W,
            "strike_plate_mm": {k: strike_hw[k] for k in ("length", "width", "thickness")},
            "joint_yc_world": JOINT_YC,
            "back_seam": {
                "x_world": BACK_SEAM_X,
                "gap": BACK_SEAM_GAP,
                "split_step_y_world": SPLIT_STEP_Y,
                "key_half_width": BACK_KEY_HW,
                "key_underside_z_at_seam": key_z0,
                "notch_clearance_y_per_side": BACK_KEY_CLR_Y,
                "notch_clearance_under_wedge_vertical": JOINT_Z_CLEAR,
                **back_seam_key(z0=key_z0, luban=luban),
            },
            "strike_pilot_diameter": CANOT_INSERT["hole_d"] if args.strike_inserts or luban else 1.8,
            "strike_pilot_depth": LUBAN_BORE_DEPTH if luban else STRIKE_PILOT_DEPTH,
            "strike_pilot_half_pitch": strike_hw["screw_pitch"] / 2,
            "dovetails": [{"name": n, "yc": yc, "proj": proj, "z_stop": z_stop,
                           "z_top": round(min(z_desk_in_print_frame(yc - hh), SKIRT_H) - 0.02, 3)}  # tongue end, flush
                          for n, yc, _, hh, proj, z_stop, *_ in JOINTS_SPEC],
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
                "inner_end_r": PAD_W / 2,
                "tip_land": PAD_TIP_T,
                "centres_world": [list(p) for p in pad_centres()],
                "desk_plane_zp_at_y0": z_desk_in_print_frame(0.0),
                "desk_plane_tilt_deg": TILT_DEG,
            },
        },
        "bodies": [
            {
                "name": name,
                "volume_mm3": round(mf.volume(), 2),
                "mass_petg_g": round(mf.volume() * 1.27e-3, 1),
                "triangles": mf.num_tri(),
                "print_plate_bounds_mm": np.round(tm.bounds, 2).tolist(),
            }
            for name, mf, tm in (("LeftHalf", left_mf, left_plate_tm), ("RightHalf", right_mf, right_plate_tm))
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
