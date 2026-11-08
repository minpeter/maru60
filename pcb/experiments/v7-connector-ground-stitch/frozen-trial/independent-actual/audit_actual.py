#!/usr/bin/python3
"""Actual one-via contract binding; read-only and fail closed, no R2 export duplication."""
import os,sys,json,hashlib,re,math,time
from pathlib import Path
if not __debug__ or sys.flags.optimize!=0 or os.environ.get('PYTHONOPTIMIZE','')not in('','0'):raise SystemExit('Actual contract audit requires assertions; optimized Python forbidden')
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parent;P=W/'v7-connector-ground-contract-c770';CON=P/'CONSTRUCTION_CONTRACT.json';h=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text());assert h(CON)=='c58baac31c087ddd115fb5ccbe7953ced52d8469c0efe675b2184ea00ff7d7a5';c=read(CON);S=Path(c['source']['board_path']);B=Path('/tmp/v7-connector-gnd-stitch-c770/filled/pcb/maru60.kicad_pcb');BS='aaafc033c6e9809afcb189290c3740157b7ab5596aaa0867e581f08d89807eca';assert h(S)==c['source']['board_sha256']and h(B)==BS;assert h(B.with_suffix('.kicad_pro'))==c['source']['project_sha256'];assert not B.with_suffix('.kicad_dru').exists()
for n,x in c['evidence_hashes'].items():assert h(P/n)==x,(n,'changed frozen input')
assert h(c['source']['active_material_helper_path'])==c['source']['active_material_helper_sha256'];assert h(c['source']['R2_graph_path'])==c['source']['R2_graph_sha256'];g=read(c['source']['R2_graph_path'])
# Independent exact raw top-level preservation, including every saved zone block.
def children(s):
 depth=0;quoted=False;escape=False;start=None;out=[]
 for i,ch in enumerate(s):
  if quoted:
   if escape:escape=False
   elif ch=='\\':escape=True
   elif ch=='"':quoted=False
   continue
  if ch=='"':quoted=True
  elif ch=='(':
   depth+=1
   if depth==2:start=i
  elif ch==')':
   if depth==2:out.append(s[start:i+1])
   depth-=1
 assert depth==0 and not quoted;return out
old=children(S.read_text());new=children(B.read_text());vu=c['only_construction_change']['uuid'];nv=[x for x in new if '(uuid "'+vu+'")'in x];assert len(nv)==1 and nv[0].startswith('(via');assert [x for x in new if x!=nv[0]]==old
os.environ['XDG_CONFIG_HOME']=str(D/'xdg/config');os.environ['XDG_CACHE_HOME']=str(D/'xdg/cache')
print('Raw source preservation passed; loading actual board',flush=True)
import pcbnew as p
assert p.GetBuildVersion()==c['source']['native_version'];b=p.LoadBoard(str(B));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];assert list(b.GetEnabledLayers().CuStack())==layers;uid=lambda q:q.m_Uuid.AsString();items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];v=next(q for q in items if uid(q)==vu);assert isinstance(v,p.PCB_VIA)and v.GetViaType()==p.VIATYPE_THROUGH;pt=v.GetPosition();assert (pt.x,pt.y)==(17200000,9900000)and v.GetNetname()=='GND'and v.GetNetCode()==83 and v.GetDrillValue()==250000;assert all(v.IsOnLayer(l)and v.GetWidth(l)==500000 for l in layers)
def poly(shape,out=False):
 r=p.SHAPE_POLY_SET();shape.TransformToPolygon(r,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);r.Simplify();return r
def intersect(a,b):
 r=p.SHAPE_POLY_SET();r.BooleanIntersection(a,b);return r
def sub(a,b):
 r=p.SHAPE_POLY_SET(a);r.BooleanSubtract(b);return r
def xor(a,b):
 r=p.SHAPE_POLY_SET(a);r.BooleanXor(b);return r.Area()
def guarded(a,b):
 x=p.SHAPE_POLY_SET(a);y=p.SHAPE_POLY_SET(b);x.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);y.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);return intersect(x,y).Area()/1e12
ownhole=poly(v.GetEffectiveHoleShape(),True);expectedhole=poly(p.SHAPE_CIRCLE(p.VECTOR2I(17200000,9900000),125000),True);assert xor(ownhole,expectedhole)==0
oldholes=p.SHAPE_POLY_SET();newholes=p.SHAPE_POLY_SET();counts={'through_vias':0,'PTH':0,'NPTH':0}
for q in items:
 if isinstance(q,p.PCB_VIA):assert q.GetViaType()==p.VIATYPE_THROUGH and all(q.IsOnLayer(l)for l in layers);typ='through_vias'
 elif isinstance(q,p.PAD)and q.HasHole():assert q.GetAttribute()in[p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH];typ='PTH'if q.GetAttribute()==p.PAD_ATTRIB_PTH else'NPTH'
 else:continue
 counts[typ]+=1;ph=poly(q.GetEffectiveHoleShape(),True);newholes.Append(ph)
 if uid(q)!=vu:oldholes.Append(ph)
print('All actual holes collected',flush=True)
oldholes.Simplify();newholes.Simplify();print('All actual holes simplified',flush=True);assert counts==c['expected_object_counts']['candidate_all_through_drills']
ann={};annrows=[]
for l in layers:
 copper=poly(v.GetEffectiveShape(l));ownann=sub(copper,ownhole);physical=sub(copper,newholes);assert xor(physical,ownann)==0 and physical.OutlineCount()==1 and physical.Area()>0;ann[l]=physical;annrows.append({'layer':b.GetLayerName(l),'width_mm':v.GetWidth(l)/1e6,'physical_annulus_mm2':physical.Area()/1e12,'foreign_drill_annular_cut_mm2':0.})
# Actual loss is source physical copper minus candidate physical copper, not a
# hole-normalized equality that hides real removal. Saved records were raw-equal.
losses=[];contacts=[];anchor='186082bb-d1d7-429b-b059-389234bbb320';root=g['object_material_roots'][anchor][0]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for l in layers:
  if not z.IsOnLayer(l):continue
  print('Zone',uid(z),b.GetLayerName(l),flush=True);saved=z.GetFilledPolysList(l);oldmat=sub(saved,oldholes);actual=sub(saved,newholes);expected=sub(oldmat,ownhole);assert xor(expected,actual)==0;loss=sub(oldmat,actual);gain=sub(actual,oldmat);assert gain.Area()==0
  if l not in[p.In1_Cu,p.In2_Cu]or z.GetNetname()!='GND':assert loss.Area()==0 and xor(oldmat,actual)==0
  else:assert xor(loss,ownhole)==0
  # Exact old physical component area binds the all-hole material to source R2.
  for i in range(oldmat.OutlineCount()):
   part=p.SHAPE_POLY_SET();part.AddOutline(oldmat.COutline(i))
   for k in range(oldmat.HoleCount(i)):part.AddHole(oldmat.CHole(i,k),0)
   if part.Area()>0:
    n='zone:'+uid(z)+':'+str(l)+':'+str(i);assert g['material_nodes'][n]['area_mm2']==part.Area()/1e12
  ar=intersect(actual,ann[l]).Area()/1e12
  if ar>0:
   assert z.GetNetname()=='GND'and l in[p.In1_Cu,p.In2_Cu];assert actual.OutlineCount()==1;node='zone:'+uid(z)+':'+str(l)+':0';assert g['material_roots'][node]==root;ga=guarded(actual,ann[l]);assert ga>0;assert sub(ann[l],actual).Area()==0;contacts.append({'layer':b.GetLayerName(l),'zone_uuid':uid(z),'inherited_source_material_node':node,'overlap_mm2':ar,'guarded_overlap_mm2':ga,'source_J1_root':root,'actual_R2_binding_pending':True})
  losses.append({'zone_uuid':uid(z),'net':z.GetNetname(),'layer':b.GetLayerName(l),'actual_physical_loss_mm2':loss.Area()/1e12,'actual_gain_mm2':gain.Area()/1e12,'expected_physical_material_XOR_nm2':xor(expected,actual),'actual_loss_equals_only_new_drill':loss.Area()>0 and xor(loss,ownhole)==0})
assert len(contacts)==2;assert len([x for x in losses if x['actual_physical_loss_mm2']>0])==2
# Current original shape shadows are unchanged, and checked against actual new hole.
print('Strict physical zone delta and positive annular contacts passed',flush=True)
shadow_checks=0;bad=[];unexpectedcontacts=[]
for q in items:
 if uid(q)==vu:continue
 for l in layers:
  if not q.IsOnLayer(l):continue
  shape=q.GetEffectiveShape(l)
  if l in[p.F_Cu,p.B_Cu]:
   shadow_checks+=1
   if intersect(poly(shape,True),ownhole).Area()>0:bad.append({'uuid':uid(q),'layer':b.GetLayerName(l)})
  # A physically copper-bearing object is a subset of its nominal copper.
  # Most nominal shapes are already disjoint; subtract all holes only if needed.
  nominal_contact=intersect(poly(shape),ann[l])
  if nominal_contact.Area()>0 and sub(nominal_contact,newholes).Area()>0:unexpectedcontacts.append({'uuid':uid(q),'layer':b.GetLayerName(l)})
assert not bad and not unexpectedcontacts
print('Current shadow and actual contact checks passed',flush=True)
# Legacy result is frozen and source-verified; actual native drill polygon equals
# the exact circle used by that audit, so this is a bound reuse, not a fresh export.
legacy=read(P/'legacy_shadow_results.json');assert h(legacy['source_path'])==legacy['source_sha256'];assert legacy['no_intersections'];assert legacy['explicit_retired_U10_Dminus_shadow'][0]['uuid']=='2c517f5c-8f2d-4a2a-9fea-dc1b7376c3cd'
assert h(B)==BS and h(S)==c['source']['board_sha256']
result={'phase':'Actual native geometry and strict material/shadow binding; actual R2 graph and final acceptance still pending','pass_geometry_and_strict_loss':True,'source_sha256':h(S),'candidate_sha256':BS,'candidate_path':str(B),'contract_sha256':h(CON),'all_old_top_level_nodes_byte_exact_ordered':True,'all_saved_zone_blocks_byte_exact':True,'actual_new_via_uuid':vu,'all_layer_annuli':annrows,'actual_through_drill_counts':counts,'physical_zone_deltas':losses,'actual_positive_inner_contacts':contacts,'actual_new_via_to_old_object_contacts':unexpectedcontacts,'current_original_outer_shape_checks':shadow_checks,'current_original_shadow_intersections':bad,'legacy_a9_actual_drill_bound_to_frozen_check':True,'retired_U10_Dminus_actual_drill_bound':legacy['explicit_retired_U10_Dminus_shadow'],'no_CAD_mutation':True,'no_SI_ESD_qualification':True,'input_hashes':{'project':h(B.with_suffix('.kicad_pro')),'source_R2_graph':h(c['source']['R2_graph_path']),'active_R2_helper':h(c['source']['active_material_helper_path'])}}
(D/'actual_geometry.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
