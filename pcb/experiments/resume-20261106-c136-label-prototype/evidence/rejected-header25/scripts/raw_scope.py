from pathlib import Path
import sexp as sx,json
R=Path('/workspace/shared/maru60-resume/continuation-fix2/header25');build=json.load(open(R/'qa/isolate-refactor-build.json'));a=sx.parse(Path('/workspace/shared/maru60-resume/continuation-c782/combined27fix2/pcb/maru60.kicad_pcb').read_text());b=sx.parse((R/'rejected/isolate-refactor/pcb/maru60.kicad_pcb').read_text());uid=lambda q:(sx.get(q,'uuid')or[None,None])[1]if isinstance(q,list)else None;A={uid(q):q for q in a if uid(q)};B={uid(q):q for q in b if uid(q)};assert set(A)-set(B)==set(build['removed']);assert set(B)-set(A)==set(build['added']);assert [q for q in a if not uid(q)]==[q for q in b if not uid(q)];changes=[]
for u in set(A)&set(B):
 if A[u]!=B[u]:
  assert A[u][0]=='zone'
  strip=lambda q:[x for x in q if not(isinstance(x,list)and x[0]in ['filled_polygon','fill_segments'])]
  assert strip(A[u])==strip(B[u]);changes.append(u)
assert all(A[u][0]=='segment'for u in build['removed']);assert all(B[u][0]=='segment'for u in build['added']);result={'source_sha256':build['source_sha256'],'rejected_pcb_sha256':build['candidate_sha256'],'removed_count':len(build['removed']),'added_count':len(build['added']),'modified_retained_objects_except_zone_fills':0,'zone_fill_changed_uuids':changes,'all_retained_source_objects_except_zone_fills_exact':True,'no_net_or_rule_changes':True};(R/'qa/raw-scope.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
