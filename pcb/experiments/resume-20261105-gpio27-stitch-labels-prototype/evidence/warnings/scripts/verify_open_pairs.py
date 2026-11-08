from pathlib import Path
import json,collections,hashlib
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-c782/warnings';G=json.loads((R/'combined-trial/qa/material-graph.json').read_text());A=json.loads((R/'combined-trial/qa/drc.json').read_text());B=json.loads((D/'qa/drc.json').read_text());raw=json.loads((D/'qa/raw-and-drc-review.json').read_text());assert raw['raw_inverse_byte_exact']and raw['only_reference_fields']==['U13','R135','R145'];rootpads=collections.defaultdict(list)
for uid in G['pad_inventory']:
 rs=G['object_material_roots'][uid];assert len(rs)==1;rootpads[rs[0]].append(uid)
def keys(d):
 out=[];records=[]
 for row in d['unconnected_items']:
  pairs=[]
  for item in row['items']:
   uid=item['uuid'];rs=G['object_material_roots'][uid];assert len(rs)==1 and rootpads[rs[0]];pairs.append(tuple(sorted(rootpads[rs[0]])))
  assert pairs[0]!=pairs[1];out.append(tuple(sorted(pairs)));records.append({'native':row,'full_endpoint_pad_components':[list(x)for x in pairs]})
 return collections.Counter(out),records
ak,ar=keys(A);bk,br=keys(B);assert ak==bk and sum(ak.values())==10;out={'pass':True,'source_sha256':raw['source_sha256'],'candidate_sha256':raw['candidate_sha256'],'source_material_graph_sha256':hashlib.sha256((R/'combined-trial/qa/material-graph.json').read_bytes()).hexdigest(),'inheritance_basis':'Complete byte-exact board reversal changes only3 reference fields; all conductive geometry, nets, drills, rule configuration and filled zones exact. Reused source material graph, not a fresh graph export.','all10_complete_open_component_pairs_exact':True,'raw_representatives_exact':A['unconnected_items']==B['unconnected_items'],'before':ar,'after':br};(D/'qa/open-component-pairs.json').write_text(json.dumps(out,indent=2)+'\n');print('All10 physical component pairs exact under raw electrical identity.')
