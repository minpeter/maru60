exec(open('/workspace/shared/maru60-resume/continuation-9d787/mcu-gpio3/scripts/assess.py').read().split('rows=[]')[0])
from shapely.geometry import Point,box
region=box(99,23,121,94)
center=(112.6,84.0)
envelope=poly(p.SHAPE_CIRCLE(V(center),450000),True)
zone_rows=[]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if z.IsOnLayer(l):
   g=geom(z.GetFilledPolysList(l))
   if not g.is_empty and g.intersects(geom(envelope)):zone_rows.append({'uuid':uid(z),'layer':b.GetLayerName(l),'net':z.GetNetname(),'clearance_mm':z.GetLocalClearance()/1e6,'fill_area_in_envelope_mm2':g.intersection(geom(envelope)).area})
print(zone_rows,flush=True)
assert max(x['clearance_mm'] for x in zone_rows)==.2
near=[]
eg=geom(envelope)
localbox=p.BOX2I(V((112.1,83.5)),V((1,1)))
for q in items:
 if not q.GetBoundingBox().Intersects(localbox):continue
 for l in [p.F_Cu,p.B_Cu]:
  if q.IsOnLayer(l) and geom(sh(q,l)).intersects(eg):near.append(dict(layer=b.GetLayerName(l),**desc(q)))
freeze={'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'new_via_xy_mm':center,'via_diameter_mm':.5,'drill_mm':.25,'track_width_mm':.15,'zone_clearance_mm':.2,'envelope_radius_mm':.45,'allowed_radius_by_layer_mm':{'F.Cu':.4,'In1.Cu':.45,'In2.Cu':.45,'B.Cu':.4},'envelope_construction':'native outside circle radius 250000+200000 nm; 1 nm polygonization; no discretionary enlargement','affected_zones':zone_rows,'retained_outer_conductors_intersecting_envelope':near,'scope':'Qualified-development prototype only; strict baseline remains immutable. Actual drill and rule-derived antipad are declared local transition change, not arbitrary plane-loss allowance. Retained conductor reference outside its own existing transition is mandatory. No candidate exists.'}
(R/'qa/transition-freeze.json').write_text(json.dumps(freeze,indent=2));print('FROZEN',near,flush=True)
# Build actual-shape continuous free-center geometry for one bounded F layer route.
ob=[];goals=[]
routebox=p.BOX2I(V((98.7,22.7)),V((22.6,71.6)))
for q in items:
 if not q.IsOnLayer(p.F_Cu) or not q.GetBoundingBox().Intersects(routebox):continue
 g=geom(sh(q,p.F_Cu))
 if not g.intersects(region.buffer(.3)):continue
 if q.GetNetname()!='MCU_GPIO3':ob.append(g)
 else:goals.append((uid(q),g))
foreign=s.union_all(ob).buffer(.225002,quad_segs=32)
# New transition only plus existing target-net via antipads. No unrelated transition allowance.
windows=[geom(envelope)];target_windows=[]
for q in items:
 if isinstance(q,p.PCB_VIA) and q.GetNetname()=='MCU_GPIO3':
  w=geom(poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(p.F_Cu)//2+200000),True));windows.append(w);target_windows.append(uid(q))
ref=geom(planes[p.In1_Cu]);allowed_ref=s.union_all([ref]+windows).buffer(-.075002,quad_segs=32)
free=region.difference(foreign).intersection(allowed_ref);parts=list(s.get_parts(free));origin=Point(*center)
reach=[g for g in parts if g.covers(origin)];assert len(reach)<=1
result={'source_sha256':freeze['source_sha256'],'region_mm':[99,23,121,94],'layer':'F.Cu','method':'Continuous actual native polygon free-space topology, conservative 0.225002 mm foreign-copper offset and 0.075002 mm reference erosion; no grid. Actual source In1 GND after all-hole cuts. Prospective transition windows declared before topology test. Not native DRC proof.','source_allowed':bool(reach),'free_components':len(parts),'source_component_bbox':list(reach[0].bounds) if reach else None,'target_same_component':[u for u,g in goals if reach and reach[0].intersects(g)],'target_transition_uuids':target_windows,'source_component_area_mm2':reach[0].area if reach else 0}
(R/'qa/qualified-route-topology.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
if reach:
 (R/'qa/reachable-region.wkt').write_text(reach[0].wkt)
# Exact native local topology impact; enumerate every changed-area contour.
planechanges=[]
for l,pl in planes.items():
 after=p.SHAPE_POLY_SET(pl);after.BooleanSubtract(envelope)
 lost=p.SHAPE_POLY_SET(pl);lost.BooleanSubtract(after);cs=[]
 for i in range(lost.OutlineCount()):
  a=p.SHAPE_POLY_SET();a.AddOutline(lost.COutline(i))
  for j in range(lost.HoleCount(i)):a.AddHole(lost.CHole(i,j),0)
  cs.append({'index':i,'area_mm2':a.Area()/1e12,'vertices':a.COutline(0).PointCount()})
 assert abs(sum(x['area_mm2'] for x in cs)-lost.Area()/1e12)<1e-12
 assert all(x['area_mm2']>0 and x['vertices']>=3 for x in cs)
 outside=p.SHAPE_POLY_SET(lost);outside.BooleanSubtract(envelope);assert outside.Area()==0 and outside.OutlineCount()==0
 planechanges.append({'layer':b.GetLayerName(l),'before_positive_contours':pl.OutlineCount(),'after_positive_contours':after.OutlineCount(),'declared_envelope_removed_GND_mm2':lost.Area()/1e12,'removed_contours':cs,'loss_outside_envelope_area_mm2':outside.Area()/1e12,'loss_outside_envelope_contours':outside.OutlineCount(),'note':'Read-only envelope subtraction, not native zone-refill result.'})
witness=[]
if reach:
 for q in items:
  if not q.IsOnLayer(p.F_Cu) or not q.GetBoundingBox().Intersects(routebox) or q.GetNetname()=='MCU_GPIO3':continue
  g=geom(sh(q,p.F_Cu))
  if reach[0].distance(g)<.225004:witness.append(desc(q))
 result['source_component_strictly_inside_search_bounds']=region.boundary.disjoint(reach[0])
 assert result['source_component_strictly_inside_search_bounds']
result['boundary_foreign_copper']=witness
(R/'qa/qualified-route-topology.json').write_text(json.dumps(result,indent=2))
(R/'qa/transition-plane-topology.json').write_text(json.dumps(planechanges,indent=2))
print('planechanges',planechanges,'boundary_witnesses',len(witness),flush=True)
