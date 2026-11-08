import os,pathlib,json,hashlib
D=pathlib.Path(__file__).parent
for k in ['CONFIG','CACHE','DATA']:os.environ['XDG_'+k+'_HOME']=str(D/k.lower())
import pcbnew as p
A=D/'source/pcb/maru60.kicad_pcb';B=D/'filled/pcb/maru60.kicad_pcb';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();a=p.LoadBoard(str(A));b=p.LoadBoard(str(B));uid=lambda q:q.m_Uuid.AsString();layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];oi={uid(q):q for q in list(a.GetTracks())+[q for f in a.GetFootprints()for q in f.Pads()]};ni={uid(q):q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};ledger=json.load(open(D/'qa/build.json'));new=ni[ledger['new_objects'][0]['uuid']];old=oi['2c0aa2c5-bec8-4dff-bff7-2e823d3e36fa'];via=oi['d382de57-3476-43c4-ac26-0a72b21acf7c']
def poly(s):
 z=p.SHAPE_POLY_SET();s.TransformToPolygon(z,1,p.ERROR_OUTSIDE);return z
def diff(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanSubtract(b);return z
def cross(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(b);return z
def dump(ps):
 def ring(r):return[[r.CPoint(i).x,r.CPoint(i).y]for i in range(r.PointCount())]
 return [dict(outline=ring(ps.COutline(i)),holes=[ring(ps.CHole(i,j))for j in range(ps.HoleCount(i))])for i in range(ps.OutlineCount())]
def netcopper(items,l):
 z=p.SHAPE_POLY_SET();holes=p.SHAPE_POLY_SET()
 for q in items.values():
  if q.GetNetname()=='BUCK_FB'and q.IsOnLayer(l):z.BooleanAdd(poly(q.GetEffectiveShape(l)))
 for q in items.values():
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()and q.IsOnLayer(l)and q.GetEffectiveHoleShape().BBox().Intersects(z.BBox()):holes.BooleanAdd(poly(q.GetEffectiveHoleShape()))
 z.BooleanSubtract(holes);return z
subset=diff(poly(new.GetEffectiveShape(p.F_Cu)),poly(old.GetEffectiveShape(p.F_Cu)));assert subset.Area()==0
ideal=poly(p.SHAPE_SEGMENT(p.VECTOR2I(181000000,85750000),p.VECTOR2I(182950000,85750000),150000));assert diff(ideal,poly(new.GetEffectiveShape(p.F_Cu))).Area()==0 and diff(poly(new.GetEffectiveShape(p.F_Cu)),ideal).Area()==0
cu=[]
for l in layers:
 oldcu=netcopper(oi,l);newcu=netcopper(ni,l);added=diff(newcu,oldcu);removed=diff(oldcu,newcu);assert added.Area()==0;cu.append(dict(layer=a.GetLayerName(l),added_FB_physical_copper_mm2=added.Area()/1e12,removed_FB_physical_copper_mm2=removed.Area()/1e12,removed=dump(removed)))
# Report source and actual replacement reference, with physical holes separately subtracted.
refs=[]
for label,board,items in [('source',a,oi),('actual',b,ni)]:
 ground=p.SHAPE_POLY_SET();holes=p.SHAPE_POLY_SET()
 for z in board.Zones():
  if z.GetNetname()=='GND'and z.IsOnLayer(p.In1_Cu):ground.BooleanAdd(z.GetFilledPolysList(p.In1_Cu))
 for q in items.values():
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()and q.IsOnLayer(p.In1_Cu)and q.GetEffectiveHoleShape().BBox().Intersects(new.GetBoundingBox()):holes.BooleanAdd(poly(q.GetEffectiveHoleShape()))
 ground.BooleanSubtract(holes);full=poly(new.GetEffectiveShape(p.F_Cu));physical=diff(full,holes);mf=diff(full,ground);mp=diff(physical,ground);refs.append(dict(snapshot=label,full_projection_missing_mm2=mf.Area()/1e12,physical_copper_missing_mm2=mp.Area()/1e12,full_missing=dump(mf),physical_missing=dump(mp)))
assert refs[0]['full_projection_missing_mm2']==refs[1]['full_projection_missing_mm2'];assert refs[0]['physical_copper_missing_mm2']==refs[1]['physical_copper_missing_mm2']
# Ground growth, resolved from actual native saved zones; explicitly split by removed drill footprint.
h=poly(via.GetEffectiveHoleShape());gains=[]
for oz in a.Zones():
 nz=next(z for z in b.Zones()if uid(z)==uid(oz))
 for l in layers:
  if not oz.IsOnLayer(l):continue
  gain=diff(nz.GetFilledPolysList(l),oz.GetFilledPolysList(l));loss=diff(oz.GetFilledPolysList(l),nz.GetFilledPolysList(l))
  if gain.Area()or loss.Area():gains.append(dict(zone_uuid=uid(oz),net=oz.GetNetname(),layer=a.GetLayerName(l),gain_mm2=gain.Area()/1e12,loss_mm2=loss.Area()/1e12,gain_inside_removed_drill_mm2=cross(gain,h).Area()/1e12,gain_outside_removed_drill_mm2=diff(gain,h).Area()/1e12,gain=dump(gain),loss=dump(loss)))
for g in gains:
 g['arithmetic_gain_outside_removed_drill_mm2']=g['gain_mm2']-g['gain_inside_removed_drill_mm2']
 g['native_split_area_accounting_residual_mm2']=g['gain_mm2']-g['gain_inside_removed_drill_mm2']-g['gain_outside_removed_drill_mm2']
 g['split_area_note']='Native Boolean clipping has non-additive area accounting at integer-grid fracture boundaries; retain the measured residual without normalization or waiver.'
contacts=[]
for u in ledger['declared_replacement_contact_uuids']:
 q=oi[u];g=poly(q.GetEffectiveShape(p.F_Cu));oldhit=cross(poly(old.GetEffectiveShape(p.F_Cu)),g);newhit=cross(poly(new.GetEffectiveShape(p.F_Cu)),g);contacts.append(dict(uuid=u,old_support_mm2=oldhit.Area()/1e12,replacement_support_mm2=newhit.Area()/1e12,support_loss_mm2=diff(oldhit,newhit).Area()/1e12,support_gain_mm2=diff(newhit,oldhit).Area()/1e12))
r=dict(source_sha256=sha(A),candidate_sha256=sha(B),replacement_exact_declared_geometry=True,replacement_copper_outside_old_track_mm2=subset.Area()/1e12,physical_FB_copper_delta=cu,replacement_reference=refs,reference_interpretation='Absolute inherited active-end deficit remains, but actual replacement is an exact subset of original copper and introduces no copper or new missing-reference region. No arbitrary endpoint mask/exemption used.',removed_drill=dict(uuid=uid(via),xy_mm=[178.15,85.75],diameter_mm=.25,projected_native_area_mm2=h.Area()/1e12,physical_drill_count_before=sum(isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()for q in oi.values()),physical_drill_count_after=sum(isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()for q in ni.values())),actual_zone_changes=gains,active_contact_support=contacts,analog_claims=False);(D/'qa/geometry-effects.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items()if k not in ['physical_FB_copper_delta','actual_zone_changes','replacement_reference']},indent=2))
