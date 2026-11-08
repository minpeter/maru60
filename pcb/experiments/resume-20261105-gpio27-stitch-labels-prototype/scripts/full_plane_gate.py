from pathlib import Path
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume/continuation-c782/header');S=Path('/workspace/shared/maru60-resume/combined-trial/pcb');C=R.parent/'combined27fix2/pcb';D=R/'qa';H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();build=json.loads((D/'BUILD.json').read_text());build['added_uuids'].append('adb09d04-e93c-4f35-bbef-200d2bb1eb64')
def poly(shape):
 q=p.SHAPE_POLY_SET();shape.TransformToPolygon(q,1,p.ERROR_OUTSIDE);q.Simplify();return q
def sub(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def inter(a,b):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,b);return q
def window(x,y):return poly(p.SHAPE_CIRCLE(p.VECTOR2I(round(x*1e6),round(y*1e6)),455000))
def capture(path):
 b=p.LoadBoard(str(path));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];holes=p.SHAPE_POLY_SET();planes={l:p.SHAPE_POLY_SET()for l in(p.In1_Cu,p.In2_Cu)}
 for x in items:
  if isinstance(x,(p.PAD,p.PCB_VIA))and x.HasHole():holes.Append(poly(x.GetEffectiveHoleShape()))
 holes.Simplify()
 for z in b.Zones():
  if z.GetIsRuleArea()or z.GetNetname()!='GND':continue
  for l in planes:
   if z.IsOnLayer(l):planes[l].BooleanAdd(p.SHAPE_POLY_SET(z.GetFilledPolysList(l)))
 for l in planes:planes[l].BooleanSubtract(holes)
 return b,items,holes,planes
ab,ai,ah,ap=capture(S/'maru60.kicad_pcb');cb,ci,ch,cp=capture(C/'maru60.kicad_pcb');move=window(96.65,41.625);route=window(96.925,40.175);route.BooleanAdd(window(92.9,42.5));allwin=p.SHAPE_POLY_SET(route);allwin.BooleanAdd(move);allwin.BooleanAdd(poly(p.SHAPE_CIRCLE(p.VECTOR2I(105650000,36050000),125000)));rows=[]
for l in ap:
 loss=sub(ap[l],cp[l]);gain=sub(cp[l],ap[l]);outside=sub(loss,allwin);hits=[]
 for x in ai:
  if x.GetNetname()in('','GND')or not x.GetBoundingBox().Intersects(loss.BBox()):continue
  for sl in(p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu):
   if not x.IsOnLayer(sl):continue
   shape=p.SHAPE_CIRCLE(x.GetPosition(),x.GetWidth(sl)//2)if isinstance(x,p.PCB_VIA)else x.GetEffectiveShape(sl);hit=inter(loss,sub(poly(shape),ah))
   if hit.Area()!=0 or hit.OutlineCount()!=0:
    out=sub(hit,move);row={'uuid':x.m_Uuid.AsString(),'net':x.GetNetname(),'layer':ab.GetLayerName(sl),'loss_mm2':hit.Area()/1e12,'outside_modified_transition_mm2':out.Area()/1e12,'declared_old_object_changed':x.m_Uuid.AsString()in build['modified_source_uuids'],'outside_outlines':out.OutlineCount()};row['integer_nm_contours']=[[(hit.COutline(j).CPoint(i).x,hit.COutline(j).CPoint(i).y)for i in range(hit.COutline(j).PointCount())]for j in range(hit.OutlineCount())];hits.append(row)
 rows.append({'plane':cb.GetLayerName(l),'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12,'outside_new_and_moved_via_windows_mm2':outside.Area()/1e12,'outside_outlines':outside.OutlineCount(),'old_components':ap[l].OutlineCount(),'new_components':cp[l].OutlineCount(),'old_projection_changes':hits});assert ap[l].OutlineCount()==cp[l].OutlineCount()==1
newtrackrefs=[];affected=[]
for x in ci:
 if isinstance(x,p.PCB_VIA)or not isinstance(x,p.PCB_TRACK):continue
 if x.m_Uuid.AsString()in build['added_uuids']:
  disks=route if x.GetNetname()=='EXT_GPIO27'else move if x.GetNetname()=='EXT_GPIO26'else p.SHAPE_POLY_SET();dest=newtrackrefs
 elif x.GetNetname()in('EXT_GPIO26','EXT_GPIO10'):disks=move if x.GetNetname()=='EXT_GPIO26'else p.SHAPE_POLY_SET();dest=affected
 else:continue
 l=x.GetLayer();ref=p.In1_Cu if l==p.F_Cu else p.In2_Cu;cu=sub(poly(x.GetEffectiveShape(l)),ch);uncovered=sub(cu,cp[ref]);out=sub(uncovered,disks)
 if dest is affected:
  # Existing unrelated gaps are not new failures: inspect added lack of reference versus source.
  old=next(q for q in ai if q.m_Uuid.AsString()==x.m_Uuid.AsString());oldcu=sub(poly(old.GetEffectiveShape(l)),ah);oldu=sub(oldcu,ap[ref]);newlack=sub(uncovered,oldu);out=sub(newlack,disks)
 dest.append({'uuid':x.m_Uuid.AsString(),'net':x.GetNetname(),'layer':cb.GetLayerName(l),'nearest_reference':cb.GetLayerName(ref),'uncovered_mm2':uncovered.Area()/1e12,'new_uncovered_outside_own_transition_windows_mm2':out.Area()/1e12,'outside_outlines':out.OutlineCount()})
result={'status':'UNSELECTED full-board diagnostics; no tolerance waiver','source_sha256':H(S/'maru60.kicad_pcb'),'candidate_sha256':H(C/'maru60.kicad_pcb'),'planes':rows,'new_track_reference':newtrackrefs,'modified_net_reference':affected,'limits':'Nominal geometry only; changed old objects and retired copper explicitly declared. Source projection differences cover full board. No SI/EMI or hardware qualification.'};(R.parent/'combined27fix2/qa/full-plane-review.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

assert all(r['outside_new_and_moved_via_windows_mm2']==0 and r['outside_outlines']==0 for r in rows)
assert all(r['new_uncovered_outside_own_transition_windows_mm2']==0 and r['outside_outlines']==0 for r in newtrackrefs+affected)
assert all(x['declared_old_object_changed'] for r in rows for x in r['old_projection_changes'])
print('PASS: machine-gated all new and affected route reference checks, with unchanged transition windows.')
