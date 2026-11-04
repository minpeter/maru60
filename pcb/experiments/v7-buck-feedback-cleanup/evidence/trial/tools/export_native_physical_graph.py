"""One BOARD/process. Native pair discovery plus drill-subtracted positive-copper
verification; split each zone by physical filled outline, never conflate islands.
This is an independent fresh checker, not a restored historical gate.
"""
import pcbnew as p,json,pathlib,sys,hashlib,collections,time,math
BP=pathlib.Path(sys.argv[1]);OUT=pathlib.Path(sys.argv[2]);sha=lambda:hashlib.sha256(BP.read_bytes()).hexdigest();before=sha();b=p.LoadBoard(str(BP));b.BuildConnectivity();cn=b.GetConnectivity();uid=lambda q:q.m_Uuid.AsString();layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];items=list(b.GetTracks())+[a for f in b.GetFootprints()for a in f.Pads()];idx={uid(q):q for q in items};uf={u:u for u in idx};cache={};start=time.monotonic()
def root(a):
 while uf[a]!=a:uf[a]=uf[uf[a]];a=uf[a]
 return a
def join(a,z):
 a,z=root(a),root(z)
 if a!=z:uf[z]=a
def poly(sh,outside=False):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_OUTSIDE if outside else p.ERROR_INSIDE);return z
def cu(q,l):
 key=uid(q),l
 if key not in cache:
  z=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l))
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():z.BooleanSubtract(poly(q.GetEffectiveHoleShape(),True))
  cache[key]=z
 return cache[key]
def area(a,z):
 if not a.BBox().Intersects(z.BBox()):return 0
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,z);return q.Area()/1e12
edges=[];reject=[];seen=set()
for q in items:
 for z in list(cn.GetConnectedTracks(q))+list(cn.GetConnectedPads(q)):
  a,d=uid(q),uid(z)
  if a==d:continue
  key=tuple(sorted((a,d)))
  if key in seen:continue
  seen.add(key);support=[]
  for l in layers:
   if q.IsOnLayer(l)and z.IsOnLayer(l):
    v=area(cu(q,l),cu(z,l))
    if v>0:support.append([b.GetLayerName(l),v])
  if support:join(a,d);edges.append([a,d,support])
  else:reject.append(list(key))
print('DIRECT',len(edges),'rejected',len(reject),'seconds',time.monotonic()-start,flush=True)
# All drilled holes are unioned without changing their outside-approximation bound.
drills=p.SHAPE_POLY_SET()
for q in items:
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():drills.Append(poly(q.GetEffectiveHoleShape(),True))
drills.Simplify();print('DRILLS',drills.OutlineCount(),flush=True)
zone_records=[];zone_edges=[]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 contacts=list(cn.GetConnectedTracks(z))+list(cn.GetConnectedPads(z))
 for l in layers:
  if not z.IsOnLayer(l):continue
  original=z.GetFilledPolysList(l);physical=p.SHAPE_POLY_SET(original);physical.BooleanSubtract(drills)
  rec={'uuid':uid(z),'net':z.GetNetname(),'layer':b.GetLayerName(l),'native_outlines':original.OutlineCount(),'physical_outlines':physical.OutlineCount(),'components':[]}
  for i in range(physical.OutlineCount()):
   s=p.SHAPE_POLY_SET();s.AddOutline(physical.COutline(i))
   for h in range(physical.HoleCount(i)):s.AddHole(physical.CHole(i,h),0)
   n='zone:'+uid(z)+':'+str(l)+':'+str(i);uf[n]=n;cc=[]
   for q in contacts:
    if not q.IsOnLayer(l):continue
    ar=area(cu(q,l),s)
    if ar>0:join(n,uid(q));zone_edges.append([n,uid(q),ar]);cc.append(uid(q))
   rec['components'].append({'id':n,'area_mm2':s.Area()/1e12,'contact_count':len(cc)})
  zone_records.append(rec)
 print('ZONE',uid(z),'seconds',time.monotonic()-start,flush=True)
# Preserve individual physical pad UUIDs, even for repeated pad numbers.
parts=collections.defaultdict(lambda:collections.defaultdict(list));pad_inventory={}
for q in items:
 if not isinstance(q,p.PAD)or not q.GetNetname():continue
 u=uid(q);r=q.GetParentFootprint().GetReference();pad_inventory[u]={'ref':r,'pad':q.GetNumber(),'net':q.GetNetname()};parts[q.GetNetname()][root(u)].append(u)
partitions={n:sorted([sorted(v)for v in co.values()])for n,co in parts.items()}
report={'source_path':str(BP),'board_sha256':before,'native_version':p.GetBuildVersion(),'method':'Native direct neighbor discovery; each edge independently checked for positive 1nm inside copper overlap after outside physical-hole subtraction; each filled zone split into physical outlines after all drill holes subtracted. Via/PTH barrel retains its object identity across layers. No plane-island conflation.','pad_inventory':pad_inventory,'pad_partitions_by_net':partitions,'direct_edges':edges,'native_pairs_without_positive_copper':reject,'zones':zone_records,'zone_edges':zone_edges,'tracks':sum(not isinstance(q,p.PCB_VIA)for q in b.GetTracks()),'vias':sum(isinstance(q,p.PCB_VIA)for q in b.GetTracks()),'footprints':len(b.GetFootprints()),'track_length_mm':math.fsum(q.GetLength()/1e6 for q in b.GetTracks()if not isinstance(q,p.PCB_VIA)),'seconds':time.monotonic()-start,'unchanged':sha()==before}
OUT.write_text(json.dumps(report,indent=2));print('DONE',OUT,'seconds',report['seconds'],flush=True)
