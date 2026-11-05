from pathlib import Path
import sys,json,hashlib,collections,math
sys.path.insert(0,'/workspace/shared/maru60-resume/tools');from sexpr_spans import children,head
import pcbnew as p
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-c782/combined27';S=R/'continuation-c782/header/trial27/pcb';C=D/'pcb';H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();norm=lambda s:' '.join(s.split());A=(S/'maru60.kicad_pcb').read_text();B=(C/'maru60.kicad_pcb').read_text();
def strip_refs(s):
 for oa,oz,fp in reversed(children(s)):
  if head(fp)!='footprint':continue
  prop=next(((a,z,t)for a,z,t in children(fp)if head(t)=='property'and any(t.startswith('(property \"Reference\" \"'+r+'\"')for r in ['U13','R135','R145','U11'])),None)
  if prop:
   a,z,t=prop;s=s[:oa+a]+s[oa+z:]
 return s
forms=lambda s:collections.Counter(norm(t)for _,_,t in children(strip_refs(s))if head(t)!='zone');aa,bb=forms(A),forms(B);removed=list((aa-bb).elements());added=list((bb-aa).elements());assert not removed and len(added)==1 and added[0].startswith('(via');zonecfg=lambda s:[norm(' '.join(t for _,_,t in children(z)if head(t)not in('filled_polygon','fill_segments')))for _,_,z in children(s)if head(z)=='zone'];assert zonecfg(A)==zonecfg(B)
companions=[f for f in S.rglob('*')if f.is_file()and f.name!='maru60.kicad_pcb'];assert len(companions)==57 and all(H(f)==H(C/f.relative_to(S))for f in companions)
def poly(shape,out=True):
 q=p.SHAPE_POLY_SET();shape.TransformToPolygon(q,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);q.Simplify();return q
def diff(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def inter(a,b):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,b);return q
def contours(q):
 return [[(q.COutline(j).CPoint(i).x,q.COutline(j).CPoint(i).y)for i in range(q.COutline(j).PointCount())]for j in range(q.OutlineCount())]
def capture(path):
 b=p.LoadBoard(str(path));items=list(b.GetTracks())+[x for f in b.GetFootprints()for x in f.Pads()];holes=p.SHAPE_POLY_SET();raw={l:p.SHAPE_POLY_SET()for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]}
 for x in items:
  if isinstance(x,(p.PAD,p.PCB_VIA))and x.HasHole():holes.Append(poly(x.GetEffectiveHoleShape()))
 holes.Simplify()
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  if z.GetNetname()!='GND':continue
  for l in raw:
   if z.IsOnLayer(l):raw[l].BooleanAdd(p.SHAPE_POLY_SET(z.GetFilledPolysList(l)))
 return b,items,holes,raw,{l:diff(q,holes)for l,q in raw.items()}
ab,ai,ah,ar,ap=capture(S/'maru60.kicad_pcb');b,bi,bh,br,bp=capture(C/'maru60.kicad_pcb');uid=json.loads((D/'qa/BUILD.json').read_text())['added_GND_stitch_uuid'];v=next(x for x in bi if x.m_Uuid.AsString()==uid);assert all(v.GetWidth(l)==500000 for l in ar) and v.GetDrillValue()==250000
nonGNDa=[norm(z)for _,_,z in children(A)if head(z)=='zone'and '(net_name "GND")'not in z];nonGNDb=[norm(z)for _,_,z in children(B)if head(z)=='zone'and '(net_name "GND")'not in z];assert nonGNDa==nonGNDb
# Sole local exemption is the actual newly introduced through-drill, not a broad region.
hole=poly(v.GetEffectiveHoleShape());rows=[]
for l in ar:
 loss=diff(ap[l],bp[l]);gain=diff(bp[l],ap[l]);outside=diff(loss,hole);rl=diff(ar[l],br[l]);rg=diff(br[l],ar[l]);shadow=[];boxes=[]
 for j in range(loss.OutlineCount()):
  q=p.SHAPE_POLY_SET();q.AddOutline(loss.COutline(j));boxes.append(q.BBox())
 for x in ai:
  if x.GetNetname()in('','GND')or not any(x.GetBoundingBox().Intersects(bb)for bb in boxes):continue
  for sl in ar:
   if not x.IsOnLayer(sl):continue
   shape=p.SHAPE_CIRCLE(x.GetPosition(),x.GetWidth(sl)//2)if isinstance(x,p.PCB_VIA)else x.GetEffectiveShape(sl);ov=inter(loss,diff(poly(shape),ah))
   if ov.Area()!=0 or ov.OutlineCount()!=0:shadow.append(dict(uuid=x.m_Uuid.AsString(),net=x.GetNetname(),layer=ab.GetLayerName(sl),loss_mm2=ov.Area()/1e12,contours_nm=contours(ov)))
 rows.append(dict(layer=b.GetLayerName(l),raw_loss_mm2=rl.Area()/1e12,raw_gain_mm2=rg.Area()/1e12,physical_loss_mm2=loss.Area()/1e12,physical_gain_mm2=gain.Area()/1e12,loss_outside_actual_new_drill_mm2=outside.Area()/1e12,loss_outside_contours_nm=contours(outside),old_signal_reference_losses=shadow,old_physical_components=ap[l].OutlineCount(),new_physical_components=bp[l].OutlineCount()))
via_dist=lambda its:min(math.hypot(x.GetPosition().x-105800000,x.GetPosition().y-37500000)/1e6 for x in its if isinstance(x,p.PCB_VIA)and x.GetNetname()=='GND')
ad=json.loads((R/'continuation-c782/header/qa/drc.json').read_text());bd=json.loads((D/'qa/drc.json').read_text());co=lambda ls:collections.Counter(json.dumps(x,sort_keys=True)for x in ls)
r=dict(source_sha256=H(S/'maru60.kicad_pcb'),candidate_sha256=H(C/'maru60.kicad_pcb'),raw_scope=dict(removed=removed,added=added,zone_configuration_equal=True,all57_companions_equal=True),drc_added=[json.loads(x)for x in(co(bd['violations'])-co(ad['violations'])).elements()],drc_removed=[json.loads(x)for x in(co(ad['violations'])-co(bd['violations'])).elements()],open_records_equal=ad['unconnected_items']==bd['unconnected_items'],planes=rows,nearest_GND_via_before_mm=via_dist(ai),nearest_GND_via_after_mm=via_dist(bi),note='No SI gain inferred from nearest-via distance. Strict prior prototype no-loss FAIL retained.')
(D/'qa/geometry.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
