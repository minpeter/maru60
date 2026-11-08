"""Mating and printability checks for the Maru60 HHKB bottom-case draft (build_bottomcase_draft.py).

Run after both builds: the printed top case (topcase-draft/halves-world.3mf, the same pocket as the stock one) is
the mating gauge, and the stock parts come from spec/: INKC 6095(gas) plate, silicone caps, strike plates and tongues,
ball-catch bodies, a GH60 PCB with its bottom-side parts and USB-C plug, battery-bay filler, decoration plate, bumpons.
Writes bottomcase-draft/verification.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import manifold3d as md
import numpy as np
import shapely.affinity as sa
import shapely.geometry as sg
from shapely.geometry.polygon import orient
from shapely import build_area
from shapely.geometry import MultiLineString
from shapely.ops import unary_union
import trimesh

import build_bottomcase_draft as bc
import rule60_spec as spec
from verify_topcase import plate_gas_world, slice_material, to_manifold

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "bottomcase-draft"
REPORT = json.loads((OUT / "draft-report.json").read_text())
Z = REPORT["z_p"]
top = bc.top


def box(x0: float, y0: float, x1: float, y1: float, z0: float, z1: float) -> md.Manifold:
    return md.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def vol(m: md.Manifold) -> float:
    return round(float(m.volume()), 4)


def main() -> None:
    # 1. Exports: closed single shells on the 256 mm bed.
    parts = ("bottom-left", "bottom-right", "coupon-front-left", "joint-test-left", "joint-test-right")
    for name in parts:
        m = trimesh.load_mesh(OUT / f"{name}-print.stl")
        assert m.is_watertight and m.is_winding_consistent and len(m.split()) == 1, name
        assert np.all(m.bounds[0] >= -1e-6) and np.all(m.bounds[1] <= [256.0, 256.0, 256.0]), (name, m.bounds)
    for name, n_obj in (("left", 1), ("right", 1), ("fit-coupon", 1), ("joint-test", 2)):
        sc = trimesh.load(OUT / f"maru60-hhkb-bottomcase-{name}.3mf", force="scene")
        assert len(sc.geometry) == n_obj and np.all(sc.bounds[0] >= -1e-6) and np.all(sc.bounds[1] <= 256.0), name

    sc = trimesh.load(ROOT / "topcase-draft" / "halves-world.3mf", force="scene")
    top_mf = md.Manifold.batch_boolean([to_manifold(t) for t in sc.dump(concatenate=False)], md.OpType.Add)
    world = {name: to_manifold(trimesh.load_mesh(OUT / f"{name}-world.stl")) for name in parts}
    bottom = world["bottom-left"] + world["bottom-right"]

    # 2. Nesting in the top-case pocket: free when seated and 0.10 mm off centre (0.15 per side), located at 0.25 mm,
    #    and only the rail tops bear on the 9.69 floor: lifting the bottom case 0.05 mm into the top case touches a wide
    #    band there and nothing at the skirt lip (20.01). No outer step (stock part): at every height below the rail tops
    #    the case stays inside the rail outline, so the top-case skirt wraps it from outside.
    seated = vol(bottom ^ top_mf)
    lateral = {f"{ax}{d:+.2f}": vol(bottom.translate([d if ax == "x" else 0.0, d if ax == "y" else 0.0, 0.0]) ^ top_mf)
               for ax in ("x", "y") for d in (-0.10, 0.10, -0.25, 0.25)}
    lifted = bottom.translate([0.0, 0.0, -0.05]) ^ top_mf
    bearing_mm2 = round(vol(lifted) / 0.05, 1)
    lip_contact = vol(lifted ^ box(-200.0, 0.0, 200.0, 250.0, top.SKIRT_H - 1.0, top.SKIRT_H + 1.0))
    rail_outline = bc.plate_box(*bc.RIM_P, r=bc.RIM_CORNER_R).buffer(0.01)
    outside_rails = {f"z_p_{z:g}": round(slice_material(bottom, z).difference(rail_outline).area, 4)
                     for z in (Z["rim_top"] + 0.3, top.SKIRT_H - 0.3, top.SKIRT_H + 0.3, top.SKIRT_H + 5.0,
                               top.SKIRT_H + 10.0)}
    assert seated < 0.01, f"Bottom case collides with the top case when seated: {seated} mm^3"
    assert max(v for k, v in lateral.items() if "0.10" in k) < 0.01, lateral
    assert min(v for k, v in lateral.items() if "0.25" in k) > 0.1, lateral
    assert bearing_mm2 > 1000.0, f"Rim top bearing on the 9.69 floor only {bearing_mm2} mm^2"
    assert lip_contact < 0.01, f"Bottom case touches the top-case skirt lip: {lip_contact} mm^3"
    assert max(outside_rails.values()) < 0.01, f"Material outside the rail outline (outer step): {outside_rails}"

    # 3. Gasket plate and caps: the plate floats free seated and 1.0 mm down; the 12 cap bottom flanges (`gasket.cap_free`
    #    pushed fully onto the tab ends, compressed to 9.00..10.20) clear every wall and bear on the recess floors.
    plate_t = spec.value("plate.thickness")
    plate = md.CrossSection([plate_gas_world()]).extrude(plate_t).translate([0.0, 0.0, top.Z_PLATE])
    plate_free = {f"down_{d:.1f}": vol(plate.translate([0.0, 0.0, d]) ^ bottom) for d in (0.0, 0.5, 1.0)}
    assert max(plate_free.values()) < 0.01, plate_free
    caps_plan = [orient(sg.Polygon([top.pw(x, y) for x, y in pts])) for pts in spec.gasket_outlines_plate()]
    flange = spec.value("gasket.top_flange_compressed")
    z_flange = top.Z_PLATE + plate_t
    caps = md.Manifold()
    for ring in caps_plan:
        caps += md.CrossSection([np.asarray(ring.exterior.coords[:-1], dtype=np.float64)]).extrude(flange - 0.01).translate(
            [0.0, 0.0, z_flange])
    caps_seated = vol(caps ^ bottom)
    caps_bear = vol(caps.translate([0.0, 0.0, 0.10]) ^ bottom)
    assert caps_seated < 0.01, f"Cap flanges collide with the recess walls: {caps_seated} mm^3"
    assert caps_bear > sum(c.area for c in caps_plan) * 0.09 * 0.95, f"Cap flanges do not all bear on the recess floors: {caps_bear}"

    # 4. Ball catches: strike plates and tongues clear; each catch body (31.8 x 6.7 x 7.7: barrels over +-10.6 rising to
    #    the catch top, ears with the screws held below the rim top) sits on its notch floor, clear of both cases and of
    #    the strike plate; the tongue tip passes the barrel axis.
    sp, (tx, ty, tz) = spec.value("ball_catch.strike_plate"), spec.value("ball_catch.strike_tongue")
    body = spec.value("ball_catch.catch_body")
    z_sp = top.Z_STRIKE + sp["thickness"]
    strikes, tongues, catches = md.Manifold(), md.Manifold(), md.Manifold()
    for _, sxp, syp in top.strike_centers_p():
        x, y = top.pw(sxp, syp)
        strikes += box(x - sp["length"] / 2, y - sp["width"] / 2, x + sp["length"] / 2, y + sp["width"] / 2,
                       top.Z_STRIKE + 0.01, z_sp)
        tongues += box(x - tx / 2, y - ty / 2, x + tx / 2, y + ty / 2, z_sp, z_sp + tz)
        hw, hl = body["width"] / 2, body["length"] / 2
        catches += box(x - 10.6, y - hw, x + 10.6, y + hw, Z["catch_top"], Z["catch_floor"] - 0.01)
        for s in (-1.0, 1.0):
            catches += box(min(x + s * 10.6, x + s * hl), y - hw, max(x + s * 10.6, x + s * hl), y + hw,
                           top.Z_FLOOR + 0.10, Z["catch_floor"] - 0.01)
    catch_gauge = {
        "strikes_and_tongues_vs_bottom_mm3": vol((strikes + tongues) ^ bottom),
        "catch_bodies_vs_bottom_mm3": vol(catches ^ bottom),
        "catch_bodies_vs_top_case_mm3": vol(catches ^ top_mf),
        "catch_bodies_vs_strike_plates_mm3": vol(catches ^ strikes),
        "catch_floor_bearing_mm3": vol(catches.translate([0.0, 0.0, 0.05]) ^ bottom),
        "tongue_tip_past_barrel_axis_mm": round(z_sp + tz - (Z["catch_top"] + body["width"] / 2), 2),
        "barrel_top_under_strike_plate_mm": round(Z["catch_top"] - z_sp, 2),
        "pilot_depths_mm": [p["depth"] for c in REPORT["catches"] for p in c["pilots"]],
    }
    assert max(v for k, v in catch_gauge.items() if k.endswith("_mm3") and "bearing" not in k) < 0.01, catch_gauge
    assert catch_gauge["catch_floor_bearing_mm3"] > 4 * 31.8 * 6.7 * 0.05 * 0.5, catch_gauge
    assert catch_gauge["tongue_tip_past_barrel_axis_mm"] >= 1.0, catch_gauge
    assert min(catch_gauge["pilot_depths_mm"]) >= 3.0, catch_gauge

    # 5. PCB: a GH60 outline (285.0 x 94.6, 1.6 mm) under the MX plate with 2.0 mm bottom-side parts and the board's
    #    USB-C receptacle (9.0 x 7.4 x 3.26 under the PCB, mouth 0.6 past the back edge) clears the cavity with the
    #    plate 0.8 mm down; a generic cable-body gauge (12.35 x 6.5, not a standard overmold maximum) clears from the
    #    receptacle out. Reported, not required (the stock notch width stays selectable): a ~13 mm retail plug, and the
    #    12.35 plug with the board's USB centre 0.3 mm off (photo-read centres).
    fr = json.loads((ROOT / "spec" / "boards.json").read_text())["frames"]["pcb_to_plate"]
    pcb_x0, pcb_y0, pcb_y1 = fr["dx"], fr["y0"] - 94.6, fr["y0"]
    z_pcb = top.Z_PLATE + 5.0
    usb_xp = spec.usb_centre_plate_x(REPORT["board"])
    (wx0, wy0), (wx1, wy1) = top.pw(pcb_x0 + 285.0, pcb_y0), top.pw(pcb_x0, pcb_y1)
    (ux0, uy0), (ux1, uy1) = top.pw(usb_xp + 4.5, pcb_y1 - 7.4), top.pw(usb_xp - 4.5, pcb_y1 + 0.6)
    pcb = box(wx0, wy0, wx1, wy1, z_pcb, z_pcb + 1.6) + box(wx0 + 1.0, wy0 + 1.0, wx1 - 1.0, wy1 - 1.0, z_pcb, z_pcb + 3.6)
    usb = box(ux0, uy0, ux1, uy1, z_pcb + 1.6, z_pcb + 1.6 + 3.26)
    pcb_free = {f"down_{d:.1f}": vol((pcb + usb).translate([0.0, 0.0, d]) ^ bottom) for d in (0.0, 0.8)}
    assert max(pcb_free.values()) < 0.01, pcb_free
    zc = z_pcb + 1.6 + 1.63
    usb_xw = top.pw(usb_xp, 0.0)[0]
    plugs = {}
    for label, w, dx in (("12.35", 12.35, 0.0), ("12.35_x+0.3", 12.35, 0.3), ("12.35_x-0.3", 12.35, -0.3),
                         ("13.0", 13.0, 0.0)):
        plug = box(usb_xw + dx - w / 2, uy1, usb_xw + dx + w / 2, 240.0, zc - 3.25, zc + 3.25)  # out past the back face
        plugs[label] = {"bottom_mm3": vol(plug ^ bottom), "top_mm3": vol(plug ^ top_mf)}
        if label == "12.35":
            plug_down = plug.translate([0.0, 0.0, 0.8])
            plug_down_free = {"bottom_mm3": vol(plug_down ^ bottom), "top_mm3": vol(plug_down ^ top_mf)}
    plug_free = plugs.pop("12.35")
    assert max(plug_free.values()) < 0.01 and max(plug_down_free.values()) < 0.01, (plug_free, plug_down_free)
    plug_reported = {k: max(v.values()) < 0.01 for k, v in plugs.items()}
    floor_gap = round(Z["cavity_floor"] - (z_pcb + 1.6 + 3.26), 2)

    # 6. Battery-bay filler (INKC drawing, 4.5 mm) drops onto the floor of the 4.69 mm bay, its top below the cavity
    #    floor; the decoration plate (3 mm) sits in its underside recess within the desk face; >= 1.0 mm of material
    #    between that recess and the bay (outside the four screw holes), and over each bumpon pocket.
    fil = spec.outline("battery_bay_filler")
    bay = REPORT["plate_frame"]["battery_bay"]
    fx0, fy0 = (bay[0] + bay[2]) / 2 - fil["bbox"][2] / 2, (bay[1] + bay[3]) / 2 - fil["bbox"][3] / 2
    filler_p = sg.Polygon([(x + fx0, y + fy0) for x, y in spec.outline_points("battery_bay_filler")])
    filler = bc.prism(bc.plate_to_world(filler_p), Z["bay_floor"] - fil["thickness"], Z["bay_floor"] - 0.01)
    assert Z["bay_floor"] - fil["thickness"] >= Z["cavity_floor"], "filler stands above the cavity floor"
    deco_poly = bc.deco_poly_print()
    deco_t, deco_d = bc.DECO["thickness"], bc.DECO_RECESS  # the plate stands deco_t - deco_d proud of the desk face
    deco = bc.from_print(bc.prism(deco_poly, deco_d - deco_t, deco_d - 0.01))
    deco_cover = bc.from_print(bc.prism(deco_poly.buffer(bc.DECO_CLEAR), deco_d + 0.05, deco_d + 1.0))
    screws = bc.deco_screws_print()
    screw_holes = md.Manifold.batch_boolean([bc.from_print(md.Manifold.cylinder(
        2.0, bc.DECO_SCREW_HOLE_D / 2 + 0.05, bc.DECO_SCREW_HOLE_D / 2 + 0.05, 32).translate([*s["print"], deco_d]))
        for s in screws], md.OpType.Add)
    assert deco_t - deco_d < top.BUMPON_H - top.POCKET_DEPTH - 1.0, "weight plate stands within 1 mm of the desk"
    pocket_r = top.POCKET_D / 2
    bumpons = [bc.from_print(md.Manifold.cylinder(top.BUMPON_H, top.BUMPON_D_MAX / 2, top.BUMPON_D_MAX / 2, 64)
                             .translate([x, bc.print_y(y), top.POCKET_DEPTH - top.BUMPON_H - 0.01]))
               for x, y in bc.bumpon_centres_world()]
    roofs = [bc.from_print(md.Manifold.cylinder(1.0, pocket_r, pocket_r, 64).translate([x, bc.print_y(y),
                                                                                        top.POCKET_DEPTH + 0.05]))
             for x, y in bc.bumpon_centres_world()]
    walls = [bc.from_print((md.Manifold.cylinder(top.POCKET_DEPTH - 0.1, pocket_r + 1.0, pocket_r + 1.0, 64)
                            - md.Manifold.cylinder(top.POCKET_DEPTH, pocket_r + 0.05, pocket_r + 0.05, 64).translate(
                                [0.0, 0.0, -0.05])).translate([x, bc.print_y(y), 0.05]))
             for x, y in bc.bumpon_centres_world()]
    fits = {
        "filler_overlap_mm3": vol(filler ^ bottom),
        "deco_plate_overlap_mm3": vol(deco ^ bottom),
        "deco_roof_1mm_void_mm3": vol(deco_cover - bottom - screw_holes),
        "bumpon_overlap_mm3": [vol(b ^ bottom) for b in bumpons],
        "bumpon_roof_1mm_void_mm3": [vol(r - bottom) for r in roofs],
        "bumpon_wall_1mm_void_mm3": [vol(w - bottom) for w in walls],
        "bumpon_protrusion_mm": round(top.BUMPON_H - top.POCKET_DEPTH, 2),
    }
    assert fits["filler_overlap_mm3"] < 0.01 and fits["deco_plate_overlap_mm3"] < 0.01, fits
    assert fits["deco_roof_1mm_void_mm3"] < 0.05, fits
    assert max(fits["bumpon_overlap_mm3"]) < 0.01 and max(fits["bumpon_roof_1mm_void_mm3"]) < 0.05, fits
    assert max(fits["bumpon_wall_1mm_void_mm3"]) < 0.05, fits

    # 6b. Weight-plate screws: four M2 from inside, through the floor into the plate's blind tapped holes (photo-read,
    #     0.5 mm float). A Ø4.0 x 2.0 head (socket cap, the largest common M2 head) on its counterbore floor and the
    #     Ø2.0 shank clear the case centred and 0.45 mm off in any direction; the head stays >= 1.5 mm below the cavity
    #     floor; >= 1.2 mm of thread in the plate with the tip >= 1.0 mm short of its outer face; each hole >= 2.5 mm
    #     inside the plate edge; two screws per half, each counterbore >= 2 mm from the seam.
    head_h, head_d, shank_d, float_xy = 2.0, 4.0, 2.0, 0.45
    left_region = bc.left_region_print()
    screw_report = []
    for s in screws:
        (px, py), z0 = s["print"], s["cbore_floor_z"]
        overlaps = []
        for dx, dy in ((0.0, 0.0), (float_xy, 0.0), (-float_xy, 0.0), (0.0, float_xy), (0.0, -float_xy)):
            head = md.Manifold.cylinder(head_h, head_d / 2, head_d / 2, 48).translate([px + dx, py + dy, z0 + 0.01])
            shank = md.Manifold.cylinder(z0 - deco_d + 0.5, shank_d / 2, shank_d / 2, 32).translate(
                [px + dx, py + dy, deco_d - 0.5])
            overlaps.append(vol(bc.from_print(head + shank) ^ bottom))
        tip_z = z0 - bc.DECO_SCREW_LEN
        point = sg.Point(px, py)
        screw_report.append({
            "plate_xy": s["plate"], "half": "left" if left_region.contains(point) else "right",
            "overlap_mm3_centred_and_shifted": overlaps,
            "head_top_below_cavity_floor_mm": round(s["cavity_floor_z"] - (z0 + head_h), 2),
            "thread_in_plate_mm": round(deco_d - tip_z, 2), "tip_to_plate_outer_face_mm": round(tip_z - (deco_d - deco_t), 2),
            "hole_to_plate_edge_mm": round(deco_poly.exterior.distance(point) - shank_d / 2, 2),
            "cbore_to_seam_mm": round(left_region.exterior.distance(point) - bc.DECO_SCREW_CBORE_D / 2, 2)})
    for r in screw_report:
        assert max(r["overlap_mm3_centred_and_shifted"]) < 0.01, r
        assert r["head_top_below_cavity_floor_mm"] >= 1.5 and r["thread_in_plate_mm"] >= 1.2, r
        assert r["tip_to_plate_outer_face_mm"] >= 1.0 and r["hole_to_plate_edge_mm"] >= 2.5 and r["cbore_to_seam_mm"] >= 2.0, r
    assert sorted(r["half"] for r in screw_report) == ["left", "left", "right", "right"], screw_report

    # 7. One desk plane: in the print frame the bottom-case underside and the wrist-rest pad faces both lie at Z' = 0.
    to_p = bc.TO_PRINT
    desk = {"bottom_min_z": round(float(bottom.transform(to_p).bounding_box()[2]), 4),
            "top_case_min_z": round(float(top_mf.transform(to_p).bounding_box()[2]), 4),
            "wrist_pad_face_area_mm2": round(float(slice_material(top_mf.transform(to_p), 0.02).area), 1)}
    assert abs(desk["bottom_min_z"]) < 1e-3 and abs(desk["top_case_min_z"]) < 0.02 and desk["wrist_pad_face_area_mm2"] > 1000.0, desk
    # 7b. ㄷ tray + triangular base (stock part): every section below the tray bottom lies inside the base outline
    #     (the steps all round stay empty), nothing sits behind the back slope plane, the base fills its outline just
    #     under the tray bottom, the tray keeps the full rail outline down to its bottom, and the desk face ends
    #     `BACK_BEVEL_INSET` in from the back rail face.
    n, off = bc.back_bevel()
    base_ol = bc.base_outline()
    tz = bc.TRAY_BOTTOM_ZP                     # tray bottom at the back rail (highest)
    tz_low = bc.tray_bottom_zp(bc.Y_FRONT)     # tray bottom at the front rail (lowest: tilted 0.2 deg)
    outside_base = {f"z_p_{z:g}": round(slice_material(bottom, z).difference(base_ol.buffer(0.01)).area, 4)
                    for z in (tz_low + 0.05, tz_low + 2.0, tz_low + 6.0, tz_low + 10.0)}
    below_tray = box(-200.0, bc.Y_BACK - bc.BACK_BEVEL_INSET - 1.0, 200.0, bc.Y_BACK + 1.0, tz + 0.05, 40.0)
    behind_bevel = vol(bottom ^ below_tray.trim_by_plane([-v for v in n], -off + 0.02))  # n . x <= off - 0.02
    under = slice_material(bottom, tz_low + 0.05)  # just under the whole tray; the bay runs through here, so compare
                                                   # outlines, not fill
    tray = slice_material(bottom, tz - 0.05)
    rail_outline_p = bc.plate_box(*bc.RIM_P, r=bc.RIM_CORNER_R)
    desk_slice = slice_material(bottom.transform(to_p), 0.05)
    tray_base = {"material_outside_base_outline_mm2": outside_base, "material_behind_slope_mm3": behind_bevel,
                 "base_bounds_world": [round(v, 2) for v in under.bounds],
                 "expected_base_bounds": [round(v, 2) for v in base_ol.bounds],
                 "tray_bottom_bounds_world": [round(v, 2) for v in tray.bounds],
                 "rail_outline_bounds": [round(v, 2) for v in rail_outline_p.bounds],
                 "desk_face_back_edge_print_y": round(desk_slice.bounds[1], 3),
                 "expected_print_y": round(bc.print_y(bc.Y_BACK - bc.BACK_BEVEL_INSET), 3)}
    assert max(outside_base.values()) < 0.01 and behind_bevel < 0.01, tray_base
    assert all(abs(a - b) < 0.1 for a, b in zip(tray_base["base_bounds_world"][:3],  # ends and front; the back is
                                                tray_base["expected_base_bounds"][:3])), tray_base  # sloped here
    assert all(abs(a - b) < 0.1 for a, b in zip(tray_base["tray_bottom_bounds_world"], tray_base["rail_outline_bounds"])), tray_base
    assert abs(tray_base["desk_face_back_edge_print_y"] - tray_base["expected_print_y"]) < 0.1, tray_base

    # 7c. ㄴㄱ seam, hybrid joint: the halves meet line-to-line without overlap, slide together freely along the
    #     insertion axis (normal to the desk face), and every in-plane shift of 0.3 mm collides on the dovetails. Each
    #     seam catch has one screw pilot in each half (its body bridges the seam); the other two sit in one half.
    hl, hr = world["bottom-left"], world["bottom-right"]
    axis, yp_axis = np.asarray(bc.FROM_PRINT)[:, 2], np.asarray(bc.FROM_PRINT)[:, 1]
    shifts = {"x+0.3": [0.3, 0.0, 0.0], "x-0.3": [-0.3, 0.0, 0.0],
              "print_y+0.3": (0.3 * yp_axis).tolist(), "print_y-0.3": (-0.3 * yp_axis).tolist()}
    seam = {"seated_overlap_mm3": vol(hl ^ hr),
            "insertion_path_max_overlap_mm3": max(vol(hl.translate((t * axis).tolist()) ^ hr)
                                                  for t in (0.2, 1.0, 3.0, 6.0, 12.0, 24.0)),
            "in_plane_shift_overlap_mm3": {k: vol(hl.translate(v) ^ hr) for k, v in shifts.items()}}
    sl, sr = slice_material(hl, Z["catch_floor"] + 1.0), slice_material(hr, Z["catch_floor"] + 1.0)
    owners = {}
    for c in REPORT["catches"]:
        owners[c["name"]] = []
        for p in c["pilots"]:
            ring = sg.Point(*p["world"]).buffer(1.6).difference(sg.Point(*p["world"]).buffer(0.95))
            cover = [ring.intersection(s).area / ring.area for s in (sl, sr)]
            owners[c["name"]].append("left" if cover[0] > 0.95 > 0.01 > cover[1] else
                                     "right" if cover[1] > 0.95 > 0.01 > cover[0] else f"? {cover}")
    seam["catch_screw_owner"] = owners
    assert seam["seated_overlap_mm3"] < 0.01 and seam["insertion_path_max_overlap_mm3"] < 0.01, seam
    assert min(seam["in_plane_shift_overlap_mm3"].values()) > 5.0, seam
    for name, o in owners.items():
        assert all(v in ("left", "right") for v in o), owners
        assert (len(set(o)) == 2) == (name in (bc.SEAM_BACK_CATCH, bc.SEAM_FRONT_CATCH)), owners

    # 8. USB slot under the top-case notch (keyboard left = world +X), same centre and width.
    z_usb = (Z["catch_floor"] + Z["cavity_floor"]) / 2  # below the catch notches, through the plug's height band
    back = slice_material(bottom, z_usb).intersection(sg.box(-200.0, top.pw(0.0, bc.LEDGE_BACK_P)[1] - 0.5, 200.0, 250.0))
    ends = sorted(c for g in getattr(back, "geoms", [back]) for c in (g.bounds[0], g.bounds[2]))
    gaps = [(a, b) for a, b in zip(ends[1:-1:2], ends[2::2]) if b - a > 5.0]
    notch = json.loads((ROOT / "topcase-draft" / "draft-report.json").read_text())["geometry_mm"]["usb_notch"]
    assert len(gaps) == 1 and abs((gaps[0][0] + gaps[0][1]) / 2 - notch["x_world"]) < 0.05, (gaps, notch)
    assert abs(gaps[0][1] - gaps[0][0] - notch["width"]) < 0.05 and gaps[0][0] > 0.0, (gaps, notch)
    # The lower-case roof over the port is flush with the surrounding rim, not a separate recessed beam.
    # Probe exported geometry: both the ceiling-less exit and recessed-roof revisions must fail.
    sy0, sy1 = REPORT["usb_slot_world"]["y"]
    open_y = sy0 + 1.0
    bridge_probe = box(gaps[0][0] + 0.02, open_y + 0.02, gaps[0][1] - 0.02, bc.Y_BACK - 0.02,
                       Z["rim_top"] + 0.02, 11.88)
    # A cap recess that reaches into the slot (PH60 Rev.3: 0.06 mm) keeps its full depth; the bridge must fill the rest.
    for recess in bc.cap_recesses_p():
        bridge_probe -= box(*bc.plate_to_world(recess).bounds[:2], *bc.plate_to_world(recess).bounds[2:],
                            Z["rim_top"] - 1.0, bc.CAP_SEAT_ZP + 0.02)
    bridge_missing = vol(bridge_probe - bottom)
    assert bridge_missing < 0.0001, f"Lower USB bridge missing: {bridge_missing} mm^3"
    bridge_bounds = (bottom ^ box(gaps[0][0] + 0.02, open_y + 0.02, gaps[0][1] - 0.02,
                                  bc.Y_BACK - 0.02, 9.0, 12.4)).bounding_box()
    # Both upper inside corners follow the top-case radius, not a square corner or a chamfer.
    radius = notch["closed_end_corner_r"]
    arch_missing, arch_blockage = 0.0, 0.0
    for edge, sign in ((gaps[0][0], 1.0), (gaps[0][1], -1.0)):
        for offset, solid in ((radius * 2 / 15, True), (radius / 3, False)):
            x, z = edge + sign * offset, 11.90 + offset
            probe = box(x - 0.02, open_y + 0.02, x + 0.02, bc.Y_BACK - 0.02, z - 0.02, z + 0.02)
            if solid:
                arch_missing += vol(probe - bottom)
            else:
                arch_blockage += vol(probe ^ bottom)
    assert arch_missing < 0.0001 and arch_blockage < 0.0001, ("USB arch radius", arch_missing, arch_blockage)
    slot_column = box(gaps[0][0] + radius + 0.02, open_y + 0.02,
                      gaps[0][1] - radius - 0.02, sy1 - 0.02, 11.92, bottom.bounding_box()[5] + 1.0)
    slot_column += box(gaps[0][0] + 0.02, open_y + 0.02, gaps[0][1] - 0.02, sy1 - 0.02,
                       11.90 + radius + 0.02, bottom.bounding_box()[5] + 1.0)
    slot_bottom_material = vol(bottom ^ slot_column)
    assert slot_bottom_material < 0.0001, f"USB exit is not open underneath: {slot_bottom_material} mm^3"
    # The lower case must have the same small free-end rounds as the upper case, not square corners behind them.
    lip_corner_checks = {}
    lip_radius = 0.5
    for edge, side in ((gaps[0][0], -1.0), (gaps[0][1], 1.0)):
        cut = not slice_material(bottom, top.SKIRT_H - lip_radius * 2 / 15).contains(
            sg.Point(edge + side * lip_radius * 2 / 15, bc.Y_BACK - 0.2))
        shoulder = slice_material(bottom, top.SKIRT_H - lip_radius * 0.4).contains(
            sg.Point(edge + side * lip_radius * 0.4, bc.Y_BACK - 0.2))
        # Continue into the open exit below the lip; a shallow groove with a square ledge underneath is not a round.
        open_below = not slice_material(bottom, top.SKIRT_H + 0.2).contains(
            sg.Point(edge + side * lip_radius / 2, open_y + 0.2))
        lip_corner_checks[str(side)] = bool(cut and shoulder and open_below)
    assert all(lip_corner_checks.values()), ("Lower USB lip rounds differ from upper case", lip_corner_checks)
    ledge_z = 21.08  # Proposed deeper mating floor; independent exported-geometry contract, not a stock measurement
    floor_air = box(gaps[0][0] + 0.02, sy0 + 0.02, gaps[0][1] - 0.02, open_y - 0.02, 20.10, 21.06)
    floor_blockage = vol(bottom ^ floor_air)
    assert floor_blockage < 0.0001, f"USB mating floor is not recessed deeply enough: {floor_blockage} mm^3"
    # A shallow local pocket, not a deep channel: its floor and raised end must both remain.
    inner_port_air = box(usb_xw - 8.0, sy0 - 13.9, usb_xw + 8.0, sy0 - 1.1, 18.22, 18.68)
    inner_port_blockage = vol(bottom ^ inner_port_air)
    assert inner_port_blockage < 0.0001, f"Floor still fills the inner USB connector recess: {inner_port_blockage} mm^3"
    inner_floor = box(usb_xw - 8.0, sy0 - 13.9, usb_xw + 8.0, sy0 - 1.1, 18.72, 19.52)
    end_land = box(usb_xw - 8.0, sy0 - 0.9, usb_xw + 8.0, sy0 - 0.1, 18.22, 18.62)
    shallow_floor_missing = vol(inner_floor - bottom)
    raised_end_missing = vol(end_land - bottom)
    assert shallow_floor_missing < 0.0001 and raised_end_missing < 0.0001, (shallow_floor_missing, raised_end_missing)
    # At least 0.8 mm remains under the separate outer ledge, including its thinnest rear edge.
    ledge_probe = box(gaps[0][0] + 0.02, sy0 + 0.02, gaps[0][1] - 0.02, open_y - 0.02,
                      ledge_z + 0.02, ledge_z + 0.82)
    ledge_missing = vol(ledge_probe - bottom)
    assert ledge_missing < 0.0001, ("USB inner ledge", ledge_missing)
    # 8a. The slot leaves no fin: between it and each cap recess the rail top keeps `SLOT_MIN_WALL` or is cut away.
    slot_plan = sg.box(gaps[0][0], sy0, gaps[0][1], sy1)
    rim = slice_material(bottom, Z["rim_top"] + 0.25)
    walls = []
    for r in (bc.plate_to_world(p) for p in bc.cap_recesses_p()):
        if slot_plan.intersects(r):  # the recess reaches into the slot: no rail left between them
            walls.append(0.0)
        elif slot_plan.distance(r) < 3.0:
            (_, ry0, _, ry1), (rx0, rx1) = r.bounds, (r.bounds[0], r.bounds[2])
            x0, x1 = (gaps[0][1], rx0) if rx0 >= gaps[0][1] else (rx1, gaps[0][0])
            between = rim.intersection(sg.box(x0, max(sy0, ry0), x1, min(sy1, ry1)))
            walls.append(round(between.bounds[2] - between.bounds[0], 3) if between.area > 1e-4 else 0.0)
    slot_check = {"cap_recess_walls_mm": walls, "open_bottom_material_mm3": slot_bottom_material,
                  "arch_corner_missing_mm3": arch_missing, "arch_corner_blockage_mm3": arch_blockage,
                  "matching_lip_corner_rounds": lip_corner_checks,
                  "recessed_floor_blockage_mm3": floor_blockage,
                  "inner_connector_recess_blockage_mm3": inner_port_blockage,
                  "shallow_port_floor_missing_mm3": shallow_floor_missing, "raised_port_end_missing_mm3": raised_end_missing,
                  "inner_ledge_missing_mm3": ledge_missing, "bridge_missing_mm3": bridge_missing,
                  "bridge_to_upper_ceiling_mm": round(bridge_bounds[2] - Z["rim_top"], 3),
                  "bridge_to_generic_plug_mm": round(zc - 3.25 - bridge_bounds[5], 3),
                  "plug_down_0p8_mm3": plug_down_free}
    assert all(w == 0.0 or w >= bc.SLOT_MIN_WALL - 0.01 for w in walls), slot_check

    # 8b. Open ends (stock part, IMG_0462/0472/0473): between the rail faces nothing rises above the cavity floor over
    #     the last 10 mm of either end, while both rails run on to the rim ends at the rim top.
    (_, ry0), (_, ry1) = top.pw(0.0, bc.LEDGE_FRONT_P), top.pw(0.0, bc.LEDGE_BACK_P)
    rim_x = abs(top.pw(bc.RIM_P[0], 0.0)[0])
    open_ends = {side: vol(bottom ^ box(min(s * (rim_x - 10.0), s * (rim_x + 1.0)), ry0 + 0.05,
                                           max(s * (rim_x - 10.0), s * (rim_x + 1.0)), ry1 - 0.05,
                                           Z["rim_top"] - 1.0, Z["cavity_floor"] - 0.05))
                 for side, s in (("left", 1.0), ("right", -1.0))}
    rail_ends = slice_material(bottom, Z["rim_top"] + 0.3).bounds
    assert max(open_ends.values()) < 0.01, f"Material between the rails at an end: {open_ends}"
    assert rail_ends[0] < -rim_x + 0.05 and rail_ends[2] > rim_x - 0.05, (rail_ends, rim_x)

    # 9. Printability, desk face down at 0.20 mm layers: no island without the layer below; no flat overhang wider than
    #    2 mm per layer, and no down-facing surface shallower than 45 deg above the bed, except the declared ones:
    #    USB bridge (requires support), bumpon-pocket roofs and decoration-recess roof, and the tray bottom (the steps:
    #    a cantilever at 6 deg; the per-layer test alone misses it because each 0.20 mm layer grows only ~1.9 mm).
    bridges = unary_union([sg.Point(x, bc.print_y(y)).buffer(pocket_r + 0.3) for x, y in bc.bumpon_centres_world()]
                          + [deco_poly.buffer(bc.DECO_CLEAR + 0.3)])
    steps_world = bc.plate_box(*bc.RIM_P, r=bc.RIM_CORNER_R).difference(base_ol)
    to_print_xy = [1.0, 0.0, 0.0, -bc.COS, 0.0, -bc.SIN * tz]  # tray-bottom points (x, y, tz) -> print (x', y')
    step_band = sa.affine_transform(steps_world, to_print_xy).buffer(0.3)
    bridge_print = bc.to_trimesh(box(gaps[0][0] - 0.8, open_y, gaps[0][1] + 0.8, bc.Y_BACK,
                                     Z["rim_top"], 11.90).transform(bc.TO_PRINT))
    usb_support = sg.MultiPoint(bridge_print.vertices[:, :2]).convex_hull.buffer(0.3)
    declared = unary_union([bridges, step_band, usb_support])
    printability = {}
    for name in parts:
        pm = trimesh.load_mesh(OUT / f"{name}-print.stl")
        shift = pm.bounds[0] - np.asarray(world[name].transform(bc.TO_PRINT).bounding_box()[:3])
        prev, islands, wide = None, [], []
        for z in np.arange(0.10, float(pm.bounds[1, 2]), 0.20):
            sec = pm.section(plane_origin=[0, 0, float(z)], plane_normal=[0, 0, 1])
            if sec is None:
                continue
            cur = build_area(MultiLineString([p[:, :2] for p in sec.discrete]))
            if prev is not None:
                for pc in getattr(cur, "geoms", [cur]):
                    if pc.area > 0.05 and pc.intersection(prev.buffer(0.28)).area < 0.001:
                        islands.append(round(float(z), 2))
                grown = cur.difference(prev.buffer(0.20))
                for g in getattr(grown, "geoms", [grown]):
                    if not g.buffer(-1.0).is_empty:
                        g_model = sg.Polygon([(x - shift[0], y - shift[1]) for x, y in g.exterior.coords])
                        if not declared.contains(g_model):
                            wide.append({"z": round(float(z), 2), "bounds": [round(v, 1) for v in g_model.bounds]})
            prev = cur
        # Down-facing faces off the bed steeper than 45 deg from vertical, outside the declared regions (model XY).
        down = (pm.face_normals[:, 2] < -0.707) & (pm.triangles_center[:, 2] > 0.05)
        shallow = [c for c in pm.triangles_center[down] - [shift[0], shift[1], 0.0]
                   if not declared.contains(sg.Point(c[0], c[1]))]
        step_area = float(pm.area_faces[down][[step_band.contains(sg.Point(c[0] - shift[0], c[1] - shift[1]))
                                               for c in pm.triangles_center[down]]].sum())
        usb_area = float(pm.area_faces[down][[usb_support.contains(sg.Point(c[0] - shift[0], c[1] - shift[1]))
                                              for c in pm.triangles_center[down]]].sum())
        printability[name] = {"islands": islands, "undeclared_overhangs": wide + [
            {"down_facing_face_at": [round(float(v), 1) for v in c]} for c in shallow[:5]],
            "usb_bridge_requires_support_mm2": round(usb_area, 2),
            "tray_step_cantilever_mm2": round(step_area, 1)}
    assert printability["bottom-left"]["usb_bridge_requires_support_mm2"] > 80.0, printability
    assert not any(v["islands"] or v["undeclared_overhangs"] for v in printability.values()), printability

    verification = {
        "status": "ALL_PASSED",
        "board": REPORT["board"],
        "top_case_pocket": {"seated_overlap_mm3": seated, "lateral_shift_overlap_mm3": lateral,
                            "rim_top_bearing_on_9p69_floor_mm2": bearing_mm2, "skirt_lip_contact_mm3": lip_contact,
                            "material_outside_rail_outline_mm2": outside_rails},
        "gasket": {"plate_free_mm3": plate_free, "cap_flanges_seated_mm3": caps_seated,
                   "cap_flanges_bearing_0p10_mm3": caps_bear, "cap_seat_z_p": Z["cap_seat"]},
        "ball_catches": catch_gauge,
        "pcb": {"gh60_pcb_and_usb_free_mm3": pcb_free, "usb_body_to_floor_mm": floor_gap, "usb_plug_free_mm3": plug_free,
                "usb_plug_side_clearance_mm": round((notch["width"] - 12.35) / 2, 3), "other_plugs_free": plug_reported},
        "drop_in_parts": fits,
        "weight_plate_screws": screw_report,
        "desk_plane": desk,
        "tray_and_base": tray_base,
        "split_seam": seam,
        "usb_slot_x_world": [round(v, 3) for v in gaps[0]],
        "usb_slot_section": slot_check,
        "open_ends_material_above_floor_mm3": open_ends,
        "printability_0p20mm": {k: {"islands": len(v["islands"]), "undeclared_overhangs": len(v["undeclared_overhangs"]),
                                    "usb_bridge_requires_support_mm2": v["usb_bridge_requires_support_mm2"],
                                    "tray_step_cantilever_mm2": v["tray_step_cantilever_mm2"]}
                                for k, v in printability.items()},
    }
    (OUT / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
