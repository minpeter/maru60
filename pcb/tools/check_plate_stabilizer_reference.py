#!/usr/bin/env python3
"""Screen the selected 7U DXF against documented Cherry dimensions.

This checks selected dimensions, not complete stabilizer or PCB/case fit.
The rounded-rectangle comparison is a conservative aperture probe, not a
manufacturer body model. A positive missing area is not a proven collision.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import ezdxf
from shapely.geometry import LineString, Polygon, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import rule60_spec as spec


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--plate', type=Path, default=ROOT/'models/maru60-hhkb-plate-7u-plate-mount-2u-backspace.dxf')
    args = ap.parse_args()
    polylines = list(ezdxf.readfile(args.plate).modelspace().query('POLYLINE'))
    candidates = [e for e in polylines if 120 < max(v.dxf.location.x for v in e.vertices)-min(v.dxf.location.x for v in e.vertices) < 125]
    if len(candidates) != 1:
        raise ValueError('Expected one 7U opening')
    vertices = [[v.dxf.location.x, v.dxf.location.y, v.dxf.bulge] for v in candidates[0].vertices]
    stock = spec.outline('plate_gas_hhkb')['cutouts'][3]
    preserved = all(abs(a-b)<1e-6 for va,vb in zip(vertices,stock) for a,b in zip(va,vb)) and len(vertices)==len(stock)
    poly = Polygon(spec.verts_points(vertices,96))
    # These straight shoulders lie away from the central wire passage and
    # rounded corner relief, and identify each 6.65 mm housing aperture.
    sections = [LineString([(x-5,19),(x+5,19)]).intersection(poly) for x in (85.8,200.1)]
    bounds = [section.bounds for section in sections]
    widths = [b[2]-b[0] for b in bounds]
    centers = [(b[0]+b[2])/2 for b in bounds]
    pitch = centers[1]-centers[0]
    checks = []
    for name, values, nominal, tolerance in [
        ('housing_width',widths,.262*25.4,.004*25.4),
        ('housing_center_pitch',[pitch],4.5*25.4,.004*25.4),
    ]:
        checks.append({'dimension':name,'actual_mm':[round(x,4) for x in values],
                       'cherry_nominal_mm':nominal,'cherry_tolerance_mm':tolerance,
                       'pass':all(abs(x-nominal)<=tolerance for x in values)})
    probes = []
    radius = .012*25.4
    for x,b in zip(centers,bounds):
        # Tangent lines of INKC's original main housing opening. This is a
        # shape screen placed on those lines, not a full Cherry datum fit.
        y0,y1 = 10.1395,22.4395
        probe = box(b[0]+radius,y0+radius,b[2]-radius,y1-radius).buffer(radius,quad_segs=64)
        probes.append({'center_x_mm':round(x,4),'probe_height_mm':y1-y0,
                       'cherry_main_height_mm':.484*25.4,
                       'cherry_main_height_tolerance_mm':.004*25.4,
                       'probe_corner_radius_mm':radius,
                       'probe_area_outside_cutout_mm2':round(probe.difference(poly).area,6)})
    result = {'status':'nominal_dimensions_match_shape_and_physical_fit_unqualified',
              'source':'https://cdn.sparkfun.com/datasheets/Components/Switches/MX%20Series.pdf',
              'source_page':'PDF page 3 / printed 10-4, metal-frame cutout and G99-0379 7U kit',
              'plate':str(args.plate.relative_to(ROOT)) if args.plate.is_relative_to(ROOT) else str(args.plate),
              'plate_sha256':hashlib.sha256(args.plate.read_bytes()).hexdigest(),
              'original_inkc_cutout_preserved':preserved,'dimension_checks':checks,
              'corner_aperture_probes':probes,
              'cherry_metal_frame_thickness_mm':{'nominal':.06*25.4,'tolerance':.004*25.4,
                   'scope':'MX metal-frame drawing; not a supplier thickness guarantee for DUROCK/Gateron/Designer Studio'},
              'all_products_qualified':False,
              'limitations':'The positive aperture-probe residual flags different corner geometry, not a measured plastic-body collision. No full Cherry-profile tolerance check, clip force, product-specific body, wire sweep, PCB component or case clearance is established.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if not preserved or not all(c['pass'] for c in checks):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
