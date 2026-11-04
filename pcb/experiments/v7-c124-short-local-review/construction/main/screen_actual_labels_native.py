import sys,pathlib,json,math
sys.path.insert(0,'/workspace/scratch/edd9a5be63e7/v7-safe-five-logo-recovered')
from native_ink import *
R=Path('/tmp/v7-c124-rebound-short/isolated-v4');sc=Scene(R/'pcb/maru60.kicad_pcb');edits=['R121','C124'];ids={UID(sc.fields[r])for r in edits};bk=sc.buckets[p.B_SilkS];bk['silk']=[(i,s)for i,s in bk['silk']if i['uuid']not in ids];out={}
for ref in edits:
 t=sc.fields[ref];o=sc.fps[ref].GetPosition();poses=[(math.hypot(x/10-o.x/1e6,y/10-o.y/1e6),x/10,y/10)for x in range(70,202,2)for y in range(118,230,2)];poses.sort();found=[]
 for _,x,y in poses:
  t.SetPosition(p.VECTOR2I(round(x*1e6),round(y*1e6)));s=effective(t)
  if any(hits(s,bk[k],150000)for k in['mask','silk','fab','courtyard','unreconstructed_fab']):continue
  if hits(s,sc.edges,250000):continue
  q=poly(s);q.BooleanSubtract(sc.outline)
  if q.Area():continue
  found.append([x,y])
  if len(found)>=5:break
 if not found:out[ref]={'blocked':'no pose in explicit grid'};continue
 t.SetPosition(p.VECTOR2I(*(round(a*1e6)for a in found[0])));bk['silk'].append((info(t,ref),effective(t)));out[ref]={'chosen':found[0],'alternates':found[1:],'measure':sc.measure_ref(ref)}
(R/'qa/reference-native-pose-screen.json').write_text(json.dumps(out,indent=2));print(json.dumps({r:{k:v for k,v in q.items()if k!='measure'}for r,q in out.items()},indent=2))
