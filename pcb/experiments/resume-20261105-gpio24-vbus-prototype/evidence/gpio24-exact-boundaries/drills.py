import pcbnew as p,json,math
from pathlib import Path
R=Path('/workspace/shared/maru60-resume');O=R/'header-exact-review';d=json.loads((O/'boundary-delta.json').read_text());centers=[(97250000,37450000),(97250000,37550000),(92350000,37750000),(105800000,37500000)]
es=[(a,b)for v in d['4'].values()for a,b in v if not any(all((c[0]-cx)**2+(c[1]-cy)**2<=455000**2 for c in(a,b))for cx,cy in centers)]
rows=[]
for n in ['frozen26b','frozen24move']:
 b=p.LoadBoard(str(R/'header-routing'/n/'pcb/maru60.kicad_pcb'));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];hs=[]
 for q in items:
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
   bb=q.GetEffectiveHoleShape().BBox();hs.append((q,(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())))
 pairs=[]
 for a,c in es:
  e=(min(a[0],c[0]),min(a[1],c[1]),max(a[0],c[0]),max(a[1],c[1]))
  for h,t in hs:
   dx=max(0,e[0]-t[2],t[0]-e[2]);dy=max(0,e[1]-t[3],t[1]-e[3]);pairs.append((dx*dx+dy*dy,h.m_Uuid.AsString(),e,t))
 least=min(pairs);track=next(q for q in items if q.m_Uuid.AsString()=='3e0fec9e-6c78-45a5-a2dc-22ae925ad604')
 rows.append(dict(board=n,physical_hole_count=len(hs),remote_changed_edge_count=len(es),conservative_min_hole_bbox_distance_nm=math.sqrt(least[0]),min_squared_nm2=least[0],nearest_hole_uuid=least[1],remote_edge_bbox=least[2],hole_bbox=least[3],target_track=dict(net=track.GetNetname(),layer=b.GetLayerName(track.GetLayer()),width_nm=track.GetWidth(),start=(track.GetStart().x,track.GetStart().y),end=(track.GetEnd().x,track.GetEnd().y))))
(O/'drills.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
