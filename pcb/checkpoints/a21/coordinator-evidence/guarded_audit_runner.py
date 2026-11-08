import os,json,hashlib,sys,runpy
from pathlib import Path
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-kicad-config'
import pcbnew as p
D=Path(__file__).parent;expected=json.load(open(D/'source-contract.json'))['project_sha256'];sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();events=[];load=p.LoadBoard

def guarded_load(name,*a,**kw):
 pro=Path(name).with_suffix('.kicad_pro');before=sha(pro);assert before==expected
 board=load(name,*a,**kw);after=sha(pro);assert after==expected;events.append({'board':str(name),'before':before,'after':after});return board
p.LoadBoard=guarded_load
for name in sys.argv[1:]:
 before=len(events);runpy.run_path(str(D/name),run_name='__main__');assert all(sha(D/(s+'.kicad_pro'))==expected for s in ['source','candidate','cold']);(D/(name.removesuffix('.py')+'-project-load-guards.json')).write_text(json.dumps(events[before:],indent=2))
