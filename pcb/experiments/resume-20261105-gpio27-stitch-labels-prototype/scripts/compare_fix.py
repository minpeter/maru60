from pathlib import Path
import json,collections,hashlib,sys,copy
sys.path.insert(0,'/workspace/shared/maru60-resume/tools');from sexpr_spans import children,head,field
R=Path('/workspace/shared/maru60-resume/continuation-c782');D=R/'combined27fix2';S=R/'combined27';H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();a=(S/'pcb/maru60.kicad_pcb').read_text();b=(D/'pcb/maru60.kicad_pcb').read_text();u='55e5d0cf-c179-4e88-925d-241a5a9d4416';n='adb09d04-e93c-4f35-bbef-200d2bb1eb64';parse=lambda s:{field(t,'uuid'):t for _,_,t in children(s)if field(t,'uuid')};A=parse(a);B=parse(b);added=set(B)-set(A);changed=[k for k in A if A[k]!=B.get(k)];assert added=={f'(uuid "{n}")'}and changed==[f'(uuid "{u}")'];k=changed[0];strip=lambda t:'\n'.join(s for _,_,s in children(t)if head(s)!='end');assert strip(A[k])==strip(B[k]);restored=b
for start,end,t in reversed(children(restored)):
 key=field(t,'uuid')
 if key==k:restored=restored[:start]+A[k]+restored[end:]
 elif key in added:restored=restored[:start]+restored[end:]
# Whitespace from the added top-level form is intentionally disregarded; every existing form remains exact.
assert [t for _,_,t in children(a)]==[t for _,_,t in children(restored)]
files=lambda p:{str(f.relative_to(p)):H(f)for f in p.rglob('*')if f.is_file()};fa,fb=files(S/'pcb'),files(D/'pcb');assert len(fa)==len(fb)==58 and [k for k in fa if fa[k]!=fb[k]]==['maru60.kicad_pcb']
g=json.loads((S/'qa/material-graph.json').read_text());h=json.loads((D/'qa/material-graph.json').read_text());assert g['board_sha256']==H(S/'pcb/maru60.kicad_pcb')and h['board_sha256']==H(D/'pcb/maru60.kicad_pcb');assert g['pad_inventory']==h['pad_inventory']and g['pad_partitions_by_net']==h['pad_partitions_by_net'];de=lambda q:{(x,y,l):area for x,y,ls in q['direct_edges']for l,area in ls};ad,bd=de(g),de(h);lost=[k for k in ad if k not in bd];changedcontacts=[dict(edge=k,before=ad[k],after=bd.get(k))for k in ad if ad[k]!=bd.get(k)];assert all(u in k[:2]for k in lost);assert all(u in r['edge'][:2]for r in changedcontacts);remaps=[]
for x,y,l in lost:
 other=y if x==u else x;key=(*sorted([other,n]),l);assert key in bd and bd[key]>0;remaps.append({'retired_pair':[x,y,l],'before_area_mm2':ad[x,y,l],'replacement_pair':key,'after_area_mm2':bd[key],'exact_patch_identity_claimed':False})
assert g['zone_edges']==h['zone_edges'];assert g['barrel_joins']==h['barrel_joins'];assert g['guard_failing_material_edges']==h['guard_failing_material_edges'];nodes=[k for k,v in g['material_nodes'].items()if v!=h['material_nodes'].get(k)];assert all(g['material_nodes'][k].get('uuid')==u for k in nodes)
from collections import defaultdict
def keys(q,d):
 rp=defaultdict(list)
 for uid in q['pad_inventory']:
  roots=q['object_material_roots'][uid];assert len(roots)==1;rp[roots[0]].append(uid)
 out=[]
 for r in d['unconnected_items']:
  comps=[]
  for e in r['items']:
   roots=q['object_material_roots'][e['uuid']];assert len(roots)==1 and rp[roots[0]];comps.append(tuple(sorted(rp[roots[0]])))
  assert len(set(comps))==2;out.append(tuple(sorted(comps)))
 return collections.Counter(out)
da=json.loads((S/'qa/drc.json').read_text());db=json.loads((D/'qa/drc.json').read_text());assert keys(g,da)==keys(h,db)and len(db['unconnected_items'])==9;co=lambda rows:collections.Counter(json.dumps(r,sort_keys=True)for r in rows);assert co(da['violations'])==co(db['violations']);result={'source_sha256':g['board_sha256'],'candidate_sha256':h['board_sha256'],'raw_scope':'One old track end and one added track only; all other raw forms including all serialized fills exact.','all57_companions_exact':True,'all_pad_partitions_exact':True,'all9_complete_open_pairs_exact':True,'all42_warning_records_exact':True,'all_undeclared_contact_areas_exact':True,'declared_changed_contacts':changedcontacts,'declared_remapped_contacts':remaps,'only_old_track_material_nodes_changed':nodes,'zone_contacts_barrels_and_guard_diagnostics_exact':True,'fullplane_gate':'See full-plane-review.json and successful full-plane.log machine assertions.','pass':True};(D/'qa/fix-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
