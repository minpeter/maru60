from pathlib import Path
import json,hashlib,re,subprocess,collections,shutil
import pcbnew as p
R=Path('/workspace/shared/maru60-resume'); O=R/'continuation-fa96a7c/usb-independent'; S=R/'selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype'; C=R/'continuation-fa96a7c/usb-stub'
u='b04e3a6d-1e98-43d1-9b10-58c23321ca28';v='ba0e0532-1586-4050-a390-d87dcee11d2c';f='cc183bf5-15f3-5270-ae14-886f402cad67';bk='a963e830-796c-53b3-b9de-ef49be1314bc'
H=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
sa=S/'pcb/maru60.kicad_pcb';ca=C/'pcb/maru60.kicad_pcb';hs=H(sa);hc=H(ca)
assert hs=='88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e';assert hc=='41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5'
r={'source_sha256':hs,'candidate_sha256':hc,'native_version':p.GetBuildVersion()}
a=sa.read_bytes();b=ca.read_bytes();pat=rb'\t\(segment\n(?:(?!\n\t\)).)*'+u.encode()+rb'(?:(?!\n\t\)).)*\n\t\)\n';match=list(re.finditer(pat,a,re.S));assert len(match)==1;assert a[:match[0].start()]+a[match[0].end():]==b
r['raw_byte_identity_except_exact_one_segment']=True;r['deleted_block']=match[0].group().decode()
files=lambda d:{str(x.relative_to(d)):H(x)for x in d.rglob('*')if x.is_file()};sf=files(S/'pcb');cf=files(C/'pcb');assert sf.keys()==cf.keys()and len(cf)==58;assert[k for k in sf if sf[k]!=cf[k]]==['maru60.kicad_pcb'];r['project_files']=58
# Independent native runs, no mutation or refill of submitted CAD.
def run(tag,args):
 with (O/(tag+'.log')).open('w')as log:subprocess.run([str(R/'run-kicad.sh')]+list(map(str,args)),stdout=log,stderr=subprocess.STDOUT,check=True)
for tag,path in [('source',sa),('candidate',ca)]:run(tag,['kicad-cli','pcb','drc','--format','json','--schematic-parity','-o',O/(tag+'-drc.json'),path])
run('erc',['kicad-cli','sch','erc','--format','json','-o',O/'erc.json',C/'pcb/maru60.kicad_sch'])
da=json.loads((O/'source-drc.json').read_text());db=json.loads((O/'candidate-drc.json').read_text());canon=lambda xs:{json.dumps(x,sort_keys=True)for x in xs};removed=canon(da['violations'])-canon(db['violations']);assert not canon(db['violations'])-canon(da['violations']);assert len(removed)==1;rr=json.loads(next(iter(removed)));assert rr['type']=='track_dangling' and u in str(rr);assert len(da['unconnected_items'])==len(db['unconnected_items'])==9;assert not da['schematic_parity']and not db['schematic_parity'];assert not any(x.get('violations')for x in json.loads((O/'erc.json').read_text())['sheets']);r['native']={'warnings':[len(da['violations']),len(db['violations'])],'opens':[9,9],'removed':rr,'parity':0,'erc':0}
# Recompute connected components from hash-bound material edge/barrel evidence, not its stored roots.
gs=[json.loads((d/'qa/material-graph.json').read_text())for d in [S,C]];assert[g['board_sha256']for g in gs]==[hs,hc]
def components(g,remove=False):
 ns={n for n,x in g['material_nodes'].items()if not(remove and x.get('uuid')==u)};adj={n:set()for n in ns}
 edges=[e[:2]for e in g['material_edges']]
 for bar in g['barrel_joins']:edges.extend(zip(bar['nodes'],bar['nodes'][1:]))
 for x,y in edges:
  if x in ns and y in ns:adj[x].add(y);adj[y].add(x)
 root={};parts=[]
 while ns:
  start=next(iter(ns));todo=[start];seen={start}
  for n in todo:
   for z in adj[n]-seen:seen.add(z);todo.append(z)
  for n in seen:root[n]=len(parts)
  parts.append(frozenset(seen));ns-=seen
 return parts,root
parts0,roots0=components(gs[0]);pa,ra=components(gs[0],True);pb,rb=components(gs[1]);assert set(pa)==set(pb);assert {frozenset(n for n in x if gs[0]['material_nodes'][n].get('uuid')!=u)for x in parts0}==set(pa)
retained=set(gs[1]['material_nodes']);edge=lambda g:{tuple(e[:2]):e[2:]for e in g['material_edges']if set(e[:2])<=retained};assert edge(gs[0])==edge(gs[1]);assert gs[0]['pad_inventory']==gs[1]['pad_inventory'];assert gs[0]['guard_failing_material_edges']==gs[1]['guard_failing_material_edges'];assert len(gs[1]['guard_failing_material_edges'])==51
# Native representative-to-entire-pad-component pairs using freshly recomputed roots.
def opens(g,roots,dr):
 objects=collections.defaultdict(set);pads=collections.defaultdict(set)
 for n,x in g['material_nodes'].items():
  if x.get('uuid'):objects[x['uuid']].add(roots[n])
 for uid in g['pad_inventory']:
  assert len(objects[uid])==1;pads[next(iter(objects[uid]))].add(uid)
 pairs=[]
 for row in dr['unconnected_items']:
  pp=[]
  for item in row['items']:
   rs=objects[item['uuid']];assert len(rs)==1;pp.append(tuple(sorted(pads[next(iter(rs))])))
  assert len(pp)==2 and pp[0]!=pp[1];pairs.append(tuple(sorted(pp)))
 return sorted(pairs)
assert opens(gs[0],roots0,da)==opens(gs[1],rb,db)
r['material_graph']={'fresh_geometry_export':False,'scope':'Independent components/edges/open-pad-pairs recomputed from PCB-hash-bound source and candidate exports; fresh junction geometry below.','retained_vertices':len(retained),'components':len(pb),'exact_retained_edges':len(edge(gs[1])),'pad_count':len(gs[1]['pad_inventory']),'physical_open_pairs_equal':True,'guard_diagnostics_unchanged':51}
# Fresh independent all-drill-subtracted stub and active annular junction scan.
board=p.LoadBoard(str(sa));items=list(board.GetTracks())+[q for fp in board.GetFootprints()for q in fp.Pads()];ix={q.m_Uuid.AsString():q for q in items}
def poly(shape,outside=False):
 z=p.SHAPE_POLY_SET();shape.TransformToPolygon(z,1,p.ERROR_OUTSIDE if outside else p.ERROR_INSIDE);z.Simplify();return z
holes=p.SHAPE_POLY_SET();hole_count=0
for q in items:
 if isinstance(q,(p.PCB_VIA,p.PAD))and q.HasHole():holes.Append(poly(q.GetEffectiveHoleShape(),True));hole_count+=1
holes.Simplify()
def cu(q,l):
 z=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l));z.BooleanSubtract(holes);return z
def inter(x,y):
 z=p.SHAPE_POLY_SET();z.BooleanIntersection(x,y);return z
stub=cu(ix[u],p.F_Cu);contacts=[]
for q in items:
 if q==ix[u]or not q.IsOnLayer(p.F_Cu):continue
 shape=cu(q,p.F_Cu) if q.GetBoundingBox().Intersects(stub.BBox()) else None
 if shape is not None:
  z=inter(stub,shape)
  if z.Area()or z.OutlineCount():contacts.append({'uuid':q.m_Uuid.AsString(),'area_mm2':z.Area()/1e12})
zonecontacts=[]
for z in board.Zones():
 if z.GetIsRuleArea()or not z.IsOnLayer(p.F_Cu):continue
 shape=p.SHAPE_POLY_SET(z.GetFilledPolysList(p.F_Cu));shape.BooleanSubtract(holes);hit=inter(stub,shape)
 if hit.Area()or hit.OutlineCount():zonecontacts.append(z.m_Uuid.AsString())
assert [c['uuid']for c in contacts]==[v]and not zonecontacts
patches=[]
for uid,l in [(f,p.F_Cu),(bk,p.B_Cu)]:
 x,y=cu(ix[uid],l),cu(ix[v],l);area=inter(x,y).Area()/1e12;x.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);y.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);guard=inter(x,y).Area()/1e12;assert area>0 and guard>0;patches.append({'uuid':uid,'layer':board.GetLayerName(l),'area_mm2':area,'guarded_2nm_each_mm2':guard})
r['fresh_junction']={'holes_subtracted':hole_count,'sole_stub_contacts':contacts,'zone_contacts':zonecontacts,'retained_active_via_contacts':patches}
# Cold refill only the independent copied unit.
shutil.copytree(C/'pcb',O/'cold-pcb');cold=O/'cold-pcb';before=files(cold);cb=p.LoadBoard(str(cold/'maru60.kicad_pcb'));cb.BuildConnectivity();p.ZONE_FILLER(cb).Fill(cb.Zones());p.SaveBoard(str(cold/'maru60.kicad_pcb'),cb);assert before==files(cold);r['cold_refill_all_58_files_exact']=True
assert H(sa)==hs and H(ca)==hc;r['submitted_CAD_unchanged']=True;r['verdict']='PASS bounded one-segment cleanup only; no selection or fabrication/SI qualification';(O/'review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
