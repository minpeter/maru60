import os,json,math
from pathlib import Path
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-placement-config';os.environ['XDG_CONFIG_HOME']='/tmp/maru-placement-config'
import pcbnew as p
r=Path(__file__).parent;b=p.LoadBoard('/workspace/shared/maru60-placement-lab/frozen.kicad_pcb');tracks=list(b.GetTracks());out=[]
for f in b.GetFootprints():
 for q in f.Pads():
  if q.GetNetname()!='GND':continue
  pos=q.GetPosition();matches=[]
  for t in tracks:
   if isinstance(t,p.PCB_VIA) or t.GetNetname()!='GND' or not q.IsOnLayer(t.GetLayer()):continue
   for v in [t.GetStart(),t.GetEnd()]:
    if q.HitTest(v):matches.append({'endpoint_mm':[p.ToMM(v.x),p.ToMM(v.y)],'offset_mm':p.ToMM(math.hypot(v.x-pos.x,v.y-pos.y)),'layer':b.GetLayerName(t.GetLayer()),'track_uuid':t.m_Uuid.AsString()})
  if matches and not any(x['offset_mm']<.000001 for x in matches):out.append({'ref':f.GetReference(),'pin':q.GetNumber(),'pad_center_mm':[p.ToMM(pos.x),p.ToMM(pos.y)],'contacts':matches})
(r/'native-gnd-offcenter-contact-examples.json').write_text(json.dumps(out,indent=2));print('GND pads with candidate non-center endpoint contact but no center endpoint:',len(out));print(json.dumps(out[:3],indent=2))
