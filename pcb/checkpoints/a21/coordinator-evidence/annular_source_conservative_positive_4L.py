#!/usr/bin/python3
"""Read-only, source-tagged conductor/filled-island contact graph. No refill/save/net edits."""
import os,sys,json,hashlib,time,argparse,collections
from pathlib import Path
import pcbnew as p
import numpy as np
sys.path.insert(0,'/workspace/shared/maru60-kicad-linux/pcb/tools');import sexp
LAYERS=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
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

def conductor_polygons(item,layer,error_nm=1000):
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

_line_cache={}
def finite_shared_boundary_mm(a,b):
 # Exact same integer-nm collinearity and positive interval union as the original,
 # indexed by primitive line direction + intercept instead of O(A_edges*B_edges).
 import math
 key=id(b)
 if key not in _line_cache:
  groups={}
  for q,r in boundary_edges(b):
   dx,dy=r[0]-q[0],r[1]-q[1]
   if not(dx or dy):continue
   g=math.gcd(abs(dx),abs(dy));ux,uy=dx//g,dy//g
   if ux<0 or(ux==0 and uy<0):ux,uy=-ux,-uy
   k=(ux,uy,q[0]*uy-q[1]*ux);axis=0 if abs(ux)>=abs(uy)else 1
   groups.setdefault(k,[]).append((min(q[axis],r[axis]),max(q[axis],r[axis])))
  _line_cache[key]=(b,groups)
 groups=_line_cache[key][1];total=0.
 for q,r in boundary_edges(a):
  dx,dy=r[0]-q[0],r[1]-q[1]
  if not(dx or dy):continue
  g=math.gcd(abs(dx),abs(dy));ux,uy=dx//g,dy//g
  if ux<0 or(ux==0 and uy<0):ux,uy=-ux,-uy
  k=(ux,uy,q[0]*uy-q[1]*ux);axis=0 if abs(ux)>=abs(uy)else 1;lo,hi=min(q[axis],r[axis]),max(q[axis],r[axis]);pieces=[]
  for l,h in groups.get(k,[]):
   l,h=max(lo,l),min(hi,h)
   if h>l:pieces.append((l,h))
  merged=[]
  for l,h in sorted(pieces):
   if merged and l<=merged[-1][1]:merged[-1]=(merged[-1][0],max(h,merged[-1][1]))
   else:merged.append((l,h))
  total+=sum(h-l for l,h in merged)*math.hypot(dx,dy)/abs(dx if axis==0 else dy)/1e6
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
      hp=p.SHAPE_POLY_SET();hs.TransformToPolygon(hp,1000,p.ERROR_OUTSIDE);hole_cache[u]=hp
     island.BooleanSubtract(hole_cache[u]);clipped.append(u)
    # Keep Boolean-normalized hole topology; never Unfracture normalized fill.
    for child in range(island.OutlineCount()):
     one=island.UnitSet(child);ii=len(units);units.append({'index':ii,'zone_uuid':uid(z),'net':z.GetNetname(),'layer':layer,'island_index':ix,'physical_drill_clipped_subisland':child,'analytically_subtracted_drill_uuids':clipped,'poly':one,'bbox':one.BBox()})
 print('ISLANDS',len(units),'elapsed',time.time()-start,flush=True)
 positive=[];ambiguous=[];island_edges=[];pair_cache={};island_cache={};shape_cache={};tested=0
 def component_contact(ci,zi):
  nonlocal tested
  key=(ci,zi)
  if key in pair_cache:return pair_cache[key]
  comp=comps[ci];z=units[zi]
  if comp['net']!=z['net']:pair_cache[key]=False;return False
  for u in comp['object_uuids']:
   q=scoped[u];layer=z['layer']
   if not q.IsOnLayer(layer)or not q.GetBoundingBox().Intersects(z['bbox']):continue
   ck=(u,layer)
   if ck not in shape_cache:shape_cache[ck]=conductor_polygons(q,layer)
   low,high,meta=shape_cache[ck]
   if high.Area()==0:continue
   cls,area,upper,shared=classify_contact(low,high,z['poly']);tested+=1
   rec={'component':ci,'island':zi,'object_uuid':u,'net':q.GetNetname(),'layer':b.GetLayerName(layer),'classification':cls,'positive_overlap_mm2':area/1e12,'finite_shared_boundary_mm':shared,'drill_excluded':meta['drill_excluded']}
   if cls in ['positive_area','finite_shared_boundary']:positive.append(rec);pair_cache[key]=True;return True
   if cls!='disjoint':ambiguous.append(rec)
  pair_cache[key]=False;return False
 def island_contact(i,j):
  key=tuple(sorted((i,j)))
  if key in island_cache:return island_cache[key]
  a,z=units[i],units[j]
  if a['net']!=z['net']or a['layer']!=z['layer']or not a['bbox'].Intersects(z['bbox']):island_cache[key]=False;return False
  cls,area,upper,shared=classify_contact(a['poly'],a['poly'],z['poly']);ok=cls in ['positive_area','finite_shared_boundary'];island_cache[key]=ok
  if ok:island_edges.append({'a':i,'b':j,'classification':cls,'positive_overlap_mm2':area/1e12,'finite_shared_boundary_mm':shared})
  return ok
 results={}
 for net,(ref,pin)in ROOTS.items():
  roots=[u for u,q in pads.items()if q.GetNetname()==net and q.GetParentFootprint().GetReference()==ref and q.GetNumber()==pin];assert roots
  target=[c['index']for c in comps if c['net']==net];zs=[z['index']for z in units if z['net']==net];visited=set();todo=[('component',owner[u])for u in roots]
  print('SOURCE',net,'components',len(target),'islands',len(zs),'elapsed',time.time()-start,flush=True)
  while todo:
   if all(('component',ci)in visited for ci in target):break
   kind,i=todo.pop()
   if(kind,i)in visited:continue
   visited.add((kind,i))
   if kind=='component':
    for zi in zs:
     if('island',zi)not in visited and component_contact(i,zi):todo.append(('island',zi))
   else:
    for ci in target:
     if('component',ci)not in visited and component_contact(ci,i):todo.append(('component',ci))
    for zi in zs:
     if zi!=i and('island',zi)not in visited and island_contact(i,zi):todo.append(('island',zi))
  un=[comps[ci]for ci in target if('component',ci)not in visited];reachable=[q for ci in target if('component',ci)in visited for q in comps[ci]['pads']];unpads=[q for c in un for q in c['pads']]
  results[net]={'root_ref_pin':[ref,pin],'total_physical_pad_count':len(reachable)+len(unpads),'reached_physical_pad_count':len(reachable),'unreached_physical_pad_count':len(unpads),'all_populated_pads_reached':not unpads,'all_scoped_copper_components_reached':not un,'unreached_populated_pads':unpads,'unreached_components':[{'index':c['index'],'classification':c['classification'],'pads':c['pads'],'object_uuids':c['object_uuids']}for c in un],'reached_component_indices':[ci for ci in target if('component',ci)in visited],'reached_island_indices':[zi for zi in zs if('island',zi)in visited]}
  print('DONE',net,'reached',len(reachable),'/',len(reachable)+len(unpads),'contacts_tested',tested,'elapsed',time.time()-start,flush=True)
 critical=set(ROOTS)|{'VBUS','XIN','XOUT','XTAL_OUT'};native=None
 if drc_path:
  drc=json.load(open(drc_path));records=[]
  for i,item in enumerate(drc['unconnected_items']):
   ids=[q['uuid']for q in item['items']];assert all(u in raw for u in ids);nets=sorted({raw[u]['intended_net']for u in ids});forbidden=any(n in critical or n.startswith(('QSPI_','USB_','VREG_'))for n in nets);records.append({'index':i,'raw_intended_nets':nets,'forbidden_critical_open':forbidden,'uuids':ids})
  native={'report_sha256':hashfile(drc_path),'all_open_items':len(records),'forbidden_open_count':sum(q['forbidden_critical_open']for q in records),'all_items_resolved_to_raw_intended_net':True,'items':records,'hard_violations':sum(q['severity']=='error'for q in drc['violations'])}
 assert before==hashfile(path)and pro_before==hashfile(pro);identity('final_no_mutation')
 r={'board':str(path),'board_sha256':before,'project_sha256':pro_before,'helper_sha256':helper_sha_before,'complete':True,'coarse_positive_only':True,'polygonization_error_nm':1000,'negative_requires_fine_refinement':True,'read_only_no_refill_no_save_no_net_relabel':True,'source_results':results,'positive_contacts':positive,'island_positive_contacts':island_edges,'nonpositive_contact_candidates':ambiguous,'native_open_guard':native,'method':'Conservative positive-source witness: root-driven graph traversal may stop once every scoped conductor component has a proved source path; remaining island-only graph is not exhaustively classified. Negative coarse results require finer refinement before a disconnection claim. Positive native lower copper intersection or exact integer finite shared boundary only, actual drill holes subtracted, 1000nm native ERROR_INSIDE conductor / ERROR_OUTSIDE drill bounds; positive contact between conservative copper subsets proves actual contact without epsilon expansion; NO Unfracture, NO spatial clipping. Memoized primitive-line indexing preserves the original collinearity/overlap predicate. Pad-free copper components included. This is a source witness, not powered qualification.','islands':[{k:(b.GetLayerName(v)if k=='layer'else v)for k,v in z.items()if k not in ['poly','bbox']}for z in units],'components':comps,'tested_conductor_contacts':tested,'tested_component_island_pairs':len(pair_cache),'tested_island_pairs':len(island_cache),'all13_populated_source_graphs_pass':all(x['all_populated_pads_reached']for x in results.values()),'all13_strict_copper_source_graphs_pass':all(x['all_scoped_copper_components_reached']for x in results.values()),'combined_contract_pass':all(x['all_scoped_copper_components_reached']for x in results.values())and native is not None and native['forbidden_open_count']==0 and native['hard_violations']==0,'elapsed_seconds':time.time()-start}
 assert hashfile(__file__)==helper_sha_before;Path(out_path).write_text(json.dumps(r,indent=2));print('COMPLETE',before,r['elapsed_seconds'],flush=True);return r
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('board');ap.add_argument('output');ap.add_argument('--native-drc');ap.add_argument('--expected-sha256');args=ap.parse_args();run(args.board,args.output,args.native_drc,args.expected_sha256)
