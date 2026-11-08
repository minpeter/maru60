from pathlib import Path
import json,hashlib,shutil,re
from sexpr_spans import children,replace_child
R=Path('/tmp/v7-support-endpoint-trial');SRC=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-c124-series-with-connector-ground/candidate/pcb');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert H(SRC/'maru60.kicad_pcb')=='7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401';sc=json.loads((R/'qa/serial-route-screen.json').read_text());assert all(not v for v in sc['failures'].values());assert not(R/'source').exists()
for stage in['source','prefill']:shutil.copytree(SRC,R/stage/'pcb')
s=(SRC/'maru60.kicad_pcb').read_text();records={re.search(r'\(uuid "([^"]+)"\)',t).group(1):(a,z,t)for a,z,t in children(s)if re.search(r'\(uuid "([^"]+)"\)',t)};ed=[]
for row in sc['plans']:
 a,z,t=records[row['uuid']];x,y=row['point'];new=replace_child(t,row['which'],f"({row['which']} {x:g} {y:g})");ed.append((a,z,new))
for a,z,n in sorted(ed,reverse=True):s=s[:a]+n+s[z:]
(R/'prefill/pcb/maru60.kicad_pcb').write_text(s);shutil.copytree(R/'prefill/pcb',R/'filled/pcb')
ct={'status':'UNSELECTED natural serial-leg correction, no added or deleted objects','source_sha256':H(SRC/'maru60.kicad_pcb'),'prefill_sha256':H(R/'prefill/pcb/maru60.kicad_pcb'),'read_only_screen_sha256':H(R/'qa/serial-route-screen.json'),'changed_main_tracks':sc['plans'],'support_tracks_unchanged':True,'all_footprints_pads_drills_rules_unchanged':True,'scope':'Three endpoint changes incorporate the retained support segments into genuine serial conductive paths. No duplicate, zero-length, fake-loop or type-changed objects. GND is not claimed exact native polygon copper equality.'};(R/'BUILD_CONTRACT.json').write_text(json.dumps(ct,indent=2)+'\n')
for stage in['source','prefill']:
 m={str(p.relative_to(R/stage/'pcb')):{'bytes':p.stat().st_size,'sha256':H(p)}for p in sorted((R/stage/'pcb').rglob('*'))if p.is_file()};assert len(m)==58;(R/(stage.upper()+'_TREE_MANIFEST.json')).write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps(ct,indent=2))
