from check_counterfactual_v4 import *
# This file constructs only native geometry objects in memory, not a BOARD candidate.
# Source PCB is read-only; no BOARD object or source item is mutated.
result={'source':str(BP),'source_sha256':sha(BP),'status':'analytical V4 only, expanded UVLO contract review required'}
retired=ret|set(path);moved=capids|rids
local=[q for q in obs if q.IsOnLayer(p.B_Cu) and q.GetBoundingBox().Intersects(p.BOX2I(vec([10,14]),vec([14,11])))]
pc={uid(q):copper(q,p.B_Cu) for q in local}
label={uid(q):(q.GetParentFootprint().GetReference()+'.'+q.GetNumber() if isinstance(q,p.PAD) else q.GetNetname()+(' via' if isinstance(q,p.PCB_VIA) else ' track'))for q in local}
def rec(q):
 r={'uuid':uid(q),'label':label.get(uid(q),''),'net':q.GetNetname(),'type':type(q).__name__,'layers':[b.GetLayerName(l)for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]if q.IsOnLayer(l)]}
 if isinstance(q,p.PAD):r.update(at=[q.GetPosition().x/1e6,q.GetPosition().y/1e6],size=[q.GetSize().x/1e6,q.GetSize().y/1e6])
 elif isinstance(q,p.PCB_VIA):r.update(at=[q.GetPosition().x/1e6,q.GetPosition().y/1e6],drill=q.GetDrillValue()/1e6,diameter=q.GetWidth(p.B_Cu)/1e6)
 else:r.update(start=[q.GetStart().x/1e6,q.GetStart().y/1e6],end=[q.GetEnd().x/1e6,q.GetEnd().y/1e6],width=q.GetWidth()/1e6,length=q.GetLength()/1e6)
 return r
result['retired_tracks']=[rec(idx[u])for u in sorted(retired)]
result['old_moved_pads']=[rec(idx[u])for u in sorted(moved)]
oldedges=[]
for i,q in enumerate(local):
 for z in local[i+1:]:
  if q.GetNetname()!=z.GetNetname():continue
  a=cross(pc[uid(q)],pc[uid(z)]).Area()/1e12
  if a>0:oldedges.append({'a':uid(q),'b':uid(z),'a_label':label[uid(q)],'b_label':label[uid(z)],'net':q.GetNetname(),'area_mm2':a})
result['old_contact_retirements']=[e for e in oldedges if e['a']in(retired|moved)or e['b']in(retired|moved)]
result['old_affected_contact_count']=len(result['old_contact_retirements'])
newedges=[]
for n,nt,s in new:
 for q in local:
  if uid(q)in(retired|moved)or q.GetNetname()!=nt:continue
  a=cross(s,pc[uid(q)]).Area()/1e12
  if a>0:newedges.append({'new':n,'old':uid(q),'old_label':label[uid(q)],'net':nt,'area_mm2':a})
result['new_to_retained_contacts']=newedges
result['new_to_new_contacts']=[dict(a=n,b=nn,net=nt,area_mm2=cross(s,ss).Area()/1e12)for i,(n,nt,s)in enumerate(new)for nn,nnt,ss in new[i+1:]if nt==nnt and cross(s,ss).Area()>0]
# Original C124 ground-pad support: both support intersections must be covered by the two-track bridge.
oldcpad=pc['f79380d7-c89c-4396-b53e-4918d8902c13']
result['ground_bridge_support']=[]
for u in ['19181a2b-164e-4055-9004-2860bebe32f4','763086b7-5549-4f5e-bb08-ce25387b3627']:
 support=cross(oldcpad,pc[u]);deficit=p.SHAPE_POLY_SET(support);deficit.BooleanSubtract(compact)
 result['ground_bridge_support'].append(dict(old_contact=u,old_area_mm2=support.Area()/1e12,not_covered_mm2=deficit.Area()/1e12,old_support=dump(support)))
# Preserve direct six-object component, replacing the old pad support as explicitly listed.
six=['f79380d7-c89c-4396-b53e-4918d8902c13','19181a2b-164e-4055-9004-2860bebe32f4','efadf2be-e519-469f-a84c-2e7cbb60672a','763086b7-5549-4f5e-bb08-ce25387b3627','abcd4fb1-881b-43f9-906e-39d93366692e','437d8abf-8e4f-4587-99b7-93c610dd4000']
result['six_object_component']=[rec(idx[u])for u in six]
result['six_object_contacts']=[e for e in oldedges if e['a']in six and e['b']in six]
# Primary source-drill and plane roots, using filled plane copper minus physical holes.
planes={};zoneids={}
for l in [p.In1_Cu,p.In2_Cu]:
 v=p.SHAPE_POLY_SET();ids=[]
 for z in b.Zones():
  if z.GetNetname()=='GND'and z.IsOnLayer(l):v.BooleanAdd(z.GetFilledPolysList(l));ids.append(uid(z))
 planes[l]=v;zoneids[l]=ids
result['plane_roots']=[]
for u in ['efadf2be-e519-469f-a84c-2e7cbb60672a','763086b7-5549-4f5e-bb08-ce25387b3627','8e0fa85d-f2bc-543d-aae7-d8f6ff75061a']:
 q=idx[u]
 for l in planes:
  result['plane_roots'].append(dict(uuid=u,layer=b.GetLayerName(l),zone_uuids=zoneids[l],physical_annulus_contact_mm2=cross(copper(q,l),planes[l]).Area()/1e12))
# Signal projection coverage of source fill with all physical drills removed.
for l in planes:
 for q in obs:
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()and q.IsOnLayer(l):planes[l].BooleanSubtract(poly(q.GetEffectiveHoleShape(),p.ERROR_OUTSIDE))
result['new_reference_coverage']=[]
for n,nt,s in new:
 if nt=='GND':continue
 for l,v in planes.items():
  loss=p.SHAPE_POLY_SET(s);loss.BooleanSubtract(v)
  result['new_reference_coverage'].append(dict(name=n,net=nt,layer=b.GetLayerName(l),uncovered_mm2=loss.Area()/1e12,uncovered_polygon=dump(loss)))
# Check all physical drill-to-new copper (including same-net holes), no via-in-pad shortcut.
result['new_drill_clearance']=[]
for n,nt,s in new:
 rows=[]
 for q in obs:
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():rows.append(dict(uuid=uid(q),net=q.GetNetname(),gap_mm=s.GetClearance(q.GetEffectiveHoleShape())/1e6))
 result['new_drill_clearance'].append(dict(name=n,nearest=sorted(rows,key=lambda r:r['gap_mm'])[:3]))
result['native_precision']='1 nm inside polygon approximation; positive gaps >>1 nm. Exact full-shape contact/root tests require separate constructed-board replay. No candidate refill performed.'
result['source_after_sha256']=sha(BP)
(D/'counterfactual-v4-contact-reference.json').write_text(json.dumps(result,indent=2))
print('CONTACT_RETIREMENTS',len(result['old_contact_retirements']));print('NEW_OLD',newedges);print('BRIDGE',[(r['old_contact'],r['old_area_mm2'],r['not_covered_mm2'])for r in result['ground_bridge_support']]);print('ROOTS',result['plane_roots']);print('NEW_REFERENCE_DEFICITS',[(r['name'],r['layer'],r['uncovered_mm2'])for r in result['new_reference_coverage']if r['uncovered_mm2']>0]);print('DONE_SOURCE_UNCHANGED',result['source_after_sha256'])
