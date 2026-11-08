import pcbnew as p,json,numpy as np,math
from pathlib import Path
D=Path(__file__).parent;a=p.LoadBoard(str(D/'checkpoint-corridor-075.kicad_pcb'));b=p.LoadBoard(str(D/'checkpoint-shorttree-070.kicad_pcb'));uid=lambda t:t.m_Uuid.AsString();xy=lambda v:(p.ToMM(v.x),p.ToMM(v.y));sourceids={uid(t) for t in a.GetTracks()};retained=[t for t in b.GetTracks()if uid(t)in sourceids and not isinstance(t,p.PCB_VIA)and t.GetLayer()in[p.F_Cu,p.B_Cu]]
za={l:[z.GetFilledPolysList(l)for z in a.Zones()if z.GetNetname()=='GND'and z.IsOnLayer(l)and not z.GetIsRuleArea()]for l in[p.B_Cu,p.F_Cu]};zb={l:[z.GetFilledPolysList(l)for z in b.Zones()if z.GetNetname()=='GND'and z.IsOnLayer(l)and not z.GetIsRuleArea()]for l in[p.B_Cu,p.F_Cu]};edges={};boxes={}
for l in za:
 old=p.SHAPE_POLY_SET();new=p.SHAPE_POLY_SET()
 for q in za[l]:old.BooleanAdd(q)
 for q in zb[l]:new.BooleanAdd(q)
 lost=p.SHAPE_POLY_SET();lost.BooleanSubtract(old,new);es=[];bb=[]
 for oi in range(lost.OutlineCount()):
  lines=[lost.COutline(oi)]+[lost.CHole(oi,hi)for hi in range(lost.HoleCount(oi))]
  for line in lines:
   pts=[xy(line.CPoint(i))for i in range(line.PointCount())];es.extend(zip(pts,pts[1:]+pts[:1]));bb.append((min(x[0]for x in pts),min(x[1]for x in pts),max(x[0]for x in pts),max(x[1]for x in pts)))
 edges[l]=np.array(es);boxes[l]=bb

def inside(polys,l,q):return any(ps.Contains(p.VECTOR2I(p.FromMM(float(q[0])),p.FromMM(float(q[1]))))for ps in polys[l])
def cuts(aa,zz,l):
 a=np.array(aa);d=np.array(zz)-a;E=edges[l]
 if not len(E):return []
 mn=np.minimum(a,a+d)-1e-9;mx=np.maximum(a,a+d)+1e-9;keep=(E[:,:,0].max(axis=1)>=mn[0])&(E[:,:,0].min(axis=1)<=mx[0])&(E[:,:,1].max(axis=1)>=mn[1])&(E[:,:,1].min(axis=1)<=mx[1]);ee=E[keep]
 if not len(ee)and not any(x0<=a[0]<=x1 and y0<=a[1]<=y1 for x0,y0,x1,y1 in boxes[l]):return []
 v=ee[:,1]-ee[:,0];q=ee[:,0]-a;det=d[0]*v[:,1]-d[1]*v[:,0];ok=np.abs(det)>1e-14;v=v[ok];q=q[ok];det=det[ok];ts=(q[:,0]*v[:,1]-q[:,1]*v[:,0])/det;us=(q[:,0]*d[1]-q[:,1]*d[0])/det;tt=sorted(set([0.,1.]+[round(max(0,min(1,float(t))),12)for t,u in zip(ts,us)if -1e-10<=t<=1+1e-10 and -1e-10<=u<=1+1e-10]));out=[]
 for t0,t1 in zip(tt,tt[1:]):
  mid=a+d*(t0+t1)/2
  if t1-t0<1e-10 or not inside(za,l,mid)or inside(zb,l,mid):continue
  out.append({'start':(a+d*t0).tolist(),'end':(a+d*t1).tolist(),'length_mm':float(np.linalg.norm(d))*(t1-t0)})
 return out
res=[]
for t in retained:
 aa,zz=xy(t.GetStart()),xy(t.GetEnd());ln=math.dist(aa,zz)
 if not ln:continue
 l=p.B_Cu if t.GetLayer()==p.F_Cu else p.F_Cu;r=p.ToMM(t.GetWidth())/2;n=(-(zz[1]-aa[1])/ln,(zz[0]-aa[0])/ln)
 ints={key:cuts([aa[i]+n[i]*off for i in range(2)],[zz[i]+n[i]*off for i in range(2)],l)for key,off in [('left',-r),('center',0),('right',r)]}
 if any(ints.values()):res.append({'uuid':uid(t),'net':t.GetNetname(),'layer':b.GetLayerName(t.GetLayer()),'start':aa,'end':zz,'new_missing_intervals':ints})
r={'method':'Native Boolean old GND minus candidate GND, continuous boundary intersections with every retained outer track centerline and parallel edges, exact oldContains and !newContains midpoint confirmation. Excludes newly added/retired tracks. No sampling approximation.','retained_track_count':len(retained),'affected_tracks':res,'totals_mm':{k:sum(v['length_mm']for rr in res for v in rr['new_missing_intervals'][k])for k in ['left','center','right']}}
(D/'final70-collateral-return.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
