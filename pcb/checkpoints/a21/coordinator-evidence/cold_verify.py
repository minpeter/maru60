import os,json,hashlib,shutil
from pathlib import Path
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-kicad-config'
import pcbnew as p
D=Path(__file__).parent;f=D/'cold.kicad_pcb';q=D/'cold.kicad_pro';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();h=sha(D/'candidate.kicad_pcb');e=json.load(open(D/'source-contract.json'))['project_sha256'];steps={};shutil.copyfile(D/'candidate.kicad_pcb',f)
def guard(n):steps[n]=sha(q);assert steps[n]==e
assert sha(D/'candidate.kicad_pro')==e;guard('before_load');b=p.LoadBoard(str(f));guard('after_load');p.ZONE_FILLER(b).Fill(b.Zones());guard('after_refill');p.SaveBoard(str(f),b);guard('after_same_path_save');assert sha(f)==h;assert sha(D/'candidate.kicad_pro')==e
(D/'cold-proof.json').write_text(json.dumps({'candidate_sha256':h,'cold_sha256':sha(f),'project_hash_guards':steps,'byte_identical':True},indent=2))
