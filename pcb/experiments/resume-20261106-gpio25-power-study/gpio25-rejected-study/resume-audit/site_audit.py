import sys,json
from pathlib import Path
sys.path.insert(0,'/workspace/shared/maru60-resume/continuation-be51692/gpio25-transition/scripts')
from screen import *
r=ROOT;scope=json.loads((r/'qa/FROZEN_STUDY_NATIVE.json').read_text());inv=json.loads((r/'qa/SITE_INVENTORY.json').read_text());out=[]
items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]
for group,points in [('J3',scope['sites_J3']),('bridge',scope['sites_bridge'])]:
 for a in points:
  copper=p.SHAPE_CIRCLE(V(*a),250000);drill=p.SHAPE_CIRCLE(V(*a),125000);rows=[];holes=[]
  for q in items:
   for l in L:
    if not q.IsOnLayer(l):continue
    shape=p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l)
    gap=copper.GetClearance(shape)
    if gap<300000:rows.append(dict(uuid=U(q),net=q.GetNetname(),layer=b.GetLayerName(l),copper_gap_nm=gap,ordinary_block=gap<150000 and q.GetNetname()!='EXT_GPIO25',screen_conservative_block=gap<(150000 if q.GetNetname() in['','GND']else 205000)))
   if isinstance(q,(p.PCB_VIA,p.PAD))and q.HasHole():
    h=q.GetEffectiveHoleShape();gap=drill.GetClearance(h)
    if gap<500000:holes.append(dict(uuid=U(q),net=q.GetNetname(),hole_to_hole_gap_nm=gap,via_copper_to_hole_gap_nm=copper.GetClearance(h)))
  old=next(v for v in inv[group]if v['point']==a)
  out.append(dict(group=group,point=a,inventory_blockers=old['blockers'],nearby_all_layer_copper=rows,nearby_all_drills=holes,ordinary_clear=not any(x['ordinary_block']for x in rows),screen_viaok=viaok('EXT_GPIO25',a)))
(r/'resume-audit/SITE_RECHECK.json').write_text(json.dumps(out,indent=2));print([(x['point'],x['ordinary_clear'],x['screen_viaok'],x['nearby_all_drills'])for x in out])
