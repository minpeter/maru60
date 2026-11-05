exec(open('/workspace/shared/maru60-resume/continuation-9d787/mcu-gpio3/scripts/assess.py').read().split('rows=[]')[0])
from shapely.geometry import Point,box
import numpy as np
pocket=s.from_wkt((R/'qa/reachable-region.wkt').read_text()); bbox=p.BOX2I(V((111,81)),V((10,10)))
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
xs=np.arange(112.2,119.801,.1);ys=np.arange(82.4,89.201,.1)
rows=[];legal=[]
for y in ys:
 for x in xs:
  pos=(round(float(x),3),round(float(y),3));pt=Point(*pos)
  if not pocket.covers(pt):continue
  clearance_ok=not via_forbidden.covers(pt);retained_ok=not retained_forbidden.covers(pt)
  row={'xy_mm':pos,'all_layer_copper_clearance_pass':clearance_ok,'retained_reference_envelope_pass':retained_ok}
  if clearance_ok and retained_ok:legal.append(pos)
  rows.append(row)
print('scanned',len(rows),'legal',len(legal),flush=True)
# B.Cu route geometry: retain actual source In2 GND except specifically declared transitions.
reg=box(99,23,121,94);rbox=p.BOX2I(V((98.7,22.7)),V((22.6,71.6)))
bs=[];goals=[]
for q in items:
 if not q.IsOnLayer(p.B_Cu) or not q.GetBoundingBox().Intersects(rbox):continue
 g=geom(sh(q,p.B_Cu))
 if q.GetNetname()!='MCU_GPIO3':bs.append(g)
 elif not(isinstance(q,p.PAD) and q.GetParentFootprint().GetReference()=='U1'):goals.append((uid(q),g))
foreign=s.union_all(bs).buffer(.225002,quad_segs=32)
ref=geom(planes[p.In2_Cu]);basefree=reg.difference(foreign)
# Per-site allowances, never a union of all candidate antipads.
results=[]
# Bounded spatially separated sites, prioritizing northward escape.
selected=[]
for pos in sorted(legal,key=lambda a:(a[1],a[0])):
 if all((pos[0]-v[0])**2+(pos[1]-v[1])**2>=.64 for v in selected):selected.append(pos)
 if len(selected)==12:break
for i,pos in enumerate(selected):
 env=geom(poly(p.SHAPE_CIRCLE(V(pos),450000),True))
 allowed=s.union_all([ref,env]).buffer(-.075002,quad_segs=32)
 free=basefree.intersection(allowed);pt=Point(*pos);reach=[g for g in s.get_parts(free) if g.covers(pt)]
 rr={'xy_mm':pos,'B_start_allowed':bool(reach),'B_component_bbox':list(reach[0].bounds) if reach else None,'escapes_F_pocket':bool(reach and not pocket.buffer(.001).covers(reach[0])),'reaches_existing_GPIO3':[u for u,g in goals if reach and reach[0].intersects(g)]}
 results.append(rr)
 if rr['escapes_F_pocket']:(R/'qa'/('second-B-%s-%s.wkt'%pos)).write_text(reach[0].wkt)
 if i%10==0:print(i,rr,flush=True)
report={'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'scan_bounds_mm':[112.2,82.4,119.8,89.2],'scan_step_mm':.1,'scan_count_inside_F_pocket':len(rows),'copper_legal_count':sum(x['all_layer_copper_clearance_pass'] for x in rows),'retained_reference_legal_count':sum(x['retained_reference_envelope_pass'] for x in rows),'legal_second_via_count':len(legal),'site_rows':rows,'selected_site_count':len(selected),'selection':'At most twelve sites in north-first order, at least0.8mm apart','B_reach_results':results,'scope':'Read-only two-transition planning; no candidate. 0.5/0.25 mm second through-via; all-layer copper clearance 0.15 mm; inner envelope radius 0.45 mm. Retained-reference screen conservatively rejects contact with any retained outer conductor. Actual native shapes/all-hole-cut GND. Each B reach has only its own candidate transition allowance, not other trial sites. B reach lacks target-via windows, so negatives at destination are conservative.'}
(R/'qa/second-transition.json').write_text(json.dumps(report,indent=2));print('DONE',len(results),'escapes',sum(x['escapes_F_pocket'] for x in results),'goals',sum(bool(x['reaches_existing_GPIO3']) for x in results),flush=True)
