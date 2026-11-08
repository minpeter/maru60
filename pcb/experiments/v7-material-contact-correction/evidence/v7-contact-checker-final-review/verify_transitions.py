#!/usr/bin/python3
from pathlib import Path
import json,hashlib,collections
R=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2'); O=Path('/tmp/v7-contact-checker-final-review')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def get(p):return json.loads(Path(p).read_text())
def demand(v,m):
 if not v:raise RuntimeError(m)
a=get(R/'2c7/physical-graph.json'); b=get(R/'j3_b5c/physical-graph.json')
new=set(b['object_nodes_by_layer'])-set(a['object_nodes_by_layer']);demand(new=={'aec7b234-8210-4a87-a022-d746958c4589','e11af75f-071f-405a-9a20-a227d234c83d','4f25e68e-e031-4aa9-8534-3e7de85924d2'},'J3 added')
demand(not(set(a['object_nodes_by_layer'])-set(b['object_nodes_by_layer'])),'J3 retired')
demand(a['pad_inventory']==b['pad_inventory'],'J3 pads')
deltas=[n for n in a['pad_partitions_by_net'] if a['pad_partitions_by_net'][n]!=b['pad_partitions_by_net'][n]];demand(deltas==['EXT_GPIO26'],'J3 intended net')
before=a['pad_partitions_by_net']['EXT_GPIO26']; after=b['pad_partitions_by_net']['EXT_GPIO26'];demand(len(before)==2 and len(after)==1 and sorted(sum(before,[]))==after[0],'EXT26 whole merger')
def direct(g,exclude):return {tuple(sorted([u,v])):s for u,v,s in g['direct_edges'] if u not in exclude and v not in exclude}
def zone(g,exclude):return {(z,u):s for z,u,s in g['zone_edges'] if u not in exclude}
demand(direct(a,set())==direct(b,new),'J3 old direct supports')
demand(zone(a,set())==zone(b,new),'J3 old zone supports')
forward=collections.defaultdict(set);reverse=collections.defaultdict(set)
for n,r in a['material_roots'].items():
 demand(n in b['material_roots'],'old material node'); q=b['material_roots'][n];forward[r].add(q);reverse[q].add(r)
demand(all(len(v)==1 for v in forward.values()),'old root split')
mergers={k:sorted(v) for k,v in reverse.items() if len(v)>1};demand(len(mergers)==1 and len(next(iter(mergers.values())))==2,'root merger count')
for target in mergers:
 demand({b['material_nodes'][n]['net'] for n in b['material_roots'] if b['material_roots'][n]==target}=={'EXT_GPIO26'},'merger net')
family={}
for label in ['j3_b5c','c124_ec487']:
 audit=get(R/'EXTRA_MATERIAL_GRAPH_AUDIT.json')['reports'][label];old=get(audit['original_graph_path']);cur=get(R/label/'physical-graph.json');demand(sha(audit['original_graph_path'])==audit['original_graph_sha256'],'original binding');demand(old['pad_inventory']==cur['pad_inventory'] and old['pad_partitions_by_net']==cur['pad_partitions_by_net'],'family partitions')
 family[label]={'original_graph_sha256':sha(audit['original_graph_path']),'corrected_graph_sha256':sha(R/label/'physical-graph.json'),'all_original_pad_identities_and_partitions_exact':True}
carry=get(R/'C124_EXACT_ELECTRICAL_CARRY.json');base=Path(carry['base_path']);final=Path(carry['final_path']);maps=[]
for root in [base.parent,final.parent]:maps.append({str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()})
demand(maps[0].keys()==maps[1].keys() and [p for p in maps[0] if maps[0][p]!=maps[1][p]]==['maru60.kicad_pcb'],'C124 file carry');demand(len(maps[0])==carry['all_files_count']==57,'C124 fullfile count')
report={'status':'PASS','J3_corrected_transition':{'only_changed_net':deltas[0],'whole_EXT26_pad_merger':True,'no_old_material_root_split':True,'only_root_merger':mergers,'old_direct_and_zone_supports_exact':True,'new_direct_contacts':len(direct(b,set()))-len(direct(a,set()))},'same_board_original_to_corrected':family,'C124_carry':{'complete_files':57,'unchanged_nonboard_files':56,'raw_carry_receipt_sha256':sha(R/'C124_EXACT_ELECTRICAL_CARRY.json'),'base_sha256':sha(base),'final_sha256':sha(final)},'inputs':{str(R/'EXTRA_MATERIAL_GRAPH_AUDIT.json'):sha(R/'EXTRA_MATERIAL_GRAPH_AUDIT.json')},'script_sha256':sha(__file__),'limits':'Only selected aead has the supplementary exact rational interior certificate for every accepted edge. Other boards use the reviewed guarded native R2 model. No CAD adoption, historical suite restoration or strict reference/plane waiver.'}
(O/'TRANSITION_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
