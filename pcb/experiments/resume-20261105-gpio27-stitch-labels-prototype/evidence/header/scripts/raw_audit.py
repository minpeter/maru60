import json,copy,hashlib
from pathlib import Path
import sexp as sx
R=Path('/workspace/shared/maru60-resume/continuation-c782/header');S=Path('/workspace/shared/maru60-resume/combined-trial/pcb');C=R/'trial27/pcb';build=json.loads((R/'qa/BUILD.json').read_text());a=sx.parse((S/'maru60.kicad_pcb').read_text());b=sx.parse((C/'maru60.kicad_pcb').read_text());getid=lambda x:(sx.get(x,'uuid')or[None,None])[1]if isinstance(x,list)else None;A={getid(x):x for x in a if getid(x)};B={getid(x):x for x in b if getid(x)};added=set(B)-set(A);removed=set(A)-set(B);changed=[u for u in A.keys()&B.keys()if A[u]!=B[u]];assert added==set(build['added_uuids'])and not removed
strip=lambda node,names:[x for x in node if not(isinstance(x,list)and x[0]in names)];rows=[]
for u in changed:
 old,new=A[u],B[u]
 if old[0]=='zone':assert strip(old,{'filled_polygon','fill_segments'})==strip(new,{'filled_polygon','fill_segments'});kind='filled polygons only'
 else:
  assert u in build['modified_source_uuids'];fields={'at'}if old[0]=='via'else{'start','end'};assert strip(old,fields)==strip(new,fields);kind='declared coordinates only'
 rows.append({'uuid':u,'kind':kind,'type':old[0],'before':{n:sx.get(old,n)for n in ['net','at','start','end']if sx.get(old,n)},'after':{n:sx.get(new,n)for n in ['net','at','start','end']if sx.get(new,n)}})
assert {u for u in changed if A[u][0]!='zone'}==set(build['modified_source_uuids']);restored=[copy.deepcopy(A[getid(x)])if getid(x)in A else x for x in b if getid(x)not in added];assert restored==a
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();fm=lambda p:{str(f.relative_to(p)):H(f)for f in p.rglob('*')if f.is_file()};sa,ca=fm(S),fm(C);assert set(sa)==set(ca)and[k for k in sa if sa[k]!=ca[k]]==['maru60.kicad_pcb'];out={'source_sha256':sa['maru60.kicad_pcb'],'candidate_sha256':ca['maru60.kicad_pcb'],'added_uuids':sorted(added),'changed_existing':rows,'all_undeclared_source_objects_exact':True,'all_57_companions_exact':True,'source_files':sa,'candidate_files':ca};(R/'qa/raw-audit.json').write_text(json.dumps(out,indent=2));print('RAW PASS',len(added),'added',len(build['modified_source_uuids']),'declared old edits')
