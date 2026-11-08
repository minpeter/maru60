#!/usr/bin/python3
"""Read-only local material/topological review. No board write; no SI or ESD model."""
import os
os.environ.setdefault('XDG_CONFIG_HOME','/tmp/kicad-stub-review')
os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl-stub-review')
import pcbnew as p,json,hashlib,collections,math
from pathlib import Path
BP=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-gnd-deadbranch-cleanup/candidate/pcb/maru60.kicad_pcb')
GP=Path('/tmp/v7-gnd-tail-cleanup-aead/qa/material-graph.json')
OUT=Path(__file__).resolve().parent
EXPECTED='c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a'
STUB='bc0a06ab-785a-4a27-a164-9c3256c7f3bd'
ANCHOR='5a2cb39f-cff7-4876-a0b9-7db4a3b9b0bc'
assert hashlib.sha256(BP.read_bytes()).hexdigest()==EXPECTED
assert p.GetBuildVersion()=='9.0.2+dfsg-1'
g=json.loads(GP.read_text()); assert g['board_sha256']==EXPECTED and g['revision']=='v2-all-through-drills-layer-island-material-graph'
b=p.LoadBoard(str(BP)); layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
uid=lambda q:q.m_Uuid.AsString()
xy=lambda q:[q.x/1e6,q.y/1e6]
items=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]; idx={uid(q):q for q in items}
def poly(shape,out=False):
 z=p.SHAPE_POLY_SET();shape.TransformToPolygon(z,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);z.Simplify();return z
def bb(s):
 r=s.BBox();return [r.GetX(),r.GetY(),r.GetRight(),r.GetBottom()]
def hits(a,c):return a[0]<=c[2]and a[2]>=c[0]and a[1]<=c[3]and a[3]>=c[1]
def area(a,c):
 if not hits(bb(a),bb(c)):return 0
 z=p.SHAPE_POLY_SET();z.BooleanIntersection(a,c);return z.Area()/1e12
def guarded(a):
 z=p.SHAPE_POLY_SET(a);z.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);return z
drills=[]
for q in items:
 if isinstance(q,(p.PAD,p.PCB_VIA)) and q.HasHole():
  h=poly(q.GetEffectiveHoleShape(),True);drills.append((uid(q),bb(h),h))
all_drills=p.SHAPE_POLY_SET()
for _,_,h in drills:all_drills.Append(h)
all_drills.Simplify()
cache={}
def copper(q,l):
 key=(uid(q),l)
 if key not in cache:
  base=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA) else q.GetEffectiveShape(l));s=p.SHAPE_POLY_SET(base);a=bb(base)
  for _,hb,h in drills:
   if hits(a,hb):s.BooleanSubtract(h)
  cache[key]=s
 return cache[key]
def desc(q):
 d=dict(uuid=uid(q),type=q.GetClass(),net=q.GetNetname(),at_mm=xy(q.GetPosition()))
 if isinstance(q,p.PAD):d.update(ref=q.GetParentFootprint().GetReference(),value=q.GetParentFootprint().GetValue(),pad=q.GetNumber(),size_mm=xy(q.GetSize()),drill_mm=xy(q.GetDrillSize()))
 elif isinstance(q,p.PCB_VIA):d.update(drill_mm=q.GetDrillValue()/1e6,width_mm=q.GetWidth(p.F_Cu)/1e6)
 else:d.update(start_mm=xy(q.GetStart()),end_mm=xy(q.GetEnd()),width_mm=q.GetWidth()/1e6,layer=b.GetLayerName(q.GetLayer()))
 return d
def gap_nm(a,c):
 # Native integer-clearance collision bisection; distance bracket <= 1 nm.
 if a.Collide(c,0):return [0,0]
 lo,hi=0,10000000
 if not a.Collide(c,hi):return None
 while hi-lo>1:
  m=(lo+hi)//2
  if a.Collide(c,m):hi=m
  else:lo=m
 return [lo,hi]
s=copper(idx[STUB],p.F_Cu);sg=guarded(s); sn=g['object_nodes_by_layer'][STUB]['F.Cu'][0]
assert abs(s.Area()/1e12-g['material_nodes'][sn]['area_mm2'])<1e-15
contacts=[];near=[]
for q in items:
 if uid(q)==STUB:continue
 for l in [p.F_Cu,p.B_Cu]:
  if not q.IsOnLayer(l):continue
  qb=q.GetBoundingBox();qb= [qb.GetX(),qb.GetY(),qb.GetRight(),qb.GetBottom()]
  if not hits(qb,[11e6,5e6,24e6,16e6]):continue
  c=copper(q,l)
  if l==p.F_Cu:
   ar=area(s,c)
   if ar>0:contacts.append(dict(**desc(q),layer=b.GetLayerName(l),area_mm2=ar,guarded_area_mm2=area(sg,guarded(c))))
  dist=gap_nm(s,c)
  if dist:near.append(dict(**desc(q),projection_layer=b.GetLayerName(l),same_layer=l==p.F_Cu,copper_edge_distance_bracket_mm=[x/1e6 for x in dist]))
zone_contacts=[]
for z in b.Zones():
 if z.GetIsRuleArea() or not z.IsOnLayer(p.F_Cu):continue
 c=p.SHAPE_POLY_SET(z.GetFilledPolysList(p.F_Cu));c.BooleanSubtract(all_drills);ar=area(s,c)
 if ar>0:zone_contacts.append(dict(uuid=uid(z),net=z.GetNetname(),area_mm2=ar,guarded_area_mm2=area(sg,guarded(c))))
assert len(contacts)==1 and contacts[0]['uuid']==ANCHOR and not zone_contacts
adj=collections.defaultdict(set)
for a,c,*_ in g['material_edges']:adj[a].add(c);adj[c].add(a)
for barrel in g['barrel_joins']:
 for a,c in zip(barrel['nodes'],barrel['nodes'][1:]):adj[a].add(c);adj[c].add(a)
assert len(adj[sn])==1
root=g['material_roots'][sn]; gndpadnodes=[n for u,d in g['pad_inventory'].items() if d['net']=='GND' for ls in g['object_nodes_by_layer'][u].values() for n in ls]
def reachable(start,exclude=None):
 seen={start};todo=[start]
 while todo:
  n=todo.pop()
  for t in adj[n]:
   if t!=exclude and t not in seen:seen.add(t);todo.append(t)
 return seen
without=reachable(next(iter(adj[sn])),sn)
assert all(n in without for n in gndpadnodes)
near.sort(key=lambda d:d['copper_edge_distance_bracket_mm'][0])
by_net_layer={}
for d in near:
 key=d['net']+' / '+d['projection_layer']
 by_net_layer.setdefault(key,d)
selectedpads=[dict(**desc(idx[u]),material_roots=g['object_material_roots'][u]) for u,v in g['pad_inventory'].items() if v['net']=='GND' and v['ref'] in ['J1','U10','R100']]
report=dict(board_path=str(BP),board_sha256=EXPECTED,graph_path=str(GP),graph_sha256=hashlib.sha256(GP.read_bytes()).hexdigest(),helper_path='/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/tools/export_material_graph.py',native_version=p.GetBuildVersion(),method='R2 graph read plus independent canonical all-through-drill copper subtraction, local native 1 nm polygons, 2 nm guard; native integer collision gap bisection. Other-layer distances are XY projections, not same-layer clearance.',stub=desc(idx[STUB]),stub_area_mm2=s.Area()/1e12,stub_material_root=root,stub_graph_degree=len(adj[sn]),independent_fcu_contacts=contacts,independent_fcu_zone_contacts=zone_contacts,anchor=desc(idx[ANCHOR]),anchor_graph_edges=[e for e in g['material_edges']if ANCHOR in str(e)],anchor_barrel_proof=[v for v in g['barrel_joins']if v['uuid']==ANCHOR],gnd_pad_count=len(g['pad_partitions_by_net']['GND'][0]),gnd_pad_partitions=len(g['pad_partitions_by_net']['GND']),removing_only_stub_graph_vertex_keeps_all_gnd_pads_reachable=True,relevant_ground_pads=selectedpads,nearest_by_net_and_projection_layer=by_net_layer,nearby_objects=near,limitations=['No CAD mutation or zone refill performed.','Graph deletion is a topological counterfactual, not a changed-board proof.','No wave, impedance, field, current, ESD or hardware model; guard/return effectiveness not proved.','Native 1 nm polygons are geometric approximations and material guard is a robustness test, not fabrication tolerance.'])
report['board_unchanged']=hashlib.sha256(BP.read_bytes()).hexdigest()==EXPECTED;assert report['board_unchanged']
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:report[k] for k in ['stub_graph_degree','stub_area_mm2','independent_fcu_contacts','independent_fcu_zone_contacts','board_unchanged']},indent=2))
for key,d in by_net_layer.items():
 if key.startswith(('USB_','CC1','GND','COL0')):print(key,d['copper_edge_distance_bracket_mm'],d['uuid'],d.get('ref',''),d.get('pad',''))
