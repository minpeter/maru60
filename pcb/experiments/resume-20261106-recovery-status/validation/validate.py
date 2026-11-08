import pathlib,json,hashlib,subprocess,shutil
B=pathlib.Path('/workspace/scratch/edd9a5be63e7/maru60-push-recovery'); S=B/'study'; R=B/'repo'; O=B/'study-validation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((S/'MANIFEST.json').read_text())['files']; actual={str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}-{'MANIFEST.json'}
errors=[]
for n,v in m.items():
 p=S/n
 if not p.is_file() or sha(p)!=v['sha256'] or p.stat().st_size!=v['bytes']:errors.append(n)
result={'manifest':{'entries':len(m),'actual_files':len(actual),'missing':sorted(set(m)-actual),'extra':sorted(actual-set(m)),'hash_or_size_errors':errors},'repo_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'comparisons':{}}
for label,src,dst in [('cad','current-source-be51692/pcb','pcb/experiments/resume-20261106-usb-pendant-prototype/pcb'),('firmware','current-source-be51692/firmware-rp2350','pcb/firmware/qmk/keyboards/maru60/rp2350')]:
 a={str(p.relative_to(S/src)):p for p in (S/src).rglob('*') if p.is_file()}; b={str(p.relative_to(R/dst)):p for p in (R/dst).rglob('*') if p.is_file()}
 bad=[n for n in a.keys()&b.keys() if sha(a[n])!=sha(b[n])]
 result['comparisons'][label]={'study_count':len(a),'repo_count':len(b),'missing_in_repo':sorted(a.keys()-b.keys()),'extra_in_repo':sorted(b.keys()-a.keys()),'different':bad}
shutil.copytree(S/'power-conditions',O/'power-conditions',dirs_exist_ok=True)
result['tests']={}
for name in ['replay.py','current_limits.py']:
 p=subprocess.run(['python3',str(O/'power-conditions'/name)],capture_output=True,text=True)
 (O/(name+'.log')).write_text(p.stdout+p.stderr); result['tests'][name]={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
result['current_limits_reproduced_exact']=sha(O/'power-conditions/CURRENT_LIMITS.json')==sha(S/'power-conditions/CURRENT_LIMITS.json')
result['u18']={'status':'NOT RUN: nonportable original paths, KiCad pcbnew and vendor PDF dependencies; geometry snapshot is manifest-verified only','pcbnew_available':subprocess.run(['python3','-c','import importlib.util; print(importlib.util.find_spec("pcbnew"))'],capture_output=True,text=True).stdout.strip(),'original_source_exists':pathlib.Path('/workspace/shared/maru60-resume/selected-repo').exists(),'vendor_pdf_exists':pathlib.Path('/workspace/shared/maru60-resume/continuation-fa96a7c/power-audit/tps62932.pdf').exists()}
result['source_unchanged_after_tests']=all((S/n).is_file() and sha(S/n)==v['sha256'] for n,v in m.items())
(O/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
