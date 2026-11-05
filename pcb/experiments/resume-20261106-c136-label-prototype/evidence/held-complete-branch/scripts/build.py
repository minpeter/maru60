from pathlib import Path
import json,hashlib,collections,pcbnew as p
R=Path('/workspace/shared/maru60-resume');S=R/'continuation-c782/combined27fix2';D=R/'continuation-9d787/branch4v';bp=S/'pcb/maru60.kicad_pcb';before=hashlib.sha256(bp.read_bytes()).hexdigest();x=json.loads((S/'qa/material-graph.json').read_text());b=p.LoadBoard(str(bp));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];ix={q.m_Uuid.AsString():q for q in items};stub='acf57724-d322-4087-84ab-2893c779cea3';rail='05a61be2-0243-4f1b-be73-9b2474fa2d93';via='83c3c335-9252-48a7-a6b9-33be2a34353e'
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
for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
 cu=copper(ix[via],l);contacts=[]
 for v,q in ix.items():
  if v==via or not q.IsOnLayer(l) or not q.GetBoundingBox().Intersects(cu.BBox()):continue
  hit=overlap(cu,copper(q,l))
  if hit.Area()>0:contacts.append({'uuid':v,'net':q.GetNetname(),'area_mm2':hit.Area()/1e12,'outlines':hit.OutlineCount()})
 zones=[]
 for q in b.Zones():
  if q.GetIsRuleArea()or not q.IsOnLayer(l):continue
  z=p.SHAPE_POLY_SET(q.GetFilledPolysList(l));z.BooleanSubtract(holes);hit=overlap(cu,z)
  if hit.Area()>0:zones.append({'uuid':q.m_Uuid.AsString(),'area_mm2':hit.Area()/1e12,'outlines':hit.OutlineCount()})
 expected={rail}if l==p.F_Cu else {'495170b7-a1dd-4ce1-a342-da4842fa597e','ec862796-4c8c-41ec-8cd8-90ffc1fdbe4e'}if l==p.B_Cu else set()
 assert {c['uuid']for c in contacts}==expected and not zones
 rows.append({'layer':b.GetLayerName(l),'contacts':contacts,'zone_contacts':zones})
ids=['495170b7-a1dd-4ce1-a342-da4842fa597e','ec862796-4c8c-41ec-8cd8-90ffc1fdbe4e','63b6ad78-ea99-409c-ae95-f861249c5bf6'];direct=[]
for i,a in enumerate(ids):
 for c in ids[i+1:]:
  ca,cc=copper(ix[a],p.B_Cu),copper(ix[c],p.B_Cu);hit=overlap(ca,cc);ca.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);cc.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);guard=overlap(ca,cc);assert hit.Area()>0 and guard.Area()>0
  direct.append({'a':a,'b':c,'area_mm2':hit.Area()/1e12,'guarded_area_mm2':guard.Area()/1e12})
(D/'qa/preedit-via-proof.json').write_text(json.dumps({'source_sha256':before,'exhaustive_via_contacts':rows,'retained_BCu_direct_contacts':direct,'interpretation':'After deleting both F.Cu leaves via has only B.Cu contacts; every pair among rail, TP3 lead and TP3 pad directly contacts without via annulus. Via hole removal may alter surrounding fill: not yet qualified.'},indent=2))
import shutil,re
assert not (D/'pcb').exists();shutil.copytree(S/'pcb',D/'pcb');text=bp.read_text()
for u in [stub,rail,via]:
 pat=r'\n\t\((?:segment|via)\s.*?\n\t\)';ms=[m for m in re.finditer(pat,text,re.S)if u in m.group()];assert len(ms)==1;m=ms[0];text=text[:m.start()]+text[m.end():]
cp=D/'pcb/maru60.kicad_pcb';cp.write_text(text);cb=p.LoadBoard(str(cp));cb.BuildConnectivity();p.ZONE_FILLER(cb).Fill(cb.Zones());p.SaveBoard(str(cp),cb);assert hashlib.sha256(bp.read_bytes()).hexdigest()==before
(D/'qa/build.json').write_text(json.dumps({'source_sha256':before,'candidate_sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'removed':[stub,rail,via]},indent=2))
