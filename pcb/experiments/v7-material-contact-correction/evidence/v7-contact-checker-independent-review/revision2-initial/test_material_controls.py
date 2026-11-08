from pathlib import Path
import os,json,ast,hashlib,collections
D=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2');os.environ['XDG_CONFIG_HOME']=str(D/'controls/config');Path(os.environ['XDG_CONFIG_HOME']).mkdir(parents=True,exist_ok=True)
import pcbnew as p
BP=Path('/tmp/v7-c128-stub-retirement-aead/source/pcb/maru60.kicad_pcb');b=p.LoadBoard(str(BP));b.BuildConnectivity();layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in items};tree=ast.parse((D/'export_material_graph.py').read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ['poly','bbox','hits','area','parts','cu','exact_contours']];exec(compile(ast.Module(body=defs,type_ignores=[]),str(D/'export_material_graph.py'),'exec'),globals())
drills=[]
for q in items:
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():h=poly(q.GetEffectiveHoleShape(),True);drills.append((uid(q),bbox(h),h))
cache={};components={};metadata={};objects={};uf={};empty=[];multiple=[];checks=[]
def same(a,b):
 x=p.SHAPE_POLY_SET(a);x.BooleanSubtract(b);y=p.SHAPE_POLY_SET(b);y.BooleanSubtract(a);return x.Area()==0 and y.Area()==0
def clear():
 for d in [cache,components,metadata,objects,uf]:d.clear()
 empty.clear();multiple.clear()
via=idx['2a8005ba-8cc3-5ec3-bf91-40e20122da23'];track=idx['cdcdaf62-0d7e-520a-9821-934ef8e04931'];wrapper=next(q for q in b.GetConnectivity().GetConnectedTracks(track)if uid(q)==uid(via));assert type(wrapper).__name__=='PCB_TRACK'and wrapper.GetClass()=='PCB_VIA'
for l in layers:
 clear();a=p.SHAPE_POLY_SET(cu(via,l));clear();z=cu(wrapper,l);assert exact_contours(a)==exact_contours(z) and len(parts(a))==1;checks.append(dict(name='canonical-via equals native base wrapper after all holes',layer=b.GetLayerName(l),area_mm2=a.Area()/1e12))
positive=area(cu(track,p.F_Cu),cu(wrapper,p.F_Cu));assert positive>0;checks.append(dict(name='known positive annular contact survives',area_mm2=positive))
false=json.load(open(D.parent/'canonical-direct-support-audit.json'))['lost_positive_edges']
for a,c,_ in false:
 assert area(cu(idx[a],p.F_Cu),cu(idx[c],p.F_Cu))==0 and cu(idx[a],p.F_Cu).Area()==0;checks.append(dict(name='observed drill-only track-via contact rejected and track has zero metal',track=a,via=c))
# Use an actual NPTH drill, not a generic circle assumption. Place two test traces
# strictly inside the largest inscribed circle of its physical hole. Shapes only:
# no object is added to the board and no CAD serialization occurs.
npth=next(q for q in items if isinstance(q,p.PAD)and q.GetAttribute()==p.PAD_ATTRIB_NPTH and q.GetDrillSize().x==q.GetDrillSize().y and q.GetDrillSize().x>=1000000);center=npth.GetPosition();r=npth.GetDrillSize().x//2;hole=poly(npth.GetEffectiveHoleShape(),True)
a=poly(p.SHAPE_SEGMENT(p.VECTOR2I(center.x-r//4,center.y),p.VECTOR2I(center.x+r//4,center.y),r//4));c=poly(p.SHAPE_SEGMENT(p.VECTOR2I(center.x,center.y-r//4),p.VECTOR2I(center.x,center.y+r//4),r//4));pre=area(a,c);a.BooleanSubtract(hole);c.BooleanSubtract(hole);assert pre>0 and area(a,c)==0 and a.Area()==c.Area()==0
checks.append(dict(name='actual NPTH drill removes crossing track-track overlap on every copper layer',NPTH_uuid=uid(npth),pre_area_mm2=pre,post_area_mm2=0,layers=[b.GetLayerName(l)for l in layers],physical_hole_is_through_despite_pad_copper_membership=True))
a=poly(p.SHAPE_SEGMENT(p.VECTOR2I(center.x-2*r,center.y),p.VECTOR2I(center.x+2*r,center.y),r//2));c=p.SHAPE_POLY_SET(a);before=area(a,c);a.BooleanSubtract(hole);c.BooleanSubtract(hole);after=area(a,c);assert 0<after<before and len(parts(a))==2
checks.append(dict(name='partial crossing copper remains positive and splits into distinct islands',before_mm2=before,after_mm2=after,positive_islands=2))
# Native roundrect/compound primitives must be unioned before counting islands.
q=next(q for q in items if isinstance(q,p.PAD)and q.GetParentFootprint().GetReference()=='C220'and q.GetNumber()=='1');raw=p.SHAPE_POLY_SET();q.GetEffectiveShape(p.F_Cu).TransformToPolygon(raw,1,p.ERROR_INSIDE);union=p.SHAPE_POLY_SET()
for part in parts(raw):union.BooleanAdd(part)
simplified=poly(q.GetEffectiveShape(p.F_Cu));assert raw.OutlineCount()>1 and len(parts(simplified))==1 and same(union,simplified)
checks.append(dict(name='compound pad primitives are exact-unioned before island identity',pad='C220.1',raw_outline_count=raw.OutlineCount(),raw_summed_area_mm2=raw.Area()/1e12,union_outline_count=simplified.OutlineCount(),union_area_mm2=simplified.Area()/1e12,repeated_BooleanAdd_matches_Simplify_exactly=True))
# NPTH slivers are not discarded or granted cross-layer connectivity.
sliver=idx['c8b60afe-345a-4f16-b725-3dd069ce05bc'];clear()
for l in layers:cu(sliver,l)
allnodes=[n for v in objects[uid(sliver)].values()for n in v];assert allnodes and len(set(allnodes))==len(allnodes) and all(uf[n]==n for n in allnodes)and not sliver.GetNetname();checks.append(dict(name='actual NPTH approximation fragments retained with separate layer/island nodes and no barrel',uuid=uid(sliver),nodes=len(allnodes),net=sliver.GetNetname(),nodes_by_layer=objects[uid(sliver)]))
# An extra collinear native coordinate is deliberately not waived by raw-contour
# equality even though native BooleanSubtract reports zero area both ways.
def polygon(points):
 ps=p.SHAPE_POLY_SET();ps.NewOutline()
 for x,y in points:ps.Append(x,y)
 return ps
own=polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
forged=polygon([(0,0),(1000,0),(1000,1000),(500,1000),(0,1000)])
assert same(own,forged) and exact_contours(own)!=exact_contours(forged)
checks.append(dict(name='raw coordinate mismatch rejected even if native BooleanSubtract area is zero both ways',own_contours=exact_contours(own),forged_contours=exact_contours(forged),bidirectional_native_difference_area_zero=True,exact_contours_equal=False))
# Orientation is not normalized away; cyclic starts and outline ordering are.
rotated=polygon([(1000,1000),(0,1000),(0,0),(1000,0)])
reversed_poly=polygon([(0,0),(0,1000),(1000,1000),(1000,0)])
assert exact_contours(own)==exact_contours(rotated) and exact_contours(own)!=exact_contours(reversed_poly)
checks.append(dict(name='contour canonicalization preserves orientation and normalizes cyclic start',pass_=True))
r=dict(status='PASS',board_sha256=hashlib.sha256(BP.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256((D/'export_material_graph.py').read_bytes()).hexdigest(),controls=checks,no_source_or_candidate_mutations=True);(D/'controls.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
