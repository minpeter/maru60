from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu')
s=(R/'scripts/audit_north_return_b_c.py').read_text().split("print('Capture source planes")[0];exec(s)
base,old,_,oh=capture(S,False);b,new,_,nh=capture(B,False);env=p.SHAPE_POLY_SET()
for xy in [(112.175,76.3),(112.16,77.0)]:env.Append(poly(p.SHAPE_CIRCLE(p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6)),455000),True))
env.Simplify();rows=[]
def rect(bb):
 z=p.SHAPE_POLY_SET();z.NewOutline()
 for x,y in [(bb[0],bb[1]),(bb[2],bb[1]),(bb[2],bb[3]),(bb[0],bb[3])]:z.Append(round(x*1e6),round(y*1e6))
 return z
def areas(q):
 out=[]
 for i in range(q.OutlineCount()):
  z=p.SHAPE_POLY_SET();z.AddOutline(q.COutline(i))
  for h in range(q.HoleCount(i)):z.AddHole(q.CHole(i,h),0)
  if z.Area()>0:out.append(z.Area()/1e12)
 return sorted(out)
for l in old:
 loss=delta(old[l],new[l]);outside=delta(loss,env);restored=p.SHAPE_POLY_SET(new[l]);restored.Append(outside);restored.Simplify();parts=[]
 for i in range(outside.OutlineCount()):
  q=p.SHAPE_POLY_SET();q.AddOutline(outside.COutline(i))
  for k in range(outside.HoleCount(i)):q.AddHole(outside.CHole(i,k),0)
  bb=q.BBox();parts.append({'area_mm2':q.Area()/1e12,'bbox_mm':[bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6]})
 boxes=[]
 for bb in [[111,75,113.1,77.9],[110.5,74.5,113.6,78.4],[110,74,114.1,78.9]]:
  a=inter(new[l],rect(bb));c=inter(restored,rect(bb));boxes.append({'box_mm':bb,'candidate_component_areas_mm2':areas(a),'candidate_with_only_outside_loss_restored_component_areas_mm2':areas(c)})
 rows.append({'plane':b.GetLayerName(l),'loss_outside_envelope_parts':parts,'local_clips':boxes,'global_candidate_components':new[l].OutlineCount(),'global_after_outside_loss_restoration_components':restored.OutlineCount()})
gnds=[q for q in b.GetTracks() if isinstance(q,p.PCB_VIA) and q.GetNetname()=='GND'];near=[]
for label,xy in [('relocated_COL5',[112.175,76.3]),('MCU_GPIO27',[112.16,77.0])]:
 ns=sorted([{'uuid':uid(q),'pos_mm':[q.GetPosition().x/1e6,q.GetPosition().y/1e6],'center_distance_mm':((q.GetPosition().x/1e6-xy[0])**2+(q.GetPosition().y/1e6-xy[1])**2)**.5} for q in gnds],key=lambda v:v['center_distance_mm'])[:4];near.append({'signal_transition':label,'pos_mm':xy,'nearest_existing_GND_vias':ns})
r={'source_sha256':h(S),'candidate_sha256':h(B),'plane_rows':rows,'nearest_GND_transition_geometry':near,'limits':'Local clipping changes connectivity at the artificial box boundary; component-count changes are diagnostic of a local corridor, not a global plane split or SI proof. Restoring outside loss is analytical only; no CAD changes.'};(R/'qa/repair-D-local-neck.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
