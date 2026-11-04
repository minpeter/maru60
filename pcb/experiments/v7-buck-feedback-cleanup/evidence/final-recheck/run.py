from pathlib import Path
import os,shutil,subprocess,json,hashlib,time
D=Path(__file__).parent;T=Path('/tmp/v7-buck-deadarm-trial-2c7e');Q=D/'qa';Q.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,source in [('source',T/'source/pcb'),('candidate',T/'filled/pcb')]:
 shutil.copytree(source,D/name/'pcb',dirs_exist_ok=True)
e=os.environ.copy()
for k in ['CONFIG','CACHE','DATA','STATE','RUNTIME']:
 p=D/'runtime'/k.lower();p.mkdir(parents=True,exist_ok=True);e['XDG_'+k+'_HOME']=str(p)
e['KICAD9_FOOTPRINT_DIR']='/usr/share/kicad/footprints';e['KICAD9_SYMBOL_DIR']='/usr/share/kicad/symbols'
records=[]
def run(cmd,name):
 t=time.monotonic()
 with (Q/(name+'.log')).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=e)
 records.append(dict(command=cmd,exit_code=r.returncode,seconds=time.monotonic()-t));(Q/'commands.json').write_text(json.dumps(records,indent=2));assert r.returncode==0;print(name,'done',flush=True)
for name in ['source','candidate']:
 b=D/name/'pcb/maru60.kicad_pcb';before=sha(b)
 run(['/usr/bin/python3',str(T/'tools/export_native_physical_graph.py'),str(b),str(Q/(name+'-physical-graph.json'))],name+'-graph')
 run(['kicad-cli','pcb','drc','--schematic-parity','--format','json','--output',str(Q/(name+'-drc.json')),str(b)],name+'-drc')
 assert sha(b)==before
run(['kicad-cli','sch','erc','--format','json','--output',str(Q/'candidate-erc.json'),str(D/'candidate/pcb/maru60.kicad_sch')],'candidate-erc')
print('ALL DONE',flush=True)
