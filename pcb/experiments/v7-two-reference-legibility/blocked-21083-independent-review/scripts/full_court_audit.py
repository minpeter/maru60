from pathlib import Path
import json,hashlib
import native_ink as n
p=n.p;R=Path('/tmp/v7-two-label-independent-review');BP=Path('/tmp/v7-selected-label-screen-7882/candidate/pcb/maru60.kicad_pcb');s=n.Scene(BP)
raw={p.F_SilkS:[],p.B_SilkS:[]}
for ref,fp in s.fps.items():
 for q in fp.GraphicalItems():
  if q.GetLayer()not in[p.F_CrtYd,p.B_CrtYd]:continue
  sl=p.F_SilkS if q.GetLayer()==p.F_CrtYd else p.B_SilkS;info=n.info(q,ref);info['stroke_width_nm']=q.GetWidth();info['shape_type']=q.GetShape();raw[sl].append((info,n.effective(q)))
def row(ref):
 f=s.fields[ref];shape=n.effective(f);sl=f.GetLayer();return {'reference':ref,'typography':n.typo(f),'normal_native_geometry':s.measure_ref(ref)['geometry'],'full_raw_stroked_courtyard_gap':n.gap(shape,raw[sl]),'raw_stroked_150um_pass':not n.hits(shape,raw[sl],150000),'raw_stroked_hits_at150um':n.hits(shape,raw[sl],150000)}
refs=['U18','L2','C100','R140','R160','R134','C124','R121','R125','U8'];before=[row(r)for r in refs]
for ref,xy in {'U18':(176700000,84250000),'L2':(174950000,77950000)}.items():s.fields[ref].SetPosition(p.VECTOR2I(*xy))
s.build();proposed=[row(r)for r in ['U18','L2']]
result={'source_trial_sha256':s.before,'status':'READ ONLY independent actual courtyard interpretation audit; trial remains unselected','criterion':'Require >=0.150 mm to actual stroked raw courtyard shapes AND filled cached courtyard interior. Do not assume uniform line width. Existing cached-only figures retained as separate measurements.','original_trial_rows':before,'proposed_readonly_pose_rows':proposed,'current_selected_eight_fields_proven_unchanged_from7882_by_raw_delta_review':True,'file_unchanged':n.SHA(BP)==s.before};(R/'qa/full-courtyard-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'before':[{'ref':r['reference'],'cache_nm':r['normal_native_geometry']['courtyard_gap']['lower_bound_nm'],'raw_gap':r['full_raw_stroked_courtyard_gap'],'rawpass':r['raw_stroked_150um_pass']}for r in before],'proposed':[{'ref':r['reference'],'raw_gap':r['full_raw_stroked_courtyard_gap'],'rawpass':r['raw_stroked_150um_pass'],'otherpass':all(v for k,v in r['normal_native_geometry'].items()if k.endswith('_target_pass')or k=='whole_ink_inside_board')}for r in proposed]},indent=2))
