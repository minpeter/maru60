from pathlib import Path
from fractions import Fraction as F
import pcbnew as p,json
R=Path('/workspace/shared/maru60-resume/continuation-fa96a7c/gpio24-via25/variants/via24-left025');a=p.LoadBoard('/workspace/shared/maru60-resume/selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype/pcb/maru60.kicad_pcb');b=p.LoadBoard(str(R/'candidate/pcb/maru60.kicad_pcb'));rows=json.loads((R/'qa/outside-loss-allholes.json').read_text());out=[]
def pts(r):return [(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
def inside(r,c):
 x,y=c;v=False
 for a,z in zip(r,r[1:]+r[:1]):
  if (a[1]>y)!=(z[1]>y)and x<F(a[0])+F(y-a[1],z[1]-a[1])*(z[0]-a[0]):v=not v
 return v
for row in rows:
 rings=[]
 for board in[a,b]:
  l=board.GetLayerID(row['layer']);z=next(z for z in board.Zones()if z.GetNetname()=='GND'and z.IsOnLayer(l));s=z.GetFilledPolysList(l);rings.append([(pts(s.COutline(i)),[pts(s.CHole(i,h))for h in range(s.HoleCount(i))])for i in range(s.OutlineCount())])
 def boundary(idx,c):
  x,y=c
  return any(min(a[0],z[0])<=x<=max(a[0],z[0]) and min(a[1],z[1])<=y<=max(a[1],z[1]) and (x-a[0])*(z[1]-a[1])==(y-a[1])*(z[0]-a[0]) for o,hs in rings[idx] for ring in [o]+hs for a,z in zip(ring,ring[1:]+ring[:1]))
 def covered(idx,c):return any(inside(o,c)and not any(inside(h,c)for h in hs)for o,hs in rings[idx])
 witnesses=[]
 for v in row['points']:
  c=(sum(F(x)for x,y in v)/len(v),sum(F(y)for x,y in v)/len(v));assert inside(v,c)
  witnesses.append(dict(point_nm=[str(x)for x in c],source_copper=covered(0,c),candidate_copper=covered(1,c),source_boundary=boundary(0,c),candidate_boundary=boundary(1,c)))
 out.append(dict(layer=row['layer'],witnesses=witnesses,has_exact_loss_witness=any(w['source_copper']and not w['candidate_copper']and not w['source_boundary']and not w['candidate_boundary']for w in witnesses)))
(R/'qa/rational-loss-strict.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
