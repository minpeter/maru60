#!/usr/bin/python3
"""Independent evidence/graph binding, with full-record multisets and reconstructed connectivity."""
import os,sys,json,hashlib,collections
from pathlib import Path
if not __debug__ or sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):
    raise SystemExit('R2 binding requires assertions; optimized Python forbidden')
D=Path(__file__).resolve().parent
P=D.parent/'v7-connector-ground-contract-c770'
R=Path('/tmp/v7-connector-gnd-stitch-c770')
h=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
ms=lambda rows:collections.Counter(json.dumps(x,sort_keys=True,separators=(',',':')) for x in rows)
C=read(P/'CONSTRUCTION_CONTRACT.json')
assert h(P/'CONSTRUCTION_CONTRACT.json')=='c58baac31c087ddd115fb5ccbe7953ced52d8469c0efe675b2184ea00ff7d7a5'
S=Path(C['source']['board_path']); B=R/'filled/pcb/maru60.kicad_pcb'; u=C['only_construction_change']['uuid']
a_path=Path(C['source']['R2_graph_path']); b_path=R/'qa/material-graph.json'
assert h(S)==C['source']['board_sha256']
assert h(B)=='aaafc033c6e9809afcb189290c3740157b7ab5596aaa0867e581f08d89807eca'
assert h(a_path)==C['source']['R2_graph_sha256']
assert h(b_path)=='1129a187d109ce4e5d8e98788f8c22cd7d3f0b9edd0e6a70f0badac5cc602824'
assert h(R/'scripts/export_material_graph.py')==C['source']['active_material_helper_sha256']
a=read(a_path);b=read(b_path)
for x,board in [(a,S),(b,B)]:
    assert x['board_sha256']==h(board) and x['unchanged'] is True
    assert x['revision']=='v2-all-through-drills-layer-island-material-graph' and x['native_version']==C['source']['native_version']
    for key in ['all_physical_holes_through','unknown_via_or_drilled_pad_types_fail','no_foreign_drill_cut_to_plated_annuli','named_pads_unique_material_root']:
        assert x['scope_assumptions'][key] is True
assert b['scope_assumptions']['actual_drill_types']==C['expected_object_counts']['candidate_all_through_drills']
assert a['contact_guard']==b['contact_guard'] and b['contact_guard']['inward_nm']==2 and b['contact_guard']['max_error_nm']==1
checks={}
for key in ['pad_inventory','pad_partitions_by_net','empty_object_layers','multiple_component_object_layers','NPTH_material']:
    assert a[key]==b[key],key
    checks[key+'_exact']=True
for key in ['direct_edges','raw_unguarded_direct_edges','guard_failing_material_edges','native_pairs_without_guarded_positive_copper']:
    assert ms(a[key])==ms(b[key]),key
    checks[key+'_full_record_multiset_exact']=True
old=set(a['material_nodes']); new=set(b['material_nodes']); added=new-old
expected_nodes={'object:'+u+':'+str(layer)+':0' for layer in [0,4,6,2]}
assert added==expected_nodes and not old-new
changed=[]
for node in old:
    av=a['material_nodes'][node];bv=b['material_nodes'][node]
    if av==bv:continue
    assert av['kind']=='zone' and av['net']=='GND' and av['layer'] in ['In1.Cu','In2.Cu']
    assert {k:v for k,v in av.items() if k!='area_mm2'}=={k:v for k,v in bv.items() if k!='area_mm2'}
    changed.append({'node':node,'before_area_mm2':av['area_mm2'],'after_area_mm2':bv['area_mm2']})
assert len(changed)==2
for node in added:
    v=b['material_nodes'][node]
    assert v['kind']=='object' and v['net']=='GND' and v['uuid']==u and v['area_mm2']==0.147260768066
for key in ['material_edges','zone_edges','raw_unguarded_zone_edges']:
    old_records=[e for e in b[key] if not any(u in str(v) for v in e[:2])]
    assert ms(a[key])==ms(old_records),key
    checks[key+'_all_old_records_exact']=True
assert ms(a['barrel_joins'])==ms([x for x in b['barrel_joins'] if x['uuid']!=u])
new_barrel=[x for x in b['barrel_joins'] if x['uuid']==u]
assert len(new_barrel)==1 and set(new_barrel[0]['nodes'])==expected_nodes
assert new_barrel[0]['type']=='PCB_VIA'
new_edges=[e for e in b['material_edges'] if any(u in str(v) for v in e[:2])]
expected_edges=[['zone:7a0e11fe-4433-4b0d-914b-0fa7262b6aa2:4:0','object:'+u+':4:0',0.147260768066,0.1472558792225],['zone:3a23a46c-3272-47d8-86cd-03a9240b82af:6:0','object:'+u+':6:0',0.147260768066,0.1472558792225]]
assert ms(new_edges)==ms(expected_edges)
for obj in a['object_nodes_by_layer']:
    assert a['object_nodes_by_layer'][obj]==b['object_nodes_by_layer'][obj]
# Reconstruct each connected component, independently of the exporter's saved root labels.
def reconstruct(g):
    parent={n:n for n in g['material_nodes']}
    def find(n):
        while parent[n]!=n:
            parent[n]=parent[parent[n]];n=parent[n]
        return n
    def join(x,y):
        assert g['material_nodes'][x]['net']==g['material_nodes'][y]['net'],('cross-net join',x,y)
        parent[find(x)]=find(y)
    for x,y,overlap,guarded in g['material_edges']:
        assert overlap>0 and guarded>0
        join(x,y)
    for barrel in g['barrel_joins']:
        for n in barrel['nodes'][1:]:join(barrel['nodes'][0],n)
    parts=collections.defaultdict(list)
    for n in parent:parts[find(n)].append(n)
    return find,{frozenset(v) for v in parts.values()}
fa,pa=reconstruct(a);fb,pb=reconstruct(b)
assert pa=={frozenset(part-added) for part in pb if part-added}
anchor=next(i for i,x in b['pad_inventory'].items() if x['ref']=='J1' and x['pad']=='A1')
anchor_nodes=[n for nodes in b['object_nodes_by_layer'][anchor].values() for n in nodes]
assert anchor_nodes
root=fb(anchor_nodes[0]);saved_root=b['object_material_roots'][anchor];assert len(saved_root)==1
gnd=[i for i,x in b['pad_inventory'].items() if x['net']=='GND']
for obj in gnd+[u]:
    assert b['object_material_roots'][obj]==saved_root
    nodes=[n for layer_nodes in b['object_nodes_by_layer'][obj].values() for n in layer_nodes]
    assert nodes and all(fb(n)==root for n in nodes)
# Full native DRC entries rather than only aggregate counts, and exact companions.
sd=read('/tmp/v7-gnd-tail-cleanup-aead/qa/drc.json');cd=read(R/'qa/drc.json');erc=read(R/'qa/erc.json')
assert cd['violations']==sd['violations'] and cd['unconnected_items']==sd['unconnected_items']
assert not cd['schematic_parity'] and all(v['severity']=='warning' for v in cd['violations'])
assert not [v for s in erc.get('sheets',[]) for v in s.get('violations',[])]
for kind in ['drc','erc']:
    e=read(R/('qa/'+kind+'.execution.json'))
    assert e['exit']==0 and e['candidate_sha256']==h(B)
    assert str(B if kind=='drc' else B.with_suffix('.kicad_sch'))==e['argv'][-1]
    assert '--severity-all' in e['argv']
    if kind=='drc':assert '--schematic-parity' in e['argv'] and '--all-track-errors' in e['argv']
source_tree=S.parent
files={str(p.relative_to(source_tree)):h(p) for p in source_tree.rglob('*') if p.is_file()}
candidate_files={str(p.relative_to(B.parent)):h(p) for p in B.parent.rglob('*') if p.is_file()}
assert set(files)==set(candidate_files)
assert all(v==candidate_files[k] for k,v in files.items() if k!='maru60.kicad_pcb')
cold=read(D/'cold_refill_results.json')
assert cold['byte_identical'] and cold['source_tree_unchanged'] and cold['cold_refilled_board_sha256']==h(B)
assert h(Path(cold['independent_copy'])/'maru60.kicad_pcb')==h(B)
checks.update({'retained_barrels_exact':True,'all_old_material_partitions_reconstructed_exact':True,'no_cross_net_accepted_material_or_barrel_join':True,'new_barrel_intact_four_layers':True,'exactly_two_new_inner_root_contacts':True,'all_GND_pads_and_new_via_reconstructed_J1_root':True,'native_full_warning_and_open_entries_exact':True,'native_other_hard_DRC_zero':True,'native_ERC_and_parity_zero':True,'all_project_companions_exact':True,'independent_normal_cold_refill_byte_equal':True})
r={'status':'PASS independent actual R2/connectivity/native/cold-refill binding; combine with actual_geometry.json for strict material and reference acceptance','source_sha256':h(S),'candidate_sha256':h(B),'contract_sha256':h(P/'CONSTRUCTION_CONTRACT.json'),'source_graph_sha256':h(a_path),'actual_graph_sha256':h(b_path),'exporter_sha256':h(R/'scripts/export_material_graph.py'),'checks':checks,'new_via_nodes':sorted(added),'new_material_edges':new_edges,'new_barrel':new_barrel[0],'retained_material_nodes':len(old),'retained_material_edges_with_witnesses':len(a['material_edges']),'old_material_components':len(pa),'actual_material_components':len(pb),'named_pad_count':len(b['pad_inventory']),'pad_net_groups':len(b['pad_partitions_by_net']),'GND_pad_count':len(gnd),'saved_J1_A1_root':saved_root,'changed_zone_areas':changed,'native_warnings':len(cd['violations']),'native_raw_opens':len(cd['unconnected_items']),'companion_count':len(files)-1,'evidence_file_hashes':{str(p):h(p) for p in [a_path,b_path,R/'qa/drc.json',R/'qa/erc.json',R/'qa/drc.execution.json',R/'qa/erc.execution.json',D/'cold_refill_results.json']},'limits':['Native geometric connectivity only; not SI, PDN, EMC, ESD or manufacturing qualification.','New grounded copper can alter USB local electromagnetic fields and coupling even though every existing signal object is unchanged.','No source-supported parasitic extraction or post-change waveform model is available for this stitch; no physical SI improvement is claimed.','Nearest-return distance is geometric only, not an inductance measurement.']}
(D/'actual_R2_binding.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
