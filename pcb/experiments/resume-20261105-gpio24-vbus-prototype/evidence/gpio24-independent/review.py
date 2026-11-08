from pathlib import Path
import sys,json,hashlib,collections
sys.path.insert(0,'/workspace/shared/maru60-resume/tools')
from sexpr_spans import children,head,field,replace_child
import pcbnew as p
R=Path('/workspace/shared/maru60-resume');S=R/'header-routing/frozen26b/pcb';C=R/'header-routing/frozen24move/pcb';D=R/'header-independent24move';H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();assert H(S/'maru60.kicad_pcb')=='04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99';assert H(C/'maru60.kicad_pcb')=='2bacda8824b543df9be08628cd8ac14b2ed6628d7ee3e221626b869da74787d4'
A=(S/'maru60.kicad_pcb').read_text();B=(C/'maru60.kicad_pcb').read_text();norm=lambda t:' '.join(t.split());obj=lambda s:{norm(field(t,'uuid')):t for _,_,t in children(s)if field(t,'uuid')and head(t)!='zone'};aa=obj(A);bb=obj(B);added=set(bb)-set(aa);removed=set(aa)-set(bb);changed=[k for k in aa.keys()&bb.keys()if norm(aa[k])!=norm(bb[k])];assert len(added)==8 and not removed and len(changed)==1;assert '976a7de4-489f-4261-a64f-3551037e01df' in changed[0];assert norm(replace_child(aa[changed[0]],'at','(at 97.25 37.45)'))==norm(bb[changed[0]])
build=json.loads((R/'header-routing/qa24move/BUILD.json').read_text());assert {k.split('"')[1]for k in added}==set(build['added_uuids'])
zoneconf=lambda s:[[norm(tt)for _,_,tt in children(t)if head(tt)not in('filled_polygon','fill_segments')]for _,_,t in children(s)if head(t)=='zone'];assert zoneconf(A)==zoneconf(B)
companions={str(q.relative_to(S)):H(q)==H(C/q.relative_to(S))for q in S.rglob('*')if q.is_file()and q.name!='maru60.kicad_pcb'};assert len(companions)==57 and all(companions.values())
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
ab,ai,ah,ap=capture(S/'maru60.kicad_pcb');cb,ci,ch,cp=capture(C/'maru60.kicad_pcb');move=window(97.25,37.45);route=window(92.35,37.75);route.BooleanAdd(window(105.8,37.5));allwin=p.SHAPE_POLY_SET(route);allwin.BooleanAdd(move);rows=[]
for l in ap:
 loss=sub(ap[l],cp[l]);gain=sub(cp[l],ap[l]);outside=sub(loss,allwin);hits=[]
 for x in ai:
  if x.GetNetname()in('','GND')or not x.GetBoundingBox().Intersects(loss.BBox()):continue
  for sl in(p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu):
   if not x.IsOnLayer(sl):continue
   shape=p.SHAPE_CIRCLE(x.GetPosition(),x.GetWidth(sl)//2)if isinstance(x,p.PCB_VIA)else x.GetEffectiveShape(sl);hit=inter(loss,sub(poly(shape),ah))
   if hit.Area()!=0 or hit.OutlineCount()!=0:
    out=sub(hit,move);row={'uuid':x.m_Uuid.AsString(),'net':x.GetNetname(),'layer':ab.GetLayerName(sl),'loss_mm2':hit.Area()/1e12,'outside_modified_transition_mm2':out.Area()/1e12,'outside_outlines':out.OutlineCount()};row['integer_nm_contours']=[[(hit.COutline(j).CPoint(i).x,hit.COutline(j).CPoint(i).y)for i in range(hit.COutline(j).PointCount())]for j in range(hit.OutlineCount())];hits.append(row)
 rows.append({'plane':cb.GetLayerName(l),'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12,'outside_new_and_moved_via_windows_mm2':outside.Area()/1e12,'outside_outlines':outside.OutlineCount(),'old_components':ap[l].OutlineCount(),'new_components':cp[l].OutlineCount(),'old_projection_changes':hits});assert ap[l].OutlineCount()==cp[l].OutlineCount()==1
newtrackrefs=[];affected=[]
for x in ci:
 if isinstance(x,p.PCB_VIA)or not isinstance(x,p.PCB_TRACK):continue
 if x.m_Uuid.AsString()in build['added_uuids']:disks=route;dest=newtrackrefs
 elif x.GetNetname()=='EXT_GPIO3':disks=move;dest=affected
 else:continue
 l=x.GetLayer();ref=p.In1_Cu if l==p.F_Cu else p.In2_Cu;cu=sub(poly(x.GetEffectiveShape(l)),ch);uncovered=sub(cu,cp[ref]);out=sub(uncovered,disks)
 if dest is affected:
  # Existing unrelated gaps are not new failures: inspect added lack of reference versus source.
  old=next(q for q in ai if q.m_Uuid.AsString()==x.m_Uuid.AsString());oldcu=sub(poly(old.GetEffectiveShape(l)),ah);oldu=sub(oldcu,ap[ref]);newlack=sub(uncovered,oldu);out=sub(newlack,disks)
 dest.append({'uuid':x.m_Uuid.AsString(),'net':x.GetNetname(),'layer':cb.GetLayerName(l),'nearest_reference':cb.GetLayerName(ref),'uncovered_mm2':uncovered.Area()/1e12,'new_uncovered_outside_own_transition_windows_mm2':out.Area()/1e12,'outside_outlines':out.OutlineCount()})
result={'status':'HOLD pending classification of explicit tiny native Boolean differences; no tolerance waiver','source_sha256':H(S/'maru60.kicad_pcb'),'candidate_sha256':H(C/'maru60.kicad_pcb'),'raw_scope':{'added_items':8,'changed_old_items':changed,'all_other_uuid_objects_exact':True,'zone_config_exact':True,'all57_companions_exact':True},'planes':rows,'new_track_reference':newtrackrefs,'modified_net_reference':affected,'limits':'Nominal geometry only.0.455mm transition windows are explicit; neither SI/EMI nor physical current distribution is qualified. Via relocation intentionally changes EXT_GPIO3 transition geometry.'};(D/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
