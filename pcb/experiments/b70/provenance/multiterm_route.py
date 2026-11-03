"""Coordinated pilot displaced-net reroute, full finite board graph and native postcheck required.
No original tracks moved further; one disconnected component pair joined at native anchors.
Preserve explicit USB/reference corridor and exact retained supply fills.
"""
from pathlib import Path
import sys,time
R=Path(__file__).parent;P=R.parent.parent
netname=sys.argv[1];width=float(sys.argv[2]);assert netname.startswith(('KEY_RGB_CHAIN_','KEY_','UG_LED_','COL','ROW'))
s=(P/'router_library_source.py').read_text().split('keys=json.load')[0].replace('P=Path(__file__).resolve().parents[1]','P=R').replace("P/'maru60.kicad_pcb'","P/'input.kicad_pcb'").replace('G=.2;NX=1426;NY=474','G=.1;NX=2851;NY=947').replace('p.FromMM(.2)',f'p.FromMM({width})').replace("'width_mm':.2",f"'width_mm':{width}").replace('p.FromMM(.6)','p.FromMM(.5)').replace('p.FromMM(.3)','p.FromMM(.25)')
s=s.replace("'diameter_mm':.6","'diameter_mm':.5").replace("'drill_mm':.3","'drill_mm':.25")
exec(compile(s,'router','exec'));exec(compile((R.parent.parent/'exact_route_masks.py').read_text().replace('.235',str(width/2+.16)),'shapes','exec'))
net=b.FindNet(netname).GetNetCode();cm,vm=masks(net);center=json.load(open(R/'smooth-pair-plan.json'))['centerline_mm'];
for a,z in zip(center,center[1:]):
 for mask in cm:capsule(mask,a,z,.65+.16+width/2)
 capsule(vm,a,z,.65+.16+.25)
# Preserved connector/core USB escapes cannot be cut by a new nonUSB route.
for q in b.GetTracks():
 if not q.GetNetname().startswith('USB_'):continue
 half=p.ToMM(q.GetWidth(p.F_Cu)if isinstance(q,p.PCB_VIA)else q.GetWidth())/2
 for mask in cm:capsule(mask,pt(q.GetStart()),pt(q.GetEnd()),half+.35+width/2)
 capsule(vm,pt(q.GetStart()),pt(q.GetEnd()),half+.6)
from matplotlib.path import Path as MPath
from scipy.ndimage import binary_dilation
for zone in b.Zones():
 if zone.GetIsRuleArea()or zone.GetNetname()in['GND',netname]:continue
 for k,layer in enumerate([p.F_Cu,p.B_Cu]):
  if not zone.IsOnLayer(layer):continue
  ps=zone.GetFilledPolysList(layer);mask=np.zeros((NY,NX),bool)
  for oi in range(ps.OutlineCount()):
   ch=ps.Outline(oi);verts=[pt(ch.CPoint(j))for j in range(ch.PointCount())];xs=[v[0]for v in verts];ys=[v[1]for v in verts];x0=max(0,int(min(xs)/G)-1);x1=min(NX,int(max(xs)/G)+2);y0=max(0,int(min(ys)/G)-1);y1=min(NY,int(max(ys)/G)+2);yy,xx=np.mgrid[y0:y1,x0:x1];pts=np.column_stack((xx.ravel()*G,yy.ravel()*G));inside=MPath(verts).contains_points(pts)
   for hi in range(ps.HoleCount(oi)):
    ch=ps.Hole(oi,hi);inside &= ~MPath([pt(ch.CPoint(j))for j in range(ch.PointCount())]).contains_points(pts)
   mask[y0:y1,x0:x1]|=inside.reshape((y1-y0,x1-x0))
  yy,xx=np.ogrid[-4:5,-4:5];cm[k]|=binary_dilation(mask,structure=(xx*xx+yy*yy<=16));vm|=binary_dilation(mask,structure=(xx*xx+yy*yy<=16))
# New strategy: all native disconnected components at once, dense existing-track
# anchors, and a closest-component spanning tree. Do not prioritize one DRC pair.
# No ripping of existing copper; route the remaining matrix/control signals.
uid=lambda q:q.m_Uuid.AsString()
c=b.GetConnectivity();c.Build(b)
objs=[q for q in b.GetTracks() if q.GetNetCode()==net]+[q for f in b.GetFootprints() for q in f.Pads() if q.GetNetCode()==net]
seen=set();groups=[]
for obj in objs:
 if uid(obj) in seen:continue
 todo=[obj];members=[];pads=[];anchors={}
 while todo:
  q=todo.pop();u=uid(q)
  if u in seen:continue
  seen.add(u);members.append(u);todo.extend(c.GetConnectedTracks(q));todo.extend(c.GetConnectedPads(q))
  if isinstance(q,p.PAD):pads.append(q.GetParentFootprint().GetReference()+'.'+q.GetNumber())
  if isinstance(q,(p.PAD,p.PCB_VIA)):positions=[pt(q.GetPosition())]
  else:
   aa,zz=pt(q.GetStart()),pt(q.GetEnd());n=max(1,math.ceil(math.dist(aa,zz)/G));positions=[[aa[0]+(zz[0]-aa[0])*i/n,aa[1]+(zz[1]-aa[1])*i/n]for i in range(n+1)]
  for l,layer in enumerate([p.F_Cu,p.B_Cu]):
   if not q.IsOnLayer(layer):continue
   for xy in positions:
    gx,gy=grid(xy)
    if not cm[l][gy,gx]:anchors[(l,gx,gy)]=xy
 groups.append({'members':members,'pads':pads,'anchors':anchors})
print(netname,'components',len(groups),'anchors',[len(x['anchors'])for x in groups],flush=True)
meta={'net':netname,'source':'input.kicad_pcb','width_mm':width,'full_board_grid_mm':G,'strategy':'All native connected components, dense original track anchors at <=0.1mm, nearest cross-component A* spanning tree, additive routing only; fixed USB strip, existing escapes and power/core protection unchanged','components_before':[{k:v for k,v in g.items()if k!='anchors'}for g in groups],'connections':[]}
existing={grid(pt(q.GetPosition()))for q in b.GetTracks()if isinstance(q,p.PCB_VIA)and q.GetNetCode()==net};started=time.monotonic()
from scipy.spatial import cKDTree
while len(groups)>1:
 pairs=[]
 for i,a in enumerate(groups):
  if not a['anchors']:continue
  ax=np.array([[x,y]for l,x,y in a['anchors']]);tree=cKDTree(ax)
  for j,z in enumerate(groups[i+1:],i+1):
   if not z['anchors']:continue
   zx=np.array([[x,y]for l,x,y in z['anchors']]);dist=tree.query(zx)[0].min();pairs.append((dist,i,j))
 found=False
 for dist,i,j in sorted(pairs):
  starts,ends=groups[i]['anchors'],groups[j]['anchors'];tx=[x for l,x,y in ends];ty=[y for l,x,y in ends];xmin,xmax,ymin,ymax=min(tx),max(tx),min(ty),max(ty)
  def h(x,y):
   dx=max(0,xmin-x,x-xmax);dy=max(0,ymin-y,y-ymax);return max(dx,dy)+.41421356*min(dx,dy)
  heap=[];cost={};prev={};path=None
  for st in starts:cost[st]=0;heapq.heappush(heap,(h(st[1],st[2]),0,*st))
  expanded=0
  while heap:
   _,g,l,x,y=heapq.heappop(heap);state=(l,x,y)
   if g>cost.get(state,1e30)+1e-8:continue
   if state in ends:
    path=[state]
    while path[-1]not in starts:path.append(prev[path[-1]])
    path=path[::-1];break
   expanded+=1
   opts=[]
   for dx,dy,w in D:
    X,Y=x+dx,y+dy
    if not(0<=X<NX and 0<=Y<NY)or cm[l][Y,X]:continue
    if dx and dy and(cm[l][y,X]or cm[l][Y,x]):continue
    opts.append((l,X,Y,w))
   if (not vm[y,x]or(x,y)in existing)and not cm[1-l][y,x]:opts.append((1-l,x,y,45))
   for L,X,Y,w in opts:
    ng=g+w;st=(L,X,Y)
    if ng>=cost.get(st,1e30):continue
    cost[st]=ng;prev[st]=state;heapq.heappush(heap,(ng+h(X,Y),ng,L,X,Y))
  print('pair',i,j,'distance',dist*G,'expanded',expanded,'found',bool(path),flush=True)
  meta['connections'].append({'groups':[i,j],'euclidean_gap_mm':dist*G,'expanded_states':expanded,'found':bool(path)})
  if not path:continue
  add3(path,net,existing)
  for endpoint,exact in[(path[0],starts[path[0]]),(path[-1],ends[path[-1]])]:
   l,x,y=endpoint;addpath([(x,y)],exact,[x*G,y*G],net,l,'exact native track interior anchor')
  groups[i]['anchors'].update(groups[j]['anchors']);groups[i]['members']+=groups[j]['members'];groups[i]['pads']+=groups[j]['pads']
  for l,x,y in path:groups[i]['anchors'][(l,x,y)]=[x*G,y*G]
  groups.pop(j);found=True;break
 if not found:break
meta['elapsed_seconds']=time.monotonic()-started;meta['path_found']=bool(segments);meta['components_remaining']=len(groups)
if segments:
 p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();out=R/('route-'+netname+'.kicad_pcb');p.SaveBoard(str(out),b)
 for ext in['.kicad_pro','.kicad_sch']:shutil.copyfile(R/('input'+ext),out.with_suffix(ext))
 meta.update(output=str(out),native_opens_presave=b.GetConnectivity().GetUnconnectedCount(False),segments=segments,vias=vias,added_length_mm=sum(math.dist(t['start'],t['end'])for t in segments));print('Saved',out,'opens',meta['native_opens_presave'],'length',meta['added_length_mm'],'vias',len(vias),flush=True)
(R/('route-'+netname+'.json')).write_text(json.dumps(meta,indent=2))
