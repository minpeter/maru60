import pcbnew as p,json,hashlib,pathlib,math,collections
D=pathlib.Path('/tmp/v7-c124-rebound-short/r121-expanded-review')
S=pathlib.Path('/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104/selected-recovered/pcb/maru60.kicad_pcb')
M=pathlib.Path('/tmp/v7-c124-rebound-short/main')
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(S)=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'
g=json.loads((M/'counterfactual-uvlo-r121-ipc-v4.json').read_text());j=json.loads((M/'counterfactual-v4-contact-reference.json').read_text())
res={'source_sha256':sha(S),'input_sha256':{n:sha(M/n)for n in ['counterfactual-uvlo-r121-ipc-v4.json','counterfactual-v4-contact-reference.json']},'version':p.GetBuildVersion()}
b=p.LoadBoard(str(S));fs={f.GetReference():f for f in b.GetFootprints()};obs=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in obs}
vec=lambda a:p.VECTOR2I(*(round(v*1e6)for v in a));xy=lambda v:[v.x/1e6,v.y/1e6]
def poly(s,loc=p.ERROR_INSIDE):
 z=p.SHAPE_POLY_SET();s.TransformToPolygon(z,1,loc);return z
def objpoly(q,loc=p.ERROR_INSIDE):
 z=poly(q.GetEffectiveShape(p.B_Cu),loc)
 if q.HasHole():z.BooleanSubtract(poly(q.GetEffectiveHoleShape(),p.ERROR_OUTSIDE if loc==p.ERROR_INSIDE else p.ERROR_INSIDE))
 return z
def inter(a,c):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(c);return z
def minus(a,c):
 z=p.SHAPE_POLY_SET(a);z.BooleanSubtract(c);return z
def seg(a,c,w,loc=p.ERROR_INSIDE):return poly(p.SHAPE_SEGMENT(vec(a),vec(c),round(w*1e6)),loc)
def rect(x,y,w,h):
 z=p.SHAPE_POLY_SET();z.NewOutline()
 for a,c in [(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)]:z.Append(round(a*1e6),round(c*1e6))
 return z
ret={x['uuid']for x in j['retired_tracks']};moved={x['uuid']for x in j['old_moved_pads']};assert len(ret)==31
mism=[]
for r in j['retired_tracks']:
 q=idx[r['uuid']]
 for k,a,z in [('net',r['net'],q.GetNetname()),('start',r['start'],xy(q.GetStart())),('end',r['end'],xy(q.GetEnd())),('width',r['width'],q.GetWidth()/1e6)]:
  if a!=z:mism.append([r['uuid'],k,a,z])
 if isinstance(q,p.PCB_VIA)or q.GetLayer()!=p.B_Cu:mism.append([r['uuid'],'not BCu track'])
res['retirement_counts']=dict(collections.Counter(idx[u].GetNetname()for u in ret));res['retirement_source_mismatches']=mism
# Copper-contact boundary check only. No full-board graph.
local=[q for q in obs if q.IsOnLayer(p.B_Cu)and q.GetBoundingBox().Intersects(p.BOX2I(vec([10,14]),vec([14,11])))]
pc={uid(q):objpoly(q)for q in local};affected=ret|moved;edges=[]
for i,q in enumerate(local):
 for z in local[i+1:]:
  a,c=uid(q),uid(z)
  if not({a,c}&affected)or q.GetNetname()!=z.GetNetname()or not q.GetBoundingBox().Intersects(z.GetBoundingBox()):continue
  ar=inter(pc[a],pc[c]).Area()/1e12
  if ar>0:edges.append({'a':a,'b':c,'net':q.GetNetname(),'area_mm2':ar})
oldpairs={tuple(sorted([e['a'],e['b']]))for e in j['old_contact_retirements']};newpairs={tuple(sorted([e['a'],e['b']]))for e in edges}
res['independent_old_contact_count']=len(edges);res['ledger_missing_pairs']=list(newpairs-oldpairs);res['ledger_spurious_pairs']=list(oldpairs-newpairs)
res['external_boundaries']=[]
for e in edges:
 if(e['a']in affected)==(e['b']in affected):continue
 ext=e['b']if e['a']in affected else e['a'];matches=[x for x in j['new_to_retained_contacts']if x['old']==ext and x['net']==e['net']]
 res['external_boundaries'].append({'old_boundary_uuid':ext,'net':e['net'],'new_contacts':matches})
# Old UVLO endpoint branches, including retained contacts at geometric neighborhoods.
uvid=set(g['uvlo_retirement_uuids']);adj=collections.defaultdict(list)
for q in b.GetTracks():
 if isinstance(q,p.PCB_VIA)or q.GetNetname()!='USB_UVLO'or q.GetLayer()!=p.B_Cu:continue
 for v in[q.GetStart(),q.GetEnd()]:adj[(v.x,v.y)].append(uid(q))
pathnodes=set()
for u in uvid:
 for v in[idx[u].GetStart(),idx[u].GetEnd()]:pathnodes.add((v.x,v.y))
res['uvlo_endpoint_external_branches']=[{'at_mm':[x/1e6,y/1e6],'retained_tracks':[u for u in adj[(x,y)]if u not in uvid]}for x,y in sorted(pathnodes)if any(u not in uvid for u in adj[(x,y)])]
# Independently build boundary route segments and verify against retained native copper.
routes={r['name']:seg(r['start'],r['end'],.15)for r in g['routes']}
res['boundary_native_rechecks']=[]
for row in j['new_to_retained_contacts']:
 if not row['new'].startswith(('UVLO','OVLO','DVDT')):continue
 ar=inter(routes[row['new']],pc[row['old']]).Area()/1e12
 res['boundary_native_rechecks'].append({'new':row['new'],'old':row['old'],'area_mm2':ar,'positive':ar>0})
# Stronger old-support inclusion: OUTSIDE old physical support against INSIDE bridge.
bridge=seg([15.5,17.725],[14.9,17.275],.28);bridge.BooleanAdd(seg([15.5,17.85],[15.5,17.25],.20))
cp=idx['f79380d7-c89c-4396-b53e-4918d8902c13'];res['support_recheck']=[]
for u in['19181a2b-164e-4055-9004-2860bebe32f4','763086b7-5549-4f5e-bb08-ce25387b3627']:
 si=inter(objpoly(cp),objpoly(idx[u]));so=inter(objpoly(cp,p.ERROR_OUTSIDE),objpoly(idx[u],p.ERROR_OUTSIDE))
 res['support_recheck'].append({'old_contact':u,'inside_area_mm2':si.Area()/1e12,'outside_area_mm2':so.Area()/1e12,'inside_support_minus_inside_bridge_mm2':minus(si,bridge).Area()/1e12,'outside_support_minus_inside_bridge_mm2':minus(so,bridge).Area()/1e12})
# R121 explicit IPC pads and exact court primitive, with all native neighboring courts.
rpad=rect(13.68,17.85,1,.9);rct=rect(13.68,18.65,1.5,3);res['r121_ground_contact_mm2']=inter(rpad,pc['abcd4fb1-881b-43f9-906e-39d93366692e']).Area()/1e12
res['r121_courtyard_collisions']=[]
for f in fs.values():
 if f.GetReference()in['R121','C124']:continue
 f.BuildCourtyardCaches();ct=f.GetCourtyard(p.B_CrtYd)
 if ct.OutlineCount()and inter(rct,ct).Area()>0:res['r121_courtyard_collisions'].append(f.GetReference())
res['new_courtyard_gaps_mm']={'R121_C124':rct.GetClearance(rect(15.38,19.17,1.6,1.05))/1e6,'R121_R125':rct.GetClearance(rect(15.54,20.27,1.8,1.05))/1e6,'C124_R125':rect(15.38,19.17,1.6,1.05).GetClearance(rect(15.54,20.27,1.8,1.05))/1e6,'U8_R125':rect(18,18.5,3,3).GetClearance(rect(15.54,20.27,1.8,1.05))/1e6}
# Native physical source plane contacts: three preserved vias, two roots each.
res['root_rechecks']=[]
for row in j['plane_roots']:
 l=b.GetLayerID(row['layer']);q=idx[row['uuid']];ann=poly(q.GetEffectiveShape(l));ann.BooleanSubtract(poly(q.GetEffectiveHoleShape(),p.ERROR_OUTSIDE));pl=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.GetNetname()=='GND'and z.IsOnLayer(l):pl.BooleanAdd(z.GetFilledPolysList(l))
 ar=inter(ann,pl).Area()/1e12;res['root_rechecks'].append({'via':row['uuid'],'layer':row['layer'],'area_mm2':ar,'positive':ar>0})
res['source_after_sha256']=sha(S);assert res['source_after_sha256']==res['source_sha256']
(D/'review_native.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
