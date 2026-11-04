from common import *
rx,ry,cx,cy=15.54,20.15,15.65,19.05
terms=[('R125.1','USB_DVDT',[rx,ry],[rx+.45,ry],[.4,.3],[rx+.175,ry-.275,rx+.55,ry+.275]),('R125.2','USB_DVDT_CAP',[rx,ry],[rx-.45,ry],[.4,.3],[rx-.55,ry-.275,rx-.175,ry+.275]),('C124.1','USB_DVDT_CAP',[cx,cy],[cx-.375,cy],[.35,.5],[cx-.525,cy-.275,cx-.125,cy+.275]),('C124.2','GND',[cx,cy],[cx+.375,cy],[.35,.5],[cx+.125,cy-.275,cx+.525,cy+.275])]
# Counterfactual UVLO retirement, read-only ONLY. Not within current retained-net construction contract.
from collections import defaultdict,deque
adj=defaultdict(list)
for q in b.GetTracks():
 if isinstance(q,p.PCB_VIA)or q.GetNetname()!='USB_UVLO'or q.GetLayer()!=p.B_Cu:continue
 a=(q.GetStart().x,q.GetStart().y);z=(q.GetEnd().x,q.GetEnd().y);adj[a].append((z,uid(q)));adj[z].append((a,uid(q)))
start=(14200000,16350000);end=(17200000,21150000);todo=deque([(start,[])]);seen=set();path=None
while todo:
 v,pp=todo.popleft()
 if v==end:path=pp;break
 if v in seen:continue
 seen.add(v)
 for z,u in adj[v]:todo.append((z,pp+[u]))
assert path is not None
ex=capids|rids|ret|set(path);new=[];envs=[];out={'source_sha':sha(BP),'status':'COUNTERFACTUAL analytical expanded UVLO contract; not approved for construction','terms':[],'r121_shift_mm':[-.32,0],'uvlo_retirement_uuids':path,'uvlo_old_length_mm':sum(idx[u].GetLength()/1e6 for u in path)}
for name,net,org,at,wh,bb in terms:
 land=rect(*at,*wh);e=envelope(org,bb);new.append((name,net,land));envs.append((name,net,e));out['terms'].append(dict(name=name,land_center=at,land_size=wh,land_clearance=clearance(land,net,exclude=ex),terminal_clearance=clearance(e,net,exclude=ex),land=dump(land),terminal=dump(e)))
for q in fs['R121'].Pads():new.append(('R121.'+q.GetNumber(),q.GetNetname(),transform(copper(q,p.B_Cu),[14,18.5],[13.68,18.5])))
new.append(('old-ground-bridge','GND',compact))
routes=[('UVLO','USB_UVLO',[[14.2,16.35],[12.75,17.05],[12.75,19.8],[14.2,21.25],[16.75,21.25],[17.2,21.15]]),('OVLO','USB_OVLO',[[13.68,19.325],[14.5,19.325],[14.5,19.95],[14.58,20.55],[14.8,20.82],[16.9,20.85],[20.575,20.825],[22,19.6]]),('DVDT','USB_DVDT',[[17.25,19.4],[16.85,19.4],[16.5,19.8],[rx+.45,ry]]),('CAP','USB_DVDT_CAP',[[rx-.45,ry],[cx-.375,cy]]),('GND','GND',[[cx+.375,cy],[16.4,18.9]])]
out['routes']=[]
for name,net,pts in routes:
 for i,(a,z)in enumerate(zip(pts,pts[1:])):
  s=seg(a,z);new.append((name+str(i),net,s));out['routes'].append(dict(name=name+str(i),net=net,start=a,end=z,length=math.dist(a,z),old=clearance(s,net,exclude=ex),terminals=sorted([dict(name=n,gap_mm=s.GetClearance(e)/1e6)for n,nt,e in envs if nt!=net],key=lambda r:r['gap_mm'])))
# R121 retained-footprint copper vs every retained old conductor.
out['r121_old']=[dict(name=n,nearest=clearance(s,net,exclude=ex))for n,net,s in new if n.startswith('R121.')]
out['pairs']=sorted([dict(a=n,b=nn,gap_mm=s.GetClearance(ss)/1e6)for i,(n,net,s)in enumerate(new)for nn,nnet,ss in new[i+1:]if net!=nnet],key=lambda r:r['gap_mm'])
cs={'R125':rect(rx,ry,1.8,1.05),'C124':rect(cx,cy,1.6,1.05)}
for f in fs.values():
 if f.GetReference()=='C124':continue
 f.BuildCourtyardCaches();s=f.GetCourtyard(p.B_CrtYd)
 if f.GetReference()=='R121':s=transform(s,[14,18.5],[13.68,18.5])
 if s.Area():cs[f.GetReference()]=s
out['court']=sorted([dict(a=n,b=nn,gap_mm=s.GetClearance(ss)/1e6,overlap_mm2=cross(s,ss).Area()/1e12)for n,s in cs.items()if n in['R125','C124']for nn,ss in cs.items()if nn!=n],key=lambda r:r['gap_mm'])
(D/'counterfactual-uvlo-r121-left320.json').write_text(json.dumps(out,indent=2))
print('R121',out['r121_old']);print('UVLO_RETIRE',len(path),out['uvlo_old_length_mm']);print('TERMS',[(r['name'],r['land_clearance'][0],r['terminal_clearance'][0])for r in out['terms']]);print('ROUTES',[(r['name'],r['old'][0],r['terminals'][0])for r in out['routes']]);print('PAIR',out['pairs'][:10]);print('COURT',out['court'][:6]);print('LENGTHS',[(name,sum(math.dist(a,z)for a,z in zip(pts,pts[1:])))for name,net,pts in routes])
