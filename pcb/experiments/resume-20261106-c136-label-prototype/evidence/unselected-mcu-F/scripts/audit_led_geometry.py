from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu-led-repair');exec((R/'scripts/audit_north_return_b_c.py').read_text().split("print('Capture source planes")[0]);a,op,_,oh=capture(S,False);b,np,_,nh=capture(B,False);ai={uid(q):q for q in a.GetTracks()};bi={uid(q):q for q in b.GetTracks()};ledids=[r['uuid'] for r in build['modified'] if r['net']=='LED_FAULT_N'];assert len(ledids)==4
# Material unions use inward 1 nm polygons and subtract every physical drill.
def union(idx,holes):
 z=p.SHAPE_POLY_SET()
 for u in ledids:z.Append(poly(idx[u].GetEffectiveShape(p.F_Cu),False))
 z.Simplify();z.BooleanSubtract(holes);return z
og=union(ai,oh);ng=union(bi,nh);assessment=json.load(open(R/'qa/read-only-assessment.json'));edges=set()
for row in assessment['original_contact_inventory']:
 for q in row['original_contacts']:edges.add(tuple(sorted([row['uuid'],q['uuid']])))
contacts=[]
for u,v in sorted(edges):
 def contact(idx,holes):
  x=delta(poly(idx[u].GetEffectiveShape(p.F_Cu),False),holes);y=delta(poly(idx[v].GetEffectiveShape(p.F_Cu),False),holes);z=inter(x,y);x.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);y.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);return z,inter(x,y).Area()/1e12
 old,oldguard=contact(ai,oh);new,newguard=contact(bi,nh);contacts.append({'uuids':[u,v],'source_overlap_mm2':old.Area()/1e12,'candidate_overlap_mm2':new.Area()/1e12,'lost_old_patch_mm2':delta(old,new).Area()/1e12,'source_2nm_guarded_overlap_mm2':oldguard,'candidate_2nm_guarded_overlap_mm2':newguard,'both_changed':u in ledids and v in ledids})
terminals=[]
for label,u,pt in [('upper','a67d3a82-3f3e-44c8-8014-bf320a87c984',[110.9,75.35]),('lower','c764e55b-1599-4838-894f-3fe4f3bca590',[110.7,76.149999])]:
 x=delta(poly(ai[u].GetEffectiveShape(p.F_Cu),False),oh);old=inter(og,x);new=inter(ng,x);v=p.SHAPE_POLY_SET(ng);v.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);x.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);guard=inter(v,x).Area()/1e12
 terminals.append({'terminal':label,'unchanged_neighbor_uuid':u,'fixed_endpoint_mm':pt,'source_contact_mm2':old.Area()/1e12,'candidate_contact_mm2':new.Area()/1e12,'lost_original_contact_patch_mm2':delta(old,new).Area()/1e12,'candidate_2nm_guarded_positive_overlap_mm2':guard,'same_net':ai[u].GetNetname()==bi[u].GetNetname()=='LED_FAULT_N'});assert guard>0
oldlen=sum(ai[u].GetLength()/1e6 for u in ledids);newlen=sum(bi[u].GetLength()/1e6 for u in ledids)
r={'source_sha256':h(S),'candidate_sha256':h(B),'modified_LED_UUIDs':ledids,'source_length_mm':oldlen,'candidate_length_mm':newlen,'length_delta_mm':newlen-oldlen,'widths_mm':[bi[u].GetWidth()/1e6 for u in ledids],'removed_physical_copper_mm2':delta(og,ng).Area()/1e12,'added_physical_copper_mm2':delta(ng,og).Area()/1e12,'original_incident_contacts':contacts,'terminals':terminals,'limits':'Intentional local same-net contact patches can change or retire when the source geometry is refactored. Full pad partitions and absence of unrelated changes are independently checked in the material graph. Positive terminal contact is not a claim of identical patch area or signal integrity.'};(R/'qa/candidate-F-led-geometry.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
# Full-board physical filled-zone changes on all copper layers, with every through-hole removed.
rows=[]
for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
 for za in a.Zones():
  if za.GetIsRuleArea() or not za.IsOnLayer(l):continue
  zb=next(z for z in b.Zones() if uid(z)==uid(za));old=delta(za.GetFilledPolysList(l),oh);new=delta(zb.GetFilledPolysList(l),nh);loss=delta(old,new);gain=delta(new,old);rows.append({'uuid':uid(za),'net':za.GetNetname(),'layer':a.GetLayerName(l),'source_components':old.OutlineCount(),'candidate_components':new.OutlineCount(),'source_area_mm2':old.Area()/1e12,'candidate_area_mm2':new.Area()/1e12,'lost_mm2':loss.Area()/1e12,'gained_mm2':gain.Area()/1e12})
(R/'qa/candidate-F-all-zone-changes.json').write_text(json.dumps({'source_sha256':h(S),'candidate_sha256':h(B),'zones':rows,'method':'Native actual filled zones with every physical through-hole subtracted; no Unfracture. Global counts do not establish local web adequacy.','limits':'Full-board physical copper changes, not SI/current distribution.'},indent=2))
