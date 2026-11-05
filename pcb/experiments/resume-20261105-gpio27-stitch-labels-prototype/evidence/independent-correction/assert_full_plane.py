from pathlib import Path
import json,hashlib
R=Path('/workspace/shared/maru60-resume/continuation-c782');O=R/'independent27fix2';d=json.loads((O/'full-plane-review.json').read_text());assert d['candidate_sha256']=='9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed';assert d['candidate_sha256']==hashlib.sha256((R/'combined27fix2/pcb/maru60.kicad_pcb').read_bytes()).hexdigest()
for row in d['planes']:
 assert row['outside_outlines']==0 and row['outside_new_and_moved_via_windows_mm2']==0
 assert row['old_components']==row['new_components']==1
 assert len(row['old_projection_changes'])==4
 assert all(x['declared_old_object_changed']for x in row['old_projection_changes'])
for field in ['new_track_reference','modified_net_reference']:
 assert all(x['outside_outlines']==0 and x['new_uncovered_outside_own_transition_windows_mm2']==0 for x in d[field]),field
assert len(d['modified_net_reference'])==137
out={'candidate_sha256':d['candidate_sha256'],'pass':True,'retained_affected_tracks':len(d['modified_net_reference']),'new_tracks':len(d['new_track_reference']),'all_new_and_affected_outside_window_areas_and_contours_zero':True,'no_undeclared_old_projection_loss':True,'plane_loss_mm2_each':[x['loss_mm2']for x in d['planes']],'plane_gain_mm2_each':[x['gain_mm2']for x in d['planes']]};(O/'full-plane-gates.json').write_text(json.dumps(out,indent=2));print(out)
