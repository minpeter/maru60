from pathlib import Path
import sexp as sx,json,hashlib
R=Path('/workspace/shared/maru60-resume/continuation-fa96a7c/gpio24-via25');S=Path('/workspace/shared/maru60-resume/selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype/pcb');build=json.loads((R/'qa/BUILD.json').read_text());a=sx.parse((S/'maru60.kicad_pcb').read_text());b=sx.parse((R/'candidate/pcb/maru60.kicad_pcb').read_text());uid=lambda q:(sx.get(q,'uuid')or[None,None])[1]if isinstance(q,list)else None;A={uid(q):q for q in a if uid(q)};B={uid(q):q for q in b if uid(q)};assert set(A)<=set(B);assert set(B)-set(A)==set(build['added']);assert [q for q in a if not uid(q)]==[q for q in b if not uid(q)];changes=[];zones=[]
for u in A:
 if A[u]!=B[u]:
  if A[u][0]=='zone':
   strip=lambda q:[x for x in q if not(isinstance(x,list)and x[0]in['filled_polygon','fill_segments'])];assert strip(A[u])==strip(B[u]);zones.append(u)
  else:changes.append(u)
assert set(changes)==set(build['modified']);h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();companions=[str(q.relative_to(S))for q in S.rglob('*')if q.is_file()and q.name!='maru60.kicad_pcb'];assert all(h(S/q)==h(R/'candidate/pcb'/q)for q in companions)
out=dict(modified_exact=changes,added_exact=build['added'],no_removed=True,all_other_geometry_exact=True,all_pin_nets_and_rules_exact=True,zone_fill_changes=zones,companion_files_identical=len(companions));(R/'qa/raw-scope.json').write_text(json.dumps(out,indent=2));print(out)
