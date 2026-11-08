exec(open('/workspace/shared/maru60-resume/continuation-9d787/mcu-gpio3/scripts/assess.py').read().split('rows=[]')[0])
from shapely.geometry import Point
report=json.loads((R/'qa/second-transition.json').read_text());rows=[];first=poly(p.SHAPE_CIRCLE(V((112.6,84)),450000),True);first_hole=geom(poly(p.SHAPE_CIRCLE(V((112.6,84)),125000),True))
for rr in report['B_reach_results']:
 pos=rr['xy_mm'];env=poly(p.SHAPE_CIRCLE(V(pos),450000),True);dr=geom(poly(p.SHAPE_CIRCLE(V(pos),125000),True));dh=dr.distance(geom(holes));df=dr.distance(first_hole)
 envboth=p.SHAPE_POLY_SET(first);envboth.Append(env);envboth.Simplify();planes_result=[]
 for l,pl in planes.items():
  after=p.SHAPE_POLY_SET(pl);after.BooleanSubtract(envboth);lost=p.SHAPE_POLY_SET(pl);lost.BooleanSubtract(after);outside=p.SHAPE_POLY_SET(lost);outside.BooleanSubtract(envboth)
  cs=[]
  for i in range(lost.OutlineCount()):
   a=p.SHAPE_POLY_SET();a.AddOutline(lost.COutline(i))
   for j in range(lost.HoleCount(i)):a.AddHole(lost.CHole(i,j),0)
   cs.append({'index':i,'area_mm2':a.Area()/1e12,'vertices':a.COutline(0).PointCount()})
  assert abs(sum(x['area_mm2'] for x in cs)-lost.Area()/1e12)<1e-12
  assert all(x['area_mm2']>0 and x['vertices']>=3 for x in cs)
  assert outside.Area()==0 and outside.OutlineCount()==0
  planes_result.append({'layer':b.GetLayerName(l),'before_contours':pl.OutlineCount(),'after_contours':after.OutlineCount(),'removed_area_mm2':lost.Area()/1e12,'removed_contours':cs,'outside_envelopes_area_mm2':0,'outside_envelopes_contours':0})
 rows.append({'xy_mm':pos,'minimum_drill_edge_clearance_existing_holes_mm':dh,'drill_edge_clearance_first_via_mm':df,'hole_clearance_pass':min(dh,df)>=.15,'plane_rows':planes_result,'prospective_plane_no_split_pass':all(x['before_contours']==x['after_contours'] for x in planes_result),'limits':'Prospective envelope subtraction is not actual refill. Both possible inner antipads are declared; no remote allowance.'})
report2={'source_sha256':report['source_sha256'],'rows':rows,'qualified_escape_sites':[x['xy_mm'] for x in rows if x['hole_clearance_pass'] and x['prospective_plane_no_split_pass']],'via_geometry_mm':{'copper_diameter':.5,'drill':.25,'minimum_copper_clearance':.15,'minimum_hole_clearance':.15,'inner_antipad_radius':.45,'outer_antipad_radius':.4}}
(R/'qa/second-transition-audit.json').write_text(json.dumps(report2,indent=2));print(json.dumps(report2,indent=2))
