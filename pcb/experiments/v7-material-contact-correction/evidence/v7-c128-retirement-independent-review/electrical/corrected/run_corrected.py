from pathlib import Path
import subprocess,os,json,time,hashlib
D=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
boards=[('aead',Path('/tmp/v7-c128-stub-retirement-aead/source/pcb/maru60.kicad_pcb')),('2c7',Path('/tmp/v7-buck-deadarm-final-recheck/source/pcb/maru60.kicad_pcb')),('cafa',Path('/tmp/v7-c128-stub-retirement-aead/filled/pcb/maru60.kicad_pcb'))];records=[]
for label,B in boards:
 env=os.environ.copy()
 for k in ['CONFIG','CACHE','DATA','STATE','RUNTIME']:
  p=D/label/k.lower();p.mkdir(parents=True,exist_ok=True);env['XDG_'+k+'_HOME']=str(p)
 out=D/label/'physical-graph.json';log=D/label/'export.log';cmd=['/usr/bin/python3',str(D/'export_native_physical_graph.py'),str(B),str(out)];before=sha(B);start=time.monotonic()
 with log.open('w')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 record=dict(label=label,command=cmd,exit_code=r.returncode,seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after=sha(B),output_sha256=sha(out)if out.exists()else None,log_sha256=sha(log),checker_sha256=sha(D/'export_native_physical_graph.py'));records.append(record);(D/'commands.json').write_text(json.dumps(records,indent=2));assert r.returncode==0 and record['input_sha256_after']==before;print(label,'DONE',flush=True)
