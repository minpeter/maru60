import json,sys
from pathlib import Path
r=Path(sys.argv[1]);a=json.load(open('/workspace/shared/maru60-resume/selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype/qa/drc.json'));b=json.load(open(r/'qa/drc.json'));sort=lambda q:sorted(json.dumps(x,sort_keys=True)for x in q);o=dict(identical_39_warnings=sort(a['violations'])==sort(b['violations']),opens=len(b['unconnected_items']),parity=len(b['schematic_parity']));o['pass']=o['identical_39_warnings']and o['opens']==8 and o['parity']==0;(r/'qa/NATIVE_GATE.json').write_text(json.dumps(o,indent=2));print(o);assert o['pass']
