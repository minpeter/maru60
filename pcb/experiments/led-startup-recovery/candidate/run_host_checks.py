#!/usr/bin/env python3
"""Fresh recovery validation; output outside candidate, no source generation in place."""
import sys
if not __debug__:raise SystemExit('Assertions required; do not use optimized Python')
sys.dont_write_bytecode=True
import argparse,ast,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
C=Path(__file__).resolve().parent;F=C/'firmware';Q=F/'qmk/keyboards/maru60/rp2350'
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline',type=Path,default=C.parent/'baseline-extracted/accepted-main/pcb/firmware/qmk/keyboards/maru60/rp2350');a=p.parse_args();O=a.output.resolve();B=a.baseline.resolve()
assert not O.is_relative_to(C) and not O.is_relative_to(B) and not O.exists(),'Output must be fresh and outside source'
O.mkdir(parents=True);(O/'tmp').mkdir();env=dict(os.environ,TMPDIR=str(O/'tmp'),PYTHONDONTWRITEBYTECODE='1');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
before=hashes(C);base_before=hashes(B);rows=[]
def run(name,cmd):
 r=subprocess.run(list(map(str,cmd)),cwd=O,capture_output=True,text=True,input='',env=env);(O/(name+'.log')).write_text('$ '+' '.join(map(str,cmd))+'\n'+r.stdout+r.stderr);assert r.returncode==0,(name,r.stdout,r.stderr);rows.append({'test':name,'status':'PASS'});print(name+': PASS',flush=True);return r.stdout
status=json.loads((C/'SOURCE-STATUS.json').read_text());known=json.loads((C.parent/'known-source-hashes.json').read_text());assert hashes(B)==known['baseline'];assert hashes(Q)==status['source_hashes'];assert set(hashes(Q))==set(known['baseline'])
run('source-verification-before',[sys.executable,C/'verify_sources.py'])
run('guard',[sys.executable,C/'tests/startup_guard/run.py','--source',Q,'--baseline',B,'--output',O/'guard'])
run('led-contract',[sys.executable,F/'tests/led_contract_test.py'])
cc=os.environ.get('CC','cc')
for name,args in [('power-policy',[F/'tests/power_policy_test.c']),('option-wkl',['-DMARU60_LAYOUT_HHKB=0','-I'+str(F/'tests/mock'),F/'tests/option_test.c',Q/'maru_layout.c']),('option-hhkb',['-DMARU60_LAYOUT_HHKB=1','-I'+str(F/'tests/mock'),F/'tests/option_test.c',Q/'maru_layout.c']),('suspend-mask',['-DMCU_RP','-DMARU60_SUSPEND_EXPERIMENT=1','-I'+str(F/'tests/suspend_mock'),F/'tests/suspend_mask_test.c',Q/'maru_suspend.c'])]:
 exe=O/(name+'-binary');run(name+'-compile',[cc,'-std=c11','-Wall','-Wextra','-Werror',*args,'-o',exe]);run(name,[exe])
with tempfile.TemporaryDirectory(dir=O/'tmp') as d:
 D=Path(d)/'pcb';shutil.copytree(C,D);run('via-regeneration',[sys.executable,D/'firmware/via/generate.py'])
 for variant in ['wkl','hhkb']:
  n=f'maru60-{variant}-64.json';assert (D/'firmware/via'/n).read_bytes()==(F/'via'/n).read_bytes()
rows.append({'test':'via-byte-reproducibility','status':'PASS'})
script=F/'tests/matrix_simultaneous_model.py';tree=ast.parse(script.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef)) or (isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in ['P','reports'] for t in n.targets)):nodes.append(n)
ns={'__file__':str(script)};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(script),'exec'),ns);ns['verify'](F/'history/fixtures/maru60.xml',Q/'keyboard.json');(O/'historical-matrix.json').write_text(json.dumps({'scope':'Recovered historical-main fixture only; not selected V7 electrical qualification','results':ns['reports']},indent=2)+'\n');rows.append({'test':'historical-main-matrix','status':'PASS'})
for n in ['via-eeprom-schema-v1','report-state-sync-v1']:
 m=json.loads((F/'qmk/patches'/f'{n}.json').read_text());assert sha(F/'qmk/patches'/f'{n}.patch')==m['patch_sha256']
rows.append({'test':'qmk-patch-hashes','status':'PASS'})
cpp=run('default-preprocessor',[cc,'-dM','-E','-x','c','-I'+str(C/'tests/startup_guard/mock'),'-I'+str(Q),'-include',Q/'config.h','-']);assert '#define MARU60_LED_POWER_QUALIFIED 0' in cpp;assert '#define MARU60_LED_POWER_SETTLE_MS ' not in cpp;assert '#define MARU60_LED_POWER_SETTLE_REPORT ' not in cpp
run('source-verification-after',[sys.executable,C/'verify_sources.py'])
assert hashes(C)==before and hashes(B)==base_before
report={'pass':True,'status':'NEW recovery source and fresh tests; NOT exact historical working packet','source_hashes':hashes(Q),'baseline_hashes':base_before,'all_sources_unchanged':True,'historical_baseline_files_exact':22,'historical_fixed_files_exact':sum(hashes(Q)[n]==known['active'][n] for n in hashes(Q)),'qualification_default':0,'tests':rows,'guard_report_sha256':sha(O/'guard/results.json'),'not_run':['Full pinned QMK/ARM WKL and HHKB builds; prerequisites unavailable','Original lost 362-file integration verifier and old startup/independent fixtures','Official VIA app/reader validation','Hardware, USB host, waveform, rail timing/current/inrush/suspend acceptance']};(O/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
