import os,pathlib,json,hashlib,math
D=pathlib.Path(__file__).parent
for k in ['CONFIG','CACHE','DATA']:os.environ['XDG_'+k+'_HOME']=str(D/k.lower())
import pcbnew as p
B=pathlib.Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb/maru60.kicad_pcb');sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before=sha(B);assert before=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373';b=p.LoadBoard(str(B));b.BuildConnectivity();co=b.GetConnectivity();uid=lambda q:q.m_Uuid.AsString();xy=lambda q:[q.x/1e6,q.y/1e6];layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];obs=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];idx={uid(q):q for q in obs};fb={u:q for u,q in idx.items()if q.GetNetname()=='BUCK_FB'};vu='d382de57-3476-43c4-ac26-0a72b21acf7c';tu='2c0aa2c5-bec8-4dff-bff7-2e823d3e36fa';ju='3c804add-ee74-5104-b471-73062ffcaeb9';via=idx[vu];track=idx[tu];tap=idx[ju]
assert xy(via.GetPosition())==[178.15,85.75] and via.GetWidth(p.F_Cu)==500000 and via.GetDrillValue()==250000;assert xy(track.GetStart())==[178.15,85.75]and xy(track.GetEnd())==[182.95,85.75]and track.GetWidth()==150000 and track.GetLayer()==p.F_Cu;assert xy(tap.GetEnd())==[181.0,85.75]
def poly(s,inside=False):
 z=p.SHAPE_POLY_SET();s.TransformToPolygon(z,1,p.ERROR_INSIDE if inside else p.ERROR_OUTSIDE);return z
def cu(q,l):
 z=poly(q.GetEffectiveShape(l),True)
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():z.BooleanSubtract(poly(q.GetEffectiveHoleShape()))
 return z
def cross(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(b);return z.Area()/1e12
adj={u:set()for u in fb};edges=[]
for u,q in fb.items():
 for z in list(co.GetConnectedTracks(q))+list(co.GetConnectedPads(q)):
  v=uid(z)
  if v not in fb or u>=v:continue
  supp=[dict(layer=b.GetLayerName(l),area_mm2=cross(cu(q,l),cu(z,l)))for l in layers if q.IsOnLayer(l)and z.IsOnLayer(l)];supp=[a for a in supp if a['area_mm2']>0]
  if supp:adj[u].add(v);adj[v].add(u);edges.append(dict(a=u,b=v,support=supp))
assert adj[vu]=={tu};assert ju in adj[tu];pads={u:q for u,q in fb.items()if isinstance(q,p.PAD)};start=next(u for u,q in pads.items()if q.GetParentFootprint().GetReference()=='U18'and q.GetNumber()=='8')
def reach(graph,retired):
 seen={start};todo=[start]
 while todo:
  for z in graph[todo.pop()]-set(retired)-seen:seen.add(z);todo.append(z)
 return sorted(set(pads)&seen)
rep=p.SHAPE_SEGMENT(p.VECTOR2I(181000000,85750000),p.VECTOR2I(182950000,85750000),150000);repPoly=poly(rep,True);repcontacts=[]
for u,q in fb.items():
 if u in [vu,tu]or not q.IsOnLayer(p.F_Cu):continue
 a=cross(repPoly,cu(q,p.F_Cu))
 if a>0:repcontacts.append(dict(uuid=u,area_mm2=a))
newgraph={u:set(v)for u,v in adj.items()};newgraph['planned_active_replacement']=set(a['uuid']for a in repcontacts)
for u in newgraph['planned_active_replacement']:newgraph[u].add('planned_active_replacement')
remaining=reach(newgraph,[vu,tu]);assert set(remaining)==set(pads)
foreign=[dict(uuid=uid(q),net=q.GetNetname())for q in obs if q.IsOnLayer(p.F_Cu)and q.GetNetname()!='BUCK_FB'and rep.Collide(q.GetEffectiveShape(p.F_Cu),150000)];assert not foreign
out=[]
for u,q in fb.items():
 r=dict(uuid=u,net=q.GetNetname(),type=q.GetClass(),physical_contacts=sorted(adj[u]),layers=[b.GetLayerName(l)for l in layers if q.IsOnLayer(l)])
 if isinstance(q,p.PAD):r.update(ref=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),xy_mm=xy(q.GetPosition()))
 elif isinstance(q,p.PCB_VIA):r.update(xy_mm=xy(q.GetPosition()),diameter_mm=q.GetWidth(p.F_Cu)/1e6,drill_mm=q.GetDrillValue()/1e6)
 else:r.update(start_mm=xy(q.GetStart()),end_mm=xy(q.GetEnd()),width_mm=q.GetWidth()/1e6,length_mm=q.GetLength()/1e6)
 out.append(r)
r=dict(status='READ ONLY PLAN; no board constructed; awaiting explicit Space-save release',source_board_sha256=before,source_project=str(B.parent),source_study='/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104/extracted/v7-buck-feedback-study-20261104',study_board_is_different='8a4ff6a646396a3faa11dda0f756c89e82c20eec18f37fe531cf730789106eea; current2c7 reverified independently',retire_uuids=[vu,tu],replacement=dict(uuid='assign new UUID only after release',net='BUCK_FB',layer='F.Cu',width_mm=.15,start_mm=[181.0,85.75],end_mm=[182.95,85.75],active_centerline_mm=1.95,retained_contacts=repcontacts),removed_dead_centerline_mm=2.85,removed_drill=dict(uuid=vu,diameter_mm=.25,xy_mm=[178.15,85.75]),FB_objects=out,physical_edges=edges,graph_controls=dict(original_reachable_FB_pads=reach(adj,[]),via_only_removal_reachable_FB_pads=reach(adj,[vu]),entire_track_removed_without_replacement_reachable_FB_pads=reach(adj,[vu,tu]),proper_trim_reachable_FB_pads=remaining),proposed_replacement_native_foreign_clearance_failures=foreign,preserve=['Every original conductor except named via and track','Original1.95mm active geometry and all three physical FB pads','All other footprints/drills/net names/project settings/fill rules','All-net physical pad partitions and rooted contacts','All original retained full-width reference shadows; quantify actual fill gain and removed hole separately'],required_after_release=['Separate immutable source/prefill/filled snapshots','Normal native refill,DRC,schematic parity,ERC','Exact retirement/replacement and unrelated geometry diff','All-net physical pad-partition and root/contact comparison','Full actual saved-fill gain/loss and old-shadow comparison','Exact warning delta including potential dangling replacement','Independent actual-board review before any parent selection'],prohibited_claims=['No improved noise or loop stability inferred','No pickup reduction inferred from lower shunt capacitance','No hardware/SI/manufacturing qualification','No wider/reworked active feedback routing']);assert sha(B)==before;(D/'PLAN.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items()if k not in ['FB_objects','physical_edges']},indent=2))
