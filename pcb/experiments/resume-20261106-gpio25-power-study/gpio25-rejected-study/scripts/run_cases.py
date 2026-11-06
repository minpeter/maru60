from pathlib import Path
import subprocess,json
R=Path('/workspace/shared/maru60-resume');root=R/'continuation-be51692/gpio25-transition';src=R/'selected-repo/pcb/experiments/resume-20261106-usb-pendant-prototype/qa/drc.json';a=json.loads(src.read_text());sort=lambda x:sorted(json.dumps(q,sort_keys=True)for q in x)
for d in sorted((root/'variants').iterdir()):
 with (d/'qa/build.log').open('w')as f:subprocess.run([str(R/'run-kicad.sh'),'/usr/bin/python3',str(root/'scripts/build.py'),str(d)],stdout=f,stderr=subprocess.STDOUT,check=True)
 with (d/'qa/drc.log').open('w')as f:subprocess.run([str(R/'run-kicad.sh'),'kicad-cli','pcb','drc','--format','json','--schematic-parity','-o',str(d/'qa/drc.json'),str(d/'candidate/pcb/maru60.kicad_pcb')],stdout=f,stderr=subprocess.STDOUT,check=True)
 b=json.loads((d/'qa/drc.json').read_text());o={'opens':len(b['unconnected_items']),'violations':len(b['violations']),'identical_38_warnings':sort(a['violations'])==sort(b['violations']),'parity':len(b['schematic_parity'])};o['pass']=o['opens']==8 and o['identical_38_warnings']and o['parity']==0;(d/'qa/NATIVE_GATE.json').write_text(json.dumps(o,indent=2));print(d.name,o,flush=True)
