from pathlib import Path
import sys,json,hashlib,collections
sys.path.insert(0,'/workspace/shared/maru60-resume/tools')
from sexpr_spans import children,head,field
import pcbnew as p
R=Path('/workspace/shared/maru60-resume');D=R/'combined-trial';S=R/'header-routing/frozen24move/pcb';C=D/'pcb';H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();removed='1e6f9b6e-9a22-418a-8cde-6feb5aafb26e';changed='b83f85ff-dd51-4f3a-987a-b80209573fa1'
A=(S/'maru60.kicad_pcb').read_text();B=(C/'maru60.kicad_pcb').read_text();Pre=(D/'prefill.kicad_pcb').read_text();na=lambda t:' '.join(t.split());pairs=lambda s:[(head(t),na(t))for _,_,t in children(s)]
ca=collections.Counter(pairs(A));cb=collections.Counter(pairs(Pre));minus=list((ca-cb).elements());plus=list((cb-ca).elements());assert len(minus)==2 and len(plus)==1;assert any(removed in t for _,t in minus) and any(changed in t for _,t in minus+plus)
nonzones=lambda s:[na(t)for _,_,t in children(s)if head(t)!='zone'];assert nonzones(Pre)==nonzones(B)
zoneconfig=lambda s:[[na(tt)for _,_,tt in children(t)if head(tt) not in ('filled_polygon','fill_segments')]for _,_,t in children(s)if head(t)=='zone'];assert zoneconfig(A)==zoneconfig(B)
companions={str(f.relative_to(S)):H(f)==H(C/f.relative_to(S))for f in S.rglob('*')if f.is_file() and f.name!='maru60.kicad_pcb'};assert len(companions)==57 and all(companions.values())
def poly(shape):
 q=p.SHAPE_POLY_SET();shape.TransformToPolygon(q,1,p.ERROR_OUTSIDE);q.Simplify();return q
def minuspoly(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def inter(a,b):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,b);return q
def capture(path):
 b=p.LoadBoard(str(path));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];holes=p.SHAPE_POLY_SET();planes={l:p.SHAPE_POLY_SET()for l in (p.In1_Cu,p.In2_Cu)};tracks=p.SHAPE_POLY_SET()
 for x in items:
  if isinstance(x,(p.PAD,p.PCB_VIA)) and x.HasHole():holes.Append(poly(x.GetEffectiveHoleShape()))
  if x.GetNetname()=='VBUS' and isinstance(x,p.PCB_TRACK) and not isinstance(x,p.PCB_VIA) and x.GetLayer()==p.B_Cu:tracks.BooleanAdd(poly(x.GetEffectiveShape(p.B_Cu)))
 holes.Simplify()
 for z in b.Zones():
  if z.GetIsRuleArea() or z.GetNetname()!='GND':continue
  for l in planes:
   if z.IsOnLayer(l):planes[l].BooleanAdd(p.SHAPE_POLY_SET(z.GetFilledPolysList(l)))
 for l in planes:planes[l].BooleanSubtract(holes)
 return b,items,holes,planes,tracks
ab,ai,ah,ap,at=capture(S/'maru60.kicad_pcb');bb,bi,bh,bp,bt=capture(C/'maru60.kicad_pcb');assert minuspoly(at,bt).Area()==0 and minuspoly(bt,at).Area()==0
physa=minuspoly(at,ah);physb=minuspoly(bt,bh);tloss=minuspoly(physa,physb);tgain=minuspoly(physb,physa);assert tloss.Area()==0
win=poly(p.SHAPE_CIRCLE(p.VECTOR2I(20150000,10950000),456000));rows=[]
for l in ap:
 loss=minuspoly(ap[l],bp[l]);gain=minuspoly(bp[l],ap[l]);outside=minuspoly(gain,win);oldloss=[];loss_boxes=[]
 for j in range(loss.OutlineCount()):
  points=[loss.COutline(j).CPoint(i)for i in range(loss.COutline(j).PointCount())];xx=[q.x for q in points];yy=[q.y for q in points];loss_boxes.append(p.BOX2I(p.VECTOR2I(min(xx),min(yy)),p.VECTOR2I(max(xx)-min(xx),max(yy)-min(yy))))
 for x in ai:
  if x.GetNetname()in('','GND')or not any(x.GetBoundingBox().Intersects(box)for box in loss_boxes):continue
  for sl in (p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu):
   if not x.IsOnLayer(sl):continue
   shape=p.SHAPE_CIRCLE(x.GetPosition(),x.GetWidth(sl)//2)if isinstance(x,p.PCB_VIA)else x.GetEffectiveShape(sl);over=inter(loss,minuspoly(poly(shape),ah))
   if over.Area()!=0 or over.OutlineCount()!=0:oldloss.append({'uuid':x.m_Uuid.AsString(),'net':x.GetNetname(),'layer':ab.GetLayerName(sl),'loss_mm2':over.Area()/1e12})
 def outlines(ps):
  return [[(ps.COutline(j).CPoint(i).x,ps.COutline(j).CPoint(i).y) for i in range(ps.COutline(j).PointCount())] for j in range(ps.OutlineCount())]
 eroded=p.SHAPE_POLY_SET(loss);eroded.Deflate(1,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 rows.append({'loss_integer_nm_outlines':outlines(loss),'gain_outside_integer_nm_outlines':outlines(outside),'loss_after_1nm_inward_guard_mm2':eroded.Area()/1e12,'layer':bb.GetLayerName(l),'old_components':ap[l].OutlineCount(),'new_components':bp[l].OutlineCount(),'loss_mm2':loss.Area()/1e12,'loss_outlines':loss.OutlineCount(),'gain_mm2':gain.Area()/1e12,'gain_outside_via_envelope_mm2':outside.Area()/1e12,'gain_outside_outlines':outside.OutlineCount(),'old_signal_reference_losses':oldloss})
 print('PLANE_DIAGNOSTIC',json.dumps(rows[-1]),flush=True)
 (D/'qa/plane-diagnostic.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert ap[l].OutlineCount()==bp[l].OutlineCount()==1
ad=json.loads((R/'header-independent24move/drc.json').read_text());bd=json.loads((D/'qa/drc.json').read_text());norm=lambda d:collections.Counter(json.dumps(x,sort_keys=True)for x in d['violations']);dw=list((norm(ad)-norm(bd)).elements());nw=list((norm(bd)-norm(ad)).elements());assert len(dw)==1 and removed in dw[0] and not nw;assert json.loads((D/'qa/open-component-pairs.json').read_text())['all10_complete_open_pad_component_pairs_exact'];assert not bd['schematic_parity']
result={'status':'HOLD pending review of explicitly recorded tiny plane-boundary losses; not waived','basic_checks_pass':True,'source_board_sha256':H(S/'maru60.kicad_pcb'),'candidate_board_sha256':H(C/'maru60.kicad_pcb'),'raw_change_scope':{'removed_via':removed,'changed_track':changed,'all_other_nonzones_unchanged':True,'zone_configuration_unchanged':True,'all57_companions_exact':True},'DRC':{'opens':len(bd['unconnected_items']),'warnings':len(bd['violations']),'removed':[json.loads(x)for x in dw],'new':nw,'all_open_component_pairs_exact':True,'native_representative_records_exact':False,'parity':bd['schematic_parity']},'VBUS_B_Cu_track_union':{'planar_union_exact':True,'physical_track_copper_loss_mm2':tloss.Area()/1e12,'physical_track_copper_gain_mm2':tgain.Area()/1e12,'method':'Native union of all VBUS B.Cu track polygons, before and after actual through-hole subtraction; via metal excluded deliberately.'},'ground_reference':rows,'limit':'Nominal geometric/connectivity result only. No transient, thermal, current-carrying, SI/EMC or physical reliability qualification.'}
(D/'qa/geometry-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
