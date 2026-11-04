from pathlib import Path
import os,json,hashlib
D=Path(__file__).parent
for k in ['CONFIG','CACHE','DATA']:os.environ['XDG_'+k+'_HOME']=str(D/k.lower())
import pcbnew as p
B=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-buck-feedback-cleanup/candidate/pcb/maru60.kicad_pcb');before=hashlib.sha256(B.read_bytes()).hexdigest();assert before=='aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f';b=p.LoadBoard(str(B));rows=[]
for f in b.GetFootprints():
 for q in f.Pads():
  if q.GetAttribute()!=p.PAD_ATTRIB_PTH:continue
  rows.append(dict(uuid=q.m_Uuid.AsString(),ref=f.GetReference(),pad=q.GetNumber(),shape=q.GetShape(),at=[q.GetPosition().x,q.GetPosition().y],offset=[q.GetOffset().x,q.GetOffset().y],size=[q.GetSize().x,q.GetSize().y],drill=[q.GetDrillSize().x,q.GetDrillSize().y],angle=q.GetOrientationDegrees(),hole_shape=q.GetDrillShape(),radius=q.GetRoundRectCornerRadius()))
print(json.dumps(rows,indent=2));(D/'PTH_INVENTORY.json').write_text(json.dumps(rows,indent=2))
