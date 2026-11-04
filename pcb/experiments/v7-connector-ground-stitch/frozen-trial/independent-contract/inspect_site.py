#!/usr/bin/python3
"""Read-only prospective via shape checks using every actual through drill.
No board object is added, moved or saved. Geometry predicates accept no loss waiver.
"""
import os,sys,json,hashlib,math,collections,uuid
from pathlib import Path
from fractions import Fraction
if not __debug__ or sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):raise SystemExit('Contract checks require assertions; optimized Python is forbidden')
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parent
os.environ['XDG_CONFIG_HOME']=str(D/'xdg/config');os.environ['XDG_CACHE_HOME']=str(D/'xdg/cache')
import pcbnew as p
B=W/'pcb-v7-recovery-20261104/pcb/experiments/v7-gnd-deadbranch-cleanup/candidate/pcb/maru60.kicad_pcb';H=W/'pcb-v7-recovery-20261104/pcb/tools/export_material_graph.py';G=Path('/tmp/v7-gnd-tail-cleanup-aead/qa/material-graph.json')
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();EXPECTED='c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a';before=sha(B);assert before==EXPECTED;assert sha(G)=='3d174b35c555dcce8b3df1097f664be12e4736cca1f750a005d46441b941452c';graph=json.loads(G.read_text());assert graph['board_sha256']==before and graph['revision']=='v2-all-through-drills-layer-island-material-graph';assert p.GetBuildVersion()==graph['native_version']=='9.0.2+dfsg-1';b=p.LoadBoard(str(B));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];assert list(b.GetEnabledLayers().CuStack())==layers
pt=p.VECTOR2I(17200000,9900000);outer=p.SHAPE_CIRCLE(pt,250000);newhole=p.SHAPE_CIRCLE(pt,125000);uid=lambda q:q.m_Uuid.AsString();items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]
newid=str(uuid.uuid5(uuid.NAMESPACE_URL,'maru60:v7:c770:connector-return-stitch:17.20,9.90'));assert all(uid(q)!=newid for q in items)
def poly(s,out=False):
 q=p.SHAPE_POLY_SET();s.TransformToPolygon(q,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);q.Simplify();return q
def intersection(a,c):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,c);return q
# Exact squared distance to each capsule axis using rational integer arithmetic.
def axis_dist2(h):
 s=h.GetSeg();ax,ay=s.A.x,s.A.y;dx,dy=s.B.x-ax,s.B.y-ay;ux,uy=pt.x-ax,pt.y-ay;v=dx*dx+dy*dy;t=ux*dx+uy*dy
 if not v or t<=0:return Fraction(ux*ux+uy*uy)
 if t>=v:return Fraction((pt.x-s.B.x)**2+(pt.y-s.B.y)**2)
 return Fraction((ux*dy-uy*dx)**2,v)
allholes=p.SHAPE_POLY_SET();hole_rows=[];types=collections.Counter()
for q in items:
 if isinstance(q,p.PCB_VIA):assert q.GetViaType()==p.VIATYPE_THROUGH and all(q.IsOnLayer(l)for l in layers);typ='through_vias'
 elif isinstance(q,p.PAD)and q.HasHole():assert q.GetAttribute()in[p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH];typ='PTH'if q.GetAttribute()==p.PAD_ATTRIB_PTH else'NPTH'
 else:continue
 h=q.GetEffectiveHoleShape();assert isinstance(h,p.SHAPE_SEGMENT);types[typ]+=1;hh=poly(h,True);allholes.Append(hh);d2=axis_dist2(h);rad=Fraction(h.GetWidth(),2)
 required=rad+125000+250000;annular=rad+250000
 hole_rows.append({'uuid':uid(q),'kind':typ,'ref':q.GetParentFootprint().GetReference()if isinstance(q,p.PAD)else None,'hole_edge_clearance_mm':(math.sqrt(float(d2))-float(rad)-125000)/1e6,'exact_hole_to_hole_0p25_pass':d2>required*required,'exact_foreign_hole_disjoint_from_new_annulus':d2>annular*annular,'exact_existing_hole_to_new_copper_0p15_pass':d2>(rad+400000)**2,'axis_distance_squared_nm2':[d2.numerator,d2.denominator]})
allholes.Simplify();assert dict(types)==graph['scope_assumptions']['actual_drill_types'];hole_rows.sort(key=lambda r:r['hole_edge_clearance_mm']);assert all(x['exact_hole_to_hole_0p25_pass']and x['exact_foreign_hole_disjoint_from_new_annulus']and x['exact_existing_hole_to_new_copper_0p15_pass']for x in hole_rows)
# Conservative normal-clearance predicates use native nominal foreign copper.
# Every old outer conductor is also checked against the actual proposed drill.
clear=[];shadow=[];nominal_fail=[];objects_checked=0;old_object_drill_hits=[]
for q in items:
 for l in layers:
  if not q.IsOnLayer(l):continue
  s=q.GetEffectiveShape(l);ln=b.GetLayerName(l);objects_checked+=1
  if s.Collide(newhole,0):old_object_drill_hits.append({'uuid':uid(q),'layer':ln,'net':q.GetNetname()})
  if q.GetNetname()!='GND':
   distance=(s.Distance(pt)-250000)/1e6;fail=bool(s.Collide(outer,150000))
   if distance<3 or fail:clear.append({'uuid':uid(q),'net':q.GetNetname(),'layer':ln,'ref':q.GetParentFootprint().GetReference()if isinstance(q,p.PAD)else None,'nominal_copper_edge_clearance_mm':distance,'native_0p15_clearance_pass':not fail})
   if fail:nominal_fail.append(clear[-1])
  if l in[p.F_Cu,p.B_Cu]:
   fail=bool(s.Collide(newhole,0));distance=(s.Distance(pt)-125000)/1e6
   if distance<3 or fail:shadow.append({'uuid':uid(q),'net':q.GetNetname(),'layer':ln,'drill_to_original_nominal_shadow_mm':distance,'no_intersection':not fail})
assert not old_object_drill_hits;assert not nominal_fail;assert all(x['no_intersection']for x in shadow);clear.sort(key=lambda r:r['nominal_copper_edge_clearance_mm']);shadow.sort(key=lambda r:r['drill_to_original_nominal_shadow_mm'])
# Reconstruct only GND inner materials, exactly as the active R2 helper does.
anchor=next(u for u,x in graph['pad_inventory'].items()if x['ref']=='J1'and x['pad']=='A1');anchor_roots=graph['object_material_roots'][anchor];assert len(anchor_roots)==1;root=anchor_roots[0]
ann=poly(outer);ann.BooleanSubtract(poly(newhole,True));ann.BooleanSubtract(allholes);ann_guard=p.SHAPE_POLY_SET(ann);ann_guard.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
plane_rows=[];zone_drill_losses=[]
for z in b.Zones():
 if z.GetIsRuleArea()or z.GetNetname()!='GND':continue
 for l in layers:
  if not z.IsOnLayer(l):continue
  physical=p.SHAPE_POLY_SET(z.GetFilledPolysList(l));physical.BooleanSubtract(allholes)
  for i in range(physical.OutlineCount()):
   part=p.SHAPE_POLY_SET();part.AddOutline(physical.COutline(i))
   for hi in range(physical.HoleCount(i)):part.AddHole(physical.CHole(i,hi),0)
   if part.Area()<=0:continue
   node='zone:'+uid(z)+':'+str(l)+':'+str(i);record=graph['material_nodes'][node];assert record['area_mm2']==part.Area()/1e12
   loss=intersection(part,poly(newhole,True));zone_drill_losses.append({'layer':b.GetLayerName(l),'node':node,'new_drill_loss_mm2':loss.Area()/1e12})
   if l in[p.F_Cu,p.B_Cu]:assert loss.Area()==0
   overlap=intersection(part,ann);guard=p.SHAPE_POLY_SET(part);guard.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);guard_overlap=intersection(guard,ann_guard)
   if overlap.Area()>0:
    assert graph['material_roots'][node]==root
    missing=p.SHAPE_POLY_SET(ann);missing.BooleanSubtract(part);assert guard_overlap.Area()>0
    if l in[p.In1_Cu,p.In2_Cu]:assert missing.Area()==0
    loss=intersection(part,poly(newhole,True));plane_rows.append({'layer':b.GetLayerName(l),'zone_uuid':uid(z),'physical_material_node':node,'J1_A1_root':root,'exact_R2_component_area_match_mm2':part.Area()/1e12,'annular_overlap_mm2':overlap.Area()/1e12,'annular_missing_mm2':missing.Area()/1e12,'positive_overlap_after_each_2nm_inward_guard_mm2':guard_overlap.Area()/1e12,'new_physical_drill_loss_outside_polygon_mm2':loss.Area()/1e12})
assert {'In1.Cu','In2.Cu'}<={r['layer']for r in plane_rows}
# Ordinary project dimensions are requirements, not manufacturer approval.
assert not B.with_suffix('.kicad_dru').exists();pro=json.loads(B.with_suffix('.kicad_pro').read_text());classes=pro['net_settings']['classes'];assert all(c['clearance']==.15 for c in classes);rules=pro['board']['design_settings']['rules'];assert .5>=rules['min_via_diameter']and .25>=rules['min_through_hole_diameter']and (.5-.25)/2>=rules['min_via_annular_width'];assert rules['min_clearance']==.15 and rules['min_hole_to_hole']==.25
zone_clear=[];keepout=[]
for z in list(b.Zones())+[z for f in b.GetFootprints()for z in f.Zones()]:
 if z.GetIsRuleArea():
  if z.GetDoNotAllowVias():keepout.append({'uuid':uid(z),'intersects_new_via':bool(z.Outline().Collide(outer,0))})
 elif z.GetNetname()!='GND':
  for l in layers:
   if z.IsOnLayer(l)and z.HasFilledPolysForLayer(l):zone_clear.append({'uuid':uid(z),'net':z.GetNetname(),'layer':b.GetLayerName(l),'pass':not bool(z.GetFilledPolysList(l).Collide(outer,150000))})
assert all(not x['intersects_new_via']for x in keepout)and all(x['pass']for x in zone_clear)
board_outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(board_outline);outside=poly(outer,True);outside.BooleanSubtract(board_outline);assert outside.Area()==0
graphics=list(b.GetDrawings())+[q for f in b.GetFootprints()for q in list(f.GraphicalItems())+list(f.GetFields())];copper_graphics=[uid(q)for q in graphics if q.GetLayer()in layers];assert not copper_graphics
edges=[]
for q in b.GetDrawings():
 if q.GetLayer()==p.Edge_Cuts:
  s=q.GetEffectiveShape();edges.append({'uuid':uid(q),'conservative_copper_edge_distance_mm':(s.Distance(pt)-250000)/1e6,'native_0p5_clearance_pass':not bool(s.Collide(outer,500000))})
assert edges and all(x['native_0p5_clearance_pass']for x in edges)

# Current nearest directly rooted two-plane GND vias, not historical guesses.
direct_plane_layers={}
for node,via,ar in graph['zone_edges']:
 if graph['material_nodes'][node]['net']=='GND' and ar>0:direct_plane_layers.setdefault(via,set()).add(graph['material_nodes'][node]['layer'])
qualified=[q for q in b.GetTracks()if isinstance(q,p.PCB_VIA) and q.GetNetname()=='GND'and graph['object_material_roots'].get(uid(q))==[root]and {'In1.Cu','In2.Cu'}<=direct_plane_layers.get(uid(q),set())]
returns=[]
for u in ['f87d754d-9071-487c-b6c8-34eb2f861a77','544a3023-571c-4ba3-b056-b27f573292aa']:
 v=next(q for q in b.GetTracks()if uid(q)==u);pos=v.GetPosition();near=min(qualified,key=lambda q:math.hypot(q.GetPosition().x-pos.x,q.GetPosition().y-pos.y));old=math.hypot(near.GetPosition().x-pos.x,near.GetPosition().y-pos.y)/1e6;new=math.hypot(pt.x-pos.x,pt.y-pos.y)/1e6;returns.append({'signal_via':u,'signal_xy_mm':[pos.x/1e6,pos.y/1e6],'current_nearest_rooted_GND_via':uid(near),'current_nearest_distance_mm':old,'proposed_via_distance_mm':new,'prospective_nearest_distance_mm':min(old,new)})

assert before==sha(B)
result={'status':'Prospective shape contract checks pass; no actual new board via exists yet','source_board':str(B),'board_sha256':before,'graph_path':str(G),'graph_sha256':sha(G),'active_helper_path':str(H),'active_helper_sha256':sha(H),'native_version':p.GetBuildVersion(),'proposed':{'uuid':newid,'net':'GND','xy_mm':[17.2,9.9],'diameter_mm':.5,'drill_mm':.25,'span':['F.Cu','B.Cu'],'nominal_annular_width_mm':.125},'return_distance_geometry':returns,'through_drill_counts':dict(types),'all_holes_checked':len(hole_rows),'nearest_physical_holes':hole_rows[:12],'all_object_layer_checks':objects_checked,'near_foreign_copper':clear[:20],'near_original_object_shadows':shadow[:20],'all_existing_object_drill_intersections':old_object_drill_hits,'all_GND_zone_drill_losses':zone_drill_losses,'copper_graphics_count':len(copper_graphics),'board_outline_new_pad_outside_area_mm2':outside.Area()/1e12,'netclass_clearances':{c['name']:c['clearance']for c in classes},'no_custom_dru':True,'physical_rooted_plane_contacts':plane_rows,'project_sha256':sha(B.with_suffix('.kicad_pro')),'source_counts':{k:graph[k]for k in ['tracks','vias','footprints']},'minimum_board_edge':min(edges,key=lambda r:r['conservative_copper_edge_distance_mm']),'keepout_checks':keepout,'foreign_zone_checks':zone_clear,'normal_project_rules':rules,'no_CAD_mutation':True,'limitations':['No inserted-candidate DRC, refill, graph or acceptance has run.','All-hole R2 source contacts are used; old local/neighbor-hole evidence is not a contact oracle.','No endpoint masks, no allowable small physical loss, and no SI/ESD qualification.','Native polygon representation uses1nm approximation; no1nm loss allowance is applied. Contact acceptance also requires positive overlap after2nm inward guard.']}
(D/'site_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
