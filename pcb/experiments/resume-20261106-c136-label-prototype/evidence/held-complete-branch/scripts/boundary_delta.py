import pcbnew as p,json,collections
from pathlib import Path
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-9d787/branch4v';sets=[]
for path in [R/'continuation-c782/combined27fix2/pcb/maru60.kicad_pcb',D/'pcb/maru60.kicad_pcb']:
 b=p.LoadBoard(str(path));out={}
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  for l in[p.In1_Cu,p.In2_Cu]:
   if not z.IsOnLayer(l):continue
   ps=z.GetFilledPolysList(l);rings=[]
   def pts(r):return [(r.CPoint(j).x,r.CPoint(j).y)for j in range(r.PointCount())]
   for i in range(ps.OutlineCount()):rings+=[pts(ps.COutline(i))]+[pts(ps.CHole(i,h))for h in range(ps.HoleCount(i))]
   ct=collections.Counter((a,c)for r in rings for a,c in zip(r,r[1:]+r[:1]));out[b.GetLayerName(l)]=collections.Counter({e:n-ct[e[::-1]]for e,n in ct.items()if n>ct[e[::-1]]})
 sets.append(out)
result={l:{'removed':list((sets[0][l]-sets[1][l]).elements()),'added':list((sets[1][l]-sets[0][l]).elements())}for l in sets[0]};(D/'qa/boundary-delta.json').write_text(json.dumps(result,indent=2));print({l:{k:len(v)for k,v in r.items()}for l,r in result.items()})
