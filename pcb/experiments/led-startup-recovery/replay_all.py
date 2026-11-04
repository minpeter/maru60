#!/usr/bin/env python3
"""Replay packaged tests in scratch without modifying reviewed source or fixtures."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Assertions required; do not use optimized Python')
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();O=a.output.resolve()
assert not O.exists() and not O.is_relative_to(P),'Fresh output outside packet required'
O.mkdir(parents=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(root):return {str(f.relative_to(root)):sha(f) for f in sorted(root.rglob('*')) if f.is_file()}
before=hashes(P); env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
def run(name,cmd):
 r=subprocess.run(list(map(str,cmd)),cwd=O,capture_output=True,text=True,env=env)
 (O/(name+'.log')).write_text('$ '+' '.join(map(str,cmd))+'\n'+r.stdout+r.stderr)
 assert r.returncode==0,(name,r.stdout,r.stderr)
 print(name+': PASS',flush=True)
run('source-verify',[sys.executable,P/'candidate/verify_sources.py'])
run('host',[sys.executable,P/'candidate/run_host_checks.py','--output',O/'host'])
X=O/'reviewer-layout';S=X/'v7-firmware-recovery-20261104/candidate';I=X/'led-recovery-independent-20261104/independent'
shutil.copytree(P/'candidate',S)
shutil.copytree(P/'evidence/independent-review/independent',I,ignore=shutil.ignore_patterns('results','__pycache__'))
run('independent',[sys.executable,I/'run.py'])
N=P/'evidence/static-v7/current-v7-netlist.xml'
run('static-v7',[sys.executable,P/'evidence/static-v7/check.py','--netlist',N,'--expected-sha256','1b46d899330d9aba0b86380ab08b7a60d309fa7a1c8962b9e6fab3ad556f2d29','--source',P/'candidate/firmware/qmk/keyboards/maru60/rp2350','--matrix-script',P/'candidate/firmware/tests/matrix_simultaneous_model.py','--output',O/'static-v7.json'])
assert before==hashes(P),'Packet changed during replay'
host=json.loads((O/'host/results.json').read_text());guard=json.loads((O/'host/guard/results.json').read_text());ind=json.loads((I/'results/results.json').read_text());static=json.loads((O/'static-v7.json').read_text())
assert host['pass'] and ind['pass'] and static['pass']
assert host['source_hashes']==ind['source_hashes']==static['source_hashes']
report={'pass':True,'candidate_manifest_sha256':sha(P/'candidate/source-manifest.json'),'packet_unchanged':True,'host_results_sha256':sha(O/'host/results.json'),'guard_results_sha256':sha(O/'host/guard/results.json'),'independent_results_sha256':sha(I/'results/results.json'),'static_results_sha256':sha(O/'static-v7.json'),'startup_executions':guard['startup_executions'],'transport_executions':guard['transport_executions'],'independent_executions':ind['independent_executions'],'invalid_contract_rejections':guard['rejected_contracts'],'killed_mutations':guard['killed_mutations'],'expected_nonatomic_limit_controls':guard['expected_nonatomic_limit_controls'],'static_gpio_bindings':static['binding_count'],'qualification_default':host['qualification_default'],'full_arm_build':False,'hardware_qualification':False}
(O/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
