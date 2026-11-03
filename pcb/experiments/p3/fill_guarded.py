import os
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-kicad-config'
import pcbnew as p,json,hashlib
from pathlib import Path
D=Path(__file__).parent;F=D/'candidate.kicad_pcb';P=F.with_suffix('.kicad_pro');h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();j=json.load(open(D/'addition-ledger.json'));expected=j['expected_net_names'];steps=[];ph=h(P);uid=lambda q:q.m_Uuid.AsString()
def check(stage):
 actual={uid(q):q.GetNetname()for q in list(b.GetTracks())+list(b.Zones())+[q for f in b.GetFootprints()for q in f.Pads()]};r={'stage':stage,'objects':len(actual),'missing':sorted(set(expected)-set(actual)),'extra':sorted(set(actual)-set(expected)),'mismatches':[{'uuid':u,'expected':expected[u],'actual':n}for u,n in actual.items()if u in expected and n!=expected[u]],'project_unchanged':h(P)==ph};steps.append(r);(D/'net-name-guard.json').write_text(json.dumps({'raw_sha':j['raw_sha256'],'current_sha':h(F),'project_sha':ph,'steps':steps},indent=2));assert not(r['missing']or r['extra']or r['mismatches'])and r['project_unchanged'],stage
b=p.LoadBoard(str(F));check('first_load');b.BuildConnectivity();check('build');p.ZONE_FILLER(b).Fill(b.Zones());check('fill');assert p.SaveBoard(str(F),b);check('save');b=p.LoadBoard(str(F));check('reload');b.BuildConnectivity();check('rebuild');print(h(F))
