from pathlib import Path
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume');S=R/'baseline-validation/pcb/maru60.kicad_pcb';C=R/'header-routing/frozen26b/pcb/maru60.kicad_pcb';O=R/'header-independent26b'
H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();assert H(S)=='2b5787cc27e7fea92dff2ad483185fccfab1d2d27bf07662395de26f7ab14d69';assert H(C)=='04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99'
def polygon(shape,out=True):
 q=p.SHAPE_POLY_SET();shape.TransformToPolygon(q,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);q.Simplify();return q
def sub(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def intersection(a,b):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,b);return q
# Capture independent unions for all ground zones on each plane, retaining holes.
def capture(path):
 b=p.LoadBoard(str(path));items=list(b.GetTracks())+[x for f in b.GetFootprints() for x in f.Pads()];holes=p.SHAPE_POLY_SET();planes={l:p.SHAPE_POLY_SET() for l in (p.In1_Cu,p.In2_Cu)}
 for x in items:
  if isinstance(x,(p.PAD,p.PCB_VIA)) and x.HasHole():holes.Append(polygon(x.GetEffectiveHoleShape()))
 holes.Simplify()
 for z in b.Zones():
  if z.GetIsRuleArea() or z.GetNetname()!='GND':continue
  for l in planes:
   if z.IsOnLayer(l):planes[l].BooleanAdd(p.SHAPE_POLY_SET(z.GetFilledPolysList(l)))
 for l in planes:planes[l].BooleanSubtract(holes)
 return b,items,planes,holes
sb,si,sp,sh=capture(S);cb,ci,cp,ch=capture(C);v=p.VECTOR2I(95075000,40175000);window=polygon(p.SHAPE_CIRCLE(v,455000));existing=polygon(p.SHAPE_CIRCLE(p.VECTOR2I(96800000,41775000),455000));transition=p.SHAPE_POLY_SET(window);transition.BooleanAdd(existing);rows=[]
for l in sp:
 loss=sub(sp[l],cp[l]);gain=sub(cp[l],sp[l]);outside=sub(loss,window);old_losses=[]
 for x in si:
  if x.GetNetname() in ('','GND') or not x.GetBoundingBox().Intersects(loss.BBox()):continue
  for sl in (p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu):
   if not x.IsOnLayer(sl):continue
   shape=p.SHAPE_CIRCLE(x.GetPosition(),x.GetWidth(sl)//2) if isinstance(x,p.PCB_VIA) else x.GetEffectiveShape(sl)
   metal=sub(polygon(shape),sh);overlap=intersection(loss,metal)
   if overlap.Area()!=0 or overlap.OutlineCount()!=0:old_losses.append({'uuid':x.m_Uuid.AsString(),'net':x.GetNetname(),'layer':sb.GetLayerName(sl),'area_mm2':overlap.Area()/1e12})
 rows.append({'plane':cb.GetLayerName(l),'old_components':sp[l].OutlineCount(),'new_components':cp[l].OutlineCount(),'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12,'loss_outside_declared_via_window_mm2':outside.Area()/1e12,'loss_outside_declared_via_window_outlines':outside.OutlineCount(),'old_signal_reference_losses':old_losses})
 assert not old_losses and outside.Area()==0 and outside.OutlineCount()==0 and cp[l].OutlineCount()==sp[l].OutlineCount()==1
oldids={x.m_Uuid.AsString() for x in si};newtracks=[x for x in ci if x.m_Uuid.AsString() not in oldids and isinstance(x,p.PCB_TRACK) and not isinstance(x,p.PCB_VIA)];newrefs=[]
assert len(newtracks)==2
for x in newtracks:
 sl=x.GetLayer();rl=p.In1_Cu if sl==p.F_Cu else p.In2_Cu;uncovered=sub(polygon(x.GetEffectiveShape(sl)),cp[rl]);outside=sub(uncovered,transition);newrefs.append({'uuid':x.m_Uuid.AsString(),'layer':cb.GetLayerName(sl),'nearest_reference':cb.GetLayerName(rl),'uncovered_mm2':uncovered.Area()/1e12,'outside_transition_windows_mm2':outside.Area()/1e12,'outside_transition_outlines':outside.OutlineCount()});assert outside.Area()==0 and outside.OutlineCount()==0
result={'pass':True,'source_sha256':H(S),'candidate_sha256':H(C),'native_version':p.GetBuildVersion(),'method':'Independent native union of every inner GND zone, actual-hole subtraction, every old non-GND object projection, nearest-plane new-track coverage; no Unfracture or area waiver. Declared0.455mm transition windows are explicit geometry, not SI qualification.','planes':rows,'new_track_reference':newrefs,'limits':'No impedance, EMI, return-current distribution or hardware qualification.'};(O/'reference-review.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
