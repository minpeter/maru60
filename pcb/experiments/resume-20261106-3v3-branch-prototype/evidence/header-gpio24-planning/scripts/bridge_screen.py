from optimistic_screen import *
front={tuple(x)for x in json.loads((ROOT/'qa/reach-last.json').read_text())}
start=(92.5,39.0);step=.05;net='EXT_GPIO24';S=tuple(round(x/step)for x in start);Q=collections.deque([S]);prev={S:None};coords=lambda t:(round(t[0]*step,6),round(t[1]*step,6));sites=[];found=None
while Q:
 n=Q.popleft();a=coords(n)
 if a in front and viaok(net,a):
  found=n;break
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
  v=n[0]+dx,n[1]+dy;z=coords(v)
  if v in prev or not(87<=z[0]<=106 and 36.8<=z[1]<=45):continue
  if not edge(net,p.B_Cu,a,z):continue
  prev[v]=n;Q.append(v)
path=[]
if found:
 while found is not None:path.append(coords(found));found=prev[found]
 path.reverse();path=simplify(net,p.B_Cu,path)
out={'B_reached_count':len(prev),'F_reached_count':len(front),'bridge_path':path,'box':[87,36.8,106,45],'step_mm':step,'optimistic_COL13_removed_only_in_memory':True}
(ROOT/'qa/bridge-screen.json').write_text(json.dumps(out,indent=2));print(out)
(ROOT/'qa/B-reach.json').write_text(json.dumps([coords(x)for x in prev]))
