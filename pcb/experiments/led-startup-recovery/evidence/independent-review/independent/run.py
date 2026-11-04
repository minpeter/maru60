import json, subprocess, pathlib, hashlib
R=pathlib.Path(__file__).resolve().parent
S=R.parents[1]/'v7-firmware-recovery-20261104/candidate/firmware/qmk/keyboards/maru60/rp2350'
O=R/'results';O.mkdir(exist_ok=False)
hashfile=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
source_hashes={str(f.relative_to(S)):hashfile(f) for f in S.rglob('*') if f.is_file()}
cases=['normal','missing-key','missing-ug','cold-fault','settling-off','settling-suspend','active-suspend','active-fault','active-health','enable-loss','zone-cycle','shutdown']
rows=[]
for opt in ['-O0','-O2']:
 for ms in [1,7,2147483647]:
  exe=O/f'fixture{opt}-{ms}'
  command=['cc','-std=c11','-Wall','-Wextra','-Werror',opt,'-fsanitize=undefined','-fno-sanitize-recover=all','-DMARU60_LED_POWER_QUALIFIED=1',f'-DMARU60_LED_POWER_SETTLE_MS={ms}','-DMARU60_LED_POWER_SETTLE_REPORT="INDEPENDENT-HOST-ONLY"','-I'+str(R/'mock'),'-I'+str(S),str(R/'lifecycle_test.c'),str(S/'maru_rgb.c'),str(S/'maru60.c'),'-o',str(exe)]
  p=subprocess.run(command,capture_output=True,text=True);assert p.returncode==0,p.stderr
  (O/f'compile{opt}-{ms}.log').write_text(' '.join(command)+'\n'+p.stdout+p.stderr)
  for case in cases:
   p=subprocess.run([str(exe),case],capture_output=True,text=True)
   (O/f'{case}{opt}-{ms}.log').write_text(p.stdout+p.stderr)
   assert p.returncode==0,(case,opt,ms,p.stderr)
   rows.append({'case':case,'opt':opt,'synthetic_ms':ms,'result':p.stdout.strip()})
# Defines duration only for the fixture's diagnostics. Firmware qualification stays OFF.
command=['cc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=undefined','-fno-sanitize-recover=all','-DMARU60_LED_POWER_SETTLE_MS=7','-I'+str(R/'mock'),'-I'+str(S),str(R/'lifecycle_test.c'),str(S/'maru_rgb.c'),str(S/'maru60.c'),'-o',str(O/'default-off')]
p=subprocess.run(command,capture_output=True,text=True);assert p.returncode==0,p.stderr
p=subprocess.run([str(O/'default-off'),'normal'],capture_output=True,text=True);assert p.returncode==0,p.stderr
rows.append({'case':'default-off-real-keyboard-wrappers','result':p.stdout.strip()})
assert source_hashes=={str(f.relative_to(S)):hashfile(f) for f in S.rglob('*') if f.is_file()}
report={'pass':True,'source_unchanged':True,'source_hashes':source_hashes,'fixture_hashes':{str(f.relative_to(R)):hashfile(f) for f in R.rglob('*') if f.is_file() and not f.is_relative_to(O)},'independent_executions':len(rows),'limits':['Real maru_rgb.c and maru60.c only; fake GPIO, scheduling, transport, USB state and user hooks','No QMK build, ARM compilation, true USB suspend ordering, hardware or electrical qualification','All enabled durations are synthetic boundary-test values, not proposed production intervals'],'tests':rows}
(O/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(rows),'independent lifecycle/wrapper executions under UBSan')
