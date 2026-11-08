from pathlib import Path
import pcbnew as p,json,hashlib,math,sys
D=Path(__file__).parent;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();a=p.LoadBoard(str(D/'source.kicad_pcb'));b=p.LoadBoard(str(D/'candidate.kicad_pcb'));uid=lambda q:q.m_Uuid.AsString();xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)];az={uid(z):z for z in a.Zones()};bz={uid(z):z for z in b.Zones()};zones=[]
def pols(ps):
 return [{'exterior':[xy(ps.COutline(i).CPoint(k))for k in range(ps.COutline(i).PointCount())],'holes':[[xy(ps.CHole(i,h).CPoint(k))for k in range(ps.CHole(i,h).PointCount())]for h in range(ps.HoleCount(i))]}for i in range(ps.OutlineCount())]
for u,z in az.items():
 if z.GetIsRuleArea():continue
 for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if not z.IsOnLayer(l):continue
  old=z.GetFilledPolysList(l);new=bz[u].GetFilledPolysList(l);lost=p.SHAPE_POLY_SET();gain=p.SHAPE_POLY_SET();lost.BooleanSubtract(old,new);gain.BooleanSubtract(new,old);zones.append({'uuid':u,'net':z.GetNetname(),'layer':b.GetLayerName(l),'lost_mm2':lost.Area()/1e12,'gained_mm2':gain.Area()/1e12,'exact_filled_polygon_coordinates_unchanged':pols(old)==pols(new),'lost_polygons':pols(lost),'gain_polygons':pols(gain)})
r={'source_sha256':sha(D/'source.kicad_pcb'),'candidate_sha256':sha(D/'candidate.kicad_pcb'),'zones':zones};(D/'fill-contact-audit.json').write_text(json.dumps(r,indent=2));print('Fill changes',[(q['net'],q['layer'],q['lost_mm2'],q['gained_mm2'])for q in zones if q['lost_mm2']or q['gained_mm2']])
