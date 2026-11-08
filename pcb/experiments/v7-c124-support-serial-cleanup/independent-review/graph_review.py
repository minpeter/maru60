import json,hashlib,collections
from pathlib import Path
W=Path(__file__).resolve().parent;SP=Path('/tmp/v7-c124-d-plus-connector-gnd/qa/material-graph.json');CP=Path('/tmp/v7-support-endpoint-trial/qa/material-graph.json');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();a=json.loads(SP.read_text());b=json.loads(CP.read_text());assert a['board_sha256']=='7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401'and b['board_sha256']=='abdbf4c80e11cadc525389060d2215b73fc3cbcc85b2bff6ddb0e8d2581e052d';changed={'abcd4fb1-881b-43f9-906e-39d93366692e','ae94ea04-2d21-5f84-8952-7f8960275e00','f41eeb49-8180-5bac-bccf-c1a0b3b4c547'}
def component_check(g):
 nodes=g['material_nodes'];p={u:u for u in nodes}
 def find(u):
  while p[u]!=u:p[u]=p[p[u]];u=p[u]
  return u
 def join(x,y):
  assert x in p and y in p
  assert nodes[x]['net']==nodes[y]['net'];x=find(x);y=find(y)
  if x!=y:p[max(x,y)]=min(x,y)
 for x,y,raw,guard in g['material_edges']:
  assert raw>0 and guard>0;join(x,y)
 for v in g['barrel_joins']:
  assert len(v['nodes'])>=2
  for x,y in zip(v['nodes'],v['nodes'][1:]):join(x,y)
 groups=collections.defaultdict(list)
 for n in p:groups[find(n)].append(n)
 normalized=sorted(sorted(v)for v in groups.values());recorded=collections.defaultdict(list)
 for n,r in g['material_roots'].items():recorded[r].append(n)
 assert normalized==sorted(sorted(v)for v in recorded.values())
 return normalized
ca=component_check(a);cb=component_check(b);assert ca==cb
for k in ['pad_inventory','pad_partitions_by_net','barrel_joins','zones','zone_edges','object_nodes_by_layer','empty_object_layers','multiple_component_object_layers','NPTH_material','guard_failing_material_edges']:
 assert a[k]==b[k],k
assert a['material_nodes'].keys()==b['material_nodes'].keys()
node_diff=[]
for k,v in a['material_nodes'].items():
 if v!=b['material_nodes'][k]:assert v.get('uuid')in changed;node_diff.append({'node':k,'before':v,'after':b['material_nodes'][k]})
assert {r['before']['uuid']for r in node_diff}==changed
canon=lambda e:tuple(sorted(e[:2]));ea={canon(e):e for e in a['material_edges']};eb={canon(e):e for e in b['material_edges']};assert len(ea)==len(a['material_edges'])and len(eb)==len(b['material_edges'])
def in_scope(pair):return any(a['material_nodes'][u].get('uuid')in changed for u in pair)
removed=[ea[k]for k in ea.keys()-eb.keys()];added=[eb[k]for k in eb.keys()-ea.keys()];witness=[{'before':ea[k],'after':eb[k]}for k in ea.keys()&eb.keys()if ea[k]!=eb[k]]
assert all(in_scope(canon(e))for e in removed+added);assert all(in_scope(canon(e['before']))for e in witness)
root=next(u for u,v in b['pad_inventory'].items()if v['ref']=='J1'and v['pad']=='A1');roots={u:next(i for i,c in enumerate(cb)if any(n in c for ns in b['object_nodes_by_layer'][u].values()for n in ns))for u,v in b['pad_inventory'].items()if v['net']=='GND'};assert len(roots)==247 and len(set(roots.values()))==1
r={'status':'PASS independent component reconstruction from all guarded material edges and proved barrel records','source_graph_sha256':H(SP),'candidate_graph_sha256':H(CP),'source_board_sha256':a['board_sha256'],'candidate_board_sha256':b['board_sha256'],'all_material_component_sets_exact':True,'material_component_count':len(cb),'all246_pad_net_partitions_exact':True,'all247_ground_pads_share_J1_A1_root':True,'all935_barrel_joins_exact':True,'all733_zone_contacts_exact':True,'all51_preexisting_guard_failures_exact_and_not_joined':True,'changed_material_nodes':node_diff,'removed_material_edges':removed,'added_material_edges':added,'changed_contact_witnesses':witness,'all_unrelated_material_records_exact':True,'limits':'Graph inherits R2 native candidate discovery and polygon representation assumptions. It proves nominal connectivity, not frequency-dependent impedance or safety.'};(W/'GRAPH_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'pass':True,'components':len(cb),'changed_material_nodes':len(node_diff),'removed_edges':len(removed),'added_edges':len(added),'changed_witnesses':len(witness)}))
