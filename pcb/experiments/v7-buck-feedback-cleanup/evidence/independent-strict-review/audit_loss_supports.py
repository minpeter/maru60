import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
# Use the same source-bound polygon loader and invariant preconditions as the passing geometry review.
d={'__file__':str(R/'compare_strip_geometry.py')};exec((R/'compare_strip_geometry.py').read_text().split('# Actual loss bounds')[0],d)
S,C,p,poly,sub,cross,area,bb=[d[k] for k in ['S','C','p','poly','sub','cross','area','bb']]
audit=json.loads((R/'contour-loss-audit.json').read_text());out=[]
for layer in audit['layers']:
 l=layer['layer'];rawloss=poly([r['polygon'] for r in layer['loss_polygons']]);oldplane,newplane=d['physical'][l];physloss=sub(oldplane,newplane);hits=[];checked=0
 for u,m in S['objects'].items():
  if u in d['ret'] or l not in m['copper']:continue
  sh=m['copper'][l];x1,y1,x2,y2=sh['bbox'];b=physloss.BBox()
  if x2<b.GetLeft() or x1>b.GetRight() or y2<b.GetTop() or y1>b.GetBottom():continue
  assert 'shape'in sh;q=poly(sh['shape'])
  if u in S['holes']:
   assert 'shape'in S['holes'][u];q.BooleanSubtract(poly(S['holes'][u]['shape']))
  checked+=1;support=cross(q,oldplane);lost_support=cross(support,physloss)
  if lost_support.Area():hits.append({'uuid':u,'net':m['net'],'lost_old_physical_plane_contact_support_mm2':area(lost_support),'bounds_mm':bb(lost_support)})
 circle=p.SHAPE_CIRCLE(p.VECTOR2I(178150000,85750000),500000);region=p.SHAPE_POLY_SET();circle.TransformToPolygon(region,1,p.ERROR_OUTSIDE)
 out.append({'layer':l,'all_inner_layer_retained_conductor_supports_tested':checked,'lost_contact_support_intersections':hits,'raw_loss_overlap_removed_via_0_50mm_radius_region_mm2':area(cross(rawloss,region)),'physical_loss_overlap_removed_via_0_50mm_radius_region_mm2':area(cross(physloss,region))})
# Current direct/plane graph supports and complete source root membership were separately reconstructed.
g=json.loads((R/'raw-graph-review.json').read_text());assert not g['zone_contact_support_changes'] and g['all_ground_pad_root_membership_exact']
r={'source_sha256':S['board_sha256'],'candidate_sha256':C['board_sha256'],'layers':out,'all_observed_731_zone_contact_support_areas_exact':True,'rooted_GND_pad_membership_exact_count':g['ground_pads_in_J1_A1_root'],'limitation':'Zero retained contact/support intersection does not waive a nonzero strict global plane loss; this is a separate consequence check.'}
(R/'loss-support-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
