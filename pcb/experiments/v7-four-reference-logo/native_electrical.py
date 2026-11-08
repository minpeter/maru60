"""Fresh native electrical/partition inventory of one recovered-source or trial board."""
import sys,json,math,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import native_ink as n
import sexp as sx
p=n.p;path=Path(sys.argv[1]);out=Path(sys.argv[2]);scene=n.Scene(path);b=scene.board;t=sx.parse(path.read_text());nets={int(x[1]):x[2]for x in sx.all(t,'net')};raw={}
for node in t:
 if not isinstance(node,list)or not node:continue
 for item in sx.all(node,'pad')if node[0]=='footprint'else[node]if node[0]in ['segment','arc','via','zone']else[]:
  u=sx.get(item,'uuid')[1];net=sx.get(item,'net');n.require(u not in raw,'Duplicate conductor UUID');raw[u]=nets[int(net[1])]if net else''
tracks=list(b.GetTracks());pads=[x for fp in b.GetFootprints()for x in fp.Pads()];allitems=tracks+pads;byid={n.UID(x):x for x in allitems};native=lambda:{n.UID(x):x.GetNetname()for x in allitems+list(b.Zones())};n.require(native()==raw,'All raw/native net identities on load');b.BuildConnectivity();n.require(native()==raw,'All raw/native net identities after connectivity');cn=b.GetConnectivity();edges=set()
for u,x in byid.items():
 if not x.GetNetname():continue
 for y in list(cn.GetConnectedTracks(x))+list(cn.GetConnectedPads(x)):
  v=n.UID(y)
  if u==v:continue
  n.require(v in byid and x.GetNetname()==y.GetNetname(),'Unknown/cross-net native edge');edges.add(tuple(sorted([u,v])))
geometry={};lengths={};holes={};pad_geometry={};units=p.UNITS_PROVIDER(p.pcbIUScale,p.EDA_UNITS_MM);diagnostics={}
for u,x in byid.items():
 pos=[n.XY(x.GetPosition())]
 if isinstance(x,p.PCB_TRACK)and not isinstance(x,p.PCB_VIA):pos+=[n.XY(x.GetStart()),n.XY(x.GetEnd())]
 diagnostics[u]={'description':x.GetItemDescription(units,True),'positions_mm':[[v/1e6 for v in xy]for xy in pos]}
 if isinstance(x,p.PAD):
  pad_geometry[u]={'position_nm':n.XY(x.GetPosition()),'size_nm':n.XY(x.GetSize()),'shape':int(x.GetShape()),'attribute':int(x.GetAttribute()),'angle_deg':x.GetOrientationDegrees(),'layers':list(x.GetLayerSet().Seq()),'net':x.GetNetname(),'number':x.GetNumber()}
 else:
  via=isinstance(x,p.PCB_VIA);r={'net':x.GetNetname(),'class':x.GetClass(),'width_nm':x.GetWidth(p.F_Cu)if via else x.GetWidth(),'layer':x.GetLayerName()}
  if via:r.update(position_nm=n.XY(x.GetPosition()),drill_nm=x.GetDrillValue(),via_type=int(x.GetViaType()),layer_pair=[b.GetLayerName(x.TopLayer()),b.GetLayerName(x.BottomLayer())])
  else:
   r.update(start_nm=n.XY(x.GetStart()),end_nm=n.XY(x.GetEnd()));lengths[u]=x.GetLength()/1e6
   if isinstance(x,p.PCB_ARC):r['mid_nm']=n.XY(x.GetMid())
  geometry[u]=r
 if x.HasHole():holes[u]={'position_nm':n.XY(x.GetPosition()),'drill_nm':n.XY(x.GetDrillSize())if isinstance(x,p.PAD)else[x.GetDrillValue()]*2,'copper_layers':[b.GetLayerName(layer)for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]if x.IsOnLayer(layer)]}
# Complete native conductor component memberships, independently derived from all edges.
parents={u:u for u in byid}
def find(u):
 while parents[u]!=u:parents[u]=parents[parents[u]];u=parents[u]
 return u
for u,v in edges:parents[find(v)]=find(u)
parts={}
for u,x in byid.items():
 if x.GetNetname():parts.setdefault((x.GetNetname(),find(u)),[]).append(u)
components=sorted([{'net':net,'object_uuids':sorted(us)}for(net,_),us in parts.items()],key=lambda q:(q['net'],q['object_uuids']))
fp_geo={r:{'uuid':n.UID(fp),'position_nm':n.XY(fp.GetPosition()),'angle_deg':fp.GetOrientationDegrees(),'layer':fp.GetLayerName()}for r,fp in scene.fps.items()}
n.require(n.SHA(path)==scene.before,'Read-only native inventory')
result={'board_sha256':scene.before,'native_version':p.GetBuildVersion(),'native_board_loads':1,'private_xdg':scene.homes,'raw_native_net_identity_before_after_connectivity_exact':True,'net_identity':raw,'track_geometry':geometry,'pad_geometry':pad_geometry,'hole_geometry':holes,'footprint_placement':fp_geo,'edges':sorted(map(list,edges)),'native_components':components,'diagnostic_items':diagnostics,'net_table':{str(k):v for k,v in nets.items()},'lengths_mm':lengths,'length_fsum_mm':math.fsum(lengths[u]for u in sorted(lengths)),'counts':{'tracks':len(lengths),'vias':len(geometry)-len(lengths),'pads':len(pad_geometry),'footprints':len(fp_geo),'native_contact_edges':len(edges)},'fresh_physical_plane_graph_or_simulation':False,'board_file_unchanged':True};out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'board_sha256':scene.before,'counts':result['counts'],'length_fsum_mm':result['length_fsum_mm']}))
