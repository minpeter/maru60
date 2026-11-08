from pathlib import Path
import sys,hashlib,json,shutil,copy
import native_ink as n,sexp as sx
p=n.p;R=Path('/workspace/shared/maru60-resume');D=R/'continuation-c782/warnings';S=R/'combined-trial/pcb';C=D/'candidate/pcb';assert not C.exists();shutil.copytree(S,C);H=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();assert H(S/'maru60.kicad_pcb')=='56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9'
s=n.Scene(S/'maru60.kicad_pcb');intents={'U13':([89800000,45300000],0),'R135':([117400000,36400000],0),'R145':([117800000,38500000],90)};changes=[]
for ref,(xy,angle)in intents.items():
 f=s.fields[ref];old=n.typo(f);f.SetPosition(p.VECTOR2I(*xy));f.SetTextSize(p.VECTOR2I(800000,800000));f.SetTextThickness(100000);f.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));changes.append({'reference':ref,'before':old,'after':n.typo(f)})
s.build();measures=[s.measure_ref(ref)for ref in intents];assert all(all(v for k,v in row['geometry'].items()if k.endswith('_target_pass')or k=='whole_ink_inside_board')for row in measures),'Ink geometry check failed';p.SaveBoard(str(C/'maru60.kicad_pcb'),s.board)
a=sx.parse((S/'maru60.kicad_pcb').read_text());b=sx.parse((C/'maru60.kicad_pcb').read_text());rev=copy.deepcopy(b);af=sx.fields(a);rf=sx.fields(rev)
for ref in intents:rf[ref][:]=copy.deepcopy(af[ref])
assert rev==a,'Unintended raw non-reference change';assert all(H(f)==H(C/f.relative_to(S))for f in S.rglob('*')if f.is_file()and f.name!='maru60.kicad_pcb');out={'source_sha256':H(S/'maru60.kicad_pcb'),'candidate_sha256':H(C/'maru60.kicad_pcb'),'changes':changes,'native_ink':measures,'raw_reversal_exact':True,'all57_companions_exact':True,'all_electrical_and_filled_geometry_exact':True,'status':'UNSELECTED pending freshDRC/coldfill/independent rawcourtyard andvisualassociation checks'};(D/'qa/BUILD.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='native_ink'},indent=2))
