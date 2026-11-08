import pcbnew as p,json
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-c782');O=R/'independent27fix2';old='55e5d0cf-c179-4e88-925d-241a5a9d4416';via='075334c3-e6fd-4cf3-8599-1a58cef3db7f'
def poly(s,e):
 q=p.SHAPE_POLY_SET();s.TransformToPolygon(q,1,e);q.Simplify();return q
def sub(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def capture(path):
 b=p.LoadBoard(str(path));its=list(b.GetTracks())+[pad for f in b.GetFootprints()for pad in f.Pads()];ds={x.m_Uuid.AsString():x for x in its};out={}
 for u in [old,via]:
  x=ds[u];shape=p.SHAPE_CIRCLE(x.GetPosition(),x.GetWidth(p.F_Cu)//2)if isinstance(x,p.PCB_VIA)else x.GetEffectiveShape(p.F_Cu);q=poly(shape,p.ERROR_INSIDE)
  for h in its:
   if isinstance(h,(p.PAD,p.PCB_VIA))and h.HasHole()and q.BBox().Intersects(h.GetEffectiveHoleShape().BBox()):q.BooleanSubtract(poly(h.GetEffectiveHoleShape(),p.ERROR_OUTSIDE))
  out[u]=q
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(out[old],out[via]);return q
s=capture(R.parent/'combined-trial/pcb/maru60.kicad_pcb');c=capture(R/'combined27fix2/pcb/maru60.kicad_pcb');loss=sub(s,c);gain=sub(c,s);d={'source_contact_mm2':s.Area()/1e12,'candidate_contact_mm2':c.Area()/1e12,'old_minus_new_mm2':loss.Area()/1e12,'old_minus_new_outlines':loss.OutlineCount(),'new_minus_old_mm2':gain.Area()/1e12,'new_minus_old_outlines':gain.OutlineCount()};(O/'source-contact.json').write_text(json.dumps(d,indent=2));print(d)
