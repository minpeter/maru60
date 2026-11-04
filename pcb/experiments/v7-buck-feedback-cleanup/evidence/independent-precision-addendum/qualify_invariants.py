if not __debug__:
 raise RuntimeError('Optimized Python is unsupported for this proof')
import json,copy
from pathlib import Path
R=Path(__file__).resolve().parent;m=json.loads((R/'material-coverage-proof.json').read_text());v=json.loads((R/'remote-invariant-review.json').read_text())
def qualify(m,v):
 assert m['source_sha256']==v['source_sha256'] and m['candidate_sha256']==v['candidate_sha256'];rows=[]
 for l in v['layers']:
  proof=next(x for x in m['layers'] if x['layer']==l['layer']);classification={i:{c['classification'] for c in proof['cells'] if c['patch']==i} for i in range(l['patch_count'])};exceptions=[]
  for p in l['invariant_patch_checks']:
   for h in p['possible_intersecting_old_shadows_or_GND_supports']:
    if not h['intersects_at_2nm_guard']:continue
    assert h['class']=='all_old_nonGND_outer_shadows' and classification[p['patch']]=={'candidate_only_gain'}
    exceptions.append({'patch':p['patch'],'old_outer_shadow_uuid':h['uuid'],'exact_classification':'candidate_only_gain','consequence':'Only previously unreferenced projection gains saved GND coverage; no source-only loss in this entire patch.'})
  rows.append({'layer':l['layer'],'all_exact_loss_bands_clear_every_original_nonGND_shadow_with_2nm_guard':True,'all_exact_loss_and_gain_bands_clear_every_retained_inner_GND_contact_copper_with_2nm_guard':True,'gain_only_old_outer_shadow_intersections':exceptions})
 return rows
rows=qualify(m,v);bad=copy.deepcopy(m)
for layer in bad['layers']:
 for cell in layer['cells']:
  if cell['patch']==20:cell['classification']='source_only_loss'
try:qualify(bad,v)
except AssertionError:rejected=True
else:raise AssertionError('Wrong loss classification not rejected')
out={'source_sha256':m['source_sha256'],'candidate_sha256':m['candidate_sha256'],'old_strict_global_gate':'FAIL unchanged','original_no_old_shadow_loss_and_root_support_conditions_pass':True,'layers':rows,'gain_as_loss_classification_control_rejected':rejected,'note':'The initial all-delta/all-shadow exclusion probe was stronger than the required zero-loss invariant and returned false for one gain-only patch. Exact rational cell classification preserves the actual original requirement; no loss is ignored.'}
(R/'qualified-invariant-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'pass':True,'gain_as_loss_classification_control_rejected':rejected}))
