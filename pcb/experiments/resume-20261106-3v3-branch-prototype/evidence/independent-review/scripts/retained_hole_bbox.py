from pathlib import Path
import json,pcbnew as p
from fractions import Fraction as F
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-97d9eb7/stub3v3-independent';S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype';b=p.LoadBoard(str(S/'pcb/maru60.kicad_pcb'));rm=set(json.loads((D/'qa/build.json').read_text())['removed']);items={q.m_Uuid.AsString():q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};via=items['0826a4b6-5567-52ab-a787-b898d20d23ac'];hole=p.SHAPE_POLY_SET();via.GetEffectiveHoleShape().TransformToPolygon(hole,1,p.ERROR_OUTSIDE);hole.Simplify();hb=hole.BBox();rows=[]
def vertices(ps):
 assert ps.OutlineCount()==1 and ps.HoleCount(0)==0
 r=ps.COutline(0);return [(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def on(a,b,c):return cross(a,b,c)==0 and min(a[0],b[0])<=c[0]<=max(a[0],b[0])and min(a[1],b[1])<=c[1]<=max(a[1],b[1])
def intersects(a,b,c,d):
 o1,o2,o3,o4=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
 return o1*o2<0 and o3*o4<0 or on(a,b,c)or on(a,b,d)or on(c,d,a)or on(c,d,b)
def inside(r,c):
 x,y=c;v=False
 for a,b in zip(r,r[1:]+r[:1]):
  if on(a,b,c):return True
  if (a[1]>y)!=(b[1]>y)and x<F(a[0])+F(y-a[1],b[1]-a[1])*(b[0]-a[0]):v=not v
 return v
hv=vertices(hole)
for u,q in items.items():
 if u in rm:continue
 for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if not q.IsOnLayer(l):continue
  z=p.SHAPE_POLY_SET();shape=p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l);shape.TransformToPolygon(z,1,p.ERROR_INSIDE);z.Simplify();bb=z.BBox();separate=bb.GetRight()<hb.GetX()or bb.GetX()>hb.GetRight()or bb.GetBottom()<hb.GetY()or bb.GetY()>hb.GetBottom()
  detail=None;disjoint=separate
  if not separate:
   vv=vertices(z);hits=[(a,c,d,e)for a,c in zip(vv,vv[1:]+vv[:1])for d,e in zip(hv,hv[1:]+hv[:1])if intersects(a,c,d,e)];disjoint=not hits and not inside(vv,hv[0])and not inside(hv,vv[0]);detail=dict(shape_vertices_nm=vv,hole_vertices_nm=hv,exact_integer_edge_intersections=hits,hole_vertex_inside_shape=inside(vv,hv[0]),shape_vertex_inside_hole=inside(hv,vv[0]))
  rows.append(dict(uuid=u,layer=b.GetLayerName(l),bbox_nm=[bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()],strictly_disjoint_from_removed_hole_bbox=separate,exact_disjoint=disjoint,exact_narrow_phase=detail))
def contours(ps):
 def ring(r):
  v=[(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
  if not v:return ()
  low=min(v);return min(tuple(v[i:]+v[:i])for i,x in enumerate(v)if x==low)
 return tuple(sorted((ring(ps.COutline(i)),tuple(sorted(ring(ps.CHole(i,h))for h in range(ps.HoleCount(i)))))for i in range(ps.OutlineCount())))
cb=p.LoadBoard(str(R/'continuation-97d9eb7/stub3v3/pcb/maru60.kicad_pcb'));zz=lambda board:{(z.m_Uuid.AsString(),l):contours(z.GetFilledPolysList(l))for z in board.Zones()if not z.GetIsRuleArea()for l in [p.F_Cu,p.B_Cu]if z.IsOnLayer(l)};za,zc=zz(b),zz(cb);assert za==zc
x=dict(outer_zone_exact_serialized_contours_equal=True,outer_zone_rows=len(za),removed_hole_bbox_nm=[hb.GetX(),hb.GetY(),hb.GetRight(),hb.GetBottom()],rows=rows,pass_all_disjoint=all(r['exact_disjoint']for r in rows));(D/'qa/retained-hole-bbox-proof.json').write_text(json.dumps(x,indent=2)+'\n');print('rows',len(rows),'intersecting',[r for r in rows if not r['strictly_disjoint_from_removed_hole_bbox']]);assert x['pass_all_disjoint']
