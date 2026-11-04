import os,json,subprocess,time,hashlib
from pathlib import Path
R=Path('/tmp/v7-connector-gnd-stitch-c770');env=dict(os.environ)
for k in ['CONFIG','CACHE','DATA','STATE']:env['XDG_'+k+'_HOME']=str(R/'xdg'/k.lower())
env['XDG_RUNTIME_DIR']=str(R/'xdg/runtime');env['QT_QPA_PLATFORM']='offscreen'
commands={'drc':['kicad-cli','pcb','drc','--format','json','--all-track-errors','--schematic-parity','--severity-all','--output',str(R/'qa/drc.json'),str(R/'filled/pcb/maru60.kicad_pcb')],'erc':['kicad-cli','sch','erc','--format','json','--severity-all','--output',str(R/'qa/erc.json'),str(R/'filled/pcb/maru60.kicad_sch')]}
for name,cmd in commands.items():
 t=time.monotonic();p=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(R/'qa'/f'{name}.log').write_text(p.stdout)
 r={'argv':cmd,'exit':p.returncode,'seconds':time.monotonic()-t,'xdg':{k:v for k,v in env.items() if k.startswith('XDG_')},'candidate_sha256':hashlib.sha256((R/'filled/pcb/maru60.kicad_pcb').read_bytes()).hexdigest()};(R/'qa'/f'{name}.execution.json').write_text(json.dumps(r,indent=2)+'\n');print(name,r['exit'],p.stdout[-1500:],flush=True);assert p.returncode==0
