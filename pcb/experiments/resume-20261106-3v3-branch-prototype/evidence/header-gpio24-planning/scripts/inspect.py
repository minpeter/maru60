import pcbnew as p,json,hashlib
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/header-gpio24-joint')
S=Path('/workspace/shared/maru60-resume/continuation-c782/combined27fix2/pcb/maru60.kicad_pcb')
b=p.LoadBoard(str(S)); rows=[]
def xy(v):return [v.x/1e6,v.y/1e6]
for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]:
 bb=q.GetBoundingBox()
 if bb.GetRight()/1e6<87 or bb.GetX()/1e6>94 or bb.GetBottom()/1e6<39 or bb.GetY()/1e6>44:continue
 row={'uuid':q.m_Uuid.AsString(),'net':q.GetNetname(),'layers':[b.GetLayerName(l) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu] if q.IsOnLayer(l)],'type':q.GetClass()}
 if isinstance(q,p.PAD):row.update(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber(),at=xy(q.GetPosition()),size=xy(q.GetSize()))
 else:row.update(start=xy(q.GetStart()),end=xy(q.GetEnd()),width=q.GetWidth(p.F_Cu)/1e6 if isinstance(q,p.PCB_VIA) else q.GetWidth()/1e6)
 rows.append(row)
(R/'qa/local-geometry.json').write_text(json.dumps(rows,indent=2))
print('sha256',hashlib.sha256(S.read_bytes()).hexdigest())
for row in rows:
 if row['net'] in ['COL13','GPIO10','EXT_GPIO24'] or row.get('ref')=='U13':print(row)
