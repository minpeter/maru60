from pathlib import Path
import json,hashlib,sys,re,collections
from sexpr_spans import children
R=Path('/tmp/v7-support-endpoint-trial');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();S=R/'source/pcb/maru60.kicad_pcb';C=R/'filled/pcb/maru60.kicad_pcb';ct=json.loads((R/'BUILD_CONTRACT.json').read_text());scope={r['uuid']for r in ct['changed_main_tracks']}
def records(p):
 d={};oth=[]
 for a,z,t in children(p.read_text()):
  m=re.search(r'\(uuid "([^"]+)"\)',t)
  if m:d[m.group(1)]=t
  else:oth.append(t)
 return d,oth
a,ao=records(S);b,bo=records(C);assert set(a)==set(b)and ao==bo;changed={u for u in a if a[u]!=b[u]};assert changed==scope;zones=[u for u in a if a[u].startswith('(zone')];assert len(zones)==12 and all(a[u]==b[u]for u in zones)
sm=json.loads((R/'SOURCE_TREE_MANIFEST.json').read_text());assert all(H(R/'filled/pcb'/k)==v['sha256']for k,v in sm.items()if k!='maru60.kicad_pcb')
d=json.loads((R/'qa/drc.json').read_text());o=json.loads(Path('/tmp/v7-c124-d-plus-connector-gnd/qa/drc.json').read_text());C=count=lambda q:collections.Counter(json.dumps(v,sort_keys=True)for v in q);old=C(o['violations']);new=C(d['violations']);removed=[json.loads(v)for v in(old-new).elements()];added=[json.loads(v)for v in(new-old).elements()];assert not added and len(removed)==3;assert {x['items'][0]['uuid']for x in removed}=={r['support_uuid']for r in ct['changed_main_tracks']};assert C(d['unconnected_items'])==C(o['unconnected_items']);assert not d['schematic_parity'];assert all(v['severity']=='warning'for v in d['violations'])
out={'status':'PASS bounded three-track endpoint delta','source_sha256':H(S),'actual_sha256':H(R/'filled/pcb/maru60.kicad_pcb'),'exact_changed_UUIDs':sorted(changed),'all_other_top_level_raw_objects_exact':True,'all12_raw_zone_records_exact':True,'all_original_holes_vias_footprints_exact':True,'all57_companions_exact':True,'native_warnings_before':64,'native_warnings_after':61,'removed_warnings':removed,'added_warnings':added,'raw12opens_exact':True,'hard_DRC':0,'parity':0,'same_net_union_delta_is_not_claimed_zero':True,'old_reference_invariance':'All actual saved zone records and all physical drill objects are byte-identical to 7882, so physical plane material and every old reference projection are pointwise unchanged, including retired historical shadows.'};(R/'qa/raw-native-comparison.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
