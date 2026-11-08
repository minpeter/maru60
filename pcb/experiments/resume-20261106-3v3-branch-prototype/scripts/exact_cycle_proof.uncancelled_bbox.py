from pathlib import Path
from fractions import Fraction as F
import json,collections,pcbnew as p
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-97d9eb7/stub3v3';S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype';x=json.loads((D/'qa/exact-boundary-paths.json').read_text());rational=json.loads((D/'qa/rational-boundary-classification.json').read_text());boards=[p.LoadBoard(str(q/'pcb/maru60.kicad_pcb'))for q in[S,D]]
def pts(r):return [(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
def inside(r,c):
 x,y=c;v=False
 for a,b in zip(r,r[1:]+r[:1]):
  if (a[1]>y)!=(b[1]>y)and x<F(a[0])+F(y-a[1],b[1]-a[1])*(b[0]-a[0]):v=not v
 return v
out={}
for l,lr in x.items():
 rings=[]
 for board in boards:
  z=next(z for z in board.Zones()if z.IsOnLayer(board.GetLayerID(l))and not z.GetIsRuleArea());ps=z.GetFilledPolysList(board.GetLayerID(l));rings.append([(pts(ps.COutline(i)),[pts(ps.CHole(i,h))for h in range(ps.HoleCount(i))])for i in range(ps.OutlineCount())])
 def covered(idx,s):return any(inside(o,s)and not any(inside(h,s)for h in hs)for o,hs in rings[idx])
 edges=lr['source_cycles_or_untraced_edges'];succ={tuple(a):tuple(b)for a,b in edges};assert len(succ)==len(edges);assert set(succ)==set(succ.values());cycles=[]
 while succ:
  start=next(iter(succ));v=[];q=start
  while q in succ:v.append(q);q=succ.pop(q)
  assert q==start;crosses=[(v[(i+1)%len(v)][0]-a[0])*(v[(i+2)%len(v)][1]-v[(i+1)%len(v)][1])-(v[(i+1)%len(v)][1]-a[1])*(v[(i+2)%len(v)][0]-v[(i+1)%len(v)][0])for i,a in enumerate(v)];convex=all(c>0 for c in crosses)or all(c<0 for c in crosses)
  center=(sum(F(a[0])for a in v)/len(v),sum(F(a[1])for a in v)/len(v));assert inside(v,center);assert not covered(0,center)and covered(1,center)
  bb=[min(a[0]for a in v),min(a[1]for a in v),max(a[0]for a in v),max(a[1]for a in v)];matches=[]
  for outer,hs in rings[1]:
   for ring in [outer]+hs:
    for a,b in zip(ring,ring[1:]+ring[:1]):
     if max(a[0],b[0])>=bb[0]and min(a[0],b[0])<=bb[2]and max(a[1],b[1])>=bb[1]and min(a[1],b[1])<=bb[3]:matches.append([a,b])
  # Stronger than no crossing: no candidate edge bounding box touches the entire removed-hole box.
  assert not matches
  area=abs(F(sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(v,v[1:]+v[:1])),2));cycles.append(dict(vertices=v,exact_gain_nm2=str(area),bbox_nm=bb,center_nm=[str(t)for t in center],source_copper_at_center=False,candidate_copper_at_center=True,strictly_convex=convex,candidate_boundary_edges_touching_bbox=0))
 assert not lr['candidate_cycles_or_untraced_edges']and not lr['unmatched_candidate_paths'];assert all('source_path_nm'in row for row in lr['matched_paths']);assert rational[l]['exact_remote_loss_nm2']=='0'
 out[l]=dict(removed_hole_cycles=cycles,all_boundary_deltas_accounted=True,exact_loss_nm2='0',exact_gain_nm2=str(sum(F(c['exact_gain_nm2'])for c in cycles)+F(rational[l]['exact_remote_gain_nm2'])),proof='Every noncancelled boundary delta is a matched path with exact gain-only classification, or a removed closed boundary whose whole bounding box is inside candidate copper with no candidate boundary entering that box. All unchanged boundaries cancel. Candidate through-drills are a subset of unchanged source drills, so subtracting them cannot create loss.')
(D/'qa/exact-full-plane-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
