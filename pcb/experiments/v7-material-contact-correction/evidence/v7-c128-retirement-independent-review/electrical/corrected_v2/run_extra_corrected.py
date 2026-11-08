from pathlib import Path
import subprocess,os,json,time,hashlib
D=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
boards=[('j3_b5c',Path('/tmp/v7-j3-unselected-closure-2c7e/filled/pcb/maru60.kicad_pcb')),('c124_ec487',Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-c124-short-local-review/construction/isolated-v4-label-carry/pcb/maru60.kicad_pcb'))];records=[]
for label,B in boards:
 env=os.environ.copy()
 for k in ['CONFIG','CACHE','DATA','STATE','RUNTIME']:
  p=D/label/k.lower();p.mkdir(parents=True,exist_ok=True);env['XDG_'+k+'_HOME']=str(p)
 out=D/label/'physical-graph.json';log=D/label/'export.log';cmd=['/usr/bin/python3',str(D/'export_material_graph.py'),str(B),str(out)];before=sha(B);start=time.monotonic()
 with log.open('w')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 record=dict(label=label,command=cmd,exit_code=r.returncode,seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after=sha(B),output_sha256=sha(out)if out.exists()else None,log_sha256=sha(log),checker_sha256=sha(D/'export_material_graph.py'));records.append(record);(D/'extra-commands.json').write_text(json.dumps(records,indent=2));assert r.returncode==0 and record['input_sha256_after']==before;print(label,'DONE',flush=True)
