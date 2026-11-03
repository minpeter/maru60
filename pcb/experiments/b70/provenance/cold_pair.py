from pathlib import Path
import os,json,hashlib,shutil
for k in ['KICAD_CONFIG_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME']:os.environ[k]='/tmp/maru-b2l-native'
import pcbnew as p
D=Path(__file__).parent;f=D/'cold.kicad_pcb';q=D/'cold.kicad_pro';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();import sys
base=sys.argv[1];dest=sys.argv[2];f=D/(dest+'.kicad_pcb');q=D/(dest+'.kicad_pro');h=sha(D/(base+'.kicad_pcb'));e=sha(D/(base+'.kicad_pro'));steps={}
for ext in ['.kicad_pcb','.kicad_pro','.kicad_sch']:shutil.copyfile(D/(base+ext),D/(dest+ext))
def guard(n):steps[n]=sha(q);assert steps[n]==e
b=None;guard('before_LoadBoard');b=p.LoadBoard(str(f));guard('after_LoadBoard');b.BuildConnectivity();guard('after_BuildConnectivity');p.ZONE_FILLER(b).Fill(b.Zones());guard('after_refill');p.SaveBoard(str(f),b);guard('after_same_path_SaveBoard');assert sha(D/(base+'.kicad_pcb'))==h;assert sha(D/(base+'.kicad_pro'))==e
r={'candidate_sha256':h,'cold_sha256':sha(f),'project_sha256':e,'project_hash_guards':steps,'byte_identical':sha(f)==h,'scope':'Independent fresh process, matching inherited B75 project preexists before LoadBoard, same-path native refill/save. Does not prove powered behavior.'};(D/(dest+'-proof.json')).write_text(json.dumps(r,indent=2));print(r)
