from pathlib import Path
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume/continuation-fa96a7c/gpio24-via25');S=Path('/workspace/shared/maru60-resume/selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype/pcb/maru60.kicad_pcb');C=R/'candidate/pcb/maru60.kicad_pcb';plan=json.loads((R/'qa/FROZEN_SCOPE.json').read_text());build=json.loads((R/'qa/BUILD.json').read_text());uid=lambda q:q.m_Uuid.AsString()
def poly(sh):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_OUTSIDE);z.Simplify();return z
def sub(a,b):z=p.SHAPE_POLY_SET(a);z.BooleanSubtract(b);return z
def inter(a,b):z=p.SHAPE_POLY_SET();z.BooleanIntersection(a,b);return z
def circle(xy):return poly(p.SHAPE_CIRCLE(p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6)),plan['transition_radius_nm']))
def union(pts):
 z=p.SHAPE_POLY_SET()
 for xy in pts:z.BooleanAdd(circle(xy))
 return z
def capture(path):
 b=p.LoadBoard(str(path));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];holes=p.SHAPE_POLY_SET();planes={l:p.SHAPE_POLY_SET()for l in[p.In1_Cu,p.In2_Cu]}
 for q in items:
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():holes.Append(poly(q.GetEffectiveHoleShape()))
 holes.Simplify()
 for z in b.Zones():
  if z.GetIsRuleArea()or z.GetNetname()!='GND':continue
  for l in planes:
   if z.IsOnLayer(l):planes[l].BooleanAdd(p.SHAPE_POLY_SET(z.GetFilledPolysList(l)))
 for l in planes:planes[l].BooleanSubtract(holes)
 return b,items,holes,planes
a,ai,ah,ap=capture(S);b,bi,bh,bp=capture(C);old={uid(q):q for q in ai};move=union([plan['via24_old'],plan['via24_new']]);sig=union(plan['gpio25_vias']);allw=p.SHAPE_POLY_SET(move);allw.BooleanAdd(sig);empty=p.SHAPE_POLY_SET();prows=[];projection=[];refs=[];fail=[]
def recordfail(kind,row):fail.append(dict(kind=kind,**row))
for l in ap:
 loss=sub(ap[l],bp[l]);gain=sub(bp[l],ap[l]);outside=sub(loss,allw);gainout=sub(gain,allw);r=dict(plane=b.GetLayerName(l),old_components=ap[l].OutlineCount(),new_components=bp[l].OutlineCount(),loss_mm2=loss.Area()/1e12,gain_mm2=gain.Area()/1e12,outside_loss_mm2=outside.Area()/1e12,outside_loss_contours=outside.OutlineCount(),outside_gain_mm2=gainout.Area()/1e12,outside_gain_contours=gainout.OutlineCount());prows.append(r)
 if outside.Area()!=0 or outside.OutlineCount()!=0:recordfail('plane_loss',r)
 if gainout.Area()!=0 or gainout.OutlineCount()!=0:recordfail('plane_gain',r)
 if ap[l].OutlineCount()!=bp[l].OutlineCount():recordfail('plane_component_count',r)
 for q in ai:
  if q.GetNetname()in['','GND']or not q.GetBoundingBox().Intersects(loss.BBox()):continue
  for sl in[p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu]:
   if not q.IsOnLayer(sl):continue
   sh=p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(sl)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(sl);hit=inter(loss,sub(poly(sh),ah));own=move if uid(q)in build['modified']else empty;out=sub(hit,own)
   r=dict(plane=b.GetLayerName(l),uuid=uid(q),net=q.GetNetname(),layer=b.GetLayerName(sl),loss_mm2=hit.Area()/1e12,loss_contours=hit.OutlineCount(),outside_own_mm2=out.Area()/1e12,outside_own_contours=out.OutlineCount());projection.append(r)
   if out.Area()!=0 or out.OutlineCount()!=0:recordfail('retained_projection_loss',r)

out=dict(planes=prows,projection=projection,failures=fail);(R/'qa/PLANE_DELTA_EARLY.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
