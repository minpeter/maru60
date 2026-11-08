import os,json,math,hashlib,numpy as np
from pathlib import Path
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-b2l-native'
import pcbnew as p
D=Path(__file__).parent;B=D/'checkpoint-shorttree-070.kicad_pcb';A=D/'checkpoint-corridor-075.kicad_pcb';a=p.LoadBoard(str(A));b=p.LoadBoard(str(B));uid=lambda t:t.m_Uuid.AsString();xy=lambda v:(p.ToMM(v.x),p.ToMM(v.y));old={uid(t)for t in a.GetTracks()};refs={};edges={}
for l in [p.F_Cu,p.B_Cu]:
 ps=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.GetNetname()=='GND'and z.IsOnLayer(l)and not z.GetIsRuleArea():ps.BooleanAdd(z.GetFilledPolysList(l))
 es=[]
 for oi in range(ps.OutlineCount()):
  for line in [ps.COutline(oi)]+[ps.CHole(oi,hi)for hi in range(ps.HoleCount(oi))]:
   pts=[xy(line.CPoint(i))for i in range(line.PointCount())];es.extend(zip(pts,pts[1:]+pts[:1]))
 refs[l]=ps;edges[l]=np.array(es)
def missing(aa,zz,l):
 a=np.array(aa);d=np.array(zz)-a;E=edges[l];mn=np.minimum(a,a+d)-1e-9;mx=np.maximum(a,a+d)+1e-9;ee=E[(E[:,:,0].max(axis=1)>=mn[0])&(E[:,:,0].min(axis=1)<=mx[0])&(E[:,:,1].max(axis=1)>=mn[1])&(E[:,:,1].min(axis=1)<=mx[1])];v=ee[:,1]-ee[:,0];q=ee[:,0]-a;det=d[0]*v[:,1]-d[1]*v[:,0];ok=np.abs(det)>1e-14;v=v[ok];q=q[ok];det=det[ok];ts=(q[:,0]*v[:,1]-q[:,1]*v[:,0])/det;us=(q[:,0]*d[1]-q[:,1]*d[0])/det;tt=sorted(set([0.,1.]+[round(max(0,min(1,float(t))),12)for t,u in zip(ts,us)if -1e-10<=t<=1+1e-10 and -1e-10<=u<=1+1e-10]));out=[]
 for t0,t1 in zip(tt,tt[1:]):
  mid=a+d*(t0+t1)/2
  if t1-t0<1e-10 or refs[l].Contains(p.VECTOR2I(p.FromMM(float(mid[0])),p.FromMM(float(mid[1])))):continue
  out.append({'start':(a+d*t0).tolist(),'end':(a+d*t1).tolist(),'length_mm':float(np.linalg.norm(d))*(t1-t0)})
 return out
rows=[];vias=[]
for t in b.GetTracks():
 if uid(t)in old:continue
 if isinstance(t,p.PCB_VIA):
  vias.append({'uuid':uid(t),'net':t.GetNetname(),'at_mm':xy(t.GetPosition()),'diameter_mm':p.ToMM(t.GetWidth(p.F_Cu)),'drill_mm':p.ToMM(t.GetDrillValue())});continue
 aa,zz=xy(t.GetStart()),xy(t.GetEnd());ln=math.dist(aa,zz);r=p.ToMM(t.GetWidth())/2;n=(-(zz[1]-aa[1])/ln,(zz[0]-aa[0])/ln);l=p.B_Cu if t.GetLayer()==p.F_Cu else p.F_Cu
 missingrows={key:missing([aa[i]+n[i]*off for i in range(2)],[zz[i]+n[i]*off for i in range(2)],l)for key,off in [('left',-r),('center',0),('right',r)]}
 lower=p.SHAPE_POLY_SET();upper=p.SHAPE_POLY_SET();t.GetEffectiveShape(t.GetLayer()).TransformToPolygon(lower,1,p.ERROR_INSIDE);t.GetEffectiveShape(t.GetLayer()).TransformToPolygon(upper,1,p.ERROR_OUTSIDE);lower.BooleanSubtract(refs[l]);upper.BooleanSubtract(refs[l]);rows.append({'uuid':uid(t),'net':t.GetNetname(),'layer':b.GetLayerName(t.GetLayer()),'reference_layer':b.GetLayerName(l),'start_mm':aa,'end_mm':zz,'length_mm':ln,'width_mm':p.ToMM(t.GetWidth()),'missing_intervals':missingrows,'full_copper_projection_missing_lower_mm2':lower.Area()/1e12,'full_copper_projection_missing_upper_mm2':upper.Area()/1e12})
r={'source_sha256':hashlib.sha256(A.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(B.read_bytes()).hexdigest(),'method':'Continuous exact polygon-boundary intersections for new-track center and edges; native effective full-copper polygonization 1nm lower/upper bounds minus opposite filled-GND union. No Unfracture and no via/endpoint exclusions. Geometric reference only, not source-connected return or powered qualification.','tracks':rows,'vias':vias,'totals_by_net':{net:{'length_mm':sum(t['length_mm']for t in rows if t['net']==net),'missing_length_mm':{k:sum(i['length_mm']for t in rows if t['net']==net for i in t['missing_intervals'][k])for k in ['left','center','right']}}for net in sorted({t['net']for t in rows})}}
(D/'final70-new-reference.json').write_text(json.dumps(r,indent=2));print(r['totals_by_net'])
