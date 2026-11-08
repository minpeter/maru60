from pathlib import Path
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume');S=R/'continuation-c782/combined27fix2';D=R/'continuation-9d787/branch4v';layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];retired=set(json.loads((D/'qa/build.json').read_text())['removed'])
def poly(s):
 q=p.SHAPE_POLY_SET();s.TransformToPolygon(q,1,p.ERROR_INSIDE);q.Simplify();return q
def sub(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def intersection(a,b):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,b);return q
def counts(q):return {'area_mm2':q.Area()/1e12,'outlines':q.OutlineCount()}
def empty(q):return q.Area()==0 and q.OutlineCount()==0
drill_by_holes={}
def capture(bp):
 b=p.LoadBoard(str(bp));items={q.m_Uuid.AsString():q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};holes=p.SHAPE_POLY_SET();drills=[]
 for q in items.values():
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
   z=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(z,1,p.ERROR_OUTSIDE);z.Simplify();holes.Append(z);drills.append((z.BBox(),z))
 holes.Simplify();drill_by_holes[id(holes)]=drills;zones={};planes={l:p.SHAPE_POLY_SET()for l in layers}
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  for l in layers:
   if z.IsOnLayer(l):
    cu=sub(z.GetFilledPolysList(l),holes);zones[(z.m_Uuid.AsString(),l)]=cu
    if z.GetNetname()=='GND':planes[l].BooleanAdd(cu)
 return b,items,holes,zones,planes
a,ai,ah,az,ap=capture(S/'pcb/maru60.kicad_pcb');b,bi,bh,bz,bp=capture(D/'pcb/maru60.kicad_pcb');assert set(ai)-set(bi)==retired and not set(bi)-set(ai);assert az.keys()==bz.keys()
def cu(q,l,holes):
 shape=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l));local=p.SHAPE_POLY_SET()
 for bb,h in drill_by_holes[id(holes)]:
  if bb.Intersects(shape.BBox()):local.Append(h)
 local.Simplify();return sub(shape,local)

rows=[]
def contour(ps):
 return [{'outer':[[ps.COutline(i).CPoint(j).x,ps.COutline(i).CPoint(j).y]for j in range(ps.COutline(i).PointCount())],'holes':[[[ps.CHole(i,h).CPoint(j).x,ps.CHole(i,h).CPoint(j).y]for j in range(ps.CHole(i,h).PointCount())]for h in range(ps.HoleCount(i))]}for i in range(ps.OutlineCount())]
for key in az:
 loss=sub(az[key],bz[key]);gain=sub(bz[key],az[key]);hits=[]
 if not empty(loss):
  for u,q in bi.items():
   if not q.GetBoundingBox().Intersects(loss.BBox()):continue
   for l in layers:
    if not q.IsOnLayer(l):continue
    hit=intersection(cu(q,l,bh),loss)
    if not empty(hit):hits.append({'uuid':u,'net':q.GetNetname(),'layer':b.GetLayerName(l),'intersection':counts(hit),'contours_nm':contour(hit)})
 rows.append({'zone':key[0],'layer':a.GetLayerName(key[1]),'loss':counts(loss),'gain':counts(gain),'loss_contours_nm':contour(loss),'gain_contours_nm':contour(gain),'retained_object_hits':hits})
(D/'qa/exact-plane-deltas.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
