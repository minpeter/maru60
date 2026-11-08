from screen import *
# Finite second transition search; no board modification, source remains verified fix2.
N='EXT_GPIO25';start=(93.925,40.175);goal=(107.1,37.325)
search(N,p.F_Cu,start,box=(89,38.8,100,44),step=.025)
reach=json.loads((ROOT/'qa/reach-last.json').read_text());points=[tuple(a)for a in reach if a[0]>=96.0 and viaok(N,a)];points.sort(key=lambda a:math.dist(a,goal));selected=[]
for a in points:
 if all(math.dist(a,z)>.5 for z in selected):selected.append(a)
 if len(selected)==10:break
out=[]
for a in selected:
 path=search(N,p.B_Cu,a,goal=goal,box=(95.5,34,112,44),step=.025);out.append({'bridge':a,'B':path})
 if path:
  fp=search(N,p.F_Cu,start,goal=a,box=(89,38.8,100,44),step=.025);plan={'J3':[(93.5,39),start],'F':fp,'B':path,'bridge':a};(ROOT/'qa/bridge25-plan.json').write_text(json.dumps(plan,indent=2));print('BRIDGE SUCCESS',plan);break
(ROOT/'qa/bridge25-attempts.json').write_text(json.dumps(out,indent=2))
