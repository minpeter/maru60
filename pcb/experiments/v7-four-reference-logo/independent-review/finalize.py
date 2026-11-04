from pathlib import Path
import json,hashlib,collections,xml.etree.ElementTree as E,math
P=Path(__file__).resolve().parent;W=P.parent/'v7-safe-five-logo-recovered';Q=W/'qa';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
source=read(Q/'source-native.json');candidate=read(Q/'candidate-four-native.json')
def components(n):
 identity=n['net_identity'];ds=n['diagnostic_items'];assert set(ds)==set(n['track_geometry'])|set(n['pad_geometry']);parent={u:u for u in ds}
 def root(u):
  while parent[u]!=u:parent[u]=parent[parent[u]];u=parent[u]
  return u
 assert n['edges']==sorted([list(x) for x in set(map(tuple,n['edges']))])
 for u,v in n['edges']:
  assert u<v and u in ds and v in ds and identity[u]==identity[v];parent[root(v)]=root(u)
 group=collections.defaultdict(list)
 for u in ds:
  if identity[u]:group[(identity[u],root(u))].append(u)
 derived={(net,tuple(sorted(ids))) for (net,r),ids in group.items()}
 assert derived=={(r['net'],tuple(r['object_uuids'])) for r in n['native_components']}
 return {u:g for g in derived for u in g[1]},derived
ownersA,groupsA=components(source);ownersB,groupsB=components(candidate);assert groupsA==groupsB and len(groupsA)==508

def opens(path,n,owners):
 d=read(path);assert d['coordinate_units']=='mm' and d['kicad_version']=='9.0.2';assert len(d['unconnected_items'])==12;answer={}
 for r in d['unconnected_items']:
  assert set(r)=={'description','items','severity','type'} and r['description']=='Missing connection between items' and r['type']=='unconnected_items' and r['severity']=='error' and len(r['items'])==2
  pair=[]
  for x in r['items']:
   assert set(x)=={'uuid','description','pos'};u=x['uuid'];assert u in owners;actual=n['diagnostic_items'][u];assert x['description']==actual['description'];assert set(x['pos'])=={'x','y'} and all(type(v) in (int,float) and math.isfinite(v) for v in x['pos'].values());assert [x['pos']['x'],x['pos']['y']] in actual['positions_mm'];pair.append(owners[u])
  assert pair[0][0]==pair[1][0] and pair[0]!=pair[1];key=tuple(sorted(pair));assert key not in answer;answer[key]=r
 return answer
A=opens(Q/'source-drc.json',source,ownersA);B=opens(Q/'candidate-four-drc.json',candidate,ownersB);assert A.keys()==B.keys()
xa=E.parse(Q/'source-netlist.xml').getroot();xb=E.parse(Q/'candidate-four-netlist.xml').getroot()
assert xa.findtext('design/source')==str(W/'input/maru60.kicad_sch');assert xb.findtext('design/source')==str(W/'candidate-four/pcb/maru60.kicad_sch')
for root in (xa,xb):
 for key in ('source','date'):root.find('design').remove(root.find('design/'+key))
local_libraries={'Maru60':'Maru60.kicad_sym','Maru60_Options':'engineering/Maru60_Options.kicad_sym','Study':'Study.kicad_sym'}
lib_provenance=[]
for name,rel in local_libraries.items():
 ua=xa.find('libraries/library[@logical="'+name+'"]/uri');ub=xb.find('libraries/library[@logical="'+name+'"]/uri');pa=W/'input'/rel;pb=W/'candidate-four/pcb'/rel
 assert ua.text==str(pa) and ub.text==str(pb) and H(pa)==H(pb)
 lib_provenance.append({'logical':name,'source_uri':ua.text,'candidate_uri':ub.text,'same_file_sha256':H(pa)})
 ua.text=ub.text=rel
assert E.tostring(xa)==E.tostring(xb)
erc=read(Q/'candidate-four-erc.json');assert erc['kicad_version']=='9.0.2' and erc['coordinate_units']=='mm' and not any(s['violations'] for s in erc['sheets'])
# Every examined executed producer stage is tied to its concrete command and logfile.
stages=['source-drc','candidate-four-drc','source-ink','candidate-four-ink','source-native','candidate-four-native','candidate-four-erc','source-netlist','candidate-four-netlist'];bindings={}
for name in stages:
 e=read(Q/(name+'.execution.json'));assert type(e['exit_code']) is int and e['exit_code']==0;assert H(Q/(name+'.log'))==e['log_sha256'];assert len(set(e['private_xdg'].values()))==5
 ext='xml' if 'netlist' in name else 'json';out=Q/(name+'.'+ext);assert str(out) in e['command'];bindings[name]={'execution_sha256':H(Q/(name+'.execution.json')),'output_sha256':H(out),'log_sha256':e['log_sha256'],'command':e['command']}
pre=read(P/'review.json');probe=read(P/'native/result.json');assert probe['pass'] is True and probe['candidate_sha256']==pre['candidate_board_sha256'];assert H(P/'native/probe.py')==probe['checker_sha256'];assert len(probe['targets'])==21
plan=read(W/'PLAN-four.json');smap={str(p.relative_to(W/'input')):H(p) for p in (W/'input').rglob('*') if p.is_file()};cmap={str(p.relative_to(W/'candidate-four/pcb')):H(p) for p in (W/'candidate-four/pcb').rglob('*') if p.is_file()};assert smap==read(W/'SOURCE.json')['files_sha256'] and cmap==plan['candidate_file_map']
report={'decision':'adoption_eligible_bounded_reference_and_logo_only_change','candidate_board_sha256':pre['candidate_board_sha256'],'source_board_sha256':pre['source_board_sha256'],'selection_performed':False,'basis':['Independent exact whole-board byte restoration after undoing only four reference fields and one whole-logo anchor.','Independent actual native ink probe passed all four labels, both complete logo polygons and the prior15 reference set.','Actual native preview inspected for owner association; no current crossed-component blocker.','All24 exact removed warning records involve the changed fields or logo; zero new records.','Full recorded native inventory/edges unchanged; independent reconstruction of all508 native partitions and exact12 endpoint-component open pairs agrees.','All53 source members preserved except board, with one separately named and hashed generated local-metadata file.','Fresh candidateERC0 and complete XML equality after exact design-source/date and three hash-identical local-library URI provenance normalization.'],'native_probe_sha256':H(P/'native/result.json'),'native_probe_checker_sha256':H(P/'native/probe.py'),'preliminary_visual_raw_record_review_sha256':H(P/'review.json'),'warning_counts':[92,68],'hard_DRC_excluding_existing_opens':0,'existing_open_pair_count':12,'complete_native_component_count':508,'open_representative_changes':sum(A[k]!=B[k] for k in A),'fresh_candidate_ERC_violations':0,'local_library_uri_provenance':lib_provenance,'recorded_native_counts':candidate['counts'],'recorded_native_length_fsum_mm':candidate['length_fsum_mm'],'actual_independent_minimum_clearance_checked_nm':{'new_four_and_both_logo_mask_silk_courtyard_closedFab_unreconstructedFab':150000,'boardedge':250000,'prior15_mask_silk':150000},'producer_stage_bindings':bindings,'all_current_source_and_candidate_maps_still_exact':True,'limitations':['This recommendation is for these exact metadata/artwork-only bytes, not certification of the rebuilt generic checker for arbitrary future edits.','No new source-rooted physical-plane graph, cold-fill replay or active circuit simulation was performed. Raw electrical geometry and saved fills remain exactly the accepted source bytes.','Existing12GPIO opens and68remaining warnings remain unresolved; no global electrical-connectivity or manufacturing pass is implied.','Mechanical/courtyard/Fab checks are2D proxies. Actual assembly3D visibility, supplier approval and hardware qualification remain false.','Independent fixed-threshold checks prove the stated150/250um bounds. Larger producer bracket values were not independently recomputed here.'],'hardware_qualified':False,'manufacturing_qualified':False,'actual_3D_qualified':False}
(P/'FINAL_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
(P/'README.md').write_text('''# Four-reference plus intact-logo review\n\n**Bounded adoption-eligible for exact candidate2c7e100a. Selection remains with the parent.**\n\nIndependent raw restoration proves that only four Reference fields and the intact LOGO1 anchor changed. Candidate electronics, pads, nets, rules, copper and saved-fill bytes are unchanged. All24 removed warning records involve those changes; none were added. Actual native preview inspection finds no crossed-component association blocker.\n\nA fresh independent read-only native probe checks all1,759 mask apertures, including eight explicit U1 mask graphics. Four changed references and both logo polygons pass150um mask/silk/courtyard/closed-and-open-Fab proxy checks,250um edge checks and conservative whole-ink board containment. Prior15 accepted references also pass150um mask/silk and no proxy intersection.\n\nIndependent comparison reconstructs all508 recorded native components and confirms the exact12 existing open-component pairs, including each diagnostic endpoint UUID, native description and position. CandidateERC is zero and full exported netlists agree after only explicit design-source/date and three hash-identical local-library URI provenance normalization.\n\nThis is an exact-candidate safety review, not a newly certified generic acceptance harness. No physical-source graph, cold-fill replay, active simulation,3D assembly or hardware qualification is claimed. The existing12GPIO opens and68remaining warnings remain. See FINAL_REVIEW.json for exact bindings and scope.\n''')
# Only durable evidence, not ephemeral private profile/cache contents.
manifest={str(p.relative_to(P)):H(p) for p in sorted(P.rglob('*')) if p.is_file() and 'runtime' not in p.relative_to(P).parts and p.name!='MANIFEST.json'}
(P/'MANIFEST.json').write_text(json.dumps({'scope':'Bounded independent actual-candidate safety review','files':manifest},indent=2)+'\n')
print(json.dumps({'decision':report['decision'],'final_review_sha256':H(P/'FINAL_REVIEW.json'),'manifest_sha256':H(P/'MANIFEST.json'),'files':len(manifest)},indent=2))
