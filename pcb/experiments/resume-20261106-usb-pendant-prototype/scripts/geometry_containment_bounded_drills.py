from pathlib import Path
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume');S=R/'selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype';D=R/'continuation-fa96a7c/usb-stub';layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];retired=set(json.loads((D/'qa/build.json').read_text())['removed'])
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
plane_losses={l:sub(ap[l],bp[l])for l in [p.In1_Cu,p.In2_Cu]}
refs=[];objects=[]
for u,q in bi.items():
 old=ai[u]
 for l in layers:
  assert old.IsOnLayer(l)==q.IsOnLayer(l)
  if not q.IsOnLayer(l):continue
  ac,bc=cu(old,l,ah),cu(q,l,bh);loss,gain=sub(ac,bc),sub(bc,ac);row={'uuid':u,'layer':b.GetLayerName(l),'loss':counts(loss),'gain':counts(gain),'no_loss':empty(loss)};objects.append(row)
  if not row['no_loss']:fail.append({'kind':'retained_object_loss',**row})
  if q.GetNetname()in ('','GND'):continue
  # Both internal ground reference planes inspected for every retained signal/power object/layer.
  for ref in [p.In1_Cu,p.In2_Cu]:
   lost_reference=intersection(ac,plane_losses[ref]);new_gain_uncovered=sub(gain,bp[ref]) if not empty(gain) else p.SHAPE_POLY_SET();row={'uuid':u,'net':q.GetNetname(),'layer':b.GetLayerName(l),'reference':b.GetLayerName(ref),'old_copper_lost_reference':counts(lost_reference),'added_copper_uncovered':counts(new_gain_uncovered),'pass':empty(lost_reference) and empty(new_gain_uncovered)};refs.append(row)
   if not row['pass']:fail.append({'kind':'new_reference_gap',**row})

result={'zone_rows':rows,'retained_object_rows':objects,'retained_reference_rows':refs,'failures':fail,'pass':not fail,'rule':'Every loss or new-uncovered area AND contour count must be zero. No tolerance. Both inner GND references inspected. Declared retired copper excluded; every retained object tested.'};(D/'qa/full-geometry-containment.json').write_text(json.dumps(result,indent=2));print(json.dumps({'zone_rows':len(rows),'object_rows':len(objects),'reference_rows':len(refs),'failures':len(fail),'first_failures':fail[:10]},indent=2));assert all(r['no_loss']for r in rows+objects) and all(r['pass']for r in refs)
