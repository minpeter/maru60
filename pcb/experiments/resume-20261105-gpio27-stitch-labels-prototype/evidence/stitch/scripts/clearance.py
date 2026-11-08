from pathlib import Path
import pcbnew as p,json,math
D=Path('/workspace/shared/maru60-resume/continuation-c782/stitch');b=p.LoadBoard(str(D/'pcb/maru60.kicad_pcb'));u=json.loads((D/'qa/build.json').read_text())['via_uuid'];v=next(x for x in b.GetTracks()if x.m_Uuid.AsString()==u);rows=[]
# Conservative outside polygons and a 0.45mm radius exclusion disk: 0.25mm copper radius plus0.20mm requested gap.
def poly(shape):
 q=p.SHAPE_POLY_SET();shape.TransformToPolygon(q,1,p.ERROR_OUTSIDE);q.Simplify();return q
win=poly(p.SHAPE_CIRCLE(v.GetPosition(),450000));items=list(b.GetTracks())+[x for f in b.GetFootprints()for x in f.Pads()]
for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
 hits=[]
 for x in items:
  if x.GetNetname()=='GND'or not x.IsOnLayer(l)or not x.GetBoundingBox().Intersects(win.BBox()):continue
  q=poly(p.SHAPE_CIRCLE(x.GetPosition(),x.GetWidth(l)//2)if isinstance(x,p.PCB_VIA)else x.GetEffectiveShape(l));q.BooleanIntersection(win)
  if q.Area()>0:hits.append(dict(uuid=x.m_Uuid.AsString(),net=x.GetNetname(),area_mm2=q.Area()/1e12))
 for z in b.Zones():
  if z.GetIsRuleArea()or z.GetNetname()=='GND'or not z.IsOnLayer(l):continue
  q=p.SHAPE_POLY_SET(z.GetFilledPolysList(l));q.BooleanIntersection(win)
  if q.Area()>0:hits.append(dict(zone=z.m_Uuid.AsString(),net=z.GetNetname(),area_mm2=q.Area()/1e12))
 rows.append(dict(layer=b.GetLayerName(l),foreign_overlaps_in_020mm_clearance_envelope=hits))
r=dict(method='Conservative outside polygons; all foreign pad/track/via and filled-zone copper screened against radius0.45mm disk. This is a clearance screen, not SI validation.',layers=rows,pass_screen=all(not x['foreign_overlaps_in_020mm_clearance_envelope']for x in rows));(D/'qa/clearance-screen.json').write_text(json.dumps(r,indent=2));print(r)
