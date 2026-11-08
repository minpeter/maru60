import json,collections
from pathlib import Path
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-97d9eb7/stub3v3';a=json.loads((R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype/qa/material-graph.json').read_text());b=json.loads((D/'qa/material-graph.json').read_text());rm=set(json.loads((D/'qa/build.json').read_text())['removed']);old={n for n,v in a['material_nodes'].items()if v.get('uuid')not in rm};assert old==set(b['material_nodes'])
def groups(g):
 bins=collections.defaultdict(set)
 for n in old:bins[g['material_roots'][n]].add(n)
 return {frozenset(v)for v in bins.values()}
assert groups(a)==groups(b)
edge=lambda g:{tuple(sorted(e[:2])):e[2:]for e in g['material_edges']if all(n in old for n in e[:2])};aa,bb=edge(a),edge(b);assert aa.keys()==bb.keys();reduced=[{'edge':k,'old':v,'new':bb[k]}for k,v in aa.items()if any(n<o for o,n in zip(v,bb[k]))];assert not reduced
out={'all_retained_material_node_ids_equal':True,'retained_material_nodes':len(old),'all_retained_material_components_equal':True,'components':len(groups(a)),'all_retained_island_contacts_preserved':True,'retained_edges':len(aa),'any_raw_or_guarded_overlap_reduced':False};(D/'qa/retained-material-partitions.json').write_text(json.dumps(out,indent=2));print(out)
