from pathlib import Path
from collections import Counter
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume');O=R/'header-exact-review';sets=[]
for name,h in [('frozen26b','04be04e5d098c974a20a60f0d0be89e0379d20e5f2e709a155418d406396ba99'),('frozen24move','2bacda8824b543df9be08628cd8ac14b2ed6628d7ee3e221626b869da74787d4')]:
 path=R/'header-routing'/name/'pcb/maru60.kicad_pcb';assert hashlib.sha256(path.read_bytes()).hexdigest()==h;b=p.LoadBoard(str(path));out={}
 for l in [p.In1_Cu,p.In2_Cu]:
  ct=Counter()
  for z in b.Zones():
   if z.GetIsRuleArea()or z.GetNetname()!='GND'or not z.IsOnLayer(l):continue
   q=z.GetFilledPolysList(l)
   for i in range(q.OutlineCount()):
    for r in [q.COutline(i)]+[q.CHole(i,j)for j in range(q.HoleCount(i))]:
     pts=[(r.CPoint(k).x,r.CPoint(k).y)for k in range(r.PointCount())];ct.update((a,c)for a,c in zip(pts,pts[1:]+pts[:1])if a!=c)
  out[l]=Counter({k:v-ct[k[::-1]]for k,v in ct.items()if v>ct[k[::-1]]})
 sets.append(out)
result={l:dict(removed=list((sets[0][l]-sets[1][l]).elements()),added=list((sets[1][l]-sets[0][l]).elements()))for l in sets[0]};(O/'boundary-delta.json').write_text(json.dumps(result,indent=2))
for l,x in result.items():
 print(l)
 for k,es in x.items():
  far=[(a,b)for a,b in es if not any(all((c[0]-cx)**2+(c[1]-cy)**2<=455000**2 for c in (a,b))for cx,cy in [(97250000,37450000),(92350000,37750000),(105800000,37500000)])];print(k,len(es),'far',len(far));print(far)
