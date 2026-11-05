import json
from pathlib import Path
r=Path('/workspace/shared/maru60-resume/continuation-fa96a7c/gpio24-via25');s=Path('/workspace/shared/maru60-resume/selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype/qa/material-graph.json');a=json.load(open(s));b=json.load(open(r/'qa/material-graph.json'));build=json.load(open(r/'qa/BUILD.json'));canon=lambda x:sorted(sorted(c)for c in x);expected=a['pad_partitions_by_net'].copy();parts=expected['EXT_GPIO25'];u='cff436d2-a051-486a-8eda-ad80c8687157';j='bee40e5c-5047-43dd-8262-df42b4062ba6';merged=[];others=[]
for c in parts:
 if u in c or j in c:merged+=c
 else:others.append(c)
expected['EXT_GPIO25']=others+[merged];intended={k:canon(v)for k,v in expected.items()}=={k:canon(v)for k,v in b['pad_partitions_by_net'].items()};assert a['pad_inventory']==b['pad_inventory']
mod=set(build['modified']);groups={};missing=[]
for node,root in a['material_roots'].items():
 m=a['material_nodes'][node]
 if m['kind']!='object'or m['uuid']in mod:continue
 if node not in b['material_roots']:missing.append(node);continue
 groups.setdefault(root,set()).add(b['material_roots'][node])
oldcontacts={tuple(sorted((x,y)))for x,y,*_ in a['material_edges']if a['material_nodes'][x].get('uuid')not in mod and a['material_nodes'][y].get('uuid')not in mod};newcontacts={tuple(sorted((x,y)))for x,y,*_ in b['material_edges']};lost=oldcontacts-newcontacts
out=dict(intended_gpio25_merger_only=intended,all_pad_nets_identical=True,retained_material_roots_no_split=all(len(v)==1 for v in groups.values()),missing_nodes=missing,retained_positive_contact_edges_lost=[list(x)for x in sorted(lost)],source_guard_diagnostics=len(a['guard_failing_material_edges']),candidate_guard_diagnostics=len(b['guard_failing_material_edges']));(r/'qa/material-comparison.json').write_text(json.dumps(out,indent=2));print(out);assert intended and out['retained_material_roots_no_split']and not missing and not lost
