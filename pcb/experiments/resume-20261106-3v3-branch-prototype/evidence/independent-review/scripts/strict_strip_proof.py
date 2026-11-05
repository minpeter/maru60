from pathlib import Path
from fractions import Fraction as F
import json,collections,pcbnew as p
R=Path('/workspace/shared/maru60-resume'); D=R/'continuation-97d9eb7/stub3v3-independent'; C=R/'continuation-97d9eb7/stub3v3'; S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype'
boards=[p.LoadBoard(str(q/'pcb/maru60.kicad_pcb')) for q in [S,C]]
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def strict_entry(a,b,poly):
 # Intersect open halfplanes with segment parameter t in [0,1].
 lo,hi=F(0),F(1)
 for u,v in zip(poly,poly[1:]+poly[:1]):
  aa,bb=cross(u,v,a),cross(u,v,b);delta=bb-aa
  if not delta:
   if aa<=0:return False
  elif delta>0:lo=max(lo,-aa/delta)
  else:hi=min(hi,-aa/delta)
 return lo<hi
out={}
for layer,lr in json.loads((D/'qa/exact-boundary-paths.json').read_text()).items():
 edges=[]
 for board in boards:
  zs=[z for z in board.Zones() if z.IsOnLayer(board.GetLayerID(layer)) and not z.GetIsRuleArea()]; assert len(zs)==1
  ps=zs[0].GetFilledPolysList(board.GetLayerID(layer));rings=[]
  for i in range(ps.OutlineCount()):
   for r in [ps.COutline(i)]+[ps.CHole(i,h) for h in range(ps.HoleCount(i))]:rings.append([(r.CPoint(j).x,r.CPoint(j).y)for j in range(r.PointCount())])
  ec=collections.Counter((a,b) for ring in rings for a,b in zip(ring,ring[1:]+ring[:1]));edges.extend((a,b) for (a,b),n in ec.items() if n>ec[b,a])
 cells=0;tested=0
 for row in lr['matched_paths']:
  a,b=row['source_path_nm'],row['candidate_path_nm']; xs=sorted(set(v[0]for v in a+b))
  for l,r in zip(xs,xs[1:]):
   m=F(l+r,2); sa=[(u,v)for u,v in zip(a,a[1:])if min(u[0],v[0])<m<max(u[0],v[0])]; sb=[(u,v)for u,v in zip(b,b[1:])if min(u[0],v[0])<m<max(u[0],v[0])]; assert len(sa)==len(sb)==1
   def y(s,x):u,v=s[0];return F(u[1])+F(v[1]-u[1],v[0]-u[0])*(x-u[0])
   d1,d2=y(sa,l)-y(sb,l),y(sa,r)-y(sb,r);cuts=[F(l),F(r)]
   if d1*d2<0:cuts.insert(1,F(l)+(r-l)*(-d1)/(d2-d1))
   for u,v in zip(cuts,cuts[1:]):
    if y(sa,(u+v)/2)==y(sb,(u+v)/2):continue
    poly=list(dict.fromkeys([(u,y(sa,u)),(v,y(sa,v)),(v,y(sb,v)),(u,y(sb,u))])); assert len(poly)>=3
    area=sum(x[0]*z[1]-x[1]*z[0]for x,z in zip(poly,poly[1:]+poly[:1])); assert area
    if area<0:poly.reverse()
    assert all(cross(poly[i-1],poly[i],poly[(i+1)%len(poly)])>=0 for i in range(len(poly)))
    bb=[min(x[0]for x in poly),min(x[1]for x in poly),max(x[0]for x in poly),max(x[1]for x in poly)]
    for e,f in edges:
     if max(e[0],f[0])<bb[0]or min(e[0],f[0])>bb[2]or max(e[1],f[1])<bb[1]or min(e[1],f[1])>bb[3]:continue
     tested+=1;assert not strict_entry(e,f,poly),(layer,poly,e,f)
    cells+=1
 out[layer]={'exact_strip_cells':cells,'bbox_candidate_edges_tested':tested,'no_source_or_candidate_boundary_enters_any_strip_interior':True,'unique_path_segment_per_slab':True}
(D/'qa/strict-strip-proof.json').write_text(json.dumps(out,indent=2));print(out)
