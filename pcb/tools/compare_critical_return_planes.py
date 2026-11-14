#!/usr/bin/env python3
"""Compare GND beneath unchanged outer critical routes; numerical CAD screen."""
import argparse,hashlib,json
from pathlib import Path
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('baseline',type=Path);ap.add_argument('candidate',type=Path);ap.add_argument('output',type=Path)
a=ap.parse_args();old=json.loads(a.baseline.read_text());new=json.loads(a.candidate.read_text())
critical=lambda n:n.startswith(('USB_DP','USB_DM','QSPI_','VREG_')) or n in ('XIN','XOUT','XTAL_OUT')
def planes(g):
 return {ly:unary_union([Polygon(rings[0],rings[1:]) for z in g['zones'] if z['net']=='GND' and not z['keepout'] for rings in z['fill'].get(ly,[]) if rings]) for ly in ('In1.Cu','In2.Cu')}
a_planes,b_planes=planes(old),planes(new);rows={}
for t in old['tracks']:
 if not critical(t['net']) or t['layer'] not in ('F.Cu','B.Cu'):continue
 ly='In1.Cu' if t['layer']=='F.Cu' else 'In2.Cu'
 line=LineString([(t['x1'],t['y1']),(t['x2'],t['y2'])]);supported=line.intersection(a_planes[ly]);lost=supported.difference(b_planes[ly])
 corridor=line.buffer(t['w']/2+.15,32);lost_area=corridor.intersection(a_planes[ly]).difference(b_planes[ly]).area
 row=rows.setdefault(t['net'],{'new_uncovered_centerline_mm':0.,'lost_ground_in_trace_plus_0p15mm_corridor_mm2':0.,'segments_with_new_gap':[]})
 row['new_uncovered_centerline_mm']+=lost.length;row['lost_ground_in_trace_plus_0p15mm_corridor_mm2']+=lost_area
 if lost.length>1e-5:row['segments_with_new_gap'].append({'layer':t['layer'],'from':[t['x1'],t['y1']],'to':[t['x2'],t['y2']],'lost_length_mm':lost.length})
maximum=max((r['new_uncovered_centerline_mm'] for r in rows.values()),default=0)
result={'scope':'GND geometry comparison only; not an electromagnetic measurement or proof of transient behavior',
 'baseline_geometry_sha256':hashlib.sha256(a.baseline.read_bytes()).hexdigest(),
 'candidate_geometry_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
 'nets':rows,'maximum_new_centerline_gap_total_mm':maximum,
 'comparison_resolution_mm':1e-6,'resolution_note':'One native KiCad coordinate unit (1 nm); raw floating point intersection differences are retained above.',
 'no_new_centerline_loss_at_native_resolution':maximum<=1e-6}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({n:r['new_uncovered_centerline_mm'] for n,r in rows.items()},indent=2))
