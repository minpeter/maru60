import sys,json,hashlib
sys.path.insert(0,'/workspace/shared/maru60-resume/mcu-routing/native-pylibs')
import pcbnew as p
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu-gpio3');S=Path('/workspace/shared/maru60-resume/continuation-c782/combined27fix2/pcb/maru60.kicad_pcb');b=p.LoadBoard(str(S));uid=lambda q:q.m_Uuid.AsString();xy=lambda a:[a.x/1e6,a.y/1e6]
def desc(q):
 d={'uuid':uid(q),'class':q.GetClass(),'net':q.GetNetname(),'layers':[b.GetLayerName(l) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu] if q.IsOnLayer(l)]}
 if isinstance(q,p.PAD):d.update(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber(),pos=xy(q.GetPosition()),size=xy(q.GetSize()))
 elif isinstance(q,p.PCB_VIA):d.update(pos=xy(q.GetPosition()),width=q.GetWidth(p.F_Cu)/1e6,drill=q.GetDrillValue()/1e6)
 else:d.update(start=xy(q.GetStart()),end=xy(q.GetEnd()),width=q.GetWidth()/1e6)
 return d
items=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];sel=[desc(q) for q in items if q.GetNetname()=='MCU_GPIO3'];print(json.dumps(sel,indent=2));(R/'qa/source-net.json').write_text(json.dumps(sel,indent=2))
region=p.BOX2I(p.VECTOR2I(109000000,82000000),p.VECTOR2I(6000000,6000000))
near=[desc(q) for q in items if q.GetBoundingBox().Intersects(region)];(R/'qa/nearby-objects.json').write_text(json.dumps(near,indent=2));print(json.dumps(near,indent=2))
