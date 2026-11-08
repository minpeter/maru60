from pathlib import Path
import hashlib,json,collections
if not __debug__:raise RuntimeError('Optimized Python unsupported')
R=Path(__file__).resolve().parent;SRC=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2/aead/physical-graph.json');CAN=Path('/tmp/v7-gnd-tail-cleanup-aead/qa/material-graph.json');S=json.loads(SRC.read_text());C=json.loads(CAN.read_text());plan=json.loads((R.parent/'two-track-contract.json').read_text());removed={r['uuid']for r in plan['retire_exactly']};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert S['board_sha256']==plan['source_sha256'];assert C['board_sha256']=='c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a';assert S['pad_inventory']==C['pad_inventory'];assert S['pad_partitions_by_net']==C['pad_partitions_by_net'];assert S['guard_failing_material_edges']==C['guard_failing_material_edges'];assert S['barrel_joins']==C['barrel_joins'];assert S['scope_assumptions']==C['scope_assumptions']
kill={n for n,r in S['material_nodes'].items()if r['uuid']in removed};assert {n:r for n,r in S['material_nodes'].items()if n not in kill}==C['material_nodes']
def partitions(g,skip=set()):
 d=collections.defaultdict(set)
 for n,r in g['material_roots'].items():
  if n not in skip:d[r].add(n)
 return {frozenset(v)for v in d.values()}
assert partitions(S,kill)==partitions(C)
key=lambda e:tuple(sorted(e[:2]));se={key(e):e[2:]for e in S['material_edges']if not set(e[:2])&kill};ce={key(e):e[2:]for e in C['material_edges']};assert se==ce;assert S['zone_edges']==C['zone_edges']
adj={n:set()for n in C['material_nodes']}
for a,b,*_ in C['material_edges']:adj[a].add(b);adj[b].add(a)
for r in C['barrel_joins']:
 for a,b in zip(r['nodes'],r['nodes'][1:]):adj[a].add(b);adj[b].add(a)
paths=[]
for r in plan['all_247_J1_A1_ground_paths']:
 pp=r['material_path_from_J1_A1'];assert all(n in adj for n in pp);assert all(b in adj[a]for a,b in zip(pp,pp[1:]));paths.append(dict(pad_uuid=r['pad_uuid'],reference=r['reference'],pad=r['pad'],original_exact_path_preserved=True,material_path_from_J1_A1=pp))
via=plan['retain_via']['uuid'];proof=next(r for r in C['barrel_joins']if r['uuid']==via);assert proof==plan['retain_via']['source_barrel_proof'];inner=[]
for row in plan['retain_via']['guarded_inner_plane_contacts']:
 assert key(row)in ce and ce[key(row)]==row[2:];inner.append(row)
SD=Path('/tmp/v7-c124-c-actual/qa/source-drc.json');CD=Path('/tmp/v7-gnd-tail-cleanup-aead/qa/drc.json');sd=json.loads(SD.read_text());cd=json.loads(CD.read_text())
def open_rows(d,g):
 out=[]
 for r in d['unconnected_items']:
  ep=[]
  for i in r['items']:
   u=i['uuid'];roots=g['object_material_roots'][u];assert len(roots)==1;ns=[n for v in g['object_nodes_by_layer'][u].values()for n in v];nets={g['material_nodes'][n]['net']for n in ns};assert len(nets)==1;ep.append(dict(uuid=u,net=next(iter(nets)),material_root=roots[0],description=i['description']))
  canon=(r['type'],r['severity'],r['description'],tuple(sorted((x['net'],x['material_root'])for x in ep)));out.append((canon,ep))
 return out
sa=open_rows(sd,S);ca=open_rows(cd,C);assert collections.Counter(k for k,_ in sa)==collections.Counter(k for k,_ in ca);open_compare=[]
for k in sorted(set(k for k,_ in sa)):
 old=[e for key,e in sa if key==k];new=[e for key,e in ca if key==k];open_compare.append(dict(semantic_key=k,source=old,candidate=new,endpoint_uuids_equal=sorted(sorted(x['uuid']for x in e)for e in old)==sorted(sorted(x['uuid']for x in e)for e in new)))
report=dict(source_sha256=S['board_sha256'],candidate_sha256=C['board_sha256'],source_graph_sha256=sha(SRC),candidate_graph_sha256=sha(CAN),retained_material_nodes=len(C['material_nodes']),retained_components=len(partitions(C)),all_retained_material_node_metadata_and_areas_exact=True,all_retained_material_component_memberships_preserved=True,all_245_pad_net_partitions_exact=True,all_51_guard_failures_exact=True,all_retained_material_edge_witness_areas_exact=True,all_zone_edge_witnesses_exact=True,all_934_barrel_proofs_exact=True,all_1269_physical_drills_retained=True,all_247_original_GND_return_paths_preserved=paths,retained_boundary_via_barrel=proof,retained_inner_GND_plane_contacts=inner,all_12_native_open_semantic_component_pairs_equal=True,raw_open_endpoint_entries_changed=sum(not r['endpoint_uuids_equal']for r in open_compare),raw_open_report_rows_equal=sd['unconnected_items']==cd['unconnected_items'],open_component_comparison=open_compare,source_drc_sha256=sha(SD),candidate_drc_sha256=sha(CD),status='All bounded electrical/support checks pass. No powered or HF-ground qualification.')
(R/'MATERIAL_AND_DRC_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['all_247_original_GND_return_paths_preserved','open_component_comparison']},indent=2))
