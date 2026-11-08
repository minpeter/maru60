from pathlib import Path
import pcbnew as p,json
R=Path('/workspace/shared/maru60-resume/continuation-c782/header');old='fdd2376a-e263-51cf-8638-7d8989c5ffc8';build=json.loads((R/'qa/BUILD.json').read_text());new=build['new_EXT_GPIO10_uuids'][-1];targets=['2e9d2717-15e1-4bce-856d-b881bc5f3e3b','b90cbf74-89de-49fa-ac51-d43df3605713','2bd88f35-bab5-4803-8710-df5ee50545de','cd5fb524-ab04-563a-a15b-b61178f9c51e']
def poly(sh):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_INSIDE);z.Simplify();return z
def capture(path,ids):
 b=p.LoadBoard(str(path));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];holes=[]
 for q in items:
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
   h=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(h,1,p.ERROR_OUTSIDE);h.Simplify();holes.append(h)
 out={}
 for q in items:
  u=q.m_Uuid.AsString()
  if u in ids:
   s=poly(q.GetEffectiveShape(p.B_Cu))
   for h in holes:
    if s.BBox().Intersects(h.BBox()):s.BooleanSubtract(h)
   out[u]=s
 return out
a=capture('/workspace/shared/maru60-resume/combined-trial/pcb/maru60.kicad_pcb',set(targets+[old]));b=capture(str(R/'trial27/pcb/maru60.kicad_pcb'),set(targets+[old,new]));rows=[]
for t in targets:
 replacement=old if t=='cd5fb524-ab04-563a-a15b-b61178f9c51e'else new
 x=p.SHAPE_POLY_SET();x.BooleanIntersection(a[old],a[t]);y=p.SHAPE_POLY_SET();y.BooleanIntersection(b[replacement],b[t]);missing=p.SHAPE_POLY_SET(x);missing.BooleanSubtract(y);gain=p.SHAPE_POLY_SET(y);gain.BooleanSubtract(x);rows.append({'old_route_uuid':old,'current_route_uuid':replacement,'target_uuid':t,'old_patch_mm2':x.Area()/1e12,'new_patch_mm2':y.Area()/1e12,'old_patch_not_covered_mm2':missing.Area()/1e12,'old_patch_not_covered_outlines':missing.OutlineCount(),'new_patch_gain_mm2':gain.Area()/1e12})
(R/'qa/retired-contact-patches.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
