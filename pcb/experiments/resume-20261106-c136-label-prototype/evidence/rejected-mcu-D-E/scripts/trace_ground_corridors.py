import sys
sys.path.insert(0,'/workspace/shared/maru60-resume/mcu-routing/native-pylibs')
import shapely as s,numpy as np,heapq,math
from shapely.geometry import Polygon,LineString,Point,box
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu');source=(R/'scripts/audit_north_return_b_c.py').read_text().split("print('Capture source planes")[0];exec(source)
b,planes,_,nh=capture(B,False)
def geom(ps):
 def pts(c):return [(c.CPoint(i).x/1e6,c.CPoint(i).y/1e6) for i in range(c.PointCount())]
 out=[]
 for i in range(ps.OutlineCount()):
  g=s.make_valid(Polygon(pts(ps.COutline(i)),[pts(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]))
  for part in s.get_parts(g):
   if part.geom_type in ['Polygon','MultiPolygon']:out.append(part)
 return s.union_all(out)
x0,y0,step,nx,ny=109,72.5,.025,281,225;xs=x0+np.arange(nx)*step;ys=y0+np.arange(ny)*step;X,Y=np.meshgrid(xs,ys);region=box(x0,y0,float(xs[-1]),float(ys[-1]));pg={l:geom(ps).intersection(region) for l,ps in planes.items()};graph=json.load(open(R/'qa/repair-D-material-graph.json'));anchor=next(u for u,v in graph['pad_inventory'].items() if v['ref']=='J1' and v['pad']=='A1');groundroot=graph['object_material_roots'][anchor]
gnds=[q for q in b.GetTracks() if isinstance(q,p.PCB_VIA) and q.GetNetname()=='GND' and graph['object_material_roots'][uid(q)]==groundroot and region.contains(Point(q.GetPosition().x/1e6,q.GetPosition().y/1e6))]
cases=[('MCU_GPIO27_B_reference',p.In2_Cu,[112.175,77.55]),('COL5_B_reference',p.In2_Cu,[112.7,77.1]),('COL5_In1_reference',p.In2_Cu,[112.35,75.5]),('modified_1V1_F_reference',p.In1_Cu,[111.275,76.45])];rows=[]
for name,l,start in cases:
 goalshapes=[]
 for v in gnds:
  pt=Point(v.GetPosition().x/1e6,v.GetPosition().y/1e6);goalshapes.append(pt.buffer(v.GetWidth(l)/2e6-.001,resolution=64).difference(pt.buffer(v.GetDrillValue()/2e6+.001,resolution=64)))
 goalgeom=s.union_all(goalshapes);sx=round((start[0]-x0)/step);sy=round((start[1]-y0)/step);attempts=[];best=None
 for radius in [.1,.075,.05]:
  safe=pg[l].buffer(-radius,resolution=32);mask=s.intersects_xy(safe,X,Y);goals=s.intersects_xy(goalgeom,X,Y)&mask
  if not mask[sy,sx]:attempts.append({'radius_mm':radius,'status':'start_outside_eroded_plane'});continue
  dist=np.full(nx*ny,np.inf);prev=np.full(nx*ny,-1,dtype=np.int32);done=np.zeros(nx*ny,dtype=bool);sid=sy*nx+sx;dist[sid]=0;hq=[(0.,sid)];found=None
  while hq:
   cost,n=heapq.heappop(hq)
   if done[n]:continue
   done[n]=True;y,x=divmod(n,nx)
   if goals[y,x]:found=n;break
   for dx,dy,w in [(1,0,1),(0,1,1),(-1,0,1),(0,-1,1),(1,1,2**.5),(-1,1,2**.5),(1,-1,2**.5),(-1,-1,2**.5)]:
    xx=x+dx;yy=y+dy
    if not(0<=xx<nx and 0<=yy<ny) or not mask[yy,xx]:continue
    if dx and dy and not(mask[y,xx] and mask[yy,x]):continue
    nn=yy*nx+xx;nc=cost+w
    if nc<dist[nn]:dist[nn]=nc;prev[nn]=n;heapq.heappush(hq,(nc,nn))
  if found is None:attempts.append({'radius_mm':radius,'status':'no_sampled_path','visited':int(done.sum())});continue
  path=[];n=found
  while n>=0:
   y,x=divmod(n,nx);path.append([float(xs[x]),float(ys[y])]);n=prev[n]
  path.reverse();simpl=[path[0]]
  for a,v,c in zip(path,path[1:],path[2:]):
   if abs((v[0]-a[0])*(c[1]-v[1])-(v[1]-a[1])*(c[0]-v[0]))<1e-9:continue
   simpl.append(v)
  simpl.append(path[-1]);line=LineString(simpl);inside=bool(pg[l].covers(line));clearance=float(line.distance(pg[l].boundary));end=Point(*simpl[-1]);target=next(v for v,g in zip(gnds,goalshapes) if g.covers(end));best={'screen_radius_mm':radius,'native_polygon_derived_path_contained':inside,'minimum_path_to_plane_boundary_distance_mm':clearance,'twice_minimum_path_clearance_mm':2*clearance,'length_mm':line.length,'path_mm':simpl,'target_GND_via_uuid':uid(target),'target_GND_via_mm':[target.GetPosition().x/1e6,target.GetPosition().y/1e6],'target_material_root_is_J1':True};attempts.append({'radius_mm':radius,'status':'path_found','visited':int(done.sum())})
  if inside and clearance>0:break
 rows.append({'name':name,'reference_plane':b.GetLayerName(l),'start_mm':start,'attempts':attempts,'path':best});print(name,best,flush=True)
r={'candidate_sha256':h(B),'region_mm':[x0,y0,float(xs[-1]),float(ys[-1])],'grid_mm':step,'paths':rows,'method':'Actual native filled planes minus every through drill, converted with make_valid preserving positive-area polygons and holes; zero-area fracture bridge lines are not copper boundaries. Candidate path containment and minimum boundary distance are checked against the resulting polygon, not inferred from graph connectedness. Width is a nominal available plane corridor along this chosen path, not a global maximum or a signal/power return-current simulation.','limits':'Local finite grid. Representative plane points, not claimed measured current paths. MCU_GPIO27 has no F.Cu continuation yet, so an actual F-to-B transition return path is not qualified. No SI, EMI or power stability claim.'};(R/'qa/repair-D-ground-corridors.json').write_text(json.dumps(r,indent=2))
