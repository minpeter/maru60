import os
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-kicad-config'
import pcbnew as p,json,math,hashlib,sys,numpy as np
from pathlib import Path
D=Path(__file__).parent;path=D/'candidate.kicad_pcb';board=p.LoadBoard(str(path));xy=lambda v:(p.ToMM(v.x),p.ToMM(v.y));uid=lambda t:t.m_Uuid.AsString();ledger={'objects':json.load(open('/workspace/shared/maru-a4l-P3-S3-1V1-0323/rejected-S3-source-regression-0336/addition-ledger.json'))['additions9']};new={x['uuid']for x in ledger['objects']};tracks=[t for t in board.GetTracks()if uid(t)in new and t.GetNetname()=='+1V1'and not isinstance(t,p.PCB_VIA)];newvias=[t for t in board.GetTracks()if uid(t)in new and t.GetNetname()=='+1V1'and isinstance(t,p.PCB_VIA)];ownvias=[xy(t.GetPosition())for t in board.GetTracks()if isinstance(t,p.PCB_VIA)and t.GetNetname()=='+1V1'];polys={l:[z.GetFilledPolysList(l)for z in board.Zones()if z.GetNetname()=='GND'and z.IsOnLayer(l)and not z.GetIsRuleArea()]for l in[p.In1_Cu,p.In2_Cu]}
# Existing validated GND witness algorithm, retaining item membership for real return-via topology.
# Return-source membership is independently proved in audit-final.json.

edges={}
for layer,ps in polys.items():
 all_edges=[]
 for poly in ps:
  for oi in range(poly.OutlineCount()):
   lines=[poly.COutline(oi)]+[poly.CHole(oi,hi)for hi in range(poly.HoleCount(oi))]
   for line in lines:
    pts=[xy(line.CPoint(i))for i in range(line.PointCount())]
    all_edges.extend(zip(pts,pts[1:]+pts[:1]))
 edges[layer]=np.array(all_edges,dtype=float)
def inside(layer,q):return any(poly.Contains(p.VECTOR2I(p.FromMM(float(q[0])),p.FromMM(float(q[1]))))for poly in polys[layer])
def point(a,d,t):return[float(a[0]+d[0]*t),float(a[1]+d[1]*t)]
def split_intervals(a,z,layer):
 a=np.array(a);d=np.array(z)-a;E=edges[layer];mn=np.minimum(a,a+d)-1e-9;mx=np.maximum(a,a+d)+1e-9;keep=(E[:,:,0].max(axis=1)>=mn[0])&(E[:,:,0].min(axis=1)<=mx[0])&(E[:,:,1].max(axis=1)>=mn[1])&(E[:,:,1].min(axis=1)<=mx[1]);ee=E[keep];v=ee[:,1]-ee[:,0];q=ee[:,0]-a;det=d[0]*v[:,1]-d[1]*v[:,0];ok=np.abs(det)>1e-14;v=v[ok];q=q[ok];det=det[ok];ts=(q[:,0]*v[:,1]-q[:,1]*v[:,0])/det;us=(q[:,0]*d[1]-q[:,1]*d[0])/det;cuts=[0.,1.]+[max(0,min(1,float(t)))for t,u in zip(ts,us)if -1e-10<=t<=1+1e-10 and -1e-10<=u<=1+1e-10]
 ll=float(d@d)
 for vxy in ownvias:
  q=a-np.array(vxy);bb=2*float(q@d);cc=float(q@q)-.55**2;disc=bb*bb-4*ll*cc
  if disc>=0:
   for t in[(-bb-math.sqrt(disc))/(2*ll),(-bb+math.sqrt(disc))/(2*ll)]:
    if 0<t<1:cuts.append(t)
 cuts=sorted(set(round(t,12)for t in cuts));out=[]
 for t0,t1 in zip(cuts,cuts[1:]):
  if t1-t0<1e-10:continue
  mid=point(a,d,(t0+t1)/2)
  if inside(layer,mid):continue
  bucket='within_own_1V1_via_0p55mm_neighborhood'if any(math.dist(mid,v)<.55for v in ownvias)else'outside_own_via_neighborhood'
  if out and out[-1]['bucket']==bucket and abs(out[-1]['t1']-t0)<1e-10:out[-1]['t1']=t1;out[-1]['end_mm']=point(a,d,t1);out[-1]['length_mm']=(t1-out[-1]['t0'])*math.sqrt(ll)
  else:out.append({'t0':t0,'t1':t1,'start_mm':point(a,d,t0),'end_mm':point(a,d,t1),'length_mm':(t1-t0)*math.sqrt(ll),'bucket':bucket})
 return out
results=[];totals={k:{'raw_missing_mm':0.,'outside_own_via_mm':0.,'outside_interval_count':0}for k in ['left_edge','centerline','right_edge']}
foreign_vias=[t for t in board.GetTracks()if isinstance(t,p.PCB_VIA)and t.GetNetname()not in ['GND','+1V1']]
for t in tracks:
 a,z=xy(t.GetStart()),xy(t.GetEnd());length=math.dist(a,z)
 if not length:continue
 normal=(-(z[1]-a[1])/length,(z[0]-a[0])/length);r=p.ToMM(t.GetWidth())/2;layer=p.In1_Cu if t.GetLayer()==p.F_Cu else p.In2_Cu;cuts={}
 for label,offset in [('left_edge',-r),('centerline',0),('right_edge',r)]:
  aa=[a[i]+normal[i]*offset for i in range(2)];zz=[z[i]+normal[i]*offset for i in range(2)];ints=split_intervals(aa,zz,layer)
  for q in ints:
   totals[label]['raw_missing_mm']+=q['length_mm']
   if q['bucket']=='outside_own_via_neighborhood':totals[label]['outside_own_via_mm']+=q['length_mm'];totals[label]['outside_interval_count']+=1
   mid=[(q['start_mm'][i]+q['end_mm'][i])/2for i in range(2)];pv=p.VECTOR2I(p.FromMM(mid[0]),p.FromMM(mid[1]));q['overlapping_copper_keepouts']=[uid(z)for z in board.Zones()if z.GetIsRuleArea()and z.IsOnLayer(layer)and z.GetDoNotAllowCopperPour()and z.Outline().Contains(pv)];q['near_foreign_via_antipads']=[{'uuid':uid(v),'net':v.GetNetname(),'at_mm':xy(v.GetPosition())}for v in foreign_vias if math.dist(mid,xy(v.GetPosition()))<p.ToMM(v.GetWidth(layer))/2+.2]
  cuts[label]=ints
 results.append({'uuid':uid(t),'copper_layer':board.GetLayerName(t.GetLayer()),'reference_layer':board.GetLayerName(layer),'start_mm':a,'end_mm':z,'width_mm':2*r,'track_length_mm':length,'missing_projection_intervals':cuts})

r={'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'new_power_tracks':len(tracks),'new_power_vias':len(newvias),'new_track_centerline_mm':sum(x['track_length_mm']for x in results),'method':'Continuous saved native GND-polygon boundary intersections at centerline and both copper edges, F to In1 and B to In2. Own-via0.55mm neighborhoods are categorization only, not qualification/waiver.','totals_by_probe':totals,'track_intervals':results,'scope':'New positive-feed reference geometry only, not full loop/impedance/PDN/current/SI proof; nearest real source-GND transitions are separately in audit-final.json.'};(D/'new-1V1-source-reference.json').write_text(json.dumps(r,indent=2));print(totals)
