from pathlib import Path
import json,collections,hashlib
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-c782/stitch/qa';A=json.loads((R/'combined-trial/qa/material-graph.json').read_text());B=json.loads((D/'material-graph.json').read_text());a=json.loads((R/'combined-trial/qa/drc.json').read_text());b=json.loads((D/'drc.json').read_text());assert A['pad_inventory']==B['pad_inventory']and A['pad_partitions_by_net']==B['pad_partitions_by_net'];assert A['board_sha256']=='56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9'and B['board_sha256']=='22761b0f007cd9b113843c0074924fee02c3728e98f33d88fc90eb7cdc14ec9c'
def keys(g,d):
 rp=collections.defaultdict(list)
 for u,meta in g['pad_inventory'].items():
  roots=g['object_material_roots'][u];assert len(roots)==1;rp[roots[0]].append(u)
 out=[];records=[]
 for row in d['unconnected_items']:
  roots=[];nets=[];ends=[]
  for item in row['items']:
   u=item['uuid'];rs=g['object_material_roots'][u];assert len(rs)==1,(u,rs);r=rs[0];assert rp[r],u;nodes=[n for ns in g['object_nodes_by_layer'][u].values()for n in ns];net={g['material_nodes'][n]['net']for n in nodes};assert len(net)==1;net=next(iter(net));roots.append(r);nets.append(net);ends.append({'uuid':u,'native_description':item['description'],'native_position':item['pos'],'complete_pad_component':sorted(rp[r])})
  assert len(set(nets))==1 and len(set(roots))==2
  k=(nets[0],tuple(sorted(tuple(x['complete_pad_component'])for x in ends)));out.append(k);records.append({'net':nets[0],'endpoints':ends})
 return collections.Counter(out),records
ak,ar=keys(A,a);bk,br=keys(B,b);assert ak==bk and sum(ak.values())==10
out={'source_sha256':A['board_sha256'],'candidate_sha256':B['board_sha256'],'all_pad_inventory_and_partitions_exact':True,'all10_complete_open_pad_component_pairs_exact':True,'raw_endpoint_records_identical':a['unconnected_items']==b['unconnected_items'],'before_native_records':a['unconnected_items'],'after_native_records':b['unconnected_items'],'source_component_pairs':ar,'candidate_component_pairs':br,'changed_representatives':'Native representative records change within identical physical components; no open is hidden or added.','pass':True};(D/'open-component-pairs.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS: all10 complete physical pad-component pairs exact; representative records differ.')
