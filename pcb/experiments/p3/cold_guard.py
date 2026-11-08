import os
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-kicad-config'
import pcbnew as p,json,hashlib,shutil
from pathlib import Path
D=Path(__file__).parent;S=D/'candidate.kicad_pcb';C=D/'cold-repeat';C.mkdir(exist_ok=True);F=C/S.name;P=F.with_suffix('.kicad_pro');h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();sh=h(S);ph=h(S.with_suffix('.kicad_pro'));shutil.copyfile(S,F);shutil.copyfile(S.with_suffix('.kicad_pro'),P)
expected=json.load(open(D/'addition-ledger.json'))['expected_net_names'];uid=lambda q:q.m_Uuid.AsString();steps=[]
def check(stage):
 actual={uid(q):q.GetNetname()for q in list(b.GetTracks())+list(b.Zones())+[q for f in b.GetFootprints()for q in f.Pads()]};r={'stage':stage,'objects':len(actual),'missing':sorted(set(expected)-set(actual)),'extra':sorted(set(actual)-set(expected)),'mismatches':[{'uuid':u,'expected':expected[u],'actual':n}for u,n in actual.items()if u in expected and n!=expected[u]],'project_unchanged':h(P)==ph,'source_unchanged':h(S)==sh};steps.append(r);assert not(r['missing']or r['extra']or r['mismatches'])and r['project_unchanged']and r['source_unchanged'],stage
b=p.LoadBoard(str(F));check('cold_LoadBoard');b.BuildConnectivity();check('cold_BuildConnectivity');p.ZONE_FILLER(b).Fill(b.Zones());check('cold_refill');assert p.SaveBoard(str(F),b);check('cold_SaveBoard');b=p.LoadBoard(str(F));check('cold_reload');b.BuildConnectivity();check('cold_rebuild');j={'source_sha256':sh,'cold_sha256':h(F),'byte_identical':sh==h(F),'project_sha256':ph,'steps':steps};(D/'cold-repeat-guard.json').write_text(json.dumps(j,indent=2));print(j);assert j['byte_identical']
