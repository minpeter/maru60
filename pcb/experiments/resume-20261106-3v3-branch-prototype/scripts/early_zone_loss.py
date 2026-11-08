from pathlib import Path
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume');S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype';D=R/'continuation-97d9eb7/stub3v3';layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];retired=set(json.loads((D/'qa/build.json').read_text())['removed'])
def poly(s):
 q=p.SHAPE_POLY_SET();s.TransformToPolygon(q,1,p.ERROR_INSIDE);q.Simplify();return q
def sub(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def intersection(a,b):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,b);return q
def counts(q):return {'area_mm2':q.Area()/1e12,'outlines':q.OutlineCount()}
def empty(q):return q.Area()==0 and q.OutlineCount()==0
drill_by_holes={}
def capture(bp):
 b=p.LoadBoard(str(bp));items={q.m_Uuid.AsString():q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};holes=p.SHAPE_POLY_SET();drills=[]
 for q in items.values():
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
   z=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(z,1,p.ERROR_OUTSIDE);z.Simplify();holes.Append(z);drills.append((z.BBox(),z))
 holes.Simplify();drill_by_holes[id(holes)]=drills;zones={};planes={l:p.SHAPE_POLY_SET()for l in layers}
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  for l in layers:
   if z.IsOnLayer(l):
    cu=sub(z.GetFilledPolysList(l),holes);zones[(z.m_Uuid.AsString(),l)]=cu
    if z.GetNetname()=='GND':planes[l].BooleanAdd(cu)
 return b,items,holes,zones,planes
a,ai,ah,az,ap=capture(S/'pcb/maru60.kicad_pcb');b,bi,bh,bz,bp=capture(D/'pcb/maru60.kicad_pcb');assert set(ai)-set(bi)==retired and not set(bi)-set(ai);assert az.keys()==bz.keys()
def cu(q,l,holes):
 shape=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l));local=p.SHAPE_POLY_SET()
 for bb,h in drill_by_holes[id(holes)]:
  if bb.Intersects(shape.BBox()):local.Append(h)
 local.Simplify();return sub(shape,local)

rows=[];fail=[]
for key in az:
 loss,gain=sub(az[key],bz[key]),sub(bz[key],az[key]);row={'zone':key[0],'layer':a.GetLayerName(key[1]),'loss':counts(loss),'gain':counts(gain),'no_loss':empty(loss)};rows.append(row)
 if not row['no_loss']:fail.append({'kind':'zone_loss',**row})
print("ZONE_ROWS",json.dumps(rows),flush=True)
result={'zone_rows':rows,'failures':fail,'pass':not fail,'rule':'Every zone loss area AND contour count must be zero; no tolerance.'};(D/'qa/early-zone-loss.json').write_text(json.dumps(result,indent=2)+'\n');assert all(r['no_loss']for r in rows)
