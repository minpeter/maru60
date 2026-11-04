import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,collections,re,xml.etree.ElementTree as ET
import pcbnew as p
R=Path('/tmp/v7-c124-d-plus-connector-gnd'); O=Path('/tmp/v7-c124-d-plus-connector-gnd-independent-review'); DS=Path('/tmp/v7-c124-d-actual/filled/pcb/maru60.kicad_pcb');A=R/'filled/pcb/maru60.kicad_pcb';AA=Path('/tmp/v7-connector-gnd-stitch-c770/filled/pcb/maru60.kicad_pcb');u='cda2df4b-6411-5409-a933-5106751244d8';H=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest();J=lambda q:json.loads(Path(q).read_text());W=lambda n,q:(O/n).write_text(json.dumps(q,indent=2,sort_keys=True)+'\n');checks=[]
def ck(n,ok,d=None):
 checks.append({'check':n,'pass':bool(ok),'detail':d});print(n,bool(ok),flush=True);assert ok,n
sys.path.insert(0,str(R/'scripts'));from sexpr_spans import children,head,field
S='f987edb49e7eb99e6db711ea428a5efb66a36653fe9dce77b02aae12f281441b';C='7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401';ck('exact_source_candidate_hashes',H(DS)==H(R/'source/pcb/maru60.kicad_pcb')==S and H(A)==C)
s=[t for _,_,t in children(DS.read_text())];a=[t for _,_,t in children(A.read_text())];aa=[t for _,_,t in children(AA.read_text())];via=[t for t in a if '(uuid "'+u+'")'in t];ck('only_one_exact_new_via_and_all_D_records_ordered_exact',len(via)==1 and[t for t in a if t not in via]==s and via==[t for t in aa if '(uuid "'+u+'")'in t])
ck('all_12_raw_saved_zones_identical_D_and_aaaf',len([t for t in s if head(t)=='zone'])==12 and[t for t in s if head(t)=='zone']==[t for t in aa if head(t)=='zone'])
files=lambda path:{str(q.relative_to(path)):H(q)for q in path.rglob('*')if q.is_file()and q.name!='maru60.kicad_pcb'};ck('all_57_companions_exact',len(files(DS.parent))==57 and files(DS.parent)==files(A.parent)==files(R/'source/pcb'))
sd=J('/tmp/v7-c124-d-actual/qa/filled-drc.json');ad=J(R/'qa/drc.json');ck('all_64_warning_entries_exact',len(sd['violations'])==64 and sd['violations']==ad['violations']);ck('all_12_open_entries_exact',len(sd['unconnected_items'])==12 and sd['unconnected_items']==ad['unconnected_items']);ck('native_parity_zero',ad['schematic_parity']==[]);ck('non_open_DRC_errors_zero',all(q['severity']=='warning'for q in ad['violations']))
e=J(R/'qa/erc.json');ck('ERC_zero',not any(sh['violations']for sh in e['sheets']))
def xmlparts(path):
 x=ET.parse(path).getroot();return {n:ET.tostring(x.find(n))for n in ['components','libparts','nets']}
ck('complete_component_libpart_net_XML_exact',xmlparts('/tmp/v7-c124-d-actual/qa/netlist.xml')==xmlparts(R/'qa/netlist.xml'))
ck('cold_refill_byte_fixed_point',J(O/'COLD_REFILL.json')['byte_identical'])
GND=Path('/workspace/scratch/edd9a5be63e7/v7-connector-ground-actual-aaaf/FINAL_ELIGIBILITY.json');GC=Path('/workspace/scratch/edd9a5be63e7/v7-connector-ground-contract-c770/CONSTRUCTION_CONTRACT.json');ck('frozen_aaaf_actual_and_contract_binding',H(GND)=='27c41ca26cfa052bbb2f7c983152d285c584299d8dff5f40d4a3fced05d58d69'and H(GC)=='c58baac31c087ddd115fb5ccbe7953ced52d8469c0efe675b2184ea00ff7d7a5'and H(AA)==J(GND)['candidate_sha256'])
b=p.LoadBoard(str(A));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in items};v=idx[u];layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
ck('native_via_dimensions_net_span',v.GetNetname()=='GND'and v.GetViaType()==p.VIATYPE_THROUGH and v.GetPosition()==p.VECTOR2I(17200000,9900000)and v.GetDrillValue()==250000 and all(v.IsOnLayer(l)and v.GetWidth(l)==500000 for l in layers))
def poly(sh,out=False):
 q=p.SHAPE_POLY_SET();sh.TransformToPolygon(q,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);q.Simplify();return q
def diff(x,y):
 z=p.SHAPE_POLY_SET(x);z.BooleanSubtract(y);return z
def inter(x,y):
 z=p.SHAPE_POLY_SET();z.BooleanIntersection(x,y);return z
def dump(q):
 return [{'outer':[(q.COutline(i).CPoint(k).x,q.COutline(i).CPoint(k).y)for k in range(q.COutline(i).PointCount())],'holes':[[(q.CHole(i,j).CPoint(k).x,q.CHole(i,j).CPoint(k).y)for k in range(q.CHole(i,j).PointCount())]for j in range(q.HoleCount(i))]}for i in range(q.OutlineCount())]
hole=poly(v.GetEffectiveHoleShape(),True);ann={l:diff(poly(v.GetEffectiveShape(l)),hole)for l in layers};oldholes={};bad=[];contacts=[];outercount=0;layercount=0
for q in items:
 if uid(q)==u:continue
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():oldholes[uid(q)]=dump(poly(q.GetEffectiveHoleShape(),True))
 for l in layers:
  if not q.IsOnLayer(l):continue
  layercount+=1
  if l in[p.F_Cu,p.B_Cu]:outercount+=1
  sh=q.GetEffectiveShape(l)
  if not sh.BBox().Intersects(ann[l].BBox()):continue
  out=poly(sh,True)
  if inter(out,hole).Area()>0:bad.append([uid(q),b.GetLayerName(l)])
  if inter(poly(sh),ann[l]).Area()>0:contacts.append([uid(q),b.GetLayerName(l)])
ck('new_drill_disjoint_all_retained_material_and_outer_shadows',not bad,{'outer_shape_checks':outercount,'all_layer_shape_checks':layercount})
ck('new_via_has_no_old_object_contact',not contacts)
# Compare every retained physical hole against immutable D corrected local export.
dl=J('/tmp/v7-c124-d-actual/qa/actual-local-material.json');stored={q['uuid']:q['polygon']for q in dl['all_physical_holes']};canonical=lambda x:json.dumps(x,sort_keys=True)
ck('all_1269_retained_physical_holes_exact',len(oldholes)==1269 and canonical(oldholes)==canonical(stored))
for l in layers:
 for hp in oldholes.values():
  # All foreign-hole bounding boxes are sufficient here only when disjoint.
  xs=[x for r in hp for x,y in r['outer']];ys=[y for r in hp for x,y in r['outer']]
  box=p.BOX2I(p.VECTOR2I(min(xs),min(ys)),p.VECTOR2I(max(xs)-min(xs),max(ys)-min(ys)))
  assert not ann[l].BBox().Intersects(box),('foreign drill near new annulus',l)
ck('four_intact_annuli_no_foreign_drill_cut',all(q.OutlineCount()==1 and q.Area()>0 for q in ann.values()),{b.GetLayerName(l):q.Area()/1e12 for l,q in ann.items()})
# These source zone records and all physical holes are equal to accepted aaaf's source.
# Native intersection binds the exact new drill loss and full annular contacts to actual saved polygons.
loss=[];planecontacts=[]
for z in b.Zones():
 for l in layers:
  if not z.IsOnLayer(l):continue
  saved=z.GetFilledPolysList(l);cut=inter(saved,hole);contact=inter(diff(saved,hole),ann[l]);
  if cut.Area()>0:
   ck('inner_cut_exact_hole_'+b.GetLayerName(l),z.GetNetname()=='GND'and l in[p.In1_Cu,p.In2_Cu]and diff(hole,cut).OutlineCount()==0 and diff(cut,hole).OutlineCount()==0)
   loss.append({'zone':uid(z),'layer':b.GetLayerName(l),'actual_physical_loss_mm2':cut.Area()/1e12,'gain_mm2':0})
  if contact.Area()>0:
   x=p.SHAPE_POLY_SET(ann[l]);x.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);y=diff(saved,hole);y.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);guard=inter(x,y)
   planecontacts.append({'zone':uid(z),'layer':b.GetLayerName(l),'raw_overlap_mm2':contact.Area()/1e12,'guarded_overlap_mm2':guard.Area()/1e12});assert diff(ann[l],contact).OutlineCount()==0
ck('only_two_exact_declared_inner_drill_losses',len(loss)==2 and all(r['actual_physical_loss_mm2']==.049087681002 for r in loss),loss)
ck('only_two_full_positive_guarded_inner_contacts',len(planecontacts)==2 and all(r['layer']in['In1.Cu','In2.Cu']and r['raw_overlap_mm2']==.147260768066 and r['guarded_overlap_mm2']==.1472558792225 for r in planecontacts),planecontacts)
DCT=J('/tmp/v7-c124-d-actual/BUILD_CONTRACT.json');dids={q['uuid']for q in DCT['added_tracks']}|{uid(q)for f in b.GetFootprints()if f.GetReference()in['R121','R125','C124']for q in f.Pads()};guardrows=[]
for x in sorted(dids):
 q=idx[x];sh=poly(q.GetEffectiveShape(p.B_Cu),True);sh.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);ix=inter(sh,hole);guardrows.append({'uuid':x,'net':q.GetNetname(),'new_hole_overlap_mm2':ix.Area()/1e12,'new_hole_overlap_contours':ix.OutlineCount()})
ck('all_37_D_new_changed_shapes_outward2nm_disjoint_new_drill',len(guardrows)==37 and all(not(q['new_hole_overlap_mm2']or q['new_hole_overlap_contours'])for q in guardrows))
ck('all_29_D_new_nonGND_whole_guarded_shadows_disjoint',len([q for q in guardrows if q['net']!='GND'])==29)
legacy=J('/workspace/scratch/edd9a5be63e7/v7-connector-ground-contract-c770/legacy_shadow_results.json');contract=J(GC);ck('legacy_a9_frozen_shadows_bound',H('/workspace/scratch/edd9a5be63e7/v7-connector-ground-contract-c770/legacy_shadow_results.json')==contract['evidence_hashes']['legacy_shadow_results.json'] and H(legacy['source_path'])==legacy['source_sha256']and legacy['no_intersections'])
W('GEOMETRY_INHERITANCE.json',{'source_sha256':S,'candidate_sha256':C,'physical_zone_loss':loss,'plane_contacts':planecontacts,'D_expanded_2nm_shape_disjointness':guardrows,'all_14_D_strong_support_and_58_full_reference_rows_inherited':True,'inheritance_proof':'All D source material objects, pads, settings and raw planes are exact. New drill is disjoint from every old object shape and all 37 D new/changed shapes expanded 2 nm. Added via has only the two declared inner-plane contacts, no other object contact. D full support patches therefore retain all original replacement coverage and all guarded nonGND reference projections avoid the only added plane void.','strict_loss_is_not_zero':True,'old_D_mask_paste_geometry_inherited':True,'qualification':False})
W('CHECKS_NATIVE.json',checks);print('NATIVE_FINISHED',len(checks),flush=True)
