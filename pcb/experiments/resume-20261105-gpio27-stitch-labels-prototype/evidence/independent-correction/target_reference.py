import pcbnew as p,json
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-c782');O=R/'independent27fix2'
def poly(s):
 q=p.SHAPE_POLY_SET();s.TransformToPolygon(q,1,p.ERROR_OUTSIDE);q.Simplify();return q
def sub(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def capture(path,uuids):
 b=p.LoadBoard(str(path));items=list(b.GetTracks())+[p for f in b.GetFootprints()for p in f.Pads()];holes=[x.GetEffectiveHoleShape() for x in items if isinstance(x,(p.PAD,p.PCB_VIA))and x.HasHole()];plane=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.GetNetname()=='GND'and z.IsOnLayer(p.In1_Cu):plane.BooleanAdd(p.SHAPE_POLY_SET(z.GetFilledPolysList(p.In1_Cu)))
 shapes={}
 for x in items:
  u=x.m_Uuid.AsString()
  if u not in uuids:continue
  q=poly(x.GetEffectiveShape(p.F_Cu))
  for h in holes:
   if q.BBox().Intersects(h.BBox()):q.BooleanSubtract(poly(h))
  # A track's physical shadow excludes all hole material. Therefore raw reference plane subtraction here equals physical-reference subtraction on the track domain.
  shapes[u]=(q,sub(q,plane))
 return b,shapes
old='55e5d0cf-c179-4e88-925d-241a5a9d4416';new='adb09d04-e93c-4f35-bbef-200d2bb1eb64';a,aa=capture(R.parent/'combined-trial/pcb/maru60.kicad_pcb',{old});b,bb=capture(R/'combined27fix2/pcb/maru60.kicad_pcb',{old,new});window=poly(p.SHAPE_CIRCLE(p.VECTOR2I(96650000,41625000),455000));rows=[]
for u,(cu,lack) in bb.items():
 fresh=sub(lack,aa[old][1]);out=sub(fresh,window);coords=[[[out.COutline(j).CPoint(i).x,out.COutline(j).CPoint(i).y]for i in range(out.COutline(j).PointCount())]for j in range(out.OutlineCount())];rows.append({'uuid':u,'current_uncovered_mm2':lack.Area()/1e12,'new_uncovered_outside_existing_moved_window_mm2':out.Area()/1e12,'outside_outlines':out.OutlineCount(),'contours_nm':coords})
res={'method':'Full track current physical material minus adjacent native GND fill, with all intersecting actual drill holes removed. Complete old unsupported track footprint removed, then unchanged moved-via window. No spatial crop or enlarged exception.','rows':rows,'pass':all(x['outside_outlines']==0 for x in rows)};(O/'target-reference.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
