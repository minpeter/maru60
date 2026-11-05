exec(open('/workspace/shared/maru60-resume/continuation-9d787/mcu-gpio3/scripts/assess.py').read().split('rows=[]')[0])
from shapely.geometry import Point,box
import numpy as np
pocket=s.from_wkt((R/'qa/second-B-113.2-82.9.wkt').read_text()); bbox=p.BOX2I(V((107.5,81)),V((7,5.5)))
# Polygonization is native; bounding boxes only prune shapes outside the entire site scan.
obj=[]
for q in items:
 if not q.GetBoundingBox().Intersects(bbox):continue
 gs={l:geom(sh(q,l)) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu] if q.IsOnLayer(l)}
 obj.append((q,gs))
obs=s.union_all([g for q,gs in obj if q.GetNetname()!='MCU_GPIO3' for g in gs.values()])
outer=s.union_all([g for q,gs in obj for l,g in gs.items() if l in [p.F_Cu,p.B_Cu]])
# Existing retained copper must not lose any reference beneath it. Deliberately conservative:
# no new envelope may touch any retained outer conductor, even within its old via window.
via_forbidden=obs.buffer(.400002,quad_segs=32)
retained_forbidden=outer.buffer(.450002,quad_segs=32)
xs=np.arange(108.2,113.801,.1);ys=np.arange(81.6,85.801,.1)
rows=[];legal=[]
old_samples={tuple(x['xy_mm']) for x in json.loads((R/'qa/third-north-only.json').read_text())['site_rows']}
hg=geom(holes)
existing_hole_forbidden=hg.buffer(.275002,quad_segs=32)
for y in ys:
 for x in xs:
  pos=(round(float(x),3),round(float(y),3));pt=Point(*pos)
  if not pocket.covers(pt) or pos in old_samples:continue
  clearance_ok=not existing_hole_forbidden.covers(pt) and not via_forbidden.covers(pt) and all(pt.distance(Point(*v))>=.400002 for v in [(112.6,84),(113.2,82.9)]);retained_ok=not retained_forbidden.covers(pt)
  row={'xy_mm':pos,'all_layer_copper_clearance_pass':clearance_ok,'retained_reference_envelope_pass':retained_ok}
  if clearance_ok and retained_ok:legal.append(pos)
  ds=sorted([(pt.distance(g),q,l) for q,gs in obj for l,g in gs.items() if q.GetNetname()!='MCU_GPIO3'],key=lambda a:a[0]);os=sorted([(pt.distance(g),q,l) for q,gs in obj for l,g in gs.items() if l in [p.F_Cu,p.B_Cu]],key=lambda a:a[0]);row['nearest_copper']=[dict(center_to_copper_mm=d,layer=b.GetLayerName(l),**desc(q)) for d,q,l in ds[:2]];row['nearest_retained_shadow']=[dict(center_to_copper_mm=d,layer=b.GetLayerName(l),**desc(q)) for d,q,l in os[:2]]
  rows.append(row)
print('scanned',len(rows),'legal',len(legal),flush=True)
# B.Cu route geometry: retain actual source In2 GND except specifically declared transitions.
reg=box(99,23,121,94);rbox=p.BOX2I(V((98.7,22.7)),V((22.6,71.6)))
bs=[];goals=[]
for q in items:
 if not q.IsOnLayer(p.F_Cu) or not q.GetBoundingBox().Intersects(rbox):continue
 g=geom(sh(q,p.F_Cu))
 if q.GetNetname()!='MCU_GPIO3':bs.append(g)
 elif not(isinstance(q,p.PAD) and q.GetParentFootprint().GetReference()=='U1'):goals.append((uid(q),g))
foreign=s.union_all(bs).buffer(.225002,quad_segs=32)
ref=geom(planes[p.In1_Cu]);basefree=reg.difference(foreign)
# Per-site allowances, never a union of all candidate antipads.
results=[]
baseparts=list(s.get_parts(basefree.intersection(ref.buffer(-.075002,quad_segs=32))))
# Bounded spatially separated sites, prioritizing northward escape.
selected=[]
remaining=sorted(legal)
while remaining and len(selected)<16:
 pos=remaining[0] if not selected else max(remaining,key=lambda v:min((v[0]-u[0])**2+(v[1]-u[1])**2 for u in selected))
 selected.append(pos);remaining=[v for v in remaining if (pos[0]-v[0])**2+(pos[1]-v[1])**2>=.16]
for i,pos in enumerate(selected):
 env=geom(poly(p.SHAPE_CIRCLE(V(pos),450000),True))
 allowed=s.union_all([ref,env]).buffer(-.075002,quad_segs=32)
 free=basefree.intersection(allowed);pt=Point(*pos);reach=[g for g in s.get_parts(free) if g.covers(pt)]
 rr={'xy_mm':pos,'F_start_allowed':bool(reach),'F_component_bbox':list(reach[0].bounds) if reach else None,'escapes_B_region':bool(reach and not pocket.buffer(.001).covers(reach[0])),'reaches_existing_GPIO3':[u for u,g in goals if reach and reach[0].intersects(g)]}
 rr['base_F_region_ids']=[j for j,g in enumerate(baseparts) if reach and reach[0].intersection(g).area>.000001]
 rr['touches_search_boundary']=bool(reach and reach[0].intersects(reg.boundary))
 rr['drill_edge_clearance_existing_mm']=max(0,pt.distance(hg)-.125)
 rr['drill_edge_clearance_proposed_vias_mm']=[pt.distance(Point(*v))-.25 for v in [(112.6,84),(113.2,82.9)]]
 results.append(rr)
 if rr['escapes_B_region']:(R/'qa'/('third-F-%s-%s.wkt'%pos)).write_text(reach[0].wkt)
 if i%10==0:print(i,rr,flush=True)
report={'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'scan_bounds_mm':[108.2,81.6,113.8,85.8],'scan_step_mm':.1,'scan_count_inside_F_pocket':len(rows),'copper_legal_count':sum(x['all_layer_copper_clearance_pass'] for x in rows),'retained_reference_legal_count':sum(x['retained_reference_envelope_pass'] for x in rows),'legal_second_via_count':len(legal),'site_rows':rows,'selected_site_count':len(selected),'selection':'At most16 spatially distributed farthest-point sites starting west; minimum0.4mm separation; exclude prior40 northern samples','B_reach_results':results,'scope':'Read-only third-transition planning; fixed first(112.6,84.0) and second(113.2,82.9); no candidate. 0.5/0.25 mm second through-via; all-layer copper clearance 0.15 mm; inner envelope radius 0.45 mm. Retained-reference screen conservatively rejects contact with any retained outer conductor. Actual native shapes/all-hole-cut GND. Each B reach has only its own candidate transition allowance, not other trial sites. B reach lacks target-via windows, so negatives at destination are conservative.'}
(R/'qa/third-whole-region.json').write_text(json.dumps(report,indent=2));print('DONE',len(results),'escapes',sum(x['escapes_B_region'] for x in results),'goals',sum(bool(x['reaches_existing_GPIO3']) for x in results),flush=True)
