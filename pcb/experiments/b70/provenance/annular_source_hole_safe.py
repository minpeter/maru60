#!/usr/bin/python3
"""Read-only, source-tagged conductor/filled-island contact graph. No refill/save/net edits."""
import os,sys,json,hashlib,time,argparse,collections
from pathlib import Path
import pcbnew as p
import numpy as np
sys.path.insert(0,'/workspace/shared/maru60-kicad-linux/pcb/tools');import sexp
LAYERS=[p.F_Cu,p.B_Cu]
ROOTS={'GND':['U1','61'],'+3V3':['U2','5'],'+1V1':['L1','1'],'+5V':['F1','2'],'VREG_LX':['U1','48'],'VREG_AVDD':['R104','2'],'+5V_LED':['U7','6'],'KEY_RGB_5V':['R110','2'],'BOOT_BUTTON':['R106','2'],'QSPI_SS':['U3','1'],'UNDERGLOW_5V_BUF':['U6','4'],'UNDERGLOW_5V':['R111','2'],'KEY_RGB_5V_BUF':['U5','4']}
hashfile=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
uid=lambda q:q.m_Uuid.AsString()
xy=lambda v:[p.ToMM(v.x),p.ToMM(v.y)]
def raw_contract(path):
 root=sexp.parse(Path(path).read_text());nets={int(q[1]):str(q[2])for q in sexp.all(root,'net')};out={}
 for q in root:
  if not isinstance(q,list)or not q:continue
  candidates=sexp.all(q,'pad')if q[0]=='footprint'else[q]if q[0]in['segment','via','arc','zone']else[]
  for item in candidates:
   u=sexp.get(item,'uuid');n=sexp.get(item,'net')
   if u:out[str(u[1])]={'intended_net':nets.get(int(n[1]),'')if n else'','type':str(item[0])}
 return out

def conductor_polygons(item,layer,error_nm=1):
 """Lower/upper copper bounds; subtract ACTUAL oriented native drill capsule, not a point/disk shortcut."""
 shape=item.GetEffectiveShape(layer);inside=p.SHAPE_POLY_SET();outside=p.SHAPE_POLY_SET()
 shape.TransformToPolygon(inside,error_nm,p.ERROR_INSIDE);shape.TransformToPolygon(outside,error_nm,p.ERROR_OUTSIDE)
 has_hole=isinstance(item,(p.PCB_VIA,p.PAD))and item.HasHole()
 if has_hole:
  hole=item.GetEffectiveHoleShape();h_in=p.SHAPE_POLY_SET();h_out=p.SHAPE_POLY_SET();hole.TransformToPolygon(h_in,error_nm,p.ERROR_INSIDE);hole.TransformToPolygon(h_out,error_nm,p.ERROR_OUTSIDE)
  inside.BooleanSubtract(h_out);outside.BooleanSubtract(h_in)
 return inside,outside,{'drill_excluded':bool(has_hole),'flashed_on_layer':bool(item.FlashLayer(layer))if hasattr(item,'FlashLayer')else True,'lower_copper_area_mm2':inside.Area()/1e12,'upper_copper_area_mm2':outside.Area()/1e12}

def boundary_edges(poly):
 clean=p.SHAPE_POLY_SET();clean.BooleanAdd(poly);edges=[]
 for oi in range(clean.OutlineCount()):
  for line in[clean.COutline(oi)]+[clean.CHole(oi,hi)for hi in range(clean.HoleCount(oi))]:
   pts=[(int(line.CPoint(i).x),int(line.CPoint(i).y))for i in range(line.PointCount())]
   edges.extend(zip(pts,pts[1:]+pts[:1]))
 return edges

def finite_shared_boundary_mm(a,b):
 # Exact integer-nm collinearity and positive-length interval overlap; no epsilon or inflated shapes.
 A=boundary_edges(a);B=boundary_edges(b)
 if not A or not B:return 0.
 E=np.array(B,dtype=np.int64);lo=E.min(axis=1);hi=E.max(axis=1);total=0.
 for aa,zz in A:
  dx,dy=zz[0]-aa[0],zz[1]-aa[1]
  if not(dx or dy):continue
  mn=[min(aa[k],zz[k])for k in[0,1]];mx=[max(aa[k],zz[k])for k in[0,1]];inds=np.where((hi[:,0]>=mn[0])&(lo[:,0]<=mx[0])&(hi[:,1]>=mn[1])&(lo[:,1]<=mx[1]))[0];axis=0 if abs(dx)>=abs(dy)else 1;pieces=[]
  for ix in inds:
   q,r=B[int(ix)]
   if (q[0]-aa[0])*dy-(q[1]-aa[1])*dx or(r[0]-aa[0])*dy-(r[1]-aa[1])*dx:continue
   l=max(min(aa[axis],zz[axis]),min(q[axis],r[axis]));h=min(max(aa[axis],zz[axis]),max(q[axis],r[axis]))
   if h>l:pieces.append((l,h))
  merged=[]
  for l,h in sorted(pieces):
   if merged and l<=merged[-1][1]:merged[-1]=(merged[-1][0],max(h,merged[-1][1]))
   else:merged.append((l,h))
  total+=sum(h-l for l,h in merged)*((dx*dx+dy*dy)**.5)/abs(dx if axis==0 else dy)/1e6
 return total

def classify_contact(lower,upper,island):
 lo=p.SHAPE_POLY_SET();lo.BooleanIntersection(lower,island);la=lo.Area()
 if la>0:return 'positive_area',la,None,0.
 finite=finite_shared_boundary_mm(lower,island)if lower.Collide(island,0)else 0.
 if finite>0:return 'finite_shared_boundary',0,0,finite
 hi=p.SHAPE_POLY_SET();hi.BooleanIntersection(upper,island);ha=hi.Area()
 if ha>0:return 'approximation_band_only_not_promoted',0,ha,0.
 if lower.Collide(island,0):return 'point_or_tangent_zero_extent_not_promoted',0,0,0.
 if upper.Collide(island,0):return 'approximation_band_boundary_not_promoted',0,0,0.
 return 'disjoint',0,0,0.

def run(board_path,out_path,drc_path=None,expected_sha=None):
 start=time.time();assert not Path(out_path).exists(), 'Use a fresh output path; no stale overwrite';helper_sha_before=hashfile(__file__);path=Path(board_path);before=hashfile(path);pro=path.with_suffix('.kicad_pro');pro_before=hashfile(pro)if pro.exists()else None
 if expected_sha:assert before==expected_sha,(before,expected_sha)
 raw=raw_contract(path);b=p.LoadBoard(str(path));allobjs=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]+list(b.Zones());objects={uid(q):q for q in allobjs}
 def identity(stage):
  diff=[{'uuid':u,'intended_net':row['intended_net'],'native_net':objects[u].GetNetname()if u in objects else None,'type':row['type']}for u,row in raw.items()if u not in objects or objects[u].GetNetname()!=row['intended_net']]
  assert not diff,{'stage':stage,'net_identity_mismatch':diff}
 identity('after_LoadBoard');b.BuildConnectivity();identity('after_BuildConnectivity');cn=b.GetConnectivity();scoped={u:q for u,q in objects.items()if not isinstance(q,p.ZONE)and q.GetNetname()in ROOTS};pads={u:q for u,q in scoped.items()if isinstance(q,p.PAD)}
 comps=[];owner={};seen=set()
 for root in scoped:
  if root in seen:continue
  reached=set();todo=[root]
  while todo:
   u=todo.pop()
   if u in reached:continue
   assert u in scoped,('foreign/unscoped native adjacency',root,u)
   reached.add(u);q=scoped[u]
   for neighbor in list(cn.GetConnectedTracks(q))+list(cn.GetConnectedPads(q)):
    v=uid(neighbor);assert v in scoped and raw[v]['intended_net']==raw[root]['intended_net'],('foreign net adjacency',root,v);todo.append(v)
  seen|=reached;ci=len(comps)
  for u in reached:owner[u]=ci
  pp=sorted(reached & pads.keys());comps.append({'index':ci,'net':raw[root]['intended_net'],'object_uuids':sorted(reached),'pad_uuids':pp,'pads':[{'uuid':u,'ref':pads[u].GetParentFootprint().GetReference(),'pin':pads[u].GetNumber()}for u in pp],'classification':'populated_pad_component'if pp else'padless_copper_component_not_automatically_orphan','contacts':[]})
 # Island identities retain native filled outline index. UnitSet copies correct hole geometry, no flattening or center inference.
 units=[];drilled=[q for q in allobjs if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()];hole_cache={}
 for z in b.Zones():
  if z.GetIsRuleArea()or z.GetNetname()not in ROOTS:continue
  for layer in LAYERS:
   if not z.IsOnLayer(layer):continue
   poly=z.GetFilledPolysList(layer)
   for ix in range(poly.OutlineCount()):
    island=poly.UnitSet(ix);clipped=[]
    # Saved same-net fills may cover a drill center. Remove actual physical drill voids analytically;
    # plated barrels connect through the explicit via/PTH component, never via fictitious hole copper.
    for q in drilled:
     if not q.IsOnLayer(layer)or not q.GetBoundingBox().Intersects(island.BBox()):continue
     hs=q.GetEffectiveHoleShape()
     if not island.Collide(hs,0):continue
     u=uid(q)
     if u not in hole_cache:
      hp=p.SHAPE_POLY_SET();hs.TransformToPolygon(hp,1,p.ERROR_OUTSIDE);hole_cache[u]=hp
     island.BooleanSubtract(hole_cache[u]);clipped.append(u)
    # Keep Boolean-normalized hole topology; never Unfracture normalized fill.
    for child in range(island.OutlineCount()):
     one=island.UnitSet(child);ii=len(units);units.append({'index':ii,'zone_uuid':uid(z),'net':z.GetNetname(),'layer':layer,'island_index':ix,'physical_drill_clipped_subisland':child,'analytically_subtracted_drill_uuids':clipped,'poly':one,'bbox':one.BBox()})
 contacts=[];ambiguous=[];center_only=[];geometry_meta={};graph=collections.defaultdict(set);contact_counts=collections.Counter();cache={}
 for u,q in scoped.items():
  for layer in LAYERS:
   if not q.IsOnLayer(layer):continue
   matching=[z for z in units if z['net']==q.GetNetname()and z['layer']==layer and q.GetBoundingBox().Intersects(z['bbox'])]
   if not matching:continue
   low,high,meta=conductor_polygons(q,layer);geometry_meta[u+':'+b.GetLayerName(layer)]=meta
   if high.Area()==0:continue
   for z in matching:
    cls,area,upper_area,shared=classify_contact(low,high,z['poly']);contact_counts[cls]+=1
    rec={'object_uuid':u,'component':owner[u],'net':q.GetNetname(),'zone_uuid':z['zone_uuid'],'layer':b.GetLayerName(layer),'native_filled_island_index':z['island_index'],'island_node':z['index'],'classification':cls,'finite_shared_boundary_mm':shared,'physical_drill_clipped_subisland':z['physical_drill_clipped_subisland'],'conservative_positive_overlap_mm2':area/1e12,'upper_only_overlap_mm2':upper_area/1e12 if upper_area is not None else None,'actual_drill_excluded':meta['drill_excluded']}
    if cls in['positive_area','finite_shared_boundary']:
     contacts.append(rec);c=('component',owner[u]);zz=('island',z['index']);graph[c].add(zz);graph[zz].add(c);comps[owner[u]]['contacts'].append(len(contacts)-1)
    elif cls!='disjoint':ambiguous.append(rec)
    if meta['drill_excluded']and z['poly'].Contains(q.GetPosition())and cls not in['positive_area','finite_shared_boundary']:center_only.append(rec)
 # Same-net SAME-LAYER island overlaps are conductive; zero-area boundaries remain explicit, not epsilon-promoted.
 island_contacts=[]
 for i,a in enumerate(units):
  for z in units[i+1:]:
   if a['net']!=z['net']or a['layer']!=z['layer']or not a['bbox'].Intersects(z['bbox']):continue
   cls,area,upper,shared=classify_contact(a['poly'],a['poly'],z['poly'])
   if cls in['positive_area','finite_shared_boundary']:
    aa=('island',a['index']);zz=('island',z['index']);graph[aa].add(zz);graph[zz].add(aa);island_contacts.append({'a':a['index'],'b':z['index'],'overlap_mm2':area/1e12,'classification':cls,'finite_shared_boundary_mm':shared})
   elif cls!='disjoint':ambiguous.append({'island_a':a['index'],'island_b':z['index'],'classification':cls})
 results={}
 for net,(ref,pin)in ROOTS.items():
  roots=[u for u,q in pads.items()if q.GetNetname()==net and q.GetParentFootprint().GetReference()==ref and q.GetNumber()==pin];assert roots,(net,ref,pin)
  visited=set();todo=[('component',owner[u])for u in roots]
  while todo:
   n=todo.pop()
   if n in visited:continue
   visited.add(n);todo+=list(graph[n])
  target=[c for c in comps if c['net']==net];un=[c for c in target if('component',c['index'])not in visited];reachable=[q for c in target if('component',c['index'])in visited for q in c['pads']];unpads=[q for c in un for q in c['pads']]
  results[net]={'root_ref_pin':[ref,pin],'root_pad_uuids':roots,'total_physical_pad_count':len(reachable)+len(unpads),'reached_physical_pad_count':len(reachable),'unreached_physical_pad_count':len(unpads),'all_populated_pads_reached':not unpads,'all_scoped_copper_components_reached':not un,'unreached_populated_pads':unpads,'unreached_components':[{'index':c['index'],'classification':c['classification'],'pads':c['pads'],'object_uuids':c['object_uuids'],'contact_indices':c['contacts']}for c in un],'reached_component_indices':[c['index']for c in target if('component',c['index'])in visited],'reached_island_indices':[n[1]for n in sorted(visited)if n[0]=='island']}
 # Independent native no-open gate: source graph success cannot cancel native power/clock/QSPI/USB opens.
 critical=set(ROOTS)|{'VBUS','XIN','XOUT','XTAL_OUT'};native=None
 if drc_path:
  drc=json.load(open(drc_path));records=[]
  for i,item in enumerate(drc['unconnected_items']):
   ids=[q['uuid']for q in item['items']];assert all(u in raw for u in ids),('unresolved native endpoint',ids)
   nets=sorted({raw[u]['intended_net']for u in ids});forbidden=any(n in critical or n.startswith(('QSPI_','USB_','VREG_'))for n in nets)
   records.append({'index':i,'native_items':item['items'],'raw_intended_nets':nets,'forbidden_critical_open':forbidden})
  native={'report_sha256':hashfile(drc_path),'all_open_items':len(records),'forbidden_open_count':sum(q['forbidden_critical_open']for q in records),'all_items_resolved_to_raw_intended_net':True,'items':records,'hard_violations':sum(q['severity']=='error'for q in drc['violations'])}
 assert before==hashfile(path);assert pro_before==(hashfile(pro)if pro.exists()else None);identity('final_no_mutation')
 r={'board':str(path),'board_sha256':before,'project_sha256':pro_before,'kicad_version':p.GetBuildVersion(),'read_only_no_refill_no_save_no_net_relabel':True,'raw_intended_object_count':len(raw),'per_object_net_identity_asserted_before_and_after_native_connectivity':True,'helper_sha256':helper_sha_before,'complete':True,'polygonization_max_error_nm':1,'filled_island_drills_analytically_removed':True,'contact_policy':'Positive area OR exact positive-length shared boundary of conservative native conductor polygon (actual oriented drill subtracted) with saved filled islands analytically drill-clipped. Zero-extent point/tangent and approximation-band-only contacts are explicit, not silently called overlap or promoted. No epsilon expansion. Native track/pad components are distinct from filled islands; native critical-open veto is independent.','loaded_vs_padless_classification_explicit':True,'source_results':results,'positive_contacts':contacts,'nonpositive_contact_candidates':ambiguous,'center_inside_island_but_annular_contact_not_proved':center_only,'islands':[{k:(b.GetLayerName(v)if k=='layer'else v)for k,v in z.items()if k not in['poly','bbox']}for z in units],'island_positive_overlap_edges':island_contacts,'components':comps,'conductor_geometry_metadata':geometry_meta,'contact_class_counts':dict(contact_counts),'native_open_guard':native,'all13_populated_source_graphs_pass':all(x['all_populated_pads_reached']for x in results.values()),'all13_strict_copper_source_graphs_pass':all(x['all_scoped_copper_components_reached']for x in results.values()),'combined_contract_pass':all(x['all_scoped_copper_components_reached']for x in results.values())and native is not None and native['forbidden_open_count']==0 and native['hard_violations']==0,'elapsed_seconds':time.time()-start,'caveat':'Copper connectivity only, not powered/current/thermal/return/SI qualification. Total pad count is NEVER a reached count. An empty convenience core subset never overrides full unreached list.'}
 assert hashfile(__file__)==helper_sha_before;temporary=Path(str(out_path)+'.partial');temporary.write_text(json.dumps(r,indent=2));temporary.replace(out_path);print(json.dumps({'board_sha256':before,'elapsed_seconds':r['elapsed_seconds'],'source_results':{n:{k:x[k]for k in['total_physical_pad_count','reached_physical_pad_count','unreached_physical_pad_count','all_scoped_copper_components_reached']}for n,x in results.items()},'combined_contract_pass':r['combined_contract_pass'],'contact_class_counts':r['contact_class_counts'],'center_only_count':len(center_only)},indent=2),flush=True)
 return r
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('board');ap.add_argument('output');ap.add_argument('--native-drc');ap.add_argument('--expected-sha256');args=ap.parse_args();run(args.board,args.output,args.native_drc,args.expected_sha256)
