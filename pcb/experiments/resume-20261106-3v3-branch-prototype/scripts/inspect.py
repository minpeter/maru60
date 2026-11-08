from pathlib import Path
import json,pcbnew as p,hashlib,collections
R=Path('/workspace/shared/maru60-resume'); S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype';D=R/'continuation-97d9eb7/stub3v3';bp=S/'pcb/maru60.kicad_pcb';h=hashlib.sha256(bp.read_bytes()).hexdigest();assert h=='2e532c1a16e64a34eafafdfbd5b85c05d70bb12ad9e52924c5cbe024fdc9aa2c';b=p.LoadBoard(str(bp));x=json.loads((S/'qa/material-graph.json').read_text());assert x['board_sha256']==h
items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];ix={q.m_Uuid.AsString():q for q in items}
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
point=lambda v:[v.x/1e6,v.y/1e6]
def describe(q):
 d=dict(uuid=q.m_Uuid.AsString(),kind=q.GetClass(),net=q.GetNetname(),position=point(q.GetPosition()))
 if isinstance(q,p.PCB_TRACK) and not isinstance(q,p.PCB_VIA):d.update(start=point(q.GetStart()),end=point(q.GetEnd()),width_mm=q.GetWidth()/1e6)
 if isinstance(q,p.PAD):d.update(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber())
 return d
rows=[];u='53e7b99f-308f-57ae-9e47-9e779e6b3272';prev=None;seen=set()
while u not in seen:
 seen.add(u);q=ix[u];l=q.GetLayer();cu=copper(q,l);contacts=[]
 for v,t in ix.items():
  if v==u or not t.IsOnLayer(l)or not t.GetBoundingBox().Intersects(cu.BBox()):continue
  hit=overlap(cu,copper(t,l))
  if hit.Area()>0 or hit.OutlineCount()>0:contacts.append(dict(**describe(t),area_mm2=hit.Area()/1e12,contours=hit.OutlineCount()))
 zones=[]
 for z in b.Zones():
  if z.GetIsRuleArea()or not z.IsOnLayer(l):continue
  mat=p.SHAPE_POLY_SET(z.GetFilledPolysList(l));mat.BooleanSubtract(holes);hit=overlap(cu,mat)
  if hit.Area()>0 or hit.OutlineCount()>0:zones.append(dict(uuid=z.m_Uuid.AsString(),net=z.GetNetname(),area_mm2=hit.Area()/1e12,contours=hit.OutlineCount()))
 row=dict(**describe(q),layer=b.GetLayerName(l),contacts=contacts,zones=zones);rows.append(row);print(json.dumps(row),flush=True)
 nexts=[c['uuid']for c in contacts if c['uuid']!=prev]
 if zones or len(nexts)!=1 or isinstance(q,(p.PAD,p.PCB_VIA)):break
 prev,u=u,nexts[0]
result=dict(source_sha256=h,rows=rows,all_holes_subtracted=True,all_objects_and_zones_scanned=True,source_unchanged=hashlib.sha256(bp.read_bytes()).hexdigest()==h)
(D/'qa/branch-trace.json').write_text(json.dumps(result,indent=2)+'\n')
