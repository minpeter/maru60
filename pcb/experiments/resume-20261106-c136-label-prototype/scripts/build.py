from pathlib import Path
import pcbnew as p,json,shutil,hashlib,sys
sys.path.insert(0,'/workspace/shared/maru60-resume/tools')
import sexpr_spans as x
D=Path(__file__).resolve().parents[1]; S=D.parent/'combined27fix2/pcb'; C=D/'pcb';H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert H(S/'maru60.kicad_pcb')=='9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed'
shutil.copytree(S,C);f=C/'maru60.kicad_pcb';old=f.read_text(); b=p.LoadBoard(str(f));fp=next(q for q in b.GetFootprints() if q.GetReference()=='C136');r=fp.Reference();r.SetPosition(p.VECTOR2I(176800000,89600000));r.SetTextAngle(p.EDA_ANGLE(90,p.DEGREES_T));r.SetTextSize(p.VECTOR2I(800000,800000));r.SetTextThickness(100000);p.SaveBoard(str(D/'qa/native-temporary.kicad_pcb'),b)
def span(t):
 for a,z,fp in x.children(t):
  if x.head(fp)!='footprint':continue
  for c,d,prop in x.children(fp):
   if prop.startswith('(property "Reference" "C136"'):return a+c,a+d,prop
 raise Exception('Missing field')
a,z,o=span(old);_,_,n=span((D/'qa/native-temporary.kicad_pcb').read_text());new=x.replace_span(old,a,z,n);f.write_text(new)
na,nz,np=span(new);assert x.replace_span(new,na,nz,o)==old
assert all(H(q)==H(C/q.relative_to(S)) for q in S.rglob('*') if q.is_file() and q.name!='maru60.kicad_pcb')
(D/'qa/build.json').write_text(json.dumps({'source_sha256':H(S/'maru60.kicad_pcb'),'candidate_sha256':H(f),'changed_references':['C136'],'raw_reversal_exact':True,'all57_companions_exact':True,'old_form':o,'new_form':n},indent=2))
print(H(f))
