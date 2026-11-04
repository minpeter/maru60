from pathlib import Path
s=Path('/tmp/v7-c124-rebound-short/main/check_route.py').read_text()
s=s.replace('rx,ry,cx,cy=15.59,20.1,15.65,19.025','rx,ry,cx,cy=15.54,20.15,15.65,19.05')
s=s.replace("ex=capids|rids|ret;new=[];envs=[];out={'source_sha':sha(BP),'status':'analytical, not constructed','terms':[],'r121_shift_mm':[-.05,0]}",'''# Counterfactual UVLO retirement, read-only ONLY. Not within current retained-net construction contract.
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
ex=capids|rids|ret|set(path);new=[];envs=[];out={'source_sha':sha(BP),'status':'COUNTERFACTUAL analytical expanded UVLO contract; not approved for construction','terms':[],'r121_shift_mm':[-.32,0],'uvlo_retirement_uuids':path,'uvlo_old_length_mm':sum(idx[u].GetLength()/1e6 for u in path)}''')
s=s.replace('[13.95,18.5]','[13.68,18.5]')
s=s.replace("routes=[('OVLO','USB_OVLO',[[13.95,19.325],[14.65,19.325],[14.65,19.9],[14.6,20.25],[14.65,20.45],[14.70,20.65],[14.95,20.75],[16.9,20.75],[20.575,20.825],[22,19.6]])", "routes=[('UVLO','USB_UVLO',[[14.2,16.35],[12.75,17.05],[12.75,19.8],[14.2,21.25],[16.75,21.25],[17.2,21.15]]),('OVLO','USB_OVLO',[[13.68,19.325],[14.5,19.325],[14.5,19.95],[14.58,20.55],[14.8,20.82],[16.9,20.85],[20.575,20.825],[22,19.6]])")
s=s.replace("out['pairs']=sorted", "# R121 retained-footprint copper vs every retained old conductor.\nout['r121_old']=[dict(name=n,nearest=clearance(s,net,exclude=ex))for n,net,s in new if n.startswith('R121.')]\nout['pairs']=sorted")
s=s.replace("route-r121-left50.json", "counterfactual-uvlo-r121-left320.json")
s=s.replace("print('TERMS'", "print('R121',out['r121_old']);print('UVLO_RETIRE',len(path),out['uvlo_old_length_mm']);print('TERMS'")
Path('/tmp/v7-c124-rebound-short/main/check_counterfactual.py').write_text(s)
