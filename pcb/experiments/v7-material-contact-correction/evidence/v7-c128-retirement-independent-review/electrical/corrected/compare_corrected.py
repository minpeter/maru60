from pathlib import Path
import os,json,hashlib,collections,math
D=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected');os.environ['XDG_CONFIG_HOME']=str(D/'compare/config');Path(os.environ['XDG_CONFIG_HOME']).mkdir(parents=True,exist_ok=True)
import pcbnew as p
L=lambda f:json.loads(f.read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();canon=lambda a:json.dumps(a,sort_keys=True,separators=(',',':'))
boards={'aead':Path('/tmp/v7-c128-stub-retirement-aead/source/pcb/maru60.kicad_pcb'),'2c7':Path('/tmp/v7-buck-deadarm-final-recheck/source/pcb/maru60.kicad_pcb'),'cafa':Path('/tmp/v7-c128-stub-retirement-aead/filled/pcb/maru60.kicad_pcb')};origpaths={'aead':Path('/tmp/v7-c128-stub-retirement-aead/qa/source-physical-graph.json'),'2c7':Path('/tmp/v7-buck-deadarm-final-recheck/qa/source-physical-graph.json'),'cafa':Path('/tmp/v7-c128-stub-retirement-aead/qa/candidate-physical-graph.json')}
g={k:L(D/k/'physical-graph.json')for k in boards};og={k:L(origpaths[k])for k in boards};inventories={}
for k,B in boards.items():
 b=p.LoadBoard(str(B));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];inv={}
 for q in items:
  r=dict(type=q.GetClass(),net=q.GetNetname(),layers=[b.GetLayerName(l)for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]if q.IsOnLayer(l)])
  if isinstance(q,p.PAD):r.update(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber())
  inv[q.m_Uuid.AsString()]=r
 inventories[k]=inv;assert sha(B)==g[k]['board_sha256']==og[k]['board_sha256']
def edges(gr,zone=False):return {tuple(x[:2])if zone else tuple(sorted(x[:2])):x[2]for x in gr['zone_edges'if zone else'direct_edges']}
def fullroots(gr,inventory):
 par={u:u for u in inventory}
 def root(u):
  par.setdefault(u,u)
  while par[u]!=u:par[u]=par[par[u]];u=par[u]
  return u
 def join(a,b):par[root(b)]=root(a)
 for a,b,_ in gr['direct_edges']+gr['zone_edges']:join(a,b)
 roots={u:root(u)for u in par};return roots
def partitions(roots,nodes):
 bins=collections.defaultdict(list)
 for u in nodes:bins[roots[u]].append(u)
 return sorted(sorted(a)for a in bins.values())
reviews={};newroots={}
for label in boards:
 original=og[label];fixed=g[label];oldroots=fullroots(original,inventories[label]);root=fullroots(fixed,inventories[label]);newroots[label]=root;detail={}
 for kind,zone in [('direct',False),('zone',True)]:
  a=edges(original,zone);b=edges(fixed,zone);removed=[dict(a=k[0],b=k[1],old_support=a[k])for k in a.keys()-b.keys()];added=[dict(a=k[0],b=k[1],new_support=b[k])for k in b.keys()-a.keys()];changed=[dict(a=k[0],b=k[1],old_support=a[k],new_support=b[k])for k in a.keys()&b.keys()if a[k]!=b[k]]
  detail[kind]=dict(original_count=len(a),corrected_count=len(b),false_positive_edges_removed=removed,positive_edges_added=added,changed_still_positive_support_count=len(changed),changed_still_positive_supports=changed)
  for r in removed:r['redundant_with_corrected_edges']=root[r['a']]==root[r['b']]
 padchange=[net for net in fixed['pad_partitions_by_net'] if original['pad_partitions_by_net'][net]!=fixed['pad_partitions_by_net'][net]]
 reviews[label]=dict(board_sha256=sha(boards[label]),original_graph_sha256=sha(origpaths[label]),corrected_graph_sha256=sha(D/label/'physical-graph.json'),pad_inventory_exact=original['pad_inventory']==fixed['pad_inventory'],changed_pad_partition_nets=padchange,all_native_object_component_partition_exact=partitions(oldroots,inventories[label])==partitions(root,inventories[label]),**detail)
 assert not padchange and reviews[label]['pad_inventory_exact'] and reviews[label]['all_native_object_component_partition_exact']
pairchecks={}
for a,b in [('2c7','aead'),('aead','cafa')]:
 retained=set(inventories[a])&set(inventories[b]);retired=set(inventories[a])-set(inventories[b]);added=set(inventories[b])-set(inventories[a]);detail={}
 for kind,zone in [('direct',False),('zone',True)]:
  ea={k:v for k,v in edges(g[a],zone).items()if not(set(k)&retired)};eb={k:v for k,v in edges(g[b],zone).items()if not(set(k)&added)}
  detail[kind]=dict(retained_contacts_and_support_exact=ea==eb,source_retained=len(ea),candidate_retained=len(eb),lost_keys=[list(k)for k in ea.keys()-eb.keys()],added_keys=[list(k)for k in eb.keys()-ea.keys()],support_changes=[dict(a=k[0],b=k[1],old=ea[k],new=eb[k])for k in ea.keys()&eb.keys()if ea[k]!=eb[k]])
 pairchecks[a+'-to-'+b]=dict(pad_inventory_exact=g[a]['pad_inventory']==g[b]['pad_inventory'],all_245_pad_partitions_exact=g[a]['pad_partitions_by_net']==g[b]['pad_partitions_by_net'],all_retained_native_object_roots_exact=partitions(newroots[a],retained)==partitions(newroots[b],retained),retired_native_objects=[dict(uuid=u,**inventories[a][u])for u in sorted(retired)],added_native_objects=[dict(uuid=u,**inventories[b][u])for u in sorted(added)],**detail)
# Corrected contract ledger: old immutable contract values kept side by side, never rewritten.
contract=L(Path('/tmp/v7-c128-deadbranch-readonly-aead/RETIREMENT_CONTRACT.json'));ret={x['uuid']for x in contract['retire']};am=edges(g['aead']);cm=edges(g['cafa']);az=edges(g['aead'],True);cz=edges(g['cafa'],True);boundary=[dict(stub_uuid=next(u for u in k if u in ret),live_uuid=next(u for u in k if u not in ret),actual_support=v)for k,v in am.items()if len(set(k)&ret)==1];assert len(boundary)==1 and boundary[0]['stub_uuid']=='0858c392-ee59-5350-bcaf-d8762f658a08'and boundary[0]['live_uuid']=='f578f80d-52bb-500f-b3df-4fe97eccdb4e'
corrected_objects=[]
for obj in contract['retire']+[contract['preserve_attachment_track']]:
 u=obj['uuid'];actual=[dict(uuid=(k[1]if k[0]==u else k[0]),support=v)for k,v in am.items()if u in k];zones=[dict(zone=k[0],area_mm2=v)for k,v in az.items()if k[1]==u];corrected_objects.append(dict(uuid=u,native_type=inventories['aead'][u]['type'],original_contract_direct_contacts=obj['direct_contacts'],corrected_source_direct_contacts=actual,original_contract_zone_contacts=obj['zone_contacts'],corrected_source_zone_contacts=zones))
aw=L(Path('/tmp/v7-c128-deadbranch-readonly-aead/ATTACHMENT_TO_C128_JOIN.json'));routes=[dict(label=' to '.join(w['endpoints']),route=w['native_positive_copper_witness'])for w in contract['live_witnesses']]+[dict(label='attachment to C128 join',route=[o['uuid']for o in aw['objects']])];witnesses=[]
for w in routes:
 proof=[]
 for a,b in zip(w['route'],w['route'][1:]):
  k=tuple(sorted((a,b)))
  if k in am:assert k in cm and am[k]==cm[k];proof.append(dict(a=a,b=b,kind='direct',actual_source_support=am[k],actual_candidate_support=cm[k]))
  else:
   k=(a,b)if a.startswith('zone:')else(b,a);assert k in az and k in cz and az[k]==cz[k];proof.append(dict(a=a,b=b,kind='zone',actual_source_area_mm2=az[k],actual_candidate_area_mm2=cz[k]))
 witnesses.append(dict(**w,edges=proof,positive_and_exact_preserved=True))
j1={}
for label in boards:
 pads=[u for u,d in g[label]['pad_inventory'].items()if d['ref']=='J1'and d['pad']=='A1'];assert len(pads)==1;u=pads[0];root=newroots[label][u];members=sorted(v for v in inventories[label]if newroots[label][v]==root);padmembers=sorted(v for v in g[label]['pad_inventory']if newroots[label][v]==root);j1[label]=dict(pad_uuid=u,net=inventories[label][u]['net'],native_object_members=members,pad_members=padmembers,native_object_count=len(members),pad_count=len(padmembers))
j1equal=j1['2c7']==j1['aead']==j1['cafa'];assert j1equal
ledger=dict(status='CORRECTED DRILL-AWARE EVIDENCE; original sealed contract untouched',original_contract_sha256=sha(Path('/tmp/v7-c128-deadbranch-readonly-aead/RETIREMENT_CONTRACT.json')),source_sha256=g['aead']['board_sha256'],candidate_sha256=g['cafa']['board_sha256'],sole_boundary_contact=boundary,retired_object_and_attachment_contacts=corrected_objects,live_and_attachment_witnesses=witnesses,J1_A1_root_members_exact_across_all_three=j1equal,J1_A1_roots=j1)
(D/'corrected-contract-witness-ledger.json').write_text(json.dumps(ledger,indent=2))
report=dict(status='CORRECTED_GRAPH_CHECKS_COMPLETE; no CAD mutation or selection; global plane gate separate',per_board_original_vs_corrected=reviews,corrected_transition_comparisons=pairchecks,controls=L(D/'controls.json'),J1_A1_root_exact_across_all_three=j1equal,all_five_C128_witnesses_corrected_and_preserved=True,corrected_contract_ledger='corrected-contract-witness-ledger.json',commands= L(D/'commands.json'))
(D/'CORRECTED_GRAPH_AUDIT.json').write_text(json.dumps(report,indent=2))
summary={label:{k:v for k,v in r.items()if k not in ['direct','zone']}|{'direct':{k:v for k,v in r['direct'].items()if k!='changed_still_positive_supports'},'zone':{k:v for k,v in r['zone'].items()if k!='changed_still_positive_supports'}}for label,r in reviews.items()};print(json.dumps(dict(per_board=summary,transitions=pairchecks,J1_A1_exact=j1equal),indent=2))
