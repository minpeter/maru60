"""Mating and printability checks for the Rule 60 V3 HHKB bottom-case draft (build_bottomcase_draft.py).

Run after both builds: the printed top case (topcase-draft/solidcraft-export.3mf, the same pocket as the stock one) is
the mating gauge, and the stock parts come from spec/: INKC 6095(gas) plate, silicone caps, strike plates and tongues,
ball-catch bodies, a GH60 PCB with its bottom-side parts and USB-C plug, battery-bay filler, decoration plate, bumpons.
Writes bottomcase-draft/verification.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import manifold3d as md
import numpy as np
import shapely.geometry as sg
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
    for name in ("bottom-left", "bottom-right", "coupon-front-left"):
        m = trimesh.load_mesh(OUT / f"{name}-print.stl")
        assert m.is_watertight and m.is_winding_consistent and len(m.split()) == 1, name
        assert np.all(m.bounds[0] >= -1e-6) and np.all(m.bounds[1] <= [256.0, 256.0, 256.0]), (name, m.bounds)
    for name in ("left", "right", "fit-coupon"):
        sc = trimesh.load(OUT / f"rule60-hhkb-bottomcase-{name}.3mf", force="scene")
        assert len(sc.geometry) == 1 and np.all(sc.bounds[1] <= 256.0), name

    sc = trimesh.load(ROOT / "topcase-draft" / "solidcraft-export.3mf", force="scene")
    top_mf = md.Manifold.batch_boolean([to_manifold(t) for t in sc.dump(concatenate=False)], md.OpType.Add)
    world = {name: to_manifold(trimesh.load_mesh(OUT / f"{name}-world.stl"))
             for name in ("bottom-left", "bottom-right", "coupon-front-left")}
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

    # 3. Gasket plate and caps: the plate floats free seated and 1.0 mm down; the 12 cap bottom flanges (compressed
    #    footprint, 9.00..10.20) clear every wall and bear on the recess floors.
    plate_t = spec.value("plate.thickness")
    plate = md.CrossSection([plate_gas_world()]).extrude(plate_t).translate([0.0, 0.0, top.Z_PLATE])
    plate_free = {f"down_{d:.1f}": vol(plate.translate([0.0, 0.0, d]) ^ bottom) for d in (0.0, 0.5, 1.0)}
    assert max(plate_free.values()) < 0.01, plate_free
    cap_l, cap_w = spec.value("gasket.cap_footprint")
    flange = spec.value("gasket.top_flange_compressed")
    z_flange = top.Z_PLATE + plate_t
    caps = md.Manifold()
    for y_mid, tabs in zip(spec.value("plate.tab_mid_y"), (spec.value("plate.front_tabs_x"), spec.value("plate.back_tabs_x"))):
        for xl, xr in tabs:
            for cx in (xl + top.CAP_INSET, xr - top.CAP_INSET):
                x, y = top.pw(cx, y_mid)
                caps += box(x - cap_l / 2, y - cap_w / 2, x + cap_l / 2, y + cap_w / 2, z_flange, z_flange + flange - 0.01)
    caps_seated = vol(caps ^ bottom)
    caps_bear = vol(caps.translate([0.0, 0.0, 0.10]) ^ bottom)
    assert caps_seated < 0.01, f"Cap flanges collide with the recess walls: {caps_seated} mm^3"
    assert caps_bear > 12 * cap_l * cap_w * 0.09 * 0.95, f"Cap flanges do not all bear on the recess floors: {caps_bear}"

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
    #    plate 0.8 mm down; the cable plug overmold (12.0 x 6.5) clears both cases from the receptacle out.
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
    plug = box(usb_xw - 6.0, uy1, usb_xw + 6.0, 240.0, zc - 3.25, zc + 3.25)  # out past the back face (197.37)
    plug_free = {"bottom_mm3": vol(plug ^ bottom), "top_mm3": vol(plug ^ top_mf)}
    assert max(plug_free.values()) < 0.01, plug_free
    floor_gap = round(Z["cavity_floor"] - (z_pcb + 1.6 + 3.26), 2)

    # 6. Battery-bay filler (INKC drawing, 4.5 mm) drops in flush; the decoration plate (3 mm) sits in its underside
    #    recess within the desk face; >= 1.0 mm of material between that recess and the bay, and over each bumpon pocket.
    fil = spec.outline("battery_bay_filler")
    bay = REPORT["plate_frame"]["battery_bay"]
    fx0, fy0 = (bay[0] + bay[2]) / 2 - fil["bbox"][2] / 2, (bay[1] + bay[3]) / 2 - fil["bbox"][3] / 2
    filler_p = sg.Polygon([(x + fx0, y + fy0) for x, y in spec.outline_points("battery_bay_filler")])
    filler = bc.prism(bc.plate_to_world(filler_p), Z["cavity_floor"], Z["bay_floor"] - 0.01)
    deco_poly = bc.deco_poly_print()
    deco = bc.from_print(bc.prism(deco_poly, 0.01, bc.DECO["thickness"]))
    deco_cover = bc.from_print(bc.prism(deco_poly.buffer(bc.DECO_CLEAR), bc.DECO["thickness"] + 0.05,
                                        bc.DECO["thickness"] + 1.0))
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
    split_gap = box(-0.06, -1e3, 0.06, 1e3, -1e3, 1e3)  # the 0.10 mm gap between the halves is not a missing wall
    fits = {
        "filler_overlap_mm3": vol(filler ^ bottom),
        "deco_plate_overlap_mm3": vol(deco ^ bottom),
        "deco_roof_1mm_void_mm3": vol(deco_cover - split_gap - bottom),
        "bumpon_overlap_mm3": [vol(b ^ bottom) for b in bumpons],
        "bumpon_roof_1mm_void_mm3": [vol(r - bottom) for r in roofs],
        "bumpon_wall_1mm_void_mm3": [vol(w - bottom) for w in walls],
        "bumpon_protrusion_mm": round(top.BUMPON_H - top.POCKET_DEPTH, 2),
    }
    assert fits["filler_overlap_mm3"] < 0.01 and fits["deco_plate_overlap_mm3"] < 0.01, fits
    assert fits["deco_roof_1mm_void_mm3"] < 0.05, fits
    assert max(fits["bumpon_overlap_mm3"]) < 0.01 and max(fits["bumpon_roof_1mm_void_mm3"]) < 0.05, fits
    assert max(fits["bumpon_wall_1mm_void_mm3"]) < 0.05, fits

    # 7. One desk plane: in the print frame the bottom-case underside and the wrist-rest pad faces both lie at Z' = 0.
    to_p = bc.TO_PRINT
    desk = {"bottom_min_z": round(float(bottom.transform(to_p).bounding_box()[2]), 4),
            "top_case_min_z": round(float(top_mf.transform(to_p).bounding_box()[2]), 4),
            "wrist_pad_face_area_mm2": round(float(slice_material(top_mf.transform(to_p), 0.02).area), 1)}
    assert abs(desk["bottom_min_z"]) < 1e-3 and abs(desk["top_case_min_z"]) < 0.02 and desk["wrist_pad_face_area_mm2"] > 1000.0, desk

    # 8. USB slot under the top-case notch (keyboard left = world +X), same centre and width.
    z_usb = (Z["catch_floor"] + Z["cavity_floor"]) / 2  # below the catch notches, through the plug's height band
    back = slice_material(bottom, z_usb).intersection(sg.box(-200.0, top.pw(0.0, bc.LEDGE_BACK_P)[1] - 0.5, 200.0, 250.0))
    ends = sorted(c for g in getattr(back, "geoms", [back]) for c in (g.bounds[0], g.bounds[2]))
    gaps = [(a, b) for a, b in zip(ends[1:-1:2], ends[2::2]) if b - a > 5.0]
    notch = json.loads((ROOT / "topcase-draft" / "draft-report.json").read_text())["geometry_mm"]["usb_notch"]
    assert len(gaps) == 1 and abs((gaps[0][0] + gaps[0][1]) / 2 - notch["x_world"]) < 0.05, (gaps, notch)
    assert abs(gaps[0][1] - gaps[0][0] - notch["width"]) < 0.05 and gaps[0][0] > 0.0, (gaps, notch)

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
    #    2 mm except the declared bridges (bumpon-pocket roofs, decoration-recess roof).
    bridges = unary_union([sg.Point(x, bc.print_y(y)).buffer(pocket_r + 0.3) for x, y in bc.bumpon_centres_world()]
                          + [deco_poly.buffer(bc.DECO_CLEAR + 0.3)])
    printability = {}
    for name in ("bottom-left", "bottom-right", "coupon-front-left"):
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
                        if not bridges.contains(g_model):
                            wide.append({"z": round(float(z), 2), "bounds": [round(v, 1) for v in g_model.bounds]})
            prev = cur
        printability[name] = {"islands": islands, "undeclared_overhangs": wide}
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
        "pcb": {"gh60_pcb_and_usb_free_mm3": pcb_free, "usb_body_to_floor_mm": floor_gap, "usb_plug_free_mm3": plug_free},
        "drop_in_parts": fits,
        "desk_plane": desk,
        "usb_slot_x_world": [round(v, 3) for v in gaps[0]],
        "open_ends_material_above_floor_mm3": open_ends,
        "printability_0p20mm": {k: {"islands": len(v["islands"]), "undeclared_overhangs": len(v["undeclared_overhangs"])}
                                for k, v in printability.items()},
    }
    (OUT / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
