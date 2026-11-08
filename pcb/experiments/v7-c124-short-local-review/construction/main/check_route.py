from common import *
rx,ry,cx,cy=15.59,20.1,15.65,19.025
terms=[('R125.1','USB_DVDT',[rx,ry],[rx+.45,ry],[.4,.3],[rx+.175,ry-.275,rx+.55,ry+.275]),('R125.2','USB_DVDT_CAP',[rx,ry],[rx-.45,ry],[.4,.3],[rx-.55,ry-.275,rx-.175,ry+.275]),('C124.1','USB_DVDT_CAP',[cx,cy],[cx-.375,cy],[.35,.5],[cx-.525,cy-.275,cx-.125,cy+.275]),('C124.2','GND',[cx,cy],[cx+.375,cy],[.35,.5],[cx+.125,cy-.275,cx+.525,cy+.275])]
ex=capids|rids|ret;new=[];envs=[];out={'source_sha':sha(BP),'status':'analytical, not constructed','terms':[],'r121_shift_mm':[-.05,0]}
for name,net,org,at,wh,bb in terms:
 land=rect(*at,*wh);e=envelope(org,bb);new.append((name,net,land));envs.append((name,net,e));out['terms'].append(dict(name=name,land_center=at,land_size=wh,land_clearance=clearance(land,net,exclude=ex),terminal_clearance=clearance(e,net,exclude=ex),land=dump(land),terminal=dump(e)))
for q in fs['R121'].Pads():new.append(('R121.'+q.GetNumber(),q.GetNetname(),transform(copper(q,p.B_Cu),[14,18.5],[13.95,18.5])))
new.append(('old-ground-bridge','GND',compact))
routes=[('OVLO','USB_OVLO',[[13.95,19.325],[14.65,19.325],[14.65,19.9],[14.6,20.25],[14.65,20.45],[14.70,20.65],[14.95,20.75],[16.9,20.75],[20.575,20.825],[22,19.6]]),('DVDT','USB_DVDT',[[17.25,19.4],[16.85,19.4],[16.5,19.8],[rx+.45,ry]]),('CAP','USB_DVDT_CAP',[[rx-.45,ry],[cx-.375,cy]]),('GND','GND',[[cx+.375,cy],[16.4,18.9]])]
out['routes']=[]
for name,net,pts in routes:
 for i,(a,z)in enumerate(zip(pts,pts[1:])):
  s=seg(a,z);new.append((name+str(i),net,s));out['routes'].append(dict(name=name+str(i),net=net,start=a,end=z,length=math.dist(a,z),old=clearance(s,net,exclude=ex),terminals=sorted([dict(name=n,gap_mm=s.GetClearance(e)/1e6)for n,nt,e in envs if nt!=net],key=lambda r:r['gap_mm'])))
out['pairs']=sorted([dict(a=n,b=nn,gap_mm=s.GetClearance(ss)/1e6)for i,(n,net,s)in enumerate(new)for nn,nnet,ss in new[i+1:]if net!=nnet],key=lambda r:r['gap_mm'])
cs={'R125':rect(rx,ry,1.8,1.05),'C124':rect(cx,cy,1.6,1.05)}
for f in fs.values():
 if f.GetReference()=='C124':continue
 f.BuildCourtyardCaches();s=f.GetCourtyard(p.B_CrtYd)
 if f.GetReference()=='R121':s=transform(s,[14,18.5],[13.95,18.5])
 if s.Area():cs[f.GetReference()]=s
out['court']=sorted([dict(a=n,b=nn,gap_mm=s.GetClearance(ss)/1e6,overlap_mm2=cross(s,ss).Area()/1e12)for n,s in cs.items()if n in['R125','C124']for nn,ss in cs.items()if nn!=n],key=lambda r:r['gap_mm'])
(D/'route-r121-left50.json').write_text(json.dumps(out,indent=2))
print('TERMS',[(r['name'],r['land_clearance'][0],r['terminal_clearance'][0])for r in out['terms']]);print('ROUTES',[(r['name'],r['old'][0],r['terminals'][0])for r in out['routes']]);print('PAIR',out['pairs'][:10]);print('COURT',out['court'][:6]);print('LENGTHS',[(name,sum(math.dist(a,z)for a,z in zip(pts,pts[1:])))for name,net,pts in routes])
