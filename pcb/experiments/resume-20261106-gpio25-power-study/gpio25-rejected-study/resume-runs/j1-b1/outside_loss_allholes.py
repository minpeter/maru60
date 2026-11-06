from pathlib import Path
import pcbnew as p,json
R=Path('/workspace/shared/maru60-resume/continuation-be51692/gpio25-transition/resume-runs/j1-b1');S=Path('/workspace/shared/maru60-resume/selected-repo/pcb/experiments/resume-20261106-usb-pendant-prototype/pcb/maru60.kicad_pcb');C=R/'candidate/pcb/maru60.kicad_pcb';a=p.LoadBoard(str(S));b=p.LoadBoard(str(C));plan=json.loads((R/'qa/FROZEN_SCOPE.json').read_text());w=p.SHAPE_POLY_SET()
for xy in [plan['via24_old'],plan['via24_new']]+plan['gpio25_vias']:
 z=p.SHAPE_POLY_SET();p.SHAPE_CIRCLE(p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6)),455000).TransformToPolygon(z,1,p.ERROR_OUTSIDE);w.BooleanAdd(z)
holes=[]
for q in list(a.GetTracks())+[q for f in a.GetFootprints()for q in f.Pads()]:
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
  h=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(h,1,p.ERROR_OUTSIDE);holes.append((q.m_Uuid.AsString(),h))
rows=[]
for l in[p.In1_Cu,p.In2_Cu]:
 az=next(z for z in a.Zones()if z.GetNetname()=='GND'and z.IsOnLayer(l));bz=next(z for z in b.Zones()if z.GetNetname()=='GND'and z.IsOnLayer(l));loss=p.SHAPE_POLY_SET(az.GetFilledPolysList(l));loss.BooleanSubtract(bz.GetFilledPolysList(l));loss.BooleanSubtract(w);hits=[]
 for uid,h in holes:
  if loss.BBox().Intersects(h.BBox()):
   hit=p.SHAPE_POLY_SET();hit.BooleanIntersection(loss,h)
   if hit.Area()!=0 or hit.OutlineCount()!=0:hits.append(uid)
   loss.BooleanSubtract(h)
 polys=[]
 for i in range(loss.OutlineCount()):
  r=loss.COutline(i);polys.append([(r.CPoint(j).x,r.CPoint(j).y)for j in range(r.PointCount())])
 rows.append(dict(layer=b.GetLayerName(l),outside_loss_mm2=loss.Area()/1e12,contours=loss.OutlineCount(),points=polys,actual_hole_intersections=hits))
(R/'qa/outside-loss-allholes.json').write_text(json.dumps(rows,indent=2));print(rows)
