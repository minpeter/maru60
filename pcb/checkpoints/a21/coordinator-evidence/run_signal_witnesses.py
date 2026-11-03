from pathlib import Path
import json,hashlib,subprocess,os
D=Path(__file__).parent;O=D/'signal-source-gates';O.mkdir(exist_ok=False);B=D/'candidate.kicad_pcb';C=Path('/workspace/shared/maru60-kicad-linux/pcb/tools/studies/experiment_a_power_witness.py');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();inputs=[B,B.with_suffix('.kicad_pro'),C];base={str(p):sha(p)for p in inputs};rows=[];env=os.environ.copy();env['KICAD_CONFIG_HOME']='/tmp/maru-kicad-config'
for name,net,ref,pin in [('XIN','XIN','U1','21'),('XOUT','XOUT','U1','22'),('XTAL','XTAL_OUT','R108','1'),('UNDERGLOW','UNDERGLOW','U1','33'),('FAULT','LED_FAULT_N','U7','4'),('ENABLE','LED_ENABLE','U1','34'),('COL1','COL1','U1','9')]:
 assert {str(p):sha(p)for p in inputs}==base
 with (O/(name+'.log')).open('w')as log:r=subprocess.run(['/usr/bin/python3',str(C),str(B),str(O/(name+'.json')),net,ref,pin],stdout=log,stderr=subprocess.STDOUT,env=env)
 assert r.returncode==0 and {str(p):sha(p)for p in inputs}==base
 j=json.load(open(O/(name+'.json')));assert not j['unreached_components'];rows.append({'name':name,'source_pad':[ref,pin],'unreached_components':0,'report_sha256':sha(O/(name+'.json'))})
(O/'BOUND-SIGNAL-RESULT.json').write_text(json.dumps({'status':'COMPLETED','bound_inputs':base,'results':rows},indent=2));print('seven source signal witnesses PASS')
