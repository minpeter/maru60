from pathlib import Path
from fractions import Fraction as F
import pcbnew as p,json
R=Path('/workspace/shared/maru60-resume/continuation-be51692/gpio25-transition');D=R/'variants/j0-b0';S=Path('/workspace/shared/maru60-resume/selected-repo/pcb/experiments/resume-20261106-usb-pendant-prototype/pcb/maru60.kicad_pcb');boards=[p.LoadBoard(str(x))for x in[S,D/'candidate/pcb/maru60.kicad_pcb']]
def pts(r):return [(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
def inside(r,c):
 x,y=c;v=False
 for a,z in zip(r,r[1:]+r[:1]):
  if min(a[0],z[0])<=x<=max(a[0],z[0])and min(a[1],z[1])<=y<=max(a[1],z[1])and(x-a[0])*(z[1]-a[1])==(y-a[1])*(z[0]-a[0]):return True
  if(a[1]>y)!=(z[1]>y)and x<F(a[0])+F(y-a[1],z[1]-a[1])*(z[0]-a[0]):v=not v
 return v
holes=[]
for bi,b in enumerate(boards):
 for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]:
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
   poly=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(poly,1,p.ERROR_OUTSIDE)
   holes.append((bi,q.m_Uuid.AsString(),[pts(poly.COutline(i))for i in range(poly.OutlineCount())]))
plan=json.loads((D/'qa/FROZEN_SCOPE.json').read_text());centers=plan['gpio25_vias']+[plan['via24_old'],plan['via24_new']];out=[]
for row in json.loads((D/'qa/rational-loss-strict.json').read_text()):
 for w in row['witnesses']:
  c=tuple(F(x)for x in w['point_nm']);hit=[(bi,u)for bi,u,rs in holes if any(inside(r,c)for r in rs)]
  dist2=[sum((c[i]-round(a[i]*1e6))**2 for i in[0,1])for a in centers]
  out.append(dict(layer=row['layer'],point_nm=w['point_nm'],all_holes_checked=len(holes),hole_hits=hit,min_changed_via_distance_squared_nm2=str(min(dist2)),outside_rejection_locator455um=all(d>455000**2 for d in dist2),exact_loss=w['source_copper']and not w['candidate_copper']and not w['source_boundary']and not w['candidate_boundary']))
(R/'resume-audit/EXACT_REMOTE_REJECTION.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));assert all(not x['hole_hits']and x['outside_rejection_locator455um']and x['exact_loss']for x in out)
