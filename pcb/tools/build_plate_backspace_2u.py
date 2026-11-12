#!/usr/bin/env python3
"""Build a 2U Backspace HHKB plate, with plate-mount 7U by default.

The 2U Backspace stabilizer remains PCB-mounted. The 7U plate-mount cutout
is inherited from INKC, not a manufacturer-qualified Designer Studio footprint.

The split Backspace plate remains separate: its switches rotate 90 degrees
in the Mill-Max candidate and need their own retention edges. This file is a
nominal CAD fit study until the selected switches/stabilizers are tried.
"""
import argparse
import json
import sys
import zipfile
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import build_plate as bp
import rule60_spec as spec
from build_plate_pcb_mount import pcb_mount_7u, SEVEN_U_INDEX

NAMES = {
    "plate": "maru60-hhkb-plate-7u-plate-mount-2u-backspace",
    "pcb": "maru60-hhkb-plate-pcb-mount-2u-backspace",
}


def geometry(seven_u_mount="plate"):
    if seven_u_mount not in NAMES:
        raise ValueError(seven_u_mount)
    rec = spec.outline("plate_gas_hhkb")
    outer = Polygon(spec.verts_points(rec["verts"], 48))
    cutouts = [Polygon(spec.verts_points(c, 48)) for c in rec["cutouts"]]
    centers = [(257.25, 91.869), (276.30, 91.869)]
    indices = [next(i for i, p in enumerate(cutouts) if p.contains(Point(*c))) for c in centers]
    assert len(set(indices)) == 2
    center = (266.775, 91.869)
    switch = affinity.translate(cutouts[indices[0]], xoff=9.525)
    # Assumed 7.75 x 14 mm stem housing, 0.25 mm radial allowance;
    # separate 0.40 mm clearances around all four mounting holes.
    stab_x = (254.3845 + .4525, 278.2605 + .4525)
    ylo, yhi = center[1] - 7.25, center[1] + 7.25
    housings = [box(x - 4.125, ylo, x + 4.125, yhi) for x in stab_x]
    holes = [Point(x, 101.06775-y).buffer(d/2+.4, quad_segs=64)
             for x in stab_x for y,d in ((2.21375,3.048),(17.45375,3.9878))]
    wire = box(stab_x[0], center[1] - 1.5, stab_x[1], center[1] + 1.5)
    backspace = unary_union([switch, wire, *housings, *holes])
    assert backspace.geom_type == "Polygon" and backspace.is_valid
    assert outer.contains(backspace)
    if seven_u_mount == "pcb":
        cutouts[SEVEN_U_INDEX] = Polygon([(x, y) for x, y, _ in pcb_mount_7u(rec["cutouts"][SEVEN_U_INDEX], .4)])
    retained = [p for i, p in enumerate(cutouts) if i not in indices]
    assert all(backspace.disjoint(p) for p in retained)
    cuts = retained + [backspace]
    plate = outer.difference(unary_union(cuts))
    assert plate.geom_type == "Polygon" and plate.is_valid
    # North/south latch edges of the center switch must remain in the plate.
    cx, cy = center
    for y in (cy - 7.1, cy + 7.1):
        assert plate.covers(Point(cx, y)), "center switch retention edge removed"
    copper = plate.buffer(-bp.COPPER_PULLBACK, quad_segs=16)
    # Preserve exact original arc vertices in every unaffected cutout. Only
    # the merged Backspace opening is polygonal; don't flatten the 7U clips.
    loops = [rec["verts"]] + [
        pcb_mount_7u(c, .4) if i == SEVEN_U_INDEX and seven_u_mount == "pcb" else c
        for i, c in enumerate(rec["cutouts"]) if i not in indices
    ] + [[[x, y, 0] for x, y in backspace.exterior.coords[:-1]]]
    return rec, outer, retained, backspace, plate, copper, loops, indices


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seven-u-mount", choices=NAMES, default="plate")
    args = ap.parse_args()
    rec, outer, retained, backspace, plate, copper, loops, indices = geometry(args.seven_u_mount)
    name = NAMES[args.seven_u_mount]
    (bp.MODELS / f"{name}.dxf").write_text(bp.dxf(loops))
    files = {
        f"{name}.GKO": bp.gerber("Profile,NP", bp.outline_strokes(loops)),
        f"{name}.GTL": bp.gerber("Copper,L1,Top", bp.regions(copper)),
        f"{name}.GBL": bp.gerber("Copper,L2,Bot", bp.regions(copper)),
        f"{name}.GTS": bp.gerber("Soldermask,Top", []),
        f"{name}.GBS": bp.gerber("Soldermask,Bot", []),
    }
    with zipfile.ZipFile(bp.MODELS / f"{name}-gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for filename, data in files.items():
            z.writestr(zipfile.ZipInfo(filename, date_time=(2026, 1, 1, 0, 0, 0)), data)
    report = {"status": "nominal_geometry_study_not_hardware_qualified",
              "source": "spec/rule60-v3-outlines.json:plate_gas_hhkb",
              "changed": "Dedicated PCB-mount 2U Backspace; " + ("original plate-mount 7U cutout preserved" if args.seven_u_mount == "plate" else "PCB-mount 7U relief"),
              "seven_u_mount": args.seven_u_mount,
              "selected_product": "Designer Studio Stabilizer (For Plate), 7U wire",
              "seven_u_original_vertices_preserved": loops[SEVEN_U_INDEX+1] == rec["cutouts"][SEVEN_U_INDEX],
              "product_fit_verified": False,
              "product_guide": "https://geonworks.kr/article/assemble-guild/5/2140/",
              "guide_contains_dimensioned_drawing": False,
              "plate_thickness_mm": {"nominal_case_stack": 1.5, "supplier_clip_range": None},
              "removed_split_cutout_indices": indices,
              "backspace_to_outer_edge_mm": round(backspace.distance(outer.boundary), 4),
              "backspace_to_other_cutout_mm": round(min(backspace.distance(p) for p in retained), 4),
              "center_switch_retention_edges": "present north and south",
              "limitations": "Assumed 7.75 x 14 mm housing with 0.25 mm allowance; mounting-hole allowance 0.40 mm. 7U clip dimensions and supported plate thickness require supplier drawing. Requires selected-parts fit test and milling review"}
    (bp.MODELS / f"{name}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
