from pathlib import Path
import json,hashlib
import native_ink as n
p=n.p;R=Path('/tmp/v7-two-label-independent-review');BP=Path('/tmp/v7-selected-label-screen-7882/candidate/pcb/maru60.kicad_pcb');s=n.Scene(BP);out=[]
for ref in ['U18','L2']:
 f=s.fields[ref];q=n.effective(f);fp=s.fps[ref];raw=[]
 for x in fp.GraphicalItems():
  if x.GetLayer()!=p.B_CrtYd:continue
  if x.GetShape()==p.SHAPE_T_RECT:shape=n.filled([n.XY(v)for v in x.GetRectCorners()]);typ='filled native rectangle centerline boundary'
  else:shape=n.effective(x);typ='native drawn boundary'
  raw.append((n.info(x,ref),shape))
 g=n.gap(q,raw);out.append({'ref':ref,'native_typography':n.typo(f),'cached_geometry':s.measure_ref(ref),'raw_courtyard_shape_types':[x.GetShape()for x in fp.GraphicalItems()if x.GetLayer()==p.B_CrtYd],'full_raw_courtyard_gap':g,'full_raw_courtyard_150um_clear':not n.hits(q,raw,150000)})
r={'actual_sha256':s.before,'rows':out,'file_unchanged':n.SHA(BP)==s.before};(R/'qa/native-probe.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
