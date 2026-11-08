from fractions import Fraction as F
from pathlib import Path
import json
R=Path('/workspace/shared/maru60-resume/combined-vbus-independent');d=json.loads((R/'boundary-delta.json').read_text())
def d2(c,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];vx,vy=c[0]-a[0],c[1]-a[1];ll=dx*dx+dy*dy;dot=vx*dx+vy*dy
 if dot<=0:return F(vx*vx+vy*vy)
 if dot>=ll:return F((c[0]-b[0])**2+(c[1]-b[1])**2)
 return F((dx*vy-dy*vx)**2,ll)
out=[]
for l,x in d.items():
 for k,opp in [('removed','added'),('added','removed')]:
  vals=[]
  for a,b in x[k]:
   # Exclude only the local physically changed removed-via clearance region.
   if any(19500000<=c[0]<=20800000 and 10300000<=c[1]<=11600000 for c in (a,b)):continue
   # Strong segment bound: entire segment lies in the capsule around one opposite segment,
   # since distance to a convex segment is convex and endpoints bound the maximum.
   dx,dy=b[0]-a[0],b[1]-a[1];ll=dx*dx+dy*dy
   cuts={F(0),F(1)}
   for c,e in x[opp]:
    for pt in (c,e):
     t=F((pt[0]-a[0])*dx+(pt[1]-a[1])*dy,ll)
     if 0<t<1:cuts.add(t)
   ts=sorted(cuts)
   for t,u in zip(ts,ts[1:]):
    aa=(a[0]+t*dx,a[1]+t*dy);bb=(a[0]+u*dx,a[1]+u*dy)
    bound,edge=min((max(d2(aa,c,e),d2(bb,c,e)),(c,e))for c,e in x[opp]);vals.append((bound,a,b,edge))
  worst=max(vals);out.append(dict(layer=l,direction=k,count=len(vals),worst_bound_nm=float(worst[0])**.5,exact_squared_bound=str(worst[0]),old_edge=worst[1:3],counter_edge=worst[3]))
print(json.dumps(out,indent=2));(R/'boundary-bound.json').write_text(json.dumps(out,indent=2))
