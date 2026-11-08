from pathlib import Path
import json,hashlib,collections
D=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2');L=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'));labels=['aead','2c7','cafa'];g={k:L(D/k/'physical-graph.json')for k in labels};v1={k:L(D.parent/'corrected'/k/'physical-graph.json')for k in labels};origpaths={'aead':Path('/tmp/v7-c128-stub-retirement-aead/qa/source-physical-graph.json'),'2c7':Path('/tmp/v7-buck-deadarm-final-recheck/qa/source-physical-graph.json'),'cafa':Path('/tmp/v7-c128-stub-retirement-aead/qa/candidate-physical-graph.json')};orig={k:L(origpaths[k])for k in labels}
def edges(graph,kind):return {tuple(sorted(e[:2]))if kind=='direct'else tuple(e[:2]):e[2]for e in graph[kind+'_edges']}
def compare_edges(a,b):return dict(source_count=len(a),target_count=len(b),removed=[dict(a=k[0],b=k[1],support=a[k])for k in a.keys()-b.keys()],added=[dict(a=k[0],b=k[1],support=b[k])for k in b.keys()-a.keys()],changed_positive_support=[dict(a=k[0],b=k[1],source_support=a[k],target_support=b[k])for k in a.keys()&b.keys()if a[k]!=b[k]],exact=a==b)
def partition(graph,nodes):
 bins=collections.defaultdict(list)
 for u in nodes:bins[graph['material_roots'][u]].append(u)
 return sorted(sorted(v)for v in bins.values())
perboard={}
for k in labels:
 gr=g[k];info=dict(board_sha256=gr['board_sha256'],native_version=gr['native_version'],graph_sha256=sha(D/k/'physical-graph.json'),pad_inventory_exact_vs_original=gr['pad_inventory']==orig[k]['pad_inventory'],changed_pad_nets_vs_original=[n for n in gr['pad_partitions_by_net']if gr['pad_partitions_by_net'][n]!=orig[k]['pad_partitions_by_net'][n]],changed_pad_nets_vs_v1=[n for n in gr['pad_partitions_by_net']if gr['pad_partitions_by_net'][n]!=v1[k]['pad_partitions_by_net'][n]],material_nodes=len(gr['material_nodes']),material_edges=len(gr['material_edges']),empty_object_layers=len(gr['empty_object_layers']),multiple_component_object_layers=len(gr['multiple_component_object_layers']),guard_failing_material_edges=gr['guard_failing_material_edges'],guard_failures=len(gr['guard_failing_material_edges']),scope_assumptions=gr['scope_assumptions'])
 for baseline,old in [('original',orig[k]),('canonical_v1',v1[k])]:info['changes_from_'+baseline]={kind:compare_edges(edges(old,kind),edges(gr,kind))for kind in ['direct','zone']}
 empty_ids={x['uuid']for x in gr['empty_object_layers']if x['net']};info['empty_net_bearing_objects']=[u for u in sorted(empty_ids)if not gr['object_material_roots'][u]];info['multi_root_objects']=[dict(uuid=u,roots=rs)for u,rs in gr['object_material_roots'].items()if len(rs)>1];perboard[k]=info
 assert info['pad_inventory_exact_vs_original'] and not info['changed_pad_nets_vs_original'] and not info['changed_pad_nets_vs_v1']
transitions={}
for a,b in [('2c7','aead'),('aead','cafa')]:
 ao=set(g[a]['object_nodes_by_layer']);bo=set(g[b]['object_nodes_by_layer']);retired=ao-bo;added=bo-ao;common_nodes=set(g[a]['material_nodes'])&set(g[b]['material_nodes']);common_nodes={n for n in common_nodes if g[a]['material_nodes'][n]['uuid']not in retired|added};checks={}
 for kind in ['direct','zone']:
  ea={k:v for k,v in edges(g[a],kind).items()if not set(k)&retired};eb={k:v for k,v in edges(g[b],kind).items()if not set(k)&added};checks[kind]=compare_edges(ea,eb)
 def me(gr):return {tuple(sorted(x[:2])):x[2:]for x in gr['material_edges']if set(x[:2])<=common_nodes}
 ga={canon(x)for x in g[a]['guard_failing_material_edges']if x['a']in common_nodes and x['b']in common_nodes};gb={canon(x)for x in g[b]['guard_failing_material_edges']if x['a']in common_nodes and x['b']in common_nodes}
 metadata_changed=[n for n in common_nodes if g[a]['material_nodes'][n]!=g[b]['material_nodes'][n]and g[a]['material_nodes'][n]['kind']!='zone']
 transitions[a+'-to-'+b]=dict(retired_native_object_uuids=sorted(retired),added_native_object_uuids=sorted(added),pad_inventory_exact=g[a]['pad_inventory']==g[b]['pad_inventory'],all_245_pad_partitions_exact=g[a]['pad_partitions_by_net']==g[b]['pad_partitions_by_net'],retained_material_vertex_partition_exact=partition(g[a],common_nodes)==partition(g[b],common_nodes),retained_material_contact_edges_and_both_support_areas_exact=me(g[a])==me(g[b]),retained_nonzone_material_metadata_changed=metadata_changed,retained_guard_failures_exact=ga==gb,retained_direct_and_zone=checks)
# Actual continuous material witnesses, including the proved barrel edges.
adj={};proof={}
for label,gr in g.items():
 a=collections.defaultdict(list);pr={}
 for x,y,raw,guard in gr['material_edges']:
  a[x].append(y);a[y].append(x);pr[tuple(sorted((x,y)))]=dict(kind='positive_material_contact',unguarded_area_mm2=raw,guarded_area_mm2=guard)
 for barrel in gr['barrel_joins']:
  for x,y in zip(barrel['nodes'],barrel['nodes'][1:]):a[x].append(y);a[y].append(x);pr[tuple(sorted((x,y)))]=dict(kind='proved_plated_barrel',uuid=barrel['uuid'],proof=barrel['proof'])
 adj[label]=a;proof[label]=pr
def owner(gr,n):return n if gr['material_nodes'][n]['kind']=='zone'else gr['material_nodes'][n]['uuid']
def nodes(gr,u):return [u]if u.startswith('zone:')else [n for ls in gr['object_nodes_by_layer'][u].values()for n in ls]
def extend_same_owner(label,states,u):
 gr=g[label];queue=collections.deque(states)
 while queue:
  x=queue.popleft()
  for y in adj[label][x]:
   if owner(gr,y)==u and y not in states:states[y]=states[x]+[y];queue.append(y)
 return states
def prescribed_material_path(label,route):
 states=extend_same_owner(label,{n:[n]for n in nodes(g[label],route[0])},route[0])
 for u in route[1:]:
  after={}
  for x,path in states.items():
   for y in adj[label][x]:
    if owner(g[label],y)==u and y not in after:after[y]=path+[y]
  states=extend_same_owner(label,after,u)
  if not states:return None
 return next(iter(states.values()))
contract=L(Path('/tmp/v7-c128-deadbranch-readonly-aead/RETIREMENT_CONTRACT.json'));aw=L(Path('/tmp/v7-c128-deadbranch-readonly-aead/ATTACHMENT_TO_C128_JOIN.json'));routes=[dict(label=' to '.join(x['endpoints']),object_route=x['native_positive_copper_witness'])for x in contract['live_witnesses']]+[dict(label='attachment to C128 join',object_route=[x['uuid']for x in aw['objects']])];witnesses=[]
for w in routes:
 path=prescribed_material_path('aead',w['object_route']);assert path is not None,(w['label'],'no continuous guarded source material path');assert all(tuple(sorted((a,b)))in proof['cafa']for a,b in zip(path,path[1:])),(w['label'],'same path not preserved');sourceproof=[dict(a=a,b=b,**proof['aead'][tuple(sorted((a,b)))])for a,b in zip(path,path[1:])];candidateproof=[dict(a=a,b=b,**proof['cafa'][tuple(sorted((a,b)))])for a,b in zip(path,path[1:])];assert sourceproof==candidateproof;witnesses.append(dict(**w,source_material_path=path,candidate_same_path_exact=True,edge_proofs=sourceproof))
ret={x['uuid']for x in contract['retire']};boundary=[dict(stub_uuid=next(u for u in k if u in ret),live_uuid=next(u for u in k if u not in ret),support=v)for k,v in edges(g['aead'],'direct').items()if len(set(k)&ret)==1];assert len(boundary)==1 and boundary[0]['stub_uuid']=='0858c392-ee59-5350-bcaf-d8762f658a08'and boundary[0]['live_uuid']=='f578f80d-52bb-500f-b3df-4fe97eccdb4e';assert not[k for k in edges(g['aead'],'zone')if k[1]in ret]
contacts=[]
for o in contract['retire']+[contract['preserve_attachment_track']]:
 u=o['uuid'];contacts.append(dict(uuid=u,original_contract_direct=o['direct_contacts'],R2_guarded_material_direct=[dict(uuid=k[1]if k[0]==u else k[0],support=v)for k,v in edges(g['aead'],'direct').items()if u in k],R2_object_material_roots=g['aead']['object_material_roots'][u]))
j1={}
for label,gr in g.items():
 us=[u for u,x in gr['pad_inventory'].items()if x['ref']=='J1'and x['pad']=='A1'];assert len(us)==1;u=us[0];rs=gr['object_material_roots'][u];assert len(rs)==1;r=rs[0];j1[label]=dict(pad_uuid=u,pad_members=sorted(v for v in gr['pad_inventory']if r in gr['object_material_roots'][v]),material_node_members=sorted(n for n in gr['material_nodes']if gr['material_roots'][n]==r),objects_with_any_material_in_root=sorted(v for v,roots in gr['object_material_roots'].items()if r in roots))
assert j1['2c7']==j1['aead']==j1['cafa']
ledger=dict(status='R2 actual material path/contract evidence; original immutable contract untouched; no acceptance/selection',source_sha256=g['aead']['board_sha256'],candidate_sha256=g['cafa']['board_sha256'],witnesses=witnesses,sole_retired_boundary_contact=boundary,contract_contact_remeasurement=contacts,J1_A1_root_exact_across_three=True,J1_A1_material_roots=j1)
(D/'material-witness-contract-ledger.json').write_text(json.dumps(ledger,indent=2))
result=dict(status='DRAFT R2 EVIDENCE COMPLETE; physical contact claims bounded by native guarded model; no global acceptance or selection',checker_sha256=sha(D/'export_material_graph.py'),controls=L(D/'controls.json'),per_board=perboard,transitions=transitions,continuous_C128_C129_and_attachment_material_witnesses_exact=True,J1_A1_full_material_root_exact_across_three=True,commands=L(D/'commands.json'),strict_plane_gate='Cafa strict native plane no-loss remains FAIL; no BUCK-only precision waiver applies.')
(D/'MATERIAL_GRAPH_AUDIT.json').write_text(json.dumps(result,indent=2));summary={k:dict(pad_nets=len(g[k]['pad_partitions_by_net']),changed_pad_nets=v['changed_pad_nets_vs_original'],accepted_direct=len(g[k]['direct_edges']),accepted_zone=len(g[k]['zone_edges']),guard_failures=v['guard_failures'],empty_net_bearing_objects=len(v['empty_net_bearing_objects']),multiple_object_layers=v['multiple_component_object_layers'],direct_removed_vs_original=len(v['changes_from_original']['direct']['removed']),direct_changed_vs_original=len(v['changes_from_original']['direct']['changed_positive_support']))for k,v in perboard.items()};print(json.dumps(dict(per_board=summary,transitions=transitions,all_five_continuous_witnesses_exact=True,J1_A1_material_root_exact=True),indent=2))
