#!/usr/bin/env python3
"""Replay diagnostic wrappers. Does not download/install software or edit vendor models."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--vendor-root',required=True,type=Path);p.add_argument('--code-model-dir',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--full',action='store_true',help='Also rerun the known-unvalidated U7 and buck diagnostics (several minutes).');a=p.parse_args();root=Path(__file__).resolve().parent;out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
identity=json.loads((root/'inputs/source-runtime-identity.json').read_text());paths={}
for model in identity['vendor']:
 suffix=model['library'].split('/vendor/',1)[1];source=a.vendor_root.resolve()/suffix
 if sha(source)!=model['library_sha256']:raise SystemExit(f'Original vendor model hash mismatch: {source}')
 paths[model['library']]=str(source)
runtime=Path(identity['runtime']['path'])
if sha(runtime)!=identity['runtime']['sha256']:raise SystemExit('Runtime differs from recorded libngspice; this replay requires the recorded runtime identity.')
install=json.loads((root/'installation.json').read_text())
for module in install['modules']:
 path=a.code_model_dir.resolve()/Path(module['path']).name
 if sha(path)!=module['sha256']:raise SystemExit(f'Code-model hash mismatch: {path}')
 module['path']=str(path)
(out/'installation.json').write_text(json.dumps(install,indent=2)+'\n');shutil.copy(root/'ngrun_xspice.py',out/'ngrun_xspice.py');(out/'netlists').mkdir()
for source in (root/'netlists').glob('*.cir'):
 content=source.read_text()
 for old,new in paths.items():content=content.replace(old,new)
 (out/'netlists'/source.name).write_text(content)
expected=json.loads((root/'netlists/buck-original-static-logic-expected.json').read_text())
cases=[('switch-control-psa','switch-control','psa',['v(out)'])]
for mode in ['ps','psa','ltpsa']:cases.append(('u7-original-xnor'+('' if mode=='ps' else '-'+mode),'u7-original-xnor',mode,['v(y00)','v(y01)','v(y10)','v(y11)']))
for mode in ['ps','psa']:
 cases.append((f'buck-original-static-logic-{mode}','buck-original-static-logic',mode,list(expected)))
 cases.append((f'reversed-limit-control-{mode}','reversed-limit-control',mode,['v(input)','v(reversed)','v(ordered)']))
if a.full:
 cases += [('u7-original-internal-probes','u7-portability','psa',['v(en)','v(out)','v(xu7.u1_n16726884)','v(xu7.u1_n16726205)','v(xu7.u1_enok)','v(xu7.powerok)']),('buck-original-portability','buck-portability','ps',['v(vin)','v(vout)','v(sw)','v(ss)','v(fb)','i(L2)']),('buck-diagnostic-24v','buck-diagnostic-24v','psa',['v(vin)','v(vout)','v(sw)','v(ss)','v(fb)','i(Lout)'])]
records=[]
for name,deck,mode,vectors in cases:
 dest=out/'runs'/name;env=dict(os.environ,NGSPICE_COMPAT=mode)
 command=[sys.executable,str(out/'ngrun_xspice.py'),str(out/'netlists'/(deck+'.cir')),str(dest),*vectors]
 try:
  run=subprocess.run(command,capture_output=True,text=True,env=env,timeout=240);rc=run.returncode;call=run.stdout+run.stderr
 except subprocess.TimeoutExpired as e:rc=124;call='Replay timed out at 240 s. Any partial output is NOT a completed result.\n'
 dest.mkdir(parents=True,exist_ok=True);(dest/'call.log').write_text(call);log=(dest/'ngspice.log').read_text() if (dest/'ngspice.log').exists() else ''
 rec={'case':name,'mode':mode,'returncode':rc,'fatal_lines':[s for s in log.splitlines() if any(x in s.lower() for x in ['simulation(s) aborted','timestep too small','circuit not parsed','mif-error'])]}
 if (dest/'waveform.txt').exists():
  lines=(dest/'waveform.txt').read_text().splitlines();rec['last']=[float(x) for x in lines[-1].split()];rec['rows']=len(lines)-1
 if name.startswith('u7-original-xnor'):rec['expected_xnor']=[1,0,0,1];rec['actual_xnor']=rec.get('last',[None])[1:]
 records.append(rec);(out/'replay-results.json').write_text(json.dumps(records,indent=2)+'\n');print(name,rc,rec.get('actual_xnor',''),flush=True)
print('Replay complete. A process exit of 0 or a waveform file is NOT semantic/hardware validation.')
