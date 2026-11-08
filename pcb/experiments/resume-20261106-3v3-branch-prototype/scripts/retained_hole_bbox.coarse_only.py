from pathlib import Path
import json,pcbnew as p
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-97d9eb7/stub3v3';S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype';b=p.LoadBoard(str(S/'pcb/maru60.kicad_pcb'));rm=set(json.loads((D/'qa/build.json').read_text())['removed']);items={q.m_Uuid.AsString():q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};via=items['0826a4b6-5567-52ab-a787-b898d20d23ac'];hole=p.SHAPE_POLY_SET();via.GetEffectiveHoleShape().TransformToPolygon(hole,1,p.ERROR_OUTSIDE);hole.Simplify();hb=hole.BBox();rows=[]
for u,q in items.items():
 if u in rm:continue
 for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if not q.IsOnLayer(l):continue
  z=p.SHAPE_POLY_SET();shape=p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l);shape.TransformToPolygon(z,1,p.ERROR_INSIDE);z.Simplify();bb=z.BBox();separate=bb.GetRight()<hb.GetX()or bb.GetX()>hb.GetRight()or bb.GetBottom()<hb.GetY()or bb.GetY()>hb.GetBottom();rows.append(dict(uuid=u,layer=b.GetLayerName(l),bbox_nm=[bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()],strictly_disjoint_from_removed_hole_bbox=separate))
def contours(ps):
 def ring(r):
  v=[(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
  if not v:return ()
  low=min(v);return min(tuple(v[i:]+v[:i])for i,x in enumerate(v)if x==low)
 return tuple(sorted((ring(ps.COutline(i)),tuple(sorted(ring(ps.CHole(i,h))for h in range(ps.HoleCount(i)))))for i in range(ps.OutlineCount())))
cb=p.LoadBoard(str(D/'pcb/maru60.kicad_pcb'));zz=lambda board:{(z.m_Uuid.AsString(),l):contours(z.GetFilledPolysList(l))for z in board.Zones()if not z.GetIsRuleArea()for l in [p.F_Cu,p.B_Cu]if z.IsOnLayer(l)};za,zc=zz(b),zz(cb);assert za==zc
x=dict(outer_zone_exact_serialized_contours_equal=True,outer_zone_rows=len(za),removed_hole_bbox_nm=[hb.GetX(),hb.GetY(),hb.GetRight(),hb.GetBottom()],rows=rows,pass_all_disjoint=all(r['strictly_disjoint_from_removed_hole_bbox']for r in rows));(D/'qa/retained-hole-bbox-proof.json').write_text(json.dumps(x,indent=2)+'\n');print('rows',len(rows),'intersecting',[r for r in rows if not r['strictly_disjoint_from_removed_hole_bbox']]);assert x['pass_all_disjoint']
