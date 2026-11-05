from pathlib import Path
import json,hashlib
R=Path('/workspace/shared/maru60-resume/continuation-c782');O=R/'independent27fix2';a=json.loads((R/'combined27/qa/material-graph.json').read_text());b=json.loads((R/'combined27fix2/qa/material-graph.json').read_text());assert b['board_sha256']==hashlib.sha256((R/'combined27fix2/pcb/maru60.kicad_pcb').read_bytes()).hexdigest()=='9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed';old='55e5d0cf-c179-4e88-925d-241a5a9d4416';new='adb09d04-e93c-4f35-bbef-200d2bb1eb64'
for field in ['pad_inventory','pad_partitions_by_net','guard_failing_material_edges','empty_object_layers','multiple_component_object_layers','barrel_joins']:
 assert a[field]==b[field],field
assert sorted(a['zone_edges'])==sorted(b['zone_edges'])
for k,v in a['material_nodes'].items():
 if v.get('uuid')!=old:assert v==b['material_nodes'][k],k
def ed(g):return {tuple(sorted(x[:2])):x[2:]for x in g['direct_edges']}
x,y=ed(a),ed(b);gone=[{'key':k,'old':x[k]}for k in x.keys()-y.keys()];changed=[{'key':k,'old':x[k],'new':y[k]}for k in x.keys()&y.keys()if x[k]!=y[k]];added=[{'key':k,'new':y[k]}for k in y.keys()-x.keys()];assert all(old in row['key']for row in gone+changed);assert all(new in row['key']for row in added)
for row in gone:
 other=next(u for u in row['key']if u!=old);assert tuple(sorted([new,other]))in y,other
assert tuple(sorted([old,new]))in y
D=json.loads((O/'drc.json').read_text());E=json.loads((R/'combined27fix2/qa/drc.json').read_text());norm=lambda d:sorted([sorted([sorted(b['object_material_roots'][x['uuid']])for x in v['items']])for v in d['unconnected_items']]);assert norm(D)==norm(E);assert D['violations']==E['violations']
out={'candidate_sha256':b['board_sha256'],'removed_direct_edges':gone,'changed_direct_edges':changed,'added_direct_edges':added,'all_removed_contacts_remapped_to_added_segment':True,'all_pad_partitions_exact':True,'old_zone_edges_exact':True,'unrelated_material_nodes_exact':True,'guard_diagnostics_exact':True,'fresh_DRC_open_components_and_warning_records_exact':True};(O/'material-comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
