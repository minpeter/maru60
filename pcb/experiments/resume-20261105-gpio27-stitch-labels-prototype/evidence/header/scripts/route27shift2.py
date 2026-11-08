import pcbnew as p,json,sys,heapq,math,time,collections,uuid
from pathlib import Path
ROOT=Path('/workspace/shared/maru60-resume/continuation-c782/header');SRC=Path('/workspace/shared/maru60-resume/combined-trial/pcb/maru60.kicad_pcb')
b=p.LoadBoard(str(SRC))
barrier_uuid='fdd2376a-e263-51cf-8638-7d8989c5ffc8'
barrier=next(q for q in b.GetTracks()if q.m_Uuid.AsString()==barrier_uuid)
detour=[(96,40.05),(96.25,40.3),(96.25,40.55),(96.5,40.8),(97.35,40.8),(97.6,40.55),(97.6,40.3),(97.85,40.05),(98.25,40.05)]
V0=lambda xy:p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6))
barrier.SetEnd(V0(detour[1]));detour_added=[]
for a,z in zip(detour[1:],detour[2:]):
 q=p.PCB_TRACK(b);q.SetStart(V0(a));q.SetEnd(V0(z));q.SetWidth(150000);q.SetLayer(p.B_Cu);q.SetNetCode(barrier.GetNetCode());b.Add(q);detour_added.append(q)
shifted_via=next(q for q in b.GetTracks()if q.m_Uuid.AsString()=='bd60c430-58d5-568a-b034-a604187f20ee');shifted_via.SetPosition(p.VECTOR2I(96650000,41625000))
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
 return all(s.GetClearance(shapes[k][1])>=(150000 if shapes[k][0] in ['','GND']else 205000) for k in keys)
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
 print('FAILED',net,b.GetLayerName(l),count,round(time.monotonic()-t,2),flush=True);return None
if __name__=='__main__':
 for n,pad in [('EXT_GPIO24','12'),('EXT_GPIO25','11')]:
  f=next(f for f in b.GetFootprints()if f.GetReference()=='U13');q=next(q for q in f.Pads()if q.GetNumber()==pad);a=(q.GetPosition().x/1e6,q.GetPosition().y/1e6)
  search(n,p.B_Cu,a,box=(87.5,39,92,46),fanout=True,step=.025)
