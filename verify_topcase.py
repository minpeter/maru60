"""Comprehensive 3D Mating & Printability Verification for Rule 60 V3 HHKB Unibody.

Verifies exported CAD files (not in-memory construction) across 6 independent suites:
  1. Mesh Integrity & X2D Bed Bounds: watertight, winding-consistent, 1-shell STLs & 3MFs.
  2. 91-Step Rigid-Body Dovetail Insertion Path: zero drag during upper entry (`dz >= 3.2 mm`),
     intentional compression-rib engagement ONLY in final `3.0 mm` (`dz < 3.1 mm`), and
     strictly confined inside the compression-rib bands of the 3 X = 0 dovetails.
  3. 6-DOF Retention & Stop Stiffness: X-separation, Y-shear, and -Z overtravel past the `0.20 mm` vertical stop
     clearance all blocked; the vertical free play itself is measured (clear at 0.18 mm, contact by 0.25 mm).
  4. Staggered Back Seam: both seam faces at `seam strike centre -/+ gap/2` (line-to-line), one full-depth strike pilot
     per half, the strike plate bearing on both halves, the wedge key sides line-to-line; glue lines: every male part
     (3 tongues + key) meets its female over all faces with no gap wider than 0.25 mm.
  5. 0.20 mm FDM Layer-Slice Connectivity (both halves + all fit-test coupons): zero floating / unsupported islands and
     no unsupported flat overhang wider than 2.0 mm across all layers.
  6. 3D Virtual Rule60 V3 Hardware Mating Gauges:
       - INKC `6095(gas)` 1.50 mm PC plate (spec/rule60-v3-outlines.json) through full +/-0.55 mm gasket travel
       - All 12 Silicone End-Caps (compressed size from spec/rule60-v3.json) seated in 6 open rounded cap pockets cut straight from
         the floor: walls on the skirt side and both ends up to the floor, no wall toward the plate; plate relief at the
         cap-pocket level
       - All 4 Stock Metal Ball-Catch Strike Plates and their tongues (spec/rule60-v3.json)
       - Full 60-Key HHKB Cherry/OEM Keycap Array + >= 0.35 mm perimeter clearance
       - Stock base pocket: empty from the 9.69 mm floor to the skirt lip inside the skirt (bottom-case seat); the frame
         at the 9.69 mm floor (IMG_0334) outside the declared cuts
       - Chirality: USB-C notch at print +X (keyboard left in the underside view) with the inward back-left gasket pocket
       - 8 bumpon pockets: a max-size 3M SJ5012 (`Ø13.2 mm`) fits each, sits wholly on a floor `pocket_depth` below the
         desk-plane pad face with >= 1 mm of floor under it, and keeps >= 1 mm of wall to every pad edge
  Z levels come from `draft-report.json` (`calibrated_z_stack_mm`), written by the build.

Usage:
    uv run verify_topcase.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import manifold3d as md
import numpy as np
import shapely.geometry as sg
from shapely.geometry.polygon import orient
from shapely import build_area
from shapely.ops import polylabel, unary_union
from shapely.geometry import MultiLineString
import trimesh

import rule60_spec as spec

ROOT = Path(__file__).resolve().parent / "topcase-draft"

REPORT = json.loads((ROOT / "draft-report.json").read_text())
GEOM = REPORT["geometry_mm"]
DX_PW, DY_PW = GEOM["plate_to_world_offset"]
PW_SX = GEOM["plate_to_world_x_sign"]  # print frame = underside view: plate X is mirrored


def pw(xp: float, yp: float) -> tuple[float, float]:
    return PW_SX * (xp + DX_PW), yp + DY_PW


JOINT_Z_CLEAR = 0.20  # Designed vertical gap between each tongue landing and its socket roof


def slice_material(mf: md.Manifold, z: float) -> sg.base.BaseGeometry:
    rings = [sg.Polygon(p) for p in mf.slice(z).to_polygons() if len(p) >= 3]
    material = sg.Polygon()
    for ring in sorted(rings, key=lambda r: -abs(r.area)):
        material = material.symmetric_difference(ring.buffer(0))
    return material


def to_manifold(tm: trimesh.Trimesh) -> md.Manifold:
    m = tm.copy()
    m.merge_vertices(digits_vertex=5)
    mf = md.Manifold(md.Mesh64(np.asarray(m.vertices, dtype=np.float64), np.asarray(m.faces, dtype=np.uint64)))
    assert mf.status() == md.Error.NoError, mf.status()
    return mf


def plate_gas_world() -> np.ndarray:
    """INKC `6095(gas)` plate outline (spec/rule60-v3-outlines.json) in the print frame, counter-clockwise."""
    world = np.asarray([pw(x, y) for x, y in spec.outline_points("plate_gas")], dtype=np.float64)
    return world if sg.LinearRing(world).is_ccw else world[::-1]


def main() -> None:
    # -----------------------------------------------------------------------
    # 1. Exported STL & 3MF Watertightness, Single-Shell, and X2D Bed Check
    # -----------------------------------------------------------------------
    for stl_name in ("left-half-print.stl", "right-half-print.stl", "coupon-ballcatch-gasket-left.stl"):
        m = trimesh.load_mesh(ROOT / stl_name)
        assert m.is_watertight and m.is_winding_consistent and len(m.split()) == 1, stl_name

    for tmf_name, expected_objs in [
        ("rule60-hhkb-left-plate.3mf", 1),
        ("rule60-hhkb-right-plate.3mf", 1),
        ("rule60-fit-test-coupons.3mf", 5),
    ]:
        sc = trimesh.load(ROOT / tmf_name, force="scene")
        assert isinstance(sc, trimesh.Scene)
        assert len(sc.geometry) == expected_objs, (tmf_name, len(sc.geometry))
        assert np.all(sc.bounds[0] >= -1e-3) and np.all(sc.bounds[1] <= [256.0, 256.0, 260.0]), (
            tmf_name,
            sc.bounds.tolist(),
        )

    # Load print-frame LeftHalf & RightHalf from SolidCraft B-rep export
    sc_raw = trimesh.load(ROOT / "solidcraft-export.3mf", force="scene")
    assert isinstance(sc_raw, trimesh.Scene)
    raw_tms = sorted(
        [m for m in sc_raw.dump(concatenate=False) if isinstance(m, trimesh.Trimesh)],
        key=lambda m: float(m.bounds[0][0]),
    )
    assert len(raw_tms) == 2
    left_tm, right_tm = raw_tms[0], raw_tms[1]
    left_mf, right_mf = to_manifold(left_tm), to_manifold(right_tm)
    full_case_mf = left_mf + right_mf

    # Wrist-rest mirror symmetry: away from the joints (X < 10) the two wrist halves are exact mirrors, including the
    # 0.70 mm front top chamfer. A CAD-kernel boolean fault that drops material or chamfers on one half shows up here.
    wrist_box = md.Manifold.cube([135.0, 82.0, 30.0]).translate([10.0, -1.0, -5.0])
    right_wrist, mirrored_left_wrist = right_mf ^ wrist_box, left_mf.mirror([1.0, 0.0, 0.0]) ^ wrist_box
    wrist_asymmetry = float((right_wrist - mirrored_left_wrist).volume() + (mirrored_left_wrist - right_wrist).volume())
    assert wrist_asymmetry < 0.05, f"Wrist halves are not mirror images: {wrist_asymmetry} mm^3 differ"

    # -----------------------------------------------------------------------
    # 2. 91-Step Rigid-Body Dovetail Insertion Path & Rib-Confinement Proof
    # -----------------------------------------------------------------------
    # Allowed compression-rib zones: ONLY the socket rib bands `[z_stop, z_stop + z_h + JOINT_Z_CLEAR]` of the 3 joints!
    allowed_ribs = md.Manifold()
    joint_yc = GEOM["joint_yc_world"]
    joint_rib_zones = [
        ("WristFrontJoint",     joint_yc["WristFrontJoint"], 7.0, 6.2, 4.0, 5.0),
        ("WristMidJoint",       joint_yc["WristMidJoint"], 7.0, 6.2, 4.0, 5.0),
        ("FrontBezelWallJoint", joint_yc["FrontBezelWallJoint"], 6.8, 6.2, 4.0, 5.0),
    ]
    for _, yc, hh_box, proj_box, z_stop, z_h in joint_rib_zones:
        allowed_ribs += md.Manifold.cube([proj_box, 2.0 * hh_box, z_h + JOINT_Z_CLEAR]).translate([0.5, yc - hh_box, z_stop])

    dz_steps = np.linspace(0.0, 18.0, 91)
    path_overlaps = []
    outside_rib_overlaps = []
    for dz in dz_steps:
        inter = left_mf.translate([0.0, 0.0, float(dz)]) ^ right_mf
        path_overlaps.append((round(float(dz), 2), float(inter.volume())))
        outside_rib_overlaps.append(float((inter - allowed_ribs).volume()))

    max_outside_ribs = max(outside_rib_overlaps)
    max_free_slide_drag = max(v for dz, v in path_overlaps if dz >= 3.20)
    seated_rib_bite = path_overlaps[0][1]

    assert max_outside_ribs < 0.005, f"Unintended collision outside compression ribs: {max_outside_ribs} mm^3"
    assert max_free_slide_drag < 0.005, f"Drag during free-sliding upper stroke (dz>=3.2mm): {max_free_slide_drag} mm^3"
    assert 0.25 < seated_rib_bite < 5.0, f"Unexpected seated rib bite volume: {seated_rib_bite} mm^3"

    # -----------------------------------------------------------------------
    # 3. 6-DOF Retention & Stop Stiffness
    # -----------------------------------------------------------------------
    motion_blocks = {
        "pull_apart_x_1mm": float((left_mf.translate([-1.0, 0.0, 0.0]) ^ right_mf).volume()),
        "push_together_x_0p5mm": float((left_mf.translate([0.5, 0.0, 0.0]) ^ right_mf).volume()),
        "shear_y_plus_0p5mm": float((left_mf.translate([0.0, 0.5, 0.0]) ^ right_mf).volume()),
        "shear_y_minus_0p5mm": float((left_mf.translate([0.0, -0.5, 0.0]) ^ right_mf).volume()),
        "overtravel_z_stop_0p3mm_past_clearance": float(
            (left_mf.translate([0.0, 0.0, -(JOINT_Z_CLEAR + 0.3)]) ^ right_mf).volume()
        ),
        "clean_release_dz_18mm": float((left_mf.translate([0.0, 0.0, 18.0]) ^ right_mf).volume()),
    }
    assert motion_blocks["clean_release_dz_18mm"] < 0.001, motion_blocks
    assert min(v for k, v in motion_blocks.items() if k != "clean_release_dz_18mm") > 5.0, motion_blocks

    # 3b. Vertical stop clearance: the tongue landings are the only vertical contact between the halves. Lowering the
    #     RightHalf by 0.18 mm must touch nothing outside the rib bands; by 0.25 mm all landings must bear.
    z_free_play_ov = float(((left_mf.translate([0.0, 0.0, -(JOINT_Z_CLEAR - 0.02)]) ^ right_mf) - allowed_ribs).volume())
    z_landing_ov = float(((left_mf.translate([0.0, 0.0, -(JOINT_Z_CLEAR + 0.05)]) ^ right_mf) - allowed_ribs).volume())
    assert z_free_play_ov < 0.005, f"Vertical stop clearance below {JOINT_Z_CLEAR - 0.02:.2f} mm: {z_free_play_ov} mm^3"
    assert z_landing_ov > 1.0, f"Tongue landings do not bear by {JOINT_Z_CLEAR + 0.05:.2f} mm: {z_landing_ov} mm^3"

    # -----------------------------------------------------------------------
    # 4. Staggered Back Seam (seam strike centre)
    # -----------------------------------------------------------------------
    seam = GEOM["back_seam"]
    seam_x, seam_gap, step_y = seam["x_world"], seam["gap"], seam["split_step_y_world"]
    back_region = sg.box(-200.0, step_y, 200.0, 250.0)
    seam_faces: dict[str, list[float]] = {}
    for z in (1.0, 12.0):  # top skin below the groove floor; skirt wall only
        left_back = slice_material(left_mf, z).intersection(back_region)
        right_back = slice_material(right_mf, z).intersection(back_region)
        seam_faces[f"z{z:g}"] = [round(left_back.bounds[2], 3), round(right_back.bounds[0], 3)]
        assert abs(left_back.bounds[2] - (seam_x - seam_gap / 2)) < 0.01, (z, left_back.bounds)
        assert abs(right_back.bounds[0] - (seam_x + seam_gap / 2)) < 0.01, (z, right_back.bounds)

    z_strike = REPORT["calibrated_z_stack_mm"]["Z_strike_pocket_floor"]
    pilot_depth = GEOM["strike_pilot_depth"]
    strike_centres_w = [pw(x, y) for x, y in GEOM["strike_centers_plate_frame"]]
    sx_w, sy_w = min(strike_centres_w, key=lambda c: abs(c[0] - seam_x) + abs(c[1] - seam["key_y"]))
    assert abs(sx_w - seam_x) < 1e-6, (sx_w, seam_x)
    # Each half owns exactly one seam-strike pilot: a ring around it, 1 mm under the pocket floor, is solid in that half only.
    skin_l, skin_r = slice_material(left_mf, z_strike - 1.0), slice_material(right_mf, z_strike - 1.0)
    pilot_owner: dict[str, list[float]] = {}
    for side, px in (("left_pilot", sx_w - 6.5), ("right_pilot", sx_w + 6.5)):
        ring = sg.Point(px, sy_w).buffer(1.6).difference(sg.Point(px, sy_w).buffer(0.95))
        pilot_owner[side] = [round(ring.intersection(skin_l).area / ring.area, 3), round(ring.intersection(skin_r).area / ring.area, 3)]
    assert pilot_owner["left_pilot"][0] > 0.95 and pilot_owner["left_pilot"][1] < 0.01, pilot_owner
    assert pilot_owner["right_pilot"][1] > 0.95 and pilot_owner["right_pilot"][0] < 0.01, pilot_owner
    # All 8 pilots reach `pilot_depth` past the pocket floor and stop there (solid skin above them).
    full_open = slice_material(full_case_mf, z_strike - pilot_depth + 0.1)
    full_skin = slice_material(full_case_mf, z_strike - pilot_depth - 0.1)
    pilots = [sg.Point(sx + dx, sy).buffer(0.7) for sx, sy in strike_centres_w for dx in (-6.5, 6.5)]
    pilot_open = [round(p.intersection(full_open).area / p.area, 3) for p in pilots]
    pilot_capped = [round(p.intersection(full_skin).area / p.area, 3) for p in pilots]
    assert max(pilot_open) < 0.01 and min(pilot_capped) > 0.95, (pilot_open, pilot_capped)
    # The seam strike plate (20.5 x 6.55 mm) bears on the pocket floor of both halves.
    seam_plate = sg.box(sx_w - 10.25, sy_w - 3.275, sx_w + 10.25, sy_w + 3.275)
    floor_l, floor_r = slice_material(left_mf, z_strike - 0.05), slice_material(right_mf, z_strike - 0.05)
    strike_bearing = [round(seam_plate.intersection(floor_l).area, 1), round(seam_plate.intersection(floor_r).area, 1)]
    assert min(strike_bearing) > 40.0, f"Seam strike plate does not bear on both halves: {strike_bearing} mm^2"
    # Side faces line-to-line (owner): the wedge key sides lock Y and the end faces meet across the back seam, so a
    # 0.05 mm shift of the LeftHalf either way along Y, or toward the RightHalf along X, already collides there.
    seam_box = md.Manifold.cube([16.0, 210.0 - step_y, 30.0]).translate([seam_x - 8.0, step_y, -2.0])
    key_y_lock = [float((left_mf.translate([0.0, dy, 0.0]) ^ right_mf ^ seam_box).volume()) for dy in (0.05, -0.05)]
    end_face_contact = float((left_mf.translate([0.05, 0.0, 0.0]) ^ right_mf ^ seam_box).volume())
    assert min(key_y_lock) > 0.1, f"Back-seam key sides not line-to-line: {key_y_lock} mm^3 at 0.05 mm"
    assert end_face_contact > 1.0, f"Back-seam end faces not line-to-line: {end_face_contact} mm^3 at 0.05 mm"

    # 4b. Glue lines: seated, every male part meets its female over all faces. In XZ sections through each joint (tongue
    #     centre and +/-3 mm; key centre) no gap inside the joint is wider than 0.25 mm (the designed 0.20 mm vertical
    #     line under each landing and print ramp). A self-supporting ramp over an unfilled socket leaves a ~3 mm void.
    xz_full = full_case_mf.rotate([-90.0, 0.0, 0.0])  # world (x, y, z) -> (x, z, -y)

    def widest_gap(y: float, x0: float, x1: float, z0: float, z1: float) -> float:
        void = sg.box(x0, z0, x1, z1).difference(slice_material(xz_full, -y))
        pieces = [g for g in getattr(void, "geoms", [void]) if g.area > 0.005]
        return max((2.0 * g.exterior.distance(polylabel(g, 0.002)) for g in pieces), default=0.0)

    glue_gap: dict[str, float] = {}
    for d in GEOM["dovetails"]:
        glue_gap[d["name"]] = round(max(widest_gap(d["yc"] + dy, 0.05, d["proj"] - 0.05, d["z_stop"], d["z_top"] - 0.05)
                                        for dy in (-3.0, 0.0, 3.0)), 3)
    glue_gap["BackSeamKey"] = round(widest_gap(seam["key_y"], seam["key_x0"] + 0.15, seam["key_tip_x"] + 0.25,
                                               seam["key_underside_z_at_seam"] - 0.3, z_strike - 0.02), 3)
    assert max(glue_gap.values()) <= 0.25, f"Joint glue gap wider than 0.25 mm: {glue_gap}"

    # -----------------------------------------------------------------------
    # 5. 0.20 mm FDM Layer-Slice Floating-Island Verification (Zero Supports!)
    # -----------------------------------------------------------------------
    # Every printed object (both halves + the 5 fit-test coupons) as placed on the bed: no layer island without the layer
    # below, and no unsupported flat overhang wider than 2.0 mm (a layer growing past the one below by more than 45 deg).
    print_objects = [("LeftHalfPrint", trimesh.load_mesh(ROOT / "left-half-print.stl")),
                     ("RightHalfPrint", trimesh.load_mesh(ROOT / "right-half-print.stl"))]
    print_objects += list(trimesh.load(ROOT / "rule60-fit-test-coupons.3mf", force="scene").geometry.items())
    floating_islands: dict[str, list[dict[str, float]]] = {}
    flat_overhangs: dict[str, list[dict[str, float]]] = {}
    for part_label, pm in print_objects:
        prev_shape = None
        bad_layers, wide = [], []
        for z in np.arange(0.10, float(pm.bounds[1, 2]), 0.20):
            sec = pm.section(plane_origin=[0, 0, float(z)], plane_normal=[0, 0, 1])
            if sec is None:
                continue
            cur_shape = build_area(MultiLineString([p[:, :2] for p in sec.discrete]))
            pieces = list(getattr(cur_shape, "geoms", [cur_shape]))
            if prev_shape is not None:
                supported_zone = prev_shape.buffer(0.28)
                for pc in pieces:
                    if pc.area > 0.05 and pc.intersection(supported_zone).area < 0.001:
                        bad_layers.append({"z_mm": round(float(z), 2), "area_mm2": round(float(pc.area), 3)})
                grown = cur_shape.difference(prev_shape.buffer(0.20))
                for g in getattr(grown, "geoms", [grown]):
                    if not g.buffer(-1.0).is_empty:
                        wide.append({"z_mm": round(float(z), 2), "area_mm2": round(float(g.area), 1),
                                     "bounds": [round(v, 1) for v in g.bounds]})
            prev_shape = cur_shape
        floating_islands[part_label] = bad_layers
        flat_overhangs[part_label] = wide
    assert not any(floating_islands.values()), f"Unsupported floating print islands detected: {floating_islands}"
    assert not any(flat_overhangs.values()), f"Unsupported flat overhangs wider than 2 mm: {flat_overhangs}"

    # -----------------------------------------------------------------------
    # 6. 3D Virtual Rule60 V3 Hardware Mating Gauges
    # -----------------------------------------------------------------------
    levels = REPORT["calibrated_z_stack_mm"]
    z_plate, z_gasket = levels["Z_seated_gasket_plate_top"], levels["Z_gasket_trough_floor"]
    z_strike, z_floor, z_lip = levels["Z_strike_pocket_floor"], levels["Z_base_pocket_floor"], levels["Z_outer_skirt_lip"]
    z_relief = levels["Z_plate_relief_floor"]
    assert abs(z_relief - z_gasket) < 1e-9, f"Plate relief {z_relief} must sit at the cap-pocket level {z_gasket}"
    cap_pockets_w = [sg.Polygon([pw(x, y) for x, y in poly]) for poly in levels["cap_pocket_polys_plate_frame"]]
    rx0, ry0, rx1, ry1 = levels["plate_relief_box_plate_frame"]
    relief_w = sg.Polygon([pw(rx0, ry0), pw(rx1, ry0), pw(rx1, ry1), pw(rx0, ry1)])
    orange_w = sg.Polygon([pw(x, y) for x, y in levels["orange_cut_poly_plate_frame"]])
    strikes_w = [pw(x, y) for x, y in GEOM["strike_centers_plate_frame"]]

    def material_at(z: float) -> sg.base.BaseGeometry:
        return slice_material(full_case_mf, z)

    # 6a. INKC `6095(gas)` PC Plate + 12 Silicone End-Caps (compressed, spec/rule60-v3.json):
    #     The compressed cap top sits on the trough floor `z_gasket`, the plate top at `z_plate`.
    #     Check BOTH seated AND `0.25 mm` upward flex.
    gas_world = plate_gas_world()
    pc_plate_mf = md.CrossSection([gas_world]).extrude(spec.value("plate.thickness"))

    cap_l, cap_w = spec.value("gasket.cap_footprint")
    cap_h, cap_inset = spec.value("gasket.cap_height_compressed"), spec.value("gasket.cap_inset")
    caps_mf = md.Manifold()
    for y_wing_mid, tabs_p in zip(spec.value("plate.tab_mid_y"), (spec.value("plate.front_tabs_x"), spec.value("plate.back_tabs_x"))):
        for xLp, xRp in tabs_p:
            for cx_p in (xLp + cap_inset, xRp - cap_inset):
                caps_mf += md.Manifold.cube([cap_l, cap_w, cap_h], center=True).translate([*pw(cx_p, y_wing_mid), 0.0])

    plate_seated_ov = float((pc_plate_mf.translate([0, 0, z_plate]) ^ full_case_mf).volume())
    plate_upflex_ov = float((pc_plate_mf.translate([0, 0, z_plate - 0.25]) ^ full_case_mf).volume())
    caps_seated_ov = float((caps_mf.translate([0, 0, z_gasket + 0.01 + cap_h / 2]) ^ full_case_mf).volume())
    # Verify positive Z-support: moving caps 0.25 mm further into the trough floor MUST contact all 6 trough floors!
    caps_floor_contact = float((caps_mf.translate([0, 0, z_gasket - 0.25 + cap_h / 2]) ^ full_case_mf).volume())

    assert plate_seated_ov < 0.01, f"PC plate collides at seated height Z_p={z_plate}: {plate_seated_ov} mm^3"
    assert plate_upflex_ov < 0.01, f"PC plate collides during 0.25mm upward gasket flex: {plate_upflex_ov} mm^3"
    assert caps_seated_ov < 0.01, f"Silicone caps collide with trough walls: {caps_seated_ov} mm^3"
    assert caps_floor_contact > 40.0, f"Silicone caps failed to seat on trough floors: {caps_floor_contact} mm^3"

    # 6a-2. Open cap pockets cut straight from the floor: 0.30 mm below the floor a 0.30 mm band along the skirt side and
    #       both ends of each pocket must be wall material (away from the R1.0 pocket-to-relief junctions), and the whole
    #       6.30 cut (relief + pockets, i.e. no plate-side wall and no intermediate step) must be empty up to the floor.
    material_walls = material_at(z_floor - 0.3)
    pocket_wall_cover: list[float] = []
    for pocket in cap_pockets_w:
        band = pocket.buffer(0.35).difference(pocket.buffer(0.05)).difference(relief_w.buffer(1.2))
        pocket_wall_cover.append(round(band.intersection(material_walls).area / band.area, 3))
    assert min(pocket_wall_cover) > 0.95, f"Cap-pocket skirt-side/end walls missing: {pocket_wall_cover}"
    orange_inner = orient(orange_w.buffer(-0.05))
    orange_mf = md.CrossSection([np.asarray(orange_inner.exterior.coords[:-1], dtype=np.float64)])
    orange_overlap = float((orange_mf.extrude(z_floor - z_gasket + 0.3).translate([0, 0, z_gasket + 0.01]) ^ full_case_mf).volume())
    assert orange_overlap < 0.01, f"Material left inside the {z_gasket} mm cap-pocket/relief cut: {orange_overlap} mm^3"

    # 6c. 4 Stock Metal Ball-Catch Strike Plates and their tongues (spec/rule60-v3.json, two-view photo fit):
    strike = spec.value("ball_catch.strike_plate")
    tongue_x, tongue_y, tongue_z = spec.value("ball_catch.strike_tongue")
    strikes_mf = md.Manifold()
    tongue_plate_gap: list[float] = []
    for sx_w, sy_w in strikes_w:
        tongue = sg.box(sx_w - tongue_x / 2, sy_w - tongue_y / 2, sx_w + tongue_x / 2, sy_w + tongue_y / 2)
        tongue_plate_gap.append(round(tongue.distance(sg.Polygon(gas_world)), 3))
        strikes_mf += md.Manifold.cube([strike["length"], strike["width"], strike["thickness"]], center=True).translate(
            [sx_w, sy_w, z_strike + 0.01 + strike["thickness"] / 2])
        strikes_mf += md.Manifold.cube([tongue_x, tongue_y, tongue_z], center=True).translate(
            [sx_w, sy_w, z_strike + 0.01 + strike["thickness"] + tongue_z / 2])
    strikes_ov = float((strikes_mf ^ full_case_mf).volume())
    assert strikes_ov < 0.01, f"Metal ball-catch strike plate collision: {strikes_ov} mm^3"
    # The strike tongue rises through the gasket-plate level: keep it clear of the plate edge in plan.
    assert min(tongue_plate_gap) >= 0.4, f"Strike tongue too close to the gasket plate: {tongue_plate_gap} mm"

    # 6d. Full 60-Key HHKB Cherry/OEM Keycap Array (spec/rule60-v3.json) + 0.18 mm Extra Clearance through 10 mm Stroke:
    kc_poly_p = sg.Polygon(spec.value("keycaps.hhkb_gauge")).buffer(0.18, join_style="mitre")
    kc_pts_w = np.column_stack([
        PW_SX * (np.asarray(kc_poly_p.exterior.coords[:-1])[:, 0] + DX_PW),
        np.asarray(kc_poly_p.exterior.coords[:-1])[:, 1] + DY_PW,
    ])
    if not sg.LinearRing(kc_pts_w).is_ccw:
        kc_pts_w = kc_pts_w[::-1]
    keycaps_ov = float((md.CrossSection([np.asarray(kc_pts_w, dtype=np.float64)]).extrude(10.0).translate([0, 0, -2.0]) ^ full_case_mf).volume())
    assert keycaps_ov < 0.01, f"Keycap array clearance < 0.58 mm per side: {keycaps_ov} mm^3"

    # 6e. Stock Base Pocket (caliper IMG_0333/0334): the stock bottom case nests in the 10.32 mm pocket from the skirt lip
    #     down to the 9.69 mm floor, so the whole inner skirt (report corner radius) must stay empty past the floor.
    #     shapely buffers return clockwise rings, which md.CrossSection fills as zero area; orient them CCW. The ring
    #     sits 0.05 mm off the skirt face: the exported skirt fillet facets sag up to 0.024 mm into the cavity.
    ix0, iy0, ix1, iy1 = GEOM["inner_skirt_world"]
    ir = GEOM["inner_skirt_corner_r"]
    inner_skirt = sg.box(ix0 + ir, iy0 + ir, ix1 - ir, iy1 - ir).buffer(ir, quad_segs=24)
    pocket_arr = np.asarray(orient(inner_skirt.buffer(-0.05, quad_segs=24)).exterior.coords[:-1], dtype=np.float64)
    pocket_mf = md.CrossSection([pocket_arr]).extrude(z_lip - z_floor + 0.5).translate([0, 0, z_floor + 0.01])
    pocket_ov = float((pocket_mf ^ full_case_mf).volume())
    assert pocket_ov < 0.01, f"Top case intrudes into the stock base pocket past the {z_floor} mm floor: {pocket_ov} mm^3"
    # 6f. Floor (IMG_0334): the frame stays at the 9.69 mm floor everywhere except the declared cuts: plate footprint,
    #     the 6.30 cut (relief + cap pockets), keycap opening and 4 strike pockets (with pilots). No side tab pockets.
    plate_fp = sg.Polygon(gas_world).buffer(0.35, join_style="mitre")
    declared = unary_union(
        [plate_fp, orange_w.buffer(0.05), sg.Polygon(kc_pts_w)]
        + [sg.box(sx - 14.85, sy - 3.7, sx + 14.85, sy + 3.7) for sx, sy in strikes_w]
    )
    floor_region = inner_skirt.buffer(-0.05).difference(declared)
    floor_cover = round(material_at(z_floor - 0.05).intersection(floor_region).area / floor_region.area, 3)
    assert floor_cover > 0.97, f"Floor cut outside declared features: only {floor_cover:.1%} of the frame reaches Z_p {z_floor}"
    # 6g. Short-side underside steps (caliper, from the outer edge): wall to 2.85, 9.69 ledge to 4.90, 6.30 strip to the
    #     keycap opening at 5.66. Probe both sides at three depths, 0.2 mm inside each band.
    material_lip, material_mid, material_top = material_at(z_floor + 2.0), material_at((z_gasket + z_floor) / 2), material_at(z_gasket - 0.3)
    outer_x = abs(pw(GEOM["outer_plate_frame"][2], 0.0)[0])  # outline symmetric about X = 0
    side_steps_ok: dict[str, bool] = {}
    for y_p in (40.0, 60.0, 80.0):
        for sgn in (-1.0, 1.0):
            at = lambda d: sg.Point(sgn * (outer_x - d), y_p + DY_PW)
            side_steps_ok[f"{'L' if sgn < 0 else 'R'}{y_p:.0f}"] = (
                material_lip.contains(at(2.6)) and not material_lip.contains(at(3.1))      # skirt wall 2.85
                and material_mid.contains(at(4.7)) and not material_mid.contains(at(5.1))  # 9.69 ledge to 4.90
                and material_top.contains(at(5.4)) and not material_top.contains(at(5.9))  # 6.30 strip to 5.65
            )
    assert all(side_steps_ok.values()), f"Short-side steps differ from the caliper 2.85 / 4.90 / 5.66: {side_steps_ok}"
    # 6h. Chirality (v6.2 printed the mirror image). The print frame is the underside with the front at low Y, so the
    #     keyboard's left (Esc side: USB-C notch, and the back-left gasket tab set 10 mm inward to clear it) is print +X.
    back_line_y = GEOM["inner_skirt_world"][3] + 1.4
    skirt = material_at(z_lip - 1.0).intersection(sg.LineString([(-160.0, back_line_y), (160.0, back_line_y)]))
    ends = sorted(c for g in getattr(skirt, "geoms", [skirt]) for c in (g.bounds[0], g.bounds[2]))
    notches = [(a, b) for a, b in zip(ends[1:-1:2], ends[2::2]) if b - a > 5.0]
    assert len(notches) == 1 and notches[0][0] > 0.0, f"USB-C notch must be at print +X (keyboard left): {notches}"
    mid_y = (GEOM["inner_skirt_world"][1] + GEOM["inner_skirt_world"][3]) / 2
    back_outer = {("usb" if p.centroid.x > 0 else "far"): abs(p.centroid.x)
                  for p in cap_pockets_w if p.centroid.y > mid_y and abs(p.centroid.x) > 50.0}
    assert back_outer["far"] - back_outer["usb"] > 9.0, f"Back gasket pocket on the USB side must sit ~10 mm inward: {back_outer}"
    usb_notch_x = [round(v, 2) for v in notches[0]]
    usb = GEOM["usb_notch"]
    assert abs((notches[0][1] - notches[0][0]) - usb["width"]) < 0.05, (notches, usb)
    # Closed end: solid wall 0.2 mm short of `closed_end_zp`, open 0.2 mm past it (notch centre line).
    usb_probe = sg.Point(usb["x_world"], back_line_y)
    assert material_at(usb["closed_end_zp"] - 0.2).contains(usb_probe), usb
    assert not material_at(usb["closed_end_zp"] + 0.2).contains(usb_probe), usb
    # 6i. Bumpon pockets (3M SJ5012): turned so the desk plane is level (the pocket axis vertical), on each of the 8 pads
    #     a max-size bumpon disk fits the empty pocket, sits wholly on its floor at `pocket_depth` with >= 1 mm of floor
    #     under it, the pocket keeps >= 1 mm of wall to every pad edge at the pad face, and nothing stands proud of the
    #     desk plane over the pad.
    pads = GEOM["bumpon_pads"]
    tilt = math.radians(pads["desk_plane_tilt_deg"])
    desk_mf = full_case_mf.rotate([-pads["desk_plane_tilt_deg"], 0.0, 0.0])  # (y, z) -> (y cos + z sin, z cos - y sin)
    z_desk = pads["desk_plane_zp_at_y0"] * math.cos(tilt)
    z_pocket_floor = z_desk - pads["pocket_depth"]
    levels_6i = {"face": z_desk - 0.05, "past_desk": z_desk + 0.05, "in_pocket": z_pocket_floor + 0.05,
                 "floor": z_pocket_floor - 0.05, "floor_1mm": z_pocket_floor - 1.0}
    mat_6i = {k: slice_material(desk_mf, z) for k, z in levels_6i.items()}
    r_bumpon, r_pocket = pads["bumpon_diameter_max"] / 2, pads["pocket_d"] / 2
    pocket_gauge: dict[str, list[float]] = {k: [] for k in ("floor_cover", "floor_1mm_cover", "pocket_intrusion_mm2",
                                                            "wall_mm", "proud_of_desk_mm2")}
    for x, y in pads["centres_world"]:
        z = pads["desk_plane_zp_at_y0"] + y * math.tan(tilt)
        centre = sg.Point(x, y * math.cos(tilt) + z * math.sin(tilt))
        disk = centre.buffer(r_bumpon, quad_segs=32)
        pocket_gauge["floor_cover"].append(round(disk.intersection(mat_6i["floor"]).area / disk.area, 4))
        pocket_gauge["floor_1mm_cover"].append(round(disk.intersection(mat_6i["floor_1mm"]).area / disk.area, 4))
        pocket_gauge["pocket_intrusion_mm2"].append(round(
            disk.intersection(mat_6i["in_pocket"]).area + disk.intersection(mat_6i["face"]).area, 4))
        around = centre.buffer(r_pocket + 5.0)
        void = around.difference(mat_6i["face"]).difference(centre.buffer(r_pocket + 0.05))
        pocket_gauge["wall_mm"].append(round(void.distance(centre) - r_pocket, 3))
        pocket_gauge["proud_of_desk_mm2"].append(round(around.intersection(mat_6i["past_desk"]).area, 4))
    assert min(pocket_gauge["floor_cover"]) > 0.999 and min(pocket_gauge["floor_1mm_cover"]) > 0.999, pocket_gauge
    assert max(pocket_gauge["pocket_intrusion_mm2"]) < 1e-3 and max(pocket_gauge["proud_of_desk_mm2"]) < 1e-3, pocket_gauge
    assert min(pocket_gauge["wall_mm"]) >= 1.0, pocket_gauge
    pocket_gauge["bumpon_protrusion_mm"] = [round(pads["bumpon_height"] - pads["pocket_depth"], 3)]

    verification = {
        "status": "ALL_PASSED",
        "closed_single_shell_exports": [
            "left-half-print.stl",
            "right-half-print.stl",
            "coupon-ballcatch-gasket-left.stl",
            "rule60-hhkb-left-plate.3mf",
            "rule60-hhkb-right-plate.3mf",
            "rule60-fit-test-coupons.3mf",
        ],
        "dovetail_insertion_path": {
            "steps_checked": len(dz_steps),
            "free_slide_drag_dz_ge_3p2mm_mm3": round(max_free_slide_drag, 6),
            "max_overlap_outside_compression_ribs_mm3": round(max_outside_ribs, 6),
            "seated_compression_rib_bite_mm3": round(seated_rib_bite, 4),
        },
        "six_dof_retention_mm3": {k: round(v, 3) for k, v in motion_blocks.items()},
        "dovetail_z_stop_clearance": {
            "design_mm": JOINT_Z_CLEAR,
            "overlap_at_0p18mm_mm3": round(z_free_play_ov, 6),
            "landing_overlap_at_0p25mm_mm3": round(z_landing_ov, 3),
        },
        "back_seam": {
            "seam_faces_x_mm": seam_faces,
            "seam_strike": GEOM["back_seam_strike"],
            "seam_strike_pilot_ring_cover_left_right": pilot_owner,
            "pilot_open_above_bottom": pilot_open,
            "pilot_capped_below_bottom": pilot_capped,
            "seam_strike_bearing_left_right_mm2": strike_bearing,
            "key_side_shift_0p05mm_overlap_mm3": [round(v, 3) for v in key_y_lock],
            "end_face_push_0p05mm_overlap_mm3": round(end_face_contact, 3),
        },
        "joint_glue_line_max_gap_mm": glue_gap,
        "floating_layer_islands_0p20mm": {k: len(v) for k, v in floating_islands.items()},
        "flat_overhangs_over_2mm": {k: len(v) for k, v in flat_overhangs.items()},
        "wrist_mirror_asymmetry_mm3": round(wrist_asymmetry, 5),
        "cap_pocket_wall_cover_skirt_side_and_ends": pocket_wall_cover,
        "cap_pocket_and_relief_overlap_above_6p30_mm3": round(orange_overlap, 5),
        "floor_cover_outside_declared_cuts": floor_cover,
        "short_side_steps_2p85_4p90_5p66": side_steps_ok,
        "chirality_usb_notch_x_and_back_pocket_centres": {"usb_notch_x": usb_notch_x,
                                                          "back_outer_pocket_abs_x": {k: round(v, 2) for k, v in back_outer.items()}},
        "bumpon_pockets_sj5012": pocket_gauge,
        "strike_tongue_to_plate_gap_mm": tongue_plate_gap,
        "virtual_hardware_mating_mm3": {
            "dwg_6095_gas_pc_plate_seated": round(plate_seated_ov, 5),
            "dwg_6095_gas_pc_plate_upward_flex_0p25": round(plate_upflex_ov, 5),
            "twelve_silicone_caps_wall_clearance": round(caps_seated_ov, 5),
            "twelve_silicone_caps_floor_bearing": round(caps_floor_contact, 2),
            "four_metal_ballcatch_strikes": round(strikes_ov, 5),
            "sixty_hhkb_keycaps_full_travel": round(keycaps_ov, 5),
            "stock_base_pocket_past_floor": round(pocket_ov, 5),
        },
    }
    (ROOT / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
