exec(open('/workspace/shared/maru60-resume/continuation-9d787/mcu-gpio3/scripts/inventory.py').read().split('items=')[0])
import shapely as s
from shapely.geometry import Polygon
items=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]
def poly(sh,out=True):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);z.Simplify();return z
def geom(ps):
 def pts(c):return [(c.CPoint(i).x/1e6,c.CPoint(i).y/1e6) for i in range(c.PointCount())]
 return s.union_all([s.make_valid(Polygon(pts(ps.COutline(i)),[pts(ps.CHole(i,h)) for h in range(ps.HoleCount(i))])) for i in range(ps.OutlineCount())])
def sh(q,l):return poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2) if isinstance(q,p.PCB_VIA) else q.GetEffectiveShape(l))
V=lambda xy:p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6))
holes=p.SHAPE_POLY_SET()
for q in items:
 if isinstance(q,(p.PCB_VIA,p.PAD)) and q.HasHole():holes.Append(poly(q.GetEffectiveHoleShape()))
holes.Simplify();planes={}
for l in [p.In1_Cu,p.In2_Cu]:
 ps=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(l):ps.Append(z.GetFilledPolysList(l))
 ps.Simplify();ps.BooleanSubtract(holes);planes[l]=ps
rows=[]
for pos in [(112.6,84.0)]:
 via=p.PCB_VIA(b);via.SetPosition(V(pos));via.SetWidth(p.F_Cu,500000);via.SetDrill(250000);via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu)
 t=p.PCB_TRACK(b);t.SetStart(V((112.2,84.25)));t.SetEnd(V(pos));t.SetWidth(150000);t.SetLayer(p.B_Cu)
 checks=[]
 for name,q,ls in [('escape',t,[p.B_Cu]),('via',via,[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu])]:
  for l in ls:
   g=geom(sh(q,l));near=[]
   for ob in items:
    if ob.GetNetname()=='MCU_GPIO3' or not ob.IsOnLayer(l):continue
    bb=ob.GetBoundingBox();vv=ob.GetPosition()
    if bb.GetRight()<110000000 or bb.GetX()>114000000 or bb.GetBottom()<83000000 or bb.GetY()>88000000:continue
    dist=g.distance(geom(sh(ob,l)));near.append((dist,ob))
   near.sort(key=lambda x:x[0]);checks.append({'object':name,'layer':b.GetLayerName(l),'nearest':[dict(clearance_mm=d,**desc(o)) for d,o in near[:3]],'pass_0p15':near[0][0]>=.15})
 ps=sh(t,p.B_Cu);ps.BooleanSubtract(holes);ps.BooleanSubtract(planes[p.In2_Cu]);bb=ps.BBox();rows.append({'via_xy':pos,'checks':checks,'B_escape_unsupported_GND_In2_mm2':ps.Area()/1e12,'unsupported_contours':ps.OutlineCount(),'unsupported_bbox_mm':[bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6]})
loss=[]
for l,plane in planes.items():
 drill=poly(via.GetEffectiveHoleShape(),False);drill.BooleanIntersection(plane);parts=[]
 for i in range(drill.OutlineCount()):
  one=p.SHAPE_POLY_SET();one.AddOutline(drill.COutline(i))
  for j in range(drill.HoleCount(i)):one.AddHole(drill.CHole(i,j),0)
  parts.append({'index':i,'area_mm2':one.Area()/1e12,'points':[[one.COutline(0).CPoint(j).x/1e6,one.COutline(0).CPoint(j).y/1e6] for j in range(one.COutline(0).PointCount())]})
 assert sum(x['area_mm2'] for x in parts)==drill.Area()/1e12
 loss.append({'layer':b.GetLayerName(l),'unavoidable_source_GND_removed_by_drill_mm2':drill.Area()/1e12,'contours':parts,'strict_exact_no_loss_pass':drill.Area()==0})
report={'unavoidable_drill_loss':loss,'source_sha256' :hashlib.sha256(S.read_bytes()).hexdigest(),'rows':rows};(R/'qa/detour-screen.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
