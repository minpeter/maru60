"""Board-specific KiCad 9 material graph v2.
Canonical native items; all asserted through-drills cut every copper layer.
Each positive object/layer/island has its own vertex. Only proved intact plated
via/PTH annuli are joined across layers. No NPTH barrel or zero-metal vertex.
Native connectivity is candidate-pair discovery, not the material edge oracle.
"""
from pathlib import Path
import sys
if not __debug__:raise RuntimeError("Optimized Python is unsupported: scope assertions must remain enabled")
import pcbnew as p,json,hashlib,collections,time,math
if p.Version()!="9.0.2" or p.GetBuildVersion()!="9.0.2+dfsg-1":raise RuntimeError("Unsupported native KiCad version")
BP=Path(sys.argv[1]);OUT=Path(sys.argv[2]);before=hashlib.sha256(BP.read_bytes()).hexdigest();b=p.LoadBoard(str(BP));b.BuildConnectivity();cn=b.GetConnectivity();layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in items};start=time.monotonic()
assert len(idx)==len(items)
assert b.GetCopperLayerCount()==4 and list(b.GetEnabledLayers().CuStack())==layers,("unsupported copper stack",list(b.GetEnabledLayers().CuStack()))
def poly(shape,out=False):
 z=p.SHAPE_POLY_SET();shape.TransformToPolygon(z,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);z.Simplify();return z
def bbox(ps):
 r=ps.BBox();return r.GetX(),r.GetY(),r.GetRight(),r.GetBottom()
def hits(a,c):return a[0]<=c[2]and a[2]>=c[0]and a[1]<=c[3]and a[3]>=c[1]
def area(a,c):
 if not hits(bbox(a),bbox(c)):return 0
 z=p.SHAPE_POLY_SET();z.BooleanIntersection(a,c);return z.Area()/1e12
def exact_contours(ps):
 def ring(r):
  v=[(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
  if not v:return ()
  low=min(v);return min(tuple(v[i:]+v[:i])for i,x in enumerate(v)if x==low)
 return tuple(sorted((ring(ps.COutline(i)),tuple(sorted(ring(ps.CHole(i,h))for h in range(ps.HoleCount(i)))))for i in range(ps.OutlineCount())))
def convex_hole_enclosure(base,hole):
 # Exact Python-integer halfplanes: both native polygon contours must be
 # simple convex single outlines, and every outside-hole vertex strictly
 # inside every edge of the inside-copper polygon. No epsilon.
 assert base.OutlineCount()==hole.OutlineCount()==1 and base.HoleCount(0)==hole.HoleCount(0)==0
 def points(ps):return [(ps.COutline(0).CPoint(i).x,ps.COutline(0).CPoint(i).y)for i in range(ps.COutline(0).PointCount())]
 def orient(v):
  twice=sum(a[0]*c[1]-c[0]*a[1]for a,c in zip(v,v[1:]+v[:1]));assert twice!=0;sgn=1 if twice>0 else -1
  assert all(sgn*((v[(i+1)%len(v)][0]-v[i][0])*(v[(i+2)%len(v)][1]-v[(i+1)%len(v)][1])-(v[(i+1)%len(v)][1]-v[i][1])*(v[(i+2)%len(v)][0]-v[(i+1)%len(v)][0]))>=0 for i in range(len(v)))
  return sgn
 outer,inner=points(base),points(hole);sgn=orient(outer);orient(inner);minimum=None
 for a,c in zip(outer,outer[1:]+outer[:1]):
  assert a!=c
  for x,y in inner:
   cross=sgn*((c[0]-a[0])*(y-a[1])-(c[1]-a[1])*(x-a[0]));assert cross>0,('hole not strictly enclosed by convex copper',a,c,x,y,cross)
   minimum=cross if minimum is None else min(minimum,cross)
 return minimum
def parts(ps):
 out=[]
 for i in range(ps.OutlineCount()):
  s=p.SHAPE_POLY_SET();s.AddOutline(ps.COutline(i))
  for h in range(ps.HoleCount(i)):s.AddHole(ps.CHole(i,h),0)
  if s.Area()>0:out.append(s)
 return out
# Actual board scope asserted, not inferred from pad copper-layer membership.
drills=[];types=collections.Counter()
for q in items:
 if isinstance(q,p.PCB_VIA):
  assert q.GetViaType()==p.VIATYPE_THROUGH,('unsupported via span',uid(q),q.GetViaType())
  assert all(q.IsOnLayer(l)for l in layers),('through via layer mismatch',uid(q));types['through_vias']+=1
 if isinstance(q,p.PAD)and q.HasHole():
  assert q.GetAttribute()in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH],('unsupported drilled pad',uid(q),q.GetAttribute());types['PTH'if q.GetAttribute()==p.PAD_ATTRIB_PTH else'NPTH']+=1
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
  h=poly(q.GetEffectiveHoleShape(),True);drills.append((uid(q),bbox(h),h))
# Every drill above is physically through-board, including NPTH pads whose copper
# layer membership is irrelevant to the material it removes on other layers.
all_drills=p.SHAPE_POLY_SET()
for _,_,h in drills:all_drills.Append(h)
all_drills.Simplify()
cache={};components={};metadata={};objects={};uf={};material_edges=[];barrels=[];empty=[];multiple=[];guard_cache={};guard_failures=[]
def guarded_area(a,c):
 for n in (a,c):
  if n not in guard_cache:
   eroded=p.SHAPE_POLY_SET(components[n]);eroded.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);guard_cache[n]=eroded
 return area(guard_cache[a],guard_cache[c])
def root(n):
 while uf[n]!=n:uf[n]=uf[uf[n]];n=uf[n]
 return n
def join(a,c):
 a,c=root(a),root(c)
 if a!=c:uf[c]=a
def cu(q,l):
 q=idx[uid(q)];key=uid(q),l
 if key not in cache:
  base=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l));s=p.SHAPE_POLY_SET(base);bb=bbox(base);holes=[]
  for owner,hb,h in drills:
   if hits(bb,hb):s.BooleanSubtract(h);holes.append(owner)
  ps=parts(s);cache[key]=s;componentlist=[]
  for i,part in enumerate(ps):
   n='object:'+uid(q)+':'+str(l)+':'+str(i);uf[n]=n;components[n]=part;metadata[n]=dict(kind='object',uuid=uid(q),layer=b.GetLayerName(l),index=i,area_mm2=part.Area()/1e12,net=q.GetNetname());componentlist.append(n)
  objects.setdefault(uid(q),{})[b.GetLayerName(l)]=componentlist
  detail=dict(uuid=uid(q),type=q.GetClass(),net=q.GetNetname(),layer=b.GetLayerName(l),positive_components=len(ps),component_ids=componentlist,areas_mm2=[z.Area()/1e12 for z in ps],bbox_intersecting_drills=holes)
  if not ps:empty.append(detail)
  if len(ps)>1:multiple.append(detail)
 return cache[key]
for q in items:
 for l in layers:
  if q.IsOnLayer(l):cu(q,l)
# Never merge arbitrary fragments of one UUID. Barrel joins are a separate,
# explicitly proved physical relation limited to actual through plated objects.
for q in items:
 plated=isinstance(q,p.PCB_VIA)or isinstance(q,p.PAD)and q.GetAttribute()==p.PAD_ATTRIB_PTH
 if not plated:continue
 assert q.HasHole() and all(q.IsOnLayer(l)for l in layers),('unsupported plated object layers',uid(q))
 nodes=[]
 for l in layers:
  ns=objects[uid(q)][b.GetLayerName(l)];assert len(ns)==1,('severed or empty plated annulus',uid(q),l,ns)
  base=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l));hole=poly(q.GetEffectiveHoleShape(),True)
  if isinstance(q,p.PCB_VIA):
   hs=q.GetEffectiveHoleShape();assert hs.GetSeg().A==q.GetPosition()==hs.GetSeg().B and hs.GetWidth()==q.GetDrillValue() and q.GetWidth(l)>q.GetDrillValue()>0,('via lacks centered continuous annulus',uid(q),l)
  else:convex_hole_enclosure(base,hole)
  own=p.SHAPE_POLY_SET(base);own.BooleanSubtract(hole);globalcu=cu(q,l)
  assert exact_contours(own)==exact_contours(globalcu),('global annulus coordinate contours differ from own-hole annulus; fail closed',uid(q),l)
  nodes+=ns
 for a,c in zip(nodes,nodes[1:]):join(a,c)
 barrels.append(dict(uuid=uid(q),type=q.GetClass(),nodes=nodes,proof='through span asserted; one positive annulus per copper layer; centered circular via or exact convex PTH hole enclosure proved; all-hole material has exact normalized native coordinate contour equality to own annulus; no foreign drill severs annulus'))
print('MATERIAL',len(metadata),'empty layers',len(empty),'multiple layers',len(multiple),'seconds',time.monotonic()-start,flush=True)
# Native candidate discovery is resolved to canonical objects before any shape use.
seen=set();direct=[];raw_direct=[];rejected=[]
for q in items:
 for wrapped in list(cn.GetConnectedTracks(q))+list(cn.GetConnectedPads(q)):
  z=idx[uid(wrapped)];a,c=uid(q),uid(z);assert q.GetNetname()==z.GetNetname(),('cross-net native direct candidate',a,c)
  if a==c:continue
  key=tuple(sorted((a,c)))
  if key in seen:continue
  seen.add(key);support=[];raw_support=[]
  for l in layers:
   ln=b.GetLayerName(l)
   if not(q.IsOnLayer(l)and z.IsOnLayer(l)):continue
   values=[];rawvalues=[]
   for an in objects[a][ln]:
    for cnod in objects[c][ln]:
     ar=area(components[an],components[cnod])
     if ar>0:
      rawvalues.append(ar);ga=guarded_area(an,cnod)
      if ga>0:join(an,cnod);values.append(ar);material_edges.append([an,cnod,ar,ga])
      else:guard_failures.append(dict(kind='direct',a=an,b=cnod,unguarded_area_mm2=ar,guarded_area_mm2=ga))
   total=math.fsum(values);rawtotal=math.fsum(rawvalues)
   if rawtotal>0:raw_support.append([ln,rawtotal])
   if total>0:support.append([ln,total])
  if raw_support:raw_direct.append([a,c,raw_support])
  if support:direct.append([a,c,support])
  else:rejected.append(list(key))
print('DIRECT',len(direct),'rejected',len(rejected),'seconds',time.monotonic()-start,flush=True)
zone_records=[];zone_edges=[];raw_zone_edges=[]
for zone in b.Zones():
 if zone.GetIsRuleArea():continue
 contacts=[idx[uid(q)]for q in list(cn.GetConnectedTracks(zone))+list(cn.GetConnectedPads(zone))]
 for l in layers:
  if not zone.IsOnLayer(l):continue
  ln=b.GetLayerName(l);original=zone.GetFilledPolysList(l);physical=p.SHAPE_POLY_SET(original);physical.BooleanSubtract(all_drills);ps=parts(physical);record=dict(uuid=uid(zone),net=zone.GetNetname(),layer=ln,native_outlines=original.OutlineCount(),physical_outlines=len(ps),components=[])
  for i,part in enumerate(ps):
   n='zone:'+uid(zone)+':'+str(l)+':'+str(i);uf[n]=n;components[n]=part;metadata[n]=dict(kind='zone',uuid=uid(zone),layer=ln,index=i,area_mm2=part.Area()/1e12,net=zone.GetNetname());count=0
   for q in contacts:
    if not q.IsOnLayer(l):continue
    assert q.GetNetname()==zone.GetNetname(),('cross-net zone candidate',uid(q),uid(zone))
    values=[];rawvalues=[]
    for qn in objects[uid(q)][ln]:
     ar=area(components[qn],part)
     if ar>0:
      rawvalues.append(ar);ga=guarded_area(n,qn)
      if ga>0:join(n,qn);values.append(ar);material_edges.append([n,qn,ar,ga])
      else:guard_failures.append(dict(kind='zone',a=n,b=qn,unguarded_area_mm2=ar,guarded_area_mm2=ga))
    total=math.fsum(values);rawtotal=math.fsum(rawvalues)
    if rawtotal>0:raw_zone_edges.append([n,uid(q),rawtotal])
    if total>0:zone_edges.append([n,uid(q),total]);count+=1
   record['components'].append(dict(id=n,area_mm2=part.Area()/1e12,contact_count=count))
  zone_records.append(record)
 print('ZONE',uid(zone),'seconds',time.monotonic()-start,flush=True)
# Stable roots are minimum material-vertex IDs, never implicitly an object's UUID.
bins=collections.defaultdict(list)
for n in uf:bins[root(n)].append(n)
rootname={old:min(nodes)for old,nodes in bins.items()};material_roots={n:rootname[root(n)]for n in uf};object_roots={u:sorted({material_roots[n]for ns in ls.values()for n in ns})for u,ls in objects.items()};pad_inventory={};padparts=collections.defaultdict(lambda:collections.defaultdict(list));pad_multi=[]
for q in items:
 if not isinstance(q,p.PAD)or not q.GetNetname():continue
 u=uid(q);pad_inventory[u]=dict(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber(),net=q.GetNetname());rs=object_roots[u]
 if len(rs)!=1:pad_multi.append(dict(uuid=u,**pad_inventory[u],material_roots=rs))
 else:padparts[q.GetNetname()][rs[0]].append(u)
assert not pad_multi,('named pad has no unique physical material component; do not conflate',pad_multi)
partitions={net:sorted(sorted(v)for v in groups.values())for net,groups in padparts.items()}
npth=[]
for q in items:
 if isinstance(q,p.PAD)and q.GetAttribute()==p.PAD_ATTRIB_NPTH:
  assert not q.GetNetname(),('unexpected net-bearing NPTH',uid(q),q.GetNetname());npth.append(dict(uuid=uid(q),ref=q.GetParentFootprint().GetReference(),nodes_by_layer=objects[uid(q)],material_roots=object_roots[uid(q)]))
report=dict(revision='v2-all-through-drills-layer-island-material-graph',source_path=str(BP),board_sha256=before,native_version=p.GetBuildVersion(),method='Canonical native candidate-pair discovery; union compound primitives; subtract every actual asserted through drill from every object and zone; positive object/layer/island vertices; only proved intact plated annuli joined across layers. All positive fragments retained without area waiver; accepted contacts additionally require positive overlap after each component is guarded inward by 2 nm; guard failures are explicit and not joined. NPTH never receives barrel join.',scope_assumptions=dict(copper_layers=[b.GetLayerName(l)for l in layers],actual_drill_types=dict(types),all_physical_holes_through=True,unknown_via_or_drilled_pad_types_fail=True,no_foreign_drill_cut_to_plated_annuli=True,named_pads_unique_material_root=True),pad_inventory=pad_inventory,pad_partitions_by_net=partitions,direct_edges=direct,raw_unguarded_direct_edges=raw_direct,native_pairs_without_guarded_positive_copper=rejected,contact_guard=dict(inward_nm=2,corner_strategy="ROUND_ALL_CORNERS",max_error_nm=1,criterion="positive native overlap of both independently guarded material components",failure_policy="record as unproved; do not join or count as accepted physical contact"),guard_failing_material_edges=guard_failures,zones=zone_records,zone_edges=zone_edges,raw_unguarded_zone_edges=raw_zone_edges,material_nodes=metadata,material_edges=material_edges,material_roots=material_roots,object_nodes_by_layer=objects,object_material_roots=object_roots,barrel_joins=barrels,empty_object_layers=empty,multiple_component_object_layers=multiple,NPTH_material=npth,tracks=sum(not isinstance(q,p.PCB_VIA)for q in b.GetTracks()),vias=sum(isinstance(q,p.PCB_VIA)for q in b.GetTracks()),footprints=len(b.GetFootprints()),track_length_mm=math.fsum(q.GetLength()/1e6 for q in b.GetTracks()if not isinstance(q,p.PCB_VIA)),seconds=time.monotonic()-start,unchanged=hashlib.sha256(BP.read_bytes()).hexdigest()==before)
assert report['unchanged'];OUT.write_text(json.dumps(report,indent=2));print('DONE',OUT,'seconds',report['seconds'],flush=True)
