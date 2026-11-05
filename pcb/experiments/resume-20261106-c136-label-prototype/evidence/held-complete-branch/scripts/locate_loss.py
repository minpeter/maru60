from pathlib import Path
from fractions import Fraction as F
import json,math
D=Path('/workspace/shared/maru60-resume/continuation-9d787/branch4v');loss=json.loads((D/'qa/exact-plane-deltas.json').read_text());paths=json.loads((D/'qa/exact-boundary-paths.json').read_text())
def bb(pts):return[min(p[0]for p in pts),min(p[1]for p in pts),max(p[0]for p in pts),max(p[1]for p in pts)]
def hits(a,b):return a[0]<=b[2]and a[2]>=b[0]and a[1]<=b[3]and a[3]>=b[1]
def d2(c,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];vx,vy=c[0]-a[0],c[1]-a[1];ll=dx*dx+dy*dy;dot=vx*dx+vy*dy
 if dot<=0:return F(vx*vx+vy*vy)
 if dot>=ll:return F((c[0]-b[0])**2+(c[1]-b[1])**2)
 return F((dx*vy-dy*vx)**2,ll)
via=(33400000,19650000);segments={'acf57724':[(22600000,18550000),(23700000,19650000)],'05a61be2':[(23700000,19650000),(33400000,19650000)]};out=[]
for row in loss:
 for i,c in enumerate(row['loss_contours_nm']):
  pts=c['outer'];edges=list(zip(pts,pts[1:]+pts[:1]));dist={'removed_via_center':min(d2(via,a,b)for a,b in edges)}
  for name,(a,b)in segments.items():
   assert not hits(bb(pts),bb([a,b]));dist[name+'_centerline']=min([d2(c,a,b)for c in pts]+[d2(c,x,y)for c in[a,b]for x,y in edges])
  near=[p for p in paths[row['layer']]['matched_paths']if hits(bb(pts),bb(p['source_path_nm']+p['candidate_path_nm']))];assert near
  out.append({'layer':row['layer'],'contour':i,'bbox_nm':bb(pts),'loss_contour_nm':c,'source_candidate_boundary_paths':near,'minimum_distances':[{'target':k,'exact_squared_distance_nm2':str(v),'distance_mm':math.sqrt(float(v))/1e6}for k,v in dist.items()]})
(D/'qa/loss-locations.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
