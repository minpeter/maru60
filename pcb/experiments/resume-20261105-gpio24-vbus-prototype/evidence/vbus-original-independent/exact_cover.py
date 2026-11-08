from fractions import Fraction as F
from collections import Counter
import argparse
from pathlib import Path
import pcbnew as p,json
R=Path('/workspace/shared/maru60-resume');res=[]
ap=argparse.ArgumentParser(description='Exact rational filled-zone containment check around a circular via; cancels exactly reversed fracture edges, no epsilon.')
ap.add_argument('--source',default=str(R/'header-routing/frozen26b/pcb/maru60.kicad_pcb'));ap.add_argument('--candidate',default=str(R/'warning-vbus-serial/pcb/maru60.kicad_pcb'));ap.add_argument('--via',default='30f42945-7f50-4bbe-b5f4-d95448eea66b');ap.add_argument('--output',default=str(R/'vbus-independent/exact-cover.json'));args=ap.parse_args()
def ringpts(r):return [(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
def inside(v,c):
 x,y=c;hit=False
 for a,b in zip(v,v[1:]+v[:1]):
  if (a[1]>y)!=(b[1]>y) and F(x)< F(a[0])+F(y-a[1],b[1]-a[1])*(b[0]-a[0]):hit=not hit
 return hit
def d2(a,b,c):
 dx,dy=b[0]-a[0],b[1]-a[1];vx,vy=c[0]-a[0],c[1]-a[1];ll=dx*dx+dy*dy;dot=vx*dx+vy*dy
 if dot<=0:return F(vx*vx+vy*vy)
 if dot>=ll:return F((c[0]-b[0])**2+(c[1]-b[1])**2)
 return F((dx*vy-dy*vx)**2,ll)
for path in [Path(args.source),Path(args.candidate)]:
 b=p.LoadBoard(str(path));via=next(v for v in b.GetTracks()if v.m_Uuid.AsString()==args.via);assert isinstance(via,p.PCB_VIA);center=(via.GetPosition().x,via.GetPosition().y);outer_radius=via.GetWidth(p.In1_Cu)//2;hole_radius=via.GetDrillValue()//2
 for z in b.Zones():
  for l in [p.In1_Cu,p.In2_Cu]:
   if not z.IsOnLayer(l)or z.GetIsRuleArea():continue
   q=z.GetFilledPolysList(l);rs=[];covered=False
   for i in range(q.OutlineCount()):
    outer=ringpts(q.COutline(i));holes=[ringpts(q.CHole(i,h))for h in range(q.HoleCount(i))];rs+=[outer]+holes
    if inside(outer,center)and not any(inside(h,center)for h in holes):covered=True
   segments=[(a,bb)for r in rs for a,bb in zip(r,r[1:]+r[:1])]
   counts=Counter(segments);physical_segments=[(a,bb)for a,bb in segments if counts[a,bb]>counts[bb,a]]
   outside_hole=[(a,bb)for a,bb in physical_segments if not all((pt[0]-center[0])**2+(pt[1]-center[1])**2<hole_radius**2 for pt in (a,bb))]
   least=min(d2(a,bb,center) for a,bb in outside_hole)
   sample=(center[0]+(outer_radius+hole_radius)//2,center[1]);sample_inside=any(inside(ringpts(q.COutline(i)),sample)and not any(inside(ringpts(q.CHole(i,h)),sample)for h in range(q.HoleCount(i)))for i in range(q.OutlineCount()))
   row=dict(board=str(path),layer=l,center_inside_exact=covered,annulus_sample_inside_exact=sample_inside,opposite_fracture_edges_cancelled=len(segments)-len(physical_segments),segments_inside_actual_drill=len(physical_segments)-len(outside_hole),min_raw_boundary_distance_mm=float(least)**.5/1e6,annulus_no_boundary_and_sample_inside_exact=sample_inside and least>outer_radius**2,min_distance_squared_nm2_fraction=str(least));res.append(row)
print(json.dumps(res,indent=2));Path(args.output).write_text(json.dumps(res,indent=2))
