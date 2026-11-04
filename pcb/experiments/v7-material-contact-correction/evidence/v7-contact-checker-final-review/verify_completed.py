#!/usr/bin/python3
import json,hashlib
from pathlib import Path
R=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2')
OUT=Path('/tmp/v7-contact-checker-final-review')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,m):
 if not v: raise RuntimeError(m)
def audit(c):
 argv=c['command']; board=Path(argv[2]); file=Path(argv[3]); g=json.loads(file.read_text()); label=c['label']
 require(type(c['exit_code']) is int and c['exit_code']==0,'exit')
 require(sha(argv[1])==c['checker_sha256']=='57987368b095de525fc729a0d4b729b14cfc207afd07b4bd214ee5463a7719b9','checker')
 require(sha(board)==c['input_sha256_before']==c['input_sha256_after']==g['board_sha256'],'board')
 require(sha(file)==c['output_sha256'],'output')
 require(sha(file.parent/'export.log')==c['log_sha256'],'log')
 require(g['source_path']==str(board) and g['unchanged'] is True,'source')
 nodes=g['material_nodes']; parent={n:n for n in nodes}
 def find(n):
  while n!=parent[n]: parent[n]=parent[parent[n]]; n=parent[n]
  return n
 def join(a,b):
  a,b=find(a),find(b)
  if a!=b: parent[max(a,b)]=min(a,b)
 keys=set()
 for a,b,raw,guard in g['material_edges']:
  require(a in nodes and b in nodes and a!=b and raw>0 and guard>0,'edge')
  require(nodes[a]['layer']==nodes[b]['layer'] and nodes[a]['net']==nodes[b]['net'],'edge identity')
  k=tuple(sorted([a,b])); require(k not in keys,'duplicateedge'); keys.add(k);join(a,b)
 npth_nodes={n for r in g['NPTH_material'] for ns in r['nodes_by_layer'].values() for n in ns}
 npth_uuids={r['uuid'] for r in g['NPTH_material']}
 for b in g['barrel_joins']:
  require(b['uuid'] not in npth_uuids and len(b['nodes'])==4,'barrel')
  require({nodes[n]['layer'] for n in b['nodes']}=={'F.Cu','In1.Cu','In2.Cu','B.Cu'},'barrel layers')
  for n in b['nodes']: require(nodes[n]['uuid']==b['uuid'],'barrel uuid'); join(b['nodes'][0],n)
 roots={n:find(n) for n in nodes};require(roots==g['material_roots'],'root reconstruction')
 objects={u:sorted({roots[n] for ns in layer.values() for n in ns}) for u,layer in g['object_nodes_by_layer'].items()}
 require(objects==g['object_material_roots'],'object roots')
 parts={}
 for u,p in g['pad_inventory'].items():
  require(len(objects[u])==1,'named pad root')
  parts.setdefault(p['net'],{}).setdefault(objects[u][0],[]).append(u)
 parts={net:sorted(sorted(pads) for pads in rs.values()) for net,rs in parts.items()}
 require(parts==g['pad_partitions_by_net'],'pad partition reconstruction')
 npth_edges=[e for e in g['material_edges'] if e[0] in npth_nodes or e[1] in npth_nodes]
 npth_failed=[e for e in g['guard_failing_material_edges'] if any(n in str(e) for n in npth_nodes)]
 require(not npth_edges and not npth_failed and not npth_uuids.intersection(g['pad_inventory']),'NPTH participation')
 return dict(label=label,board_sha256=g['board_sha256'],graph_sha256=sha(file),commands_bound=True,roots_independently_reconstructed=True,pad_partitions_independently_reconstructed=True,named_pad_count=len(g['pad_inventory']),net_count=len(parts),material_nodes=len(nodes),material_edges=len(keys),barrels=len(g['barrel_joins']),npth_fragment_nodes=len(npth_nodes),npth_accepted_edges=0,npth_guard_failed_edges=0,npth_named_pad_participation=0,guard_failures=len(g['guard_failing_material_edges']),direct_edges=len(g['direct_edges']),zone_edges=len(g['zone_edges']))
commands=json.loads((R/'commands.json').read_text())
report={'status':'PASS','scope':'Independent pure result/command/root/NPTH audit; no native rerun, no acceptance or selection.','main_runs':[audit(c) for c in commands],'source_bindings':{str(R/'commands.json'):sha(R/'commands.json')}}
W=Path('/tmp/v7-contact-positive-witness-helper/selected-aead-exact-witnesses-order-replay.json')
w=json.loads(W.read_text());g=json.loads((R/'aead/physical-graph.json').read_text())
require(w['status']=='passed' and w['all_pinned_inputs_unchanged'] is True and w['failed_edge_count']==0,'witness status')
require(w['verified_edge_count']==len(g['material_edges'])==22531,'witness count')
require({r[0] for r in w['witnesses']}==set(range(22531)) and len(w['witnesses'])==22531,'witness coverage')
for p,h in w['input_sha256'].items():require(sha(p)==h,'witness input')
require(sha(w['prior_report_path'])==w['prior_report_sha256'],'prior')
for edge in g['material_edges']:require(edge[0] in w['component_sha256'] and edge[1] in w['component_sha256'],'coordinate coverage')
report['selected_exact_interior_supplement']={'sha256':sha(W),'all_22531_edges_covered_exactly_once':True,'all_component_coordinate_hashes_present':True,'method':w['method'],'bound_inputs_rehashed':True,'scope':w['scope']}
report['script_sha256']=sha(__file__)
(OUT/'CURRENT_SELECTION_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
