import sys,os,json,copy,shutil,hashlib
from pathlib import Path
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));sys.dont_write_bytecode=True
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 d=W/'reproduce-runtime'/k.lower();d.mkdir(parents=True,exist_ok=True,mode=0o700);os.environ[k]=str(d)
os.environ['QT_QPA_PLATFORM']='offscreen'
import native_ink as n,sexp as sx
p=n.p;S=W/'source/pcb';D=W/'reproduced/pcb';assert not D.exists();shutil.copytree(S,D)
fm=lambda d:{str(f.relative_to(d)):n.SHA(f)for f in sorted(d.rglob('*'))if f.is_file()};before=fm(S);assert before['maru60.kicad_pcb']=='7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401'
s=n.Scene(S/'maru60.kicad_pcb');intents={'U18':([176750000,84250000],0),'L2':([174950000,78000000],0)};changes=[]
for r,(xy,a)in intents.items():
 f=s.fields[r];old=n.typo(f);f.SetPosition(p.VECTOR2I(*xy));f.SetTextSize(p.VECTOR2I(800000,800000));f.SetTextThickness(120000);f.SetTextAngle(p.EDA_ANGLE(a,p.DEGREES_T));changes.append({'reference':r,'before':old,'after':n.typo(f)})
s.build();measure=[s.measure_ref(r)for r in intents]
assert all(all(v for k,v in row['geometry'].items()if k.endswith('_target_pass')or k=='whole_ink_inside_board')for row in measure),'Full 2-label ink screen failed'
p.SaveBoard(str(D/'maru60.kicad_pcb'),s.board)
a=sx.parse((S/'maru60.kicad_pcb').read_text());b=sx.parse((D/'maru60.kicad_pcb').read_text());restored=copy.deepcopy(b);af=sx.fields(a);rf=sx.fields(restored);bf=sx.fields(b)
for r in intents:
 rf[r][:]=copy.deepcopy(af[r])
assert restored==a,'Unexpected non-reference raw source change'
cf=fm(D);assert set(cf)==set(before) and [x for x in cf if cf[x]!=before[x]]==['maru60.kicad_pcb'];assert fm(S)==before
out={'source_board_sha256':before['maru60.kicad_pcb'],'candidate_board_sha256':cf['maru60.kicad_pcb'],'source_files':before,'candidate_files':cf,'changes':changes,'native_ink':measure,'only_two_entire_reference_fields_differ':True,'all_electrical_objects_holes_zones_unchanged':True,'selected':False,'association_visual_review_pending':True,'fresh_drc_pending':True}
(W/'REPRODUCED_BUILD.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'candidate_sha':cf['maru60.kicad_pcb'],'all_source_electrical_raw_objects_identical':True,'native_ink_pass':True}))

assert cf['maru60.kicad_pcb']=='21083e9498512939d40d95eb6866850367939e590fcf949440b4d4642b46727b'
