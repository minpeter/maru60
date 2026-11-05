from pathlib import Path
import json,hashlib
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-97d9eb7/stub3v3-independent';C=R/'continuation-97d9eb7/stub3v3';S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype';Q=D/'qa';j=lambda n:json.loads((Q/n).read_text());x=j('full-geometry-containment.json')
for r in x['zone_rows']:assert r['loss']=={'area_mm2':0,'outlines':0}
for r in x['retained_object_rows']:
 for k in ['loss','gain']:assert r[k]=={'area_mm2':0,'outlines':0},r
assert len(x['zone_rows'])==11 and len(x['retained_object_rows'])==15362 and len(x['retained_reference_rows'])==25726
assert all(r['pass']for r in x['retained_reference_rows'])and not x['failures']
b=j('retained-hole-bbox-proof.json');assert b['pass_all_disjoint'];narrow=[r for r in b['rows']if not r['strictly_disjoint_from_removed_hole_bbox']];assert len(narrow)==4 and all(r['exact_disjoint']for r in narrow)
trace=j('full-branch-trace.json');removed=set(j('build.json')['removed']);boundary=[]
for r in trace['rows']:
 if r['uuid']in removed:
  assert not r['zones'];boundary.extend((r['uuid'],r['layer'],c['uuid'])for c in r['contacts']if c['uuid']not in removed)
assert boundary==[('0858c392-ee59-5350-bcaf-d8762f658a08','F.Cu','f578f80d-52bb-500f-b3df-4fe97eccdb4e')]
for q in[S,C]:
 sha=hashlib.sha256((q/'pcb/maru60.kicad_pcb').read_bytes()).hexdigest(); graph=json.loads(((Q if q==C else q/'qa')/'material-graph.json').read_text());assert graph['board_sha256']==sha
assert j('material-comparison.json')['pass']
assert all(v['exact_loss_nm2']=='0'for v in j('exact-full-plane-proof.json').values())
assert all(v['no_source_or_candidate_boundary_enters_any_strip_interior']for v in j('strict-strip-proof.json').values())
r={'status':'PASS_BOUNDED_RELATIVE_CLEANUP','source_sha256':j('identity-scope.json')['source_sha256'],'candidate_sha256':j('identity-scope.json')['candidate_sha256'],'fresh_native':[ [40,9,0],[39,9,0]],'zone_rows_zero_loss_area_and_contours':11,'retained_rows_zero_loss_and_gain_area_and_contours':15362,'reference_rows':25726,'exact_diagonal_hole_disjoint_rows':4,'branch_boundary':boundary,'fresh_material_comparison':j('material-comparison.json'),'retained_partitions':j('retained-material-partitions.json'),'strict_strip_proof':j('strict-strip-proof.json'),'limits':'Immediate-source finite pendant cleanup only. Inherited c782/ef45 exact no-loss failure and 51 guarded-contact diagnostics remain. No strict baseline, SI/PDN/active-stability, hardware, fabrication or production qualification. No PCB edits or selection.'}
(D/'SUMMARY.json').write_text(json.dumps(r,indent=2));print(r)
