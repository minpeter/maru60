exec(open('/workspace/shared/maru60-resume/combined-vbus-independent/exact_cover.py').read().split('for path in [')[0])
from collections import Counter
sets=[]
for path in [R/'header-routing/frozen24move/pcb/maru60.kicad_pcb',R/'combined-trial/pcb/maru60.kicad_pcb']:
 b=p.LoadBoard(str(path));out={}
 for z in b.Zones():
  for l in [p.In1_Cu,p.In2_Cu]:
   if not z.IsOnLayer(l)or z.GetIsRuleArea():continue
   q=z.GetFilledPolysList(l);rs=[]
   for i in range(q.OutlineCount()):rs+=[ringpts(q.COutline(i))]+[ringpts(q.CHole(i,h))for h in range(q.HoleCount(i))]
   ct=Counter((a,bb)for r in rs for a,bb in zip(r,r[1:]+r[:1]));out[l]=Counter({k:v-ct[k[::-1]]for k,v in ct.items()if v>ct[k[::-1]]})
 sets.append(out)
result={l:dict(removed=list((sets[0][l]-sets[1][l]).elements()),added=list((sets[1][l]-sets[0][l]).elements()))for l in sets[0]}
(O if 'O'in globals()else R/'combined-vbus-independent').joinpath('boundary-delta.json').write_text(json.dumps(result,indent=2))
for l,x in result.items():
 print(l,len(x['removed']),len(x['added']))
 for kind,edges in x.items():
  print(kind)
  for a,b in edges:
   if a[0]<19000000 or a[0]>22000000:print(a,b)
