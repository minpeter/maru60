import json
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-c782');O=R/'independent27';a=json.loads((O/'drc.json').read_text());b=json.loads((R/'combined27/qa/drc.json').read_text());g=json.loads((R/'combined27/qa/material-graph.json').read_text())
def canonical(d):
 out=[]
 for row in d['unconnected_items']:
  out.append(sorted([sorted(g['object_material_roots'][x['uuid']]) for x in row['items']]))
 return sorted(out)
x,y=canonical(a),canonical(b);assert x==y
out={'all_nine_material_open_pairs_exact':True,'fresh_warning_records_exact':a['violations']==b['violations'],'fresh_parity':len(a['schematic_parity']),'fresh_unconnected':len(a['unconnected_items']),'fresh_warnings':len(a['violations']),'canonical_open_pairs':x};(O/'drc-comparison.json').write_text(json.dumps(out,indent=2));print(out)
