import os,subprocess,json,concurrent.futures
from pathlib import Path
D=Path(__file__).parent;S=Path('/workspace/shared/maru-a4l-P3-S1-reconstruction-0236/handoff-P3-S1-netcorrect-0303');T=Path('/workspace/shared/maru60-kicad-linux/pcb/tools/studies');env=os.environ.copy();env.update({'KICAD_CONFIG_HOME':'/tmp/maru-kicad-config','XDG_CONFIG_HOME':'/tmp/maru-kicad-config','XDG_CACHE_HOME':'/tmp/maru-kicad-cache','XDG_DATA_HOME':'/tmp/maru-kicad-data','KICAD9_SYMBOL_DIR':'/usr/share/kicad/symbols','KICAD9_FOOTPRINT_DIR':'/usr/share/kicad/footprints'});(D/'witnesses').mkdir(exist_ok=True)
jobs=[('native-drc',['kicad-cli','pcb','drc','--severity-all','--all-track-errors','--schematic-parity','--format','json','--output',str(D/'native-drc.json'),str(D/'candidate.kicad_pcb')]),('native-erc',['kicad-cli','sch','erc','--severity-all','--format','json','--output',str(D/'native-erc.json'),str(D/'candidate.kicad_sch')])]
for f in sorted((S/'witnesses').glob('*.json')):
 j=json.load(open(f));cmd=['/usr/bin/python3',str(T/('experiment_a4l_ground_witness.py'if f.stem=='GND'else'experiment_a_power_witness.py')),str(D/'candidate.kicad_pcb'),str(D/'witnesses'/f.name)]
 if f.stem!='GND':cmd +=[j['net'],*j['root']]
 jobs.append(('witnesses/'+f.stem,cmd))
def run(job):
 name,cmd=job
 with open(D/(name+'.log'),'w')as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,cwd=D)
 return {'name':name,'returncode':r.returncode,'command':cmd}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:rows=list(ex.map(run,jobs))
(D/'gate-commands.json').write_text(json.dumps(rows,indent=2));print(rows)
