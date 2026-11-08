import sys
sys.path.insert(0,'/workspace/shared/maru60-resume/mcu-routing/native-pylibs')
import pcbnew as p,shapely as s,numpy as np,json,heapq,math,time,hashlib,shutil
from shapely.geometry import Polygon,Point,LineString,box
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-c782/mcu');S=R/'north-escape-c/pcb/maru60.kicad_pcb';b=p.LoadBoard(str(S));layers=[p.F_Cu,p.B_Cu];inners=[p.In1_Cu,p.In2_Cu];net='MCU_GPIO27';region=box(110.01,32,140.01,78.5);uid=lambda q:q.m_Uuid.AsString()
def geom(ps):
 def pts(c):return [(c.CPoint(i).x/1e6,c.CPoint(i).y/1e6) for i in range(c.PointCount())]
 gs=[]
 for i in range(ps.OutlineCount()):
  z=s.make_valid(Polygon(pts(ps.COutline(i)),[pts(ps.CHole(i,h)) for h in range(ps.HoleCount(i))]))
  gs.extend(g for g in s.get_parts(z) if g.geom_type in ['Polygon','MultiPolygon'])
 return s.union_all(gs)
def shape(q,l):
 sh=p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2) if isinstance(q,p.PCB_VIA) else q.GetEffectiveShape(l);ps=p.SHAPE_POLY_SET();sh.TransformToPolygon(ps,100,p.ERROR_OUTSIDE);ps.Simplify();return geom(ps)
items=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];obs=[[],[]];vobs=[];holes=[];goals=[];owntrans=[]
print('Collect geometry',flush=True)
for q in items:
 for i,l in enumerate(layers):
  if not q.IsOnLayer(l):continue
  g=shape(q,l)
  if not g.intersects(region.buffer(1)):continue
  vobs.append(g)
  if q.GetNetname()!=net:obs[i].append(g)
  if q.GetNetname()==net and isinstance(q,p.PAD) and q.GetParentFootprint().GetReference() in ['R145','R135']:goals.append((g.buffer(-.2),i))
 if isinstance(q,(p.PAD,p.PCB_VIA)) and q.HasHole():
  sh=q.GetEffectiveHoleShape();ps=p.SHAPE_POLY_SET();sh.TransformToPolygon(ps,100,p.ERROR_OUTSIDE);g=geom(ps)
  if g.intersects(region.buffer(1)):holes.append(g)
 if isinstance(q,p.PCB_VIA) and q.GetNetname()==net:owntrans.append(Point(q.GetPosition().x/1e6,q.GetPosition().y/1e6).buffer(q.GetWidth(p.F_Cu)/2e6+.205,resolution=64))
planes=[]
for l in inners:
 ps=s.union_all([geom(z.GetFilledPolysList(l)) for z in b.Zones() if z.IsOnLayer(l) and z.GetNetname()=='GND' and not z.GetIsRuleArea()]).difference(s.union_all(holes));planes.append(ps)
ob=[s.union_all(x).buffer(.2251,resolution=32) for x in obs];vob=s.union_all(vobs).buffer(.456,resolution=32);ref=[s.union_all([q,s.union_all(owntrans)]).buffer(-.0751,resolution=32) for q in planes]
step=.05;x0=110.01;y0=32;nx=601;ny=931;xs=x0+np.arange(nx)*step;ys=y0+np.arange(ny)*step;X,Y=np.meshgrid(xs,ys);mask=np.stack([~s.intersects_xy(o,X,Y) for o in ob]);
for i in range(2):mask[i]&=s.intersects_xy(ref[i],X,Y)
# Stronger source-plane web screen:0.455mm antipad +0.20mm nominal remaining web.
raw_vmask=~s.intersects_xy(vob,X,Y);vmask=raw_vmask.copy()
for pl in planes:vmask&=s.intersects_xy(pl.buffer(-.655,resolution=32),X,Y)
gmask=np.zeros_like(mask)
for g,i in goals:gmask[i]|=s.intersects_xy(g,X,Y)
gmask&=mask
start=(43,900,0);print('masks',mask.sum(axis=(1,2)),vmask.sum(),'start',mask[start[2],start[1],start[0]],'goals',gmask.sum(),flush=True)
def idx(x,y,l):return l*nx*ny+y*nx+x
def inv(n):l,k=divmod(n,nx*ny);y,x=divmod(k,nx);return x,y,l
N=nx*ny*2;dist=np.full(N,np.inf);prev=np.full(N,-1,dtype=np.int32);closed=np.zeros(N,dtype=bool);sid=idx(*start);dist[sid]=0;queue=[(0.,sid)];count=0;found=None;t=time.monotonic()
while queue:
 cost,n=heapq.heappop(queue)
 if closed[n]:continue
 closed[n]=1;count+=1;x,y,l=inv(n)
 if gmask[l,y,x]:found=n;break
 for dx,dy,w in [(1,0,1),(0,1,1),(-1,0,1),(0,-1,1),(1,1,2**.5),(-1,1,2**.5),(1,-1,2**.5),(-1,-1,2**.5)]:
  xx=x+dx;yy=y+dy
  if not(0<=xx<nx and 0<=yy<ny) or not mask[l,yy,xx]:continue
  if dx and dy and not(mask[l,y,xx] and mask[l,yy,x]):continue
  nn=idx(xx,yy,l);nc=cost+w
  if nc<dist[nn]:dist[nn]=nc;prev[nn]=n;heapq.heappush(queue,(nc,nn))
 if vmask[y,x] and mask[1-l,y,x]:
  nn=idx(x,y,1-l);nc=cost+80
  if nc<dist[nn]:dist[nn]=nc;prev[nn]=n;heapq.heappush(queue,(nc,nn))
 if count%100000==0:print('visited',count,flush=True)
path=[]
if found is not None:
 n=found
 while n>=0:
  x,y,l=inv(n);path.append([round(float(xs[x]),6),round(float(ys[y]),6),int(l)]);n=prev[n]
 path.reverse();simple=[path[0]]
 for a,v,c in zip(path,path[1:],path[2:]):
  if a[2]==v[2]==c[2] and abs((v[0]-a[0])*(c[1]-v[1])-(v[1]-a[1])*(c[0]-v[0]))<1e-9:continue
  simple.append(v)
 simple.append(path[-1]);path=simple
reached=[]
for l in range(2):
 yy,xx=np.nonzero(closed.reshape(2,ny,nx)[l]);reached.append({'layer':b.GetLayerName(layers[l]),'vertices':len(xx),'bbox_mm':[float(xs[xx.min()]),float(ys[yy.min()]),float(xs[xx.max()]),float(ys[yy.max()])] if len(xx) else None})
r={'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'region_mm':[110.01,32,140.01,78.5],'grid_mm':step,'new_via_plane_boundary_screen_mm':.655,'new_via_old_shadow_screen_mm':.456,'found':found is not None,'visited':count,'seconds':time.monotonic()-t,'path':path,'reached':reached};(R/'qa/gpio27-continuation-search.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)
if found is None:
 reach=closed.reshape(2,ny,nx);cand=reach[0]&raw_vmask&mask[1];yy,xx=np.nonzero(cand);opts=[]
 for y,x in zip(yy,xx):
  pt=Point(float(xs[x]),float(ys[y]));bounds=[float(pt.distance(pl.boundary)) if pl.covers(pt) else -float(pt.distance(pl)) for pl in planes];opts.append({'xy_mm':[float(xs[x]),float(ys[y])],'plane_boundary_distances_mm':bounds,'minimum_mm':min(bounds)})
 opts.sort(key=lambda q:q['minimum_mm'],reverse=True);r['reachable_outer_shadow_screened_via_sites_before_plane_web_test']=len(opts);r['best_ordinary_screened_sites']=opts[:10];r['south_boundary_reached']=bool(reach[:,-1,:].any());(R/'qa/gpio27-continuation-frontier.json').write_text(json.dumps(r,indent=2));print('FRONTIER',len(opts),opts[:10],flush=True);sys.exit(2)

raise RuntimeError('Unexpected path during diagnostic-only repeat; no CAD write permitted')
