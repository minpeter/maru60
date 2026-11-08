from pathlib import Path
import subprocess,json,hashlib
R=Path('/workspace/shared/maru60-resume');root=R/'continuation-be51692/gpio25-transition';out=root/'resume-runs';a=json.loads((R/'selected-repo/pcb/experiments/resume-20261106-usb-pendant-prototype/qa/drc.json').read_text());sort=lambda x:sorted(json.dumps(q,sort_keys=True)for q in x)
for name in ['j2-b2','j1-b1','j0-b1','j0-b2','j1-b0','j1-b2','j2-b0','j2-b1']:
 d=out/name; (d/'qa').mkdir(parents=True,exist_ok=True)
 if not (d/'qa/FROZEN_SCOPE.json').exists():(d/'qa/FROZEN_SCOPE.json').write_bytes((root/'variants'/name/'qa/FROZEN_SCOPE.json').read_bytes())
 def run(args,log):
  with (d/'qa'/log).open('x')as f:subprocess.run([str(R/'run-kicad.sh')]+args,stdout=f,stderr=subprocess.STDOUT,check=True)
 if not (d/'qa/BUILD.json').exists():run(['/usr/bin/python3',str(root/'scripts/build.py'),str(d)],'build.log')
 if not (d/'qa/drc.json').exists():run(['kicad-cli','pcb','drc','--format','json','--schematic-parity','-o',str(d/'qa/drc.json'),str(d/'candidate/pcb/maru60.kicad_pcb')],'drc.log')
 b=json.loads((d/'qa/drc.json').read_text());o={'opens':len(b['unconnected_items']),'violations':len(b['violations']),'identical_38_warnings':sort(a['violations'])==sort(b['violations']),'parity':len(b['schematic_parity'])};o['pass']=o['opens']==8 and o['identical_38_warnings']and o['parity']==0;(d/'qa/NATIVE_GATE.json').write_text(json.dumps(o,indent=2));print(name,o,flush=True)
 if o['pass']:
  for script in ['outside_loss_allholes.py','rational_loss_strict.py']:
   dest=d/script;dest.write_text((root/'resume-audit'/script).read_text().replace(str(root/'variants/j0-b0'),str(d)))
   run(['/usr/bin/python3',str(dest)],script+'.log')
  run(['/usr/bin/python3',str(out/'foreign_reference.py'),str(d)],'foreign-reference.log')
  print(name,'post-native done',flush=True)
