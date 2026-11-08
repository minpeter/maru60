from pathlib import Path
from collections import Counter
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume');O=R/'continuation-c782/stitch/qa';sets=[]
for name,h in [('combined-trial','56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9'),('continuation-c782/stitch','22761b0f007cd9b113843c0074924fee02c3728e98f33d88fc90eb7cdc14ec9c')]:
 path=R/name/'pcb/maru60.kicad_pcb';assert hashlib.sha256(path.read_bytes()).hexdigest()==h;b=p.LoadBoard(str(path));out={}
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
print({l:{k:len(v)for k,v in x.items()}for l,x in result.items()})
