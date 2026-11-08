import json,collections,difflib
from pathlib import Path
R=Path(__file__).resolve().parent;D=Path('/tmp/v7-buck-deadarm-independent-review')
def cycles(pts):
 es=collections.Counter(zip(pts,pts[1:]+pts[:1]));remain=es.copy()
 for edge,num in es.items():remain[edge]-=min(num,es[edge[::-1]])
 remain=+remain;assert all(n==1 for n in remain.values());adj={a:b for a,b in remain};assert len(adj)==len(remain) and set(adj)==set(adj.values());out={}
 while adj:
  start=min(adj);chain=[];u=start
  while True:
   chain.append(u);v=adj.pop(u);u=v
   if u==start:break
  assert start not in out;out[start]=chain
 return out
s=json.loads((D/'source-strip.json').read_text());c=json.loads((D/'candidate-strip.json').read_text());ans=[]
for z in s['zones']:
 if z['net']!='GND' or z['layer']not in ('In1.Cu','In2.Cu'):continue
 v=next(x for x in c['zones'] if (x['uuid'],x['layer'])==(z['uuid'],z['layer']));a=cycles(list(map(tuple,z['fills'][0]['outline'])));b=cycles(list(map(tuple,v['fills'][0]['outline'])));out={'layer':z['layer'],'old_cycles':len(a),'new_cycles':len(b),'removed':{str(k):v for k,v in a.items() if k not in b},'added':{str(k):v for k,v in b.items() if k not in a},'changed':[]};print(z['layer'],'cycles',len(a),len(b),'removed',set(a)-set(b),'added',set(b)-set(a))
 for k in a.keys()&b.keys():
  if a[k]==b[k]:continue
  ops=[(tag,i,j,h,l,a[k][i:j],b[k][h:l]) for tag,i,j,h,l in difflib.SequenceMatcher(a=a[k],b=b[k],autojunk=False).get_opcodes() if tag!='equal'];out['changed'].append({'anchor':k,'old':a[k],'new':b[k],'ops':ops});print('changed',k,len(a[k]),len(b[k]),[(op[0],op[2]-op[1],op[4]-op[3]) for op in ops])
 ans.append(out)
(R/'boundary-cycle-inventory.json').write_text(json.dumps(ans,indent=2)+'\n')
