from pathlib import Path
import os,ast,json,hashlib
D=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected');os.environ['XDG_CONFIG_HOME']=str(D/'controls/config');Path(os.environ['XDG_CONFIG_HOME']).mkdir(parents=True,exist_ok=True)
import pcbnew as p
B=Path('/tmp/v7-c128-stub-retirement-aead/filled/pcb/maru60.kicad_pcb');b=p.LoadBoard(str(B));b.BuildConnectivity();idx={q.m_Uuid.AsString():q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};uid=lambda q:q.m_Uuid.AsString();cache={};tree=ast.parse((D/'export_native_physical_graph.py').read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ['poly','cu','area']];exec(compile(ast.Module(body=defs,type_ignores=[]),str(D/'export_native_physical_graph.py'),'exec'),globals())
def dump(ps):
 def ring(r):return [[r.CPoint(i).x,r.CPoint(i).y]for i in range(r.PointCount())]
 return [dict(outline=ring(ps.COutline(i)),holes=[ring(ps.CHole(i,h))for h in range(ps.HoleCount(i))])for i in range(ps.OutlineCount())]
viaid='2a8005ba-8cc3-5ec3-bf91-40e20122da23';trackid='cdcdaf62-0d7e-520a-9821-934ef8e04931';canonical=idx[viaid];wrapper=next(q for q in b.GetConnectivity().GetConnectedTracks(idx[trackid])if uid(q)==viaid);assert type(wrapper).__name__=='PCB_TRACK'and wrapper.GetClass()=='PCB_VIA'and not isinstance(wrapper,p.PCB_VIA)
checks=[]
for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
 cache.clear();a=cu(canonical,l);cache.clear();z=cu(wrapper,l);assert dump(a)==dump(z)
 baseline=poly(p.SHAPE_CIRCLE(canonical.GetPosition(),canonical.GetWidth(l)//2));baseline.BooleanSubtract(poly(canonical.GetEffectiveHoleShape(),True));assert dump(a)==dump(baseline)
 checks.append(dict(control='canonical_vs_neighbor_wrapper_and_multilayer_drill',layer=b.GetLayerName(l),area_mm2=a.Area()/1e12,geometry_exact=True))
known=area(cu(idx[trackid],p.F_Cu),cu(wrapper,p.F_Cu));assert known==0.0564735324735;checks.append(dict(control='known_positive_annular_contact',track=trackid,via=viaid,area_mm2=known))
observed=json.load(open(D.parent/'canonical-direct-support-audit.json'))['lost_positive_edges']
for a,z,_ in observed:
 support=[]
 for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if idx[a].IsOnLayer(l)and idx[z].IsOnLayer(l):
   v=area(cu(idx[a],l),cu(idx[z],l))
   if v>0:support.append([b.GetLayerName(l),v])
 assert support==[];checks.append(dict(control='reject_observed_drill_only_false_contact',a=a,b=z,positive_support=support))
# Native pad handling unchanged for every pad and layer; no duplicate native graph export.
pad_counts={'total_pads':0,'hole_pads':0,'pad_layer_checks':0,'PTH':0,'NPTH':0}
for q in idx.values():
 if not isinstance(q,p.PAD):continue
 pad_counts['total_pads']+=1
 if q.HasHole():
  pad_counts['hole_pads']+=1
  if q.GetAttribute()==p.PAD_ATTRIB_PTH:pad_counts['PTH']+=1
  if q.GetAttribute()==p.PAD_ATTRIB_NPTH:pad_counts['NPTH']+=1
 for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if not q.IsOnLayer(l):continue
  baseline=poly(q.GetEffectiveShape(l))
  if q.HasHole():baseline.BooleanSubtract(poly(q.GetEffectiveHoleShape(),True))
  assert dump(cu(q,l))==dump(baseline);pad_counts['pad_layer_checks']+=1
checks.append(dict(control='all_native_pad_shapes_and_drill_handling_unchanged',**pad_counts))
r=dict(status='PASS',board_sha256=hashlib.sha256(B.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256((D/'export_native_physical_graph.py').read_bytes()).hexdigest(),mechanism=dict(wrapper_native_class=wrapper.GetClass(),wrapper_python_type=type(wrapper).__name__,canonical_python_type=type(canonical).__name__),controls=checks);(D/'controls.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
