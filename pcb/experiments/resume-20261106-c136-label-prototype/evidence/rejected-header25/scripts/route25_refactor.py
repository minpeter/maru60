import pcbnew as p,json,sys,heapq,math,time,collections,uuid
from pathlib import Path
ROOT=Path('/workspace/shared/maru60-resume/continuation-fix2/header25');SRC=Path('/workspace/shared/maru60-resume/continuation-c782/combined27fix2/pcb/maru60.kicad_pcb')
b=p.LoadBoard(str(SRC))
V0=lambda a:p.VECTOR2I(round(a[0]*1e6),round(a[1]*1e6))
removed=[];removed_objects=[]
for q in list(b.GetTracks()):
 if isinstance(q,p.PCB_VIA)or q.GetNetname()!='GPIO_ISOLATE'or q.GetLayer()!=p.B_Cu:continue
 a,z=q.GetStart(),q.GetEnd()
 if min(a.y,z.y)>=35050000 and max(a.y,z.y)<=41500000 and min(a.x,z.x)>=108100000 and max(a.x,z.x)<=109300000:
  removed.append(q.m_Uuid.AsString());removed_objects.append(q);code=q.GetNetCode();b.Remove(q)
detour=[(108.1,35.05),(109.6,35.05),(109.6,40.0),(109.3,40.3),(109.3,41.5)];refactor_added=[]
for a,z in zip(detour,detour[1:]):
 q=p.PCB_TRACK(b);q.SetStart(V0(a));q.SetEnd(V0(z));q.SetWidth(150000);q.SetLayer(p.B_Cu);q.SetNetCode(code);b.Add(q);refactor_added.append(q)
V=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6));U=lambda q:q.m_Uuid.AsString();L=[p.B_Cu,p.F_Cu,p.In1_Cu,p.In2_Cu];ST=.025;C=150000;W=150000
shapes={};bins={l:collections.defaultdict(list)for l in L}
def addobs(q):
 for l in L:
  if not q.IsOnLayer(l):continue
  s=p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l);bb=s.BBox();key=(U(q),l);shapes[key]=(q.GetNetname(),s)
  for x in range(bb.GetX()//1000000-1,bb.GetRight()//1000000+2):
   for y in range(bb.GetY()//1000000-1,bb.GetBottom()//1000000+2):bins[l][x,y].append(key)
for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]:addobs(q)
drilled_signal_uuids={U(q)for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]if isinstance(q,(p.PCB_VIA,p.PAD))and q.HasHole()and q.GetNetname()not in['','GND']}
def coll(net,l,s):
 bb=s.BBox();keys=set()
 for x in range(bb.GetX()//1000000,bb.GetRight()//1000000+1):
  for y in range(bb.GetY()//1000000,bb.GetBottom()//1000000+1):keys.update(bins[l].get((x,y),()))
 return any(shapes[k][0]!=net and s.GetClearance(shapes[k][1])<(205000 if k[0]in drilled_signal_uuids else C) for k in keys)
def edge(net,l,a,z,w=W):return not coll(net,l,p.SHAPE_SEGMENT(V(*a),V(*z),w))
pads=[q for f in b.GetFootprints()for q in f.Pads()]
def viaok(net,a):
 s=p.SHAPE_CIRCLE(V(*a),250000);bb=s.BBox();keys=set()
 for l in L:
  for x in range(bb.GetX()//1000000,bb.GetRight()//1000000+1):
   for y in range(bb.GetY()//1000000,bb.GetBottom()//1000000+1):keys.update(bins[l].get((x,y),()))
 return all(shapes[k][0]==net or s.GetClearance(shapes[k][1])>=(150000 if shapes[k][0] in ['','GND']else 205000) for k in keys)
def simplify(net,l,path):
 # Greedy visibility shortcuts retain clearance; favor long straight runs.
 out=[path[0]];i=0
 while i<len(path)-1:
  j=len(path)-1
  while j>i+1 and not edge(net,l,path[i],path[j]):j-=1
  out.append(path[j]);i=j
 return out
def search(net,l,start,goal=None,box=None,fanout=False,step=.05):
 X0,Y0,X1,Y1=box;coords=lambda t:(round(t[0]*step,6),round(t[1]*step,6));S=tuple(round(x/step)for x in start);G=tuple(round(x/step)for x in goal)if goal else None
 def h(n):return math.hypot(n[0]-G[0],n[1]-G[1])if G else 0
 heap=[(h(S),0,S)];dist={S:0};prev={};count=0;via_cache={};t=time.monotonic()
 while heap:
  _,g,n=heapq.heappop(heap)
  if g!=dist[n]:continue
  count+=1;a=coords(n)
  if (G and n==G)or(fanout and math.dist(a,start)>=.45 and viaok(net,a)):
   path=[a]
   while n!=S:n=prev[n];path.append(coords(n))
   path.reverse();path[0]=start
   if goal:path[-1]=goal
   simple=simplify(net,l,path); print('FOUND',net,b.GetLayerName(l),count,round(time.monotonic()-t,2),simple,flush=True);return simple
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   v=n[0]+dx,n[1]+dy;z=coords(v)
   if not(X0<=z[0]<=X1 and Y0<=z[1]<=Y1):continue
   ng=g+(1.41421356237 if dx and dy else 1)
   if ng>=dist.get(v,float('inf')):continue
   if not edge(net,l,a,z):continue
   dist[v]=ng;prev[v]=n;heapq.heappush(heap,(ng+h(v),ng,v))
 (ROOT/'qa/reach-last.json').write_text(json.dumps([coords(q)for q in dist]));print('FAILED',net,b.GetLayerName(l),count,round(time.monotonic()-t,2), 'bbox', tuple([min(coords(q)[0]for q in dist),min(coords(q)[1]for q in dist),max(coords(q)[0]for q in dist),max(coords(q)[1]for q in dist)]),flush=True);return None
if __name__=='__main__':
 N='EXT_GPIO25';u=search(N,p.B_Cu,(107.1,37.325),box=(106,37,109.2,41.3),fanout=True,step=.025);j=search(N,p.B_Cu,(93.5,39),box=(92,39,96,42),fanout=True,step=.025);f=search(N,p.F_Cu,j[-1],goal=u[-1],box=(90,38.8,111,46),step=.025)if u and j else None
 plan={'U11':u,'J3':j,'F':f,'removed':removed,'detour':detour};(ROOT/'qa/route25-refactor-plan.json').write_text(json.dumps(plan,indent=2));print(plan)
