from pathlib import Path
import json,hashlib,collections,pcbnew as p
R=Path('/workspace/shared/maru60-resume');S=R/'continuation-c782/combined27fix2';D=R/'continuation-9d787/stub4v';bp=S/'pcb/maru60.kicad_pcb';before=hashlib.sha256(bp.read_bytes()).hexdigest();x=json.loads((S/'qa/material-graph.json').read_text());b=p.LoadBoard(str(bp));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];ix={q.m_Uuid.AsString():q for q in items};stub='acf57724-d322-4087-84ab-2893c779cea3';rail='05a61be2-0243-4f1b-be73-9b2474fa2d93';via='83c3c335-9252-48a7-a6b9-33be2a34353e'
def poly(s,out=False):
 z=p.SHAPE_POLY_SET();s.TransformToPolygon(z,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);z.Simplify();return z
holes=p.SHAPE_POLY_SET()
for q in items:
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():holes.Append(poly(q.GetEffectiveHoleShape(),True))
holes.Simplify()
def copper(q,l):
 z=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l));z.BooleanSubtract(holes);return z
def overlap(a,c):
 z=p.SHAPE_POLY_SET();z.BooleanIntersection(a,c);return z
rows=[]
for u in [stub,rail]:
 cu=copper(ix[u],p.F_Cu);contacts=[]
 for v,q in ix.items():
  if v==u or not q.IsOnLayer(p.F_Cu)or not q.GetBoundingBox().Intersects(cu.BBox()):continue
  hit=overlap(cu,copper(q,p.F_Cu))
  if hit.Area()>0:contacts.append({'uuid':v,'kind':q.GetClass(),'net':q.GetNetname(),'area_mm2':hit.Area()/1e12,'outlines':hit.OutlineCount()})
 zones=[]
 for q in b.Zones():
  if q.GetIsRuleArea()or not q.IsOnLayer(p.F_Cu):continue
  z=p.SHAPE_POLY_SET(q.GetFilledPolysList(p.F_Cu));z.BooleanSubtract(holes);hit=overlap(cu,z)
  if hit.Area()>0:zones.append({'uuid':q.m_Uuid.AsString(),'net':q.GetNetname(),'area_mm2':hit.Area()/1e12,'outlines':hit.OutlineCount()})
 expected={rail}if u==stub else{stub,via};assert {c['uuid']for c in contacts}==expected and not zones
 rows.append({'uuid':u,'exhaustive_all_object_contacts':contacts,'all_zone_contacts':zones})
# Traverse material graph after pruning both proposed retired objects, not native endpoint counts.
nodes=x['material_nodes'];adj=collections.defaultdict(set)
for e in x['material_edges']:
 if any(nodes[n].get('uuid')in[stub,rail]for n in e[:2]):continue
 adj[e[0]].add(e[1]);adj[e[1]].add(e[0])
for bar in x['barrel_joins']:
 for a,c in zip(bar['nodes'],bar['nodes'][1:]):adj[a].add(c);adj[c].add(a)
start=[n for n,v in nodes.items()if v.get('uuid')==via];todo=collections.deque(start);paths={n:[n]for n in start};pads=[]
while todo:
 n=todo.popleft();u=nodes[n].get('uuid')
 if u in x['pad_inventory']:
  pads.append({'pad':x['pad_inventory'][u],'uuid':u,'path':paths[n]});continue
 for c in sorted(adj[n]):
  if c not in paths:paths[c]=paths[n]+[c];todo.append(c)
result={'source_sha256':before,'exhaustive_branch_contacts':rows,'retained_via':via,'first_pad_paths_without_two_tracks':pads,'via_barrel_proof':next(v for v in x['barrel_joins']if v['uuid']==via),'limits':'Read-only topology, no altered-board proof; required via and all B.Cu conductors retained. Real dynamic current distribution/parasitics unmodeled.'};(D/'qa/read-only-branch.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert hashlib.sha256(bp.read_bytes()).hexdigest()==before
