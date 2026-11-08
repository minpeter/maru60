from pathlib import Path
from fractions import Fraction as F
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume/header-routing');paths={'26b':R/'frozen26b/pcb/maru60.kicad_pcb','24move':R/'frozen24move/pcb/maru60.kicad_pcb'};tri=[(F(274475000),F(37899499)),(F(274540691),F(37899499)),(F(274540691),F(37917104)),(F(274475000),F(37917104))];bb=(274475000,37899499,274540691,37917104);raw={};near={};holes={}
def ring(c):return [(c.CPoint(i).x,c.CPoint(i).y)for i in range(c.PointCount())]
def overlap(box):return not(box.GetRight()<bb[0]or box.GetX()>bb[2]or box.GetBottom()<bb[1]or box.GetY()>bb[3])
for label,path in paths.items():
 b=p.LoadBoard(str(path));raw[label]={};near[label]={};holes[label]=[]
 for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]:
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()and overlap(q.GetEffectiveHoleShape().BBox()):holes[label].append(q.m_Uuid.AsString())
 for l in [p.In1_Cu,p.In2_Cu]:
  records=[];local=set()
  for z in b.Zones():
   if z.GetIsRuleArea()or z.GetNetname()!='GND'or not z.IsOnLayer(l):continue
   ps=z.GetFilledPolysList(l)
   for i in range(ps.OutlineCount()):
    rings=[ring(ps.COutline(i))]+[ring(ps.CHole(i,j))for j in range(ps.HoleCount(i))];records.append(rings)
    for pts in rings:
     for a,c in zip(pts,pts[1:]+pts[:1]):
      if a!=c and not(max(a[0],c[0])<bb[0]or min(a[0],c[0])>bb[2]or max(a[1],c[1])<bb[1]or min(a[1],c[1])>bb[3]):local.add(tuple(sorted((a,c))))
  raw[label][l]=records;near[label][l]=local
assert not any(holes.values()),holes
cross=lambda a,b,x:(b[0]-a[0])*(x[1]-a[1])-(b[1]-a[1])*(x[0]-a[0])
def area(poly):return abs(sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(poly,poly[1:]+poly[:1])))/2
def clip(poly,a,b,sign):
 out=[]
 for u,v in zip(poly,poly[1:]+poly[:1]):
  cu,cv=cross(a,b,u)*sign,cross(a,b,v)*sign
  if cu>=0:out.append(u)
  if (cu<0<cv)or(cv<0<cu):
   t=cu/(cu-cv);out.append((u[0]+t*(v[0]-u[0]),u[1]+t*(v[1]-u[1])))
 if not out:return []
 clean=[]
 for x in out:
  if not clean or clean[-1]!=x:clean.append(x)
 if len(clean)>1 and clean[0]==clean[-1]:clean.pop()
 return clean if len(clean)>2 and area(clean)>0 else []
def winding(pts,x):
 w=0
 for a,b in zip(pts,pts[1:]+pts[:1]):
  c=cross(a,b,x)
  if c==0 and min(a[0],b[0])<=x[0]<=max(a[0],b[0])and min(a[1],b[1])<=x[1]<=max(a[1],b[1]):return None
  if a[1]<=x[1]<b[1]and c>0:w+=1
  elif b[1]<=x[1]<a[1]and c<0:w-=1
 return w!=0
def inside(records,x):
 vals=[]
 for rings in records:
  outer=winding(rings[0],x)
  if outer is None:return None
  if not outer:continue
  hs=[winding(h,x)for h in rings[1:]]
  if any(h is None for h in hs):return None
  if not any(hs):return True
 return False
fmt=lambda x:str(x.numerator)if x.denominator==1 else str(x)
rows=[]
for l in [p.In1_Cu,p.In2_Cu]:
 edges=near['26b'][l]|near['24move'][l];cells=[tri]
 for a,b in sorted(edges):
  new=[]
  for cell in cells:
   for sign in [-1,1]:
    cut=clip(cell,a,b,sign)
    if cut:new.append(cut)
  cells=new
 results=[];loss=F(0)
 for cell in cells:
  pt=(sum(x[0]for x in cell)/len(cell),sum(x[1]for x in cell)/len(cell));s=inside(raw['26b'][l],pt);c=inside(raw['24move'][l],pt);assert s is not None and c is not None
  ar=area(cell)
  if s and not c:loss+=ar
  results.append({'area_nm2_exact':fmt(ar),'source_inside':s,'candidate_inside':c,'sample_nm':[fmt(x)for x in pt],'cell_vertices_nm':[[fmt(x),fmt(y)]for x,y in cell]})
 assert sum(area(cell)for cell in cells)==area(tri)
 rows.append({'layer':{p.In1_Cu:'In1.Cu',p.In2_Cu:'In2.Cu'}[l],'near_source_edges':[list(x)for x in sorted(near['26b'][l])],'near_candidate_edges':[list(x)for x in sorted(near['24move'][l])],'review_rectangle_area_nm2_exact':fmt(area(tri)),'exact_raw_zone_loss_nm2':fmt(loss),'cells':results})
out={'source_sha256':hashlib.sha256(paths['26b'].read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(paths['24move'].read_bytes()).hexdigest(),'status':'Exact local raw-zone loss within the affected +4V_LED track rectangle; other remote residues not classified by this file.','method':'No polygon Boolean or Unfracture: split the exact copper-track rectangle covering all differing raw boundary segments by the supporting line of every raw source/candidate polygon edge whose bounding box intersects it; exact Fraction arithmetic; classify each positive cell by exact winding of the unsimplified raw native filled outlines and holes. Assert cell area conservation and no physical drill bbox intersects the triangle.','physical_drills_intersecting_review_bbox':holes,'planes':rows};(Path('/workspace/shared/maru60-resume/header-exact-review/reproduced-local.json')).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
