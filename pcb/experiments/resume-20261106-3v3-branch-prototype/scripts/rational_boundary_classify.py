from pathlib import Path
from fractions import Fraction as F
import json,pcbnew as p
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-97d9eb7/stub3v3';paths=json.loads((D/'qa/exact-boundary-paths.json').read_text());boards=[p.LoadBoard(str(q))for q in[R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype/pcb/maru60.kicad_pcb',D/'pcb/maru60.kicad_pcb']]
def pts(r):return [(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
def inside(r,c):
 x,y=c;v=False
 for a,b in zip(r,r[1:]+r[:1]):
  if (a[1]>y)!=(b[1]>y) and x<F(a[0])+F(y-a[1],b[1]-a[1])*(b[0]-a[0]):v=not v
 return v
out={}
for l,lr in paths.items():
 rings=[]
 for board in boards:
  z=next(z for z in board.Zones()if z.IsOnLayer(board.GetLayerID(l))and not z.GetIsRuleArea());ps=z.GetFilledPolysList(board.GetLayerID(l));rings.append([(pts(ps.COutline(i)),[pts(ps.CHole(i,h))for h in range(ps.HoleCount(i))])for i in range(ps.OutlineCount())])
 def covered(idx,s):return any(inside(o,s)and not any(inside(h,s)for h in hs)for o,hs in rings[idx])
 rows=[]
 for row in lr['matched_paths']:
  a,c=row['source_path_nm'],row['candidate_path_nm'];xs=sorted(set(v[0]for v in a+c));lost=F(0);gained=F(0);samples=[]
  def segment(path,x):return next((u,v)for u,v in zip(path,path[1:])if min(u[0],v[0])<x<max(u[0],v[0]))
  def y(seg,x):
   u,v=seg;return F(u[1])+F(v[1]-u[1],v[0]-u[0])*(x-u[0])
  for x1,x2 in zip(xs,xs[1:]):
   mid=F(x1+x2,2);aa,cc=segment(a,mid),segment(c,mid);d1=y(aa,x1)-y(cc,x1);d2=y(aa,x2)-y(cc,x2);cuts=[F(x1),F(x2)]
   if d1*d2<0:cuts.insert(1,F(x1)+(x2-x1)*(-d1)/(d2-d1))
   for u,v in zip(cuts,cuts[1:]):
    m=(u+v)/2;ay,cy=y(aa,m),y(cc,m)
    if ay==cy:continue
    sample=(m,(ay+cy)/2);old,new=covered(0,sample),covered(1,sample);area=(v-u)*(abs(y(aa,u)-y(cc,u))+abs(y(aa,v)-y(cc,v)))/2;assert old!=new
    if old:lost+=area
    else:gained+=area
    samples.append({'point_nm':[str(t)for t in sample],'source_inside':old,'candidate_inside':new,'exact_area_nm2':str(area)})
  rows.append({'source_path_nm':a,'candidate_path_nm':c,'exact_loss_nm2':str(lost),'exact_gain_nm2':str(gained),'loss_mm2':float(lost)/1e12,'gain_mm2':float(gained)/1e12,'rational_samples':samples})
 out[l]={'rows':rows,'exact_remote_loss_nm2':str(sum(F(r['exact_loss_nm2'])for r in rows)),'exact_remote_gain_nm2':str(sum(F(r['exact_gain_nm2'])for r in rows))}
(D/'qa/rational-boundary-classification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
