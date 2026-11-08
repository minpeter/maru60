from pathlib import Path
import json,hashlib,collections
O=Path('/tmp/v7-c124-d-plus-connector-gnd-independent-review');R=Path('/tmp/v7-c124-d-plus-connector-gnd');J=lambda p:json.loads(Path(p).read_text());H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();s=J('/tmp/v7-c124-d-actual/qa/actual-material-graph.json');d=J(R/'qa/material-graph.json');u='cda2df4b-6411-5409-a933-5106751244d8';checks=[]
def ck(n,ok,detail=None):
 checks.append({'check':n,'pass':bool(ok),'detail':detail});assert ok,n
ck('actual_R2_hash_source_binding',H(R/'qa/material-graph.json')=='304954c5b4195c28bcea68ef950625584efd557fd3475430c1245c0078ff877c'and d['board_sha256']=='7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401'and d['unchanged'])
canon=lambda rows:collections.Counter(json.dumps(q,sort_keys=True)for q in rows)
for k in ['pad_inventory','pad_partitions_by_net','direct_edges','raw_unguarded_direct_edges','native_pairs_without_guarded_positive_copper','guard_failing_material_edges','empty_object_layers','multiple_component_object_layers','NPTH_material']:
 ck(k+'_exact',canon(s[k])==canon(d[k]) if isinstance(s[k],list) else s[k]==d[k],{'ordered_equal':s[k]==d[k]})
old=set(s['material_nodes']);new=set(d['material_nodes'])-old;ck('four_new_material_nodes_only',len(new)==4 and set(s['material_nodes'])<=set(d['material_nodes'])and all(d['material_nodes'][n]['uuid']==u for n in new))
changed={n for n in old if s['material_nodes'][n]!=d['material_nodes'][n]};ck('only_two_expected_inner_zone_area_changes',len(changed)==2 and all(s['material_nodes'][n]['kind']=='zone'and s['material_nodes'][n]['layer']in['In1.Cu','In2.Cu']and {k:v for k,v in s['material_nodes'][n].items()if k!='area_mm2'}=={k:v for k,v in d['material_nodes'][n].items()if k!='area_mm2'}and s['material_nodes'][n]['area_mm2']>d['material_nodes'][n]['area_mm2']for n in changed),sorted(changed))
ck('all_retained_material_edges_exact',canon(s['material_edges'])==canon([e for e in d['material_edges']if e[0]in old and e[1]in old]),len(s['material_edges']))
ne=[e for e in d['material_edges']if e[0]in new or e[1]in new];ck('exactly_two_new_guarded_plane_contacts',len(ne)==2 and all((e[0]in new)^(e[1]in new) and (e[0]in changed or e[1]in changed)and e[2]==.147260768066 and e[3]==.1472558792225 for e in ne),ne)
ck('all_old_barrels_exact',canon(s['barrel_joins'])==canon([q for q in d['barrel_joins']if q['uuid']!=u]),len(s['barrel_joins']));nb=[q for q in d['barrel_joins']if q['uuid']==u];ck('exactly_one_intact_four_layer_new_barrel',len(nb)==1 and set(nb[0]['nodes'])==new,nb)
# Independent complete DSU, no trust in exported root labels.
def roots(g):
 par={n:n for n in g['material_nodes']}
 def root(n):
  while par[n]!=n:par[n]=par[par[n]];n=par[n]
  return n
 def join(a,b):
  a,b=root(a),root(b)
  if a!=b:par[max(a,b)]=min(a,b)
 for a,b,raw,guard in g['material_edges']:
  assert raw > 0 and guard > 0;join(a,b)
 for q in g['barrel_joins']:
  for a,b in zip(q['nodes'],q['nodes'][1:]):join(a,b)
 ret={n:root(n)for n in par};assert ret==g['material_roots'];return ret
sr=roots(s);dr=roots(d);ck('full_DSU_rebuilt_roots_and_all_old_roots_exact',all(sr[n]==dr[n]for n in old),{'old_nodes':len(old),'source_components':len(set(sr.values())),'candidate_components':len(set(dr.values()))})
ck('all_existing_object_roots_exact',all(s['object_material_roots'][x]==d['object_material_roots'][x]for x in s['object_material_roots']))
gnd=[x for x,q in s['pad_inventory'].items()if q['net']=='GND'];ck('all_247_GND_pad_roots_exact',len(gnd)==247 and all(s['object_material_roots'][x]==d['object_material_roots'][x]for x in gnd));ck('new_via_joins_same_J1_GND_root',d['object_material_roots'][u]==s['object_material_roots']['186082bb-d1d7-429b-b059-389234bbb320'])
sd=J('/tmp/v7-c124-d-actual/qa/filled-drc.json');dd=J(R/'qa/drc.json');sem=lambda rows,g:sorted(tuple(sorted(tuple(g['object_material_roots'][q['uuid']])for q in row['items']))for row in rows)
ck('all_12_native_open_component_pairs_exact',len(sd['unconnected_items'])==len(dd['unconnected_items'])==12 and sem(sd['unconnected_items'],s)==sem(dd['unconnected_items'],d))
(O/'GRAPH_REVIEW.json').write_text(json.dumps({'checks':checks,'source_graph_sha256':H('/tmp/v7-c124-d-actual/qa/actual-material-graph.json'),'candidate_graph_sha256':H(R/'qa/material-graph.json'),'candidate_sha256':d['board_sha256'],'source_sha256':s['board_sha256'],'new_edges':ne,'new_barrel':nb,'strict_zone_area_basis':'Floating graph metadata changes only two expected zone area fields. Exact physical loss is verified independently by native contour equality in GEOMETRY_INHERITANCE.json, not by a rounded-area tolerance.'},indent=2)+'\n');print('GRAPH_FINISHED',len(checks))
