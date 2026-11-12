#!/usr/bin/env python3
"""Build a dedicated 2U Backspace / PCB-mount stabilizer HHKB plate.

The split Backspace plate remains separate: its switches rotate 90 degrees
in the Mill-Max candidate and need their own retention edges. This file is a
nominal CAD fit study until the selected switches/stabilizers are tried.
"""
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

NAME = "maru60-hhkb-plate-pcb-mount-2u-backspace"


def main():
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
    loops = [rec["verts"]] + [[[x, y, 0] for x, y in p.exterior.coords[:-1]] for p in cuts]
    (bp.MODELS / f"{NAME}.dxf").write_text(bp.dxf(loops))
    files = {
        f"{NAME}.GKO": bp.gerber("Profile,NP", bp.outline_strokes(loops)),
        f"{NAME}.GTL": bp.gerber("Copper,L1,Top", bp.regions(copper)),
        f"{NAME}.GBL": bp.gerber("Copper,L2,Bot", bp.regions(copper)),
        f"{NAME}.GTS": bp.gerber("Soldermask,Top", []),
        f"{NAME}.GBS": bp.gerber("Soldermask,Bot", []),
    }
    with zipfile.ZipFile(bp.MODELS / f"{NAME}-gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    report = {"status": "nominal_geometry_study_not_hardware_qualified",
              "source": "spec/rule60-v3-outlines.json:plate_gas_hhkb",
              "changed": "PCB-mount 7U relief and dedicated 2U Backspace; stock plate unchanged",
              "removed_split_cutout_indices": indices,
              "backspace_to_outer_edge_mm": round(backspace.distance(outer.boundary), 4),
              "backspace_to_other_cutout_mm": round(min(backspace.distance(p) for p in retained), 4),
              "center_switch_retention_edges": "present north and south",
              "limitations": "Assumed 7.75 x 14 mm housing with 0.25 mm allowance; mounting-hole allowance 0.40 mm. Requires selected-parts fit test and milling review"}
    (bp.MODELS / f"{NAME}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
