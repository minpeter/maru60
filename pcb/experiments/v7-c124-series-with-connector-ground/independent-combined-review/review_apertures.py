from pathlib import Path
import re,json,math,hashlib
O=Path('/tmp/v7-c124-d-plus-connector-gnd-independent-review');targetrefs={'R121','R125','C124'}
def bbox_ap(kind,v):
 if kind in ['R','O']:return(-v[0]/2,-v[1]/2,v[0]/2,v[1]/2)
 if kind=='C':return(-v[0]/2,-v[0]/2,v[0]/2,v[0]/2)
 if kind=='RoundRect':
  r=v[0];xs=v[1:9:2];ys=v[2:9:2];return(min(xs)-r,min(ys)-r,max(xs)+r,max(ys)+r)
 if kind=='HorizOval':
  r=v[0]/2;return(min(v[1],v[3])-r,min(v[2],v[4])-r,max(v[1],v[3])+r,max(v[2],v[4])+r)
 raise ValueError(kind)
def gap(a,b):return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
def parse(path):
 t=path.read_text();assert '%FSLAX46Y46*%'in t and '%MOMM*%'in t and not re.search(r'^G0[23]',t,re.M) and '%LPC*%'not in t
 ap={int(n):(kind,list(map(float,s.split('X'))))for n,kind,s in re.findall(r'%ADD(\d+)([^,]+),([^*]+)\*%',t)};a=None;ref=None;reg=None;objects=[]
 for line in t.splitlines():
  if line.startswith('%TO.C,'):ref=line[6:-2]
  elif line=='%TD*%':ref=None
  elif re.fullmatch(r'D\d+\*',line):a=int(line[1:-1])
  elif line=='G36*':reg=[]
  elif line=='G37*':
   xs=[q[0]for q in reg];ys=[q[1]for q in reg];objects.append({'ref':ref,'type':'region','bbox':[min(xs),min(ys),max(xs),max(ys)]});reg=None
  else:
   m=re.fullmatch(r'X(-?\d+)Y(-?\d+)D(0[123])\*',line)
   if not m:continue
   x,y=float(m[1])/1e6,float(m[2])/1e6;op=m[3]
   if reg is not None:reg.append((x,y))
   elif op=='03':
    kind,v=ap[a];bb=bbox_ap(kind,v);objects.append({'ref':ref,'type':kind,'aperture':a,'parameters':v,'center':[x,y],'bbox':[x+bb[0],y+bb[1],x+bb[2],y+bb[3]]})
   else:raise AssertionError(('unsupported nonregion draw',line))
 targets=[q for q in objects if q['ref']in targetrefs];assert len(targets)==6
 expected={'R121':(.3,.4,[(13.68,-19.1),(13.68,-18.2)]),'C124':(.5,.5,[(14.685,-19.375),(15.685,-19.375)]),'R125':(.4,.3,[(15.81,-20.48),(14.91,-20.48)])}
 for q in targets:
  w,h,centers=expected[q['ref']];assert q['type']=='R'and q['parameters']==[w,h]and tuple(q['center'])in centers
  others=sorted([{'ref':z['ref'],'type':z['type'],'bbox_mm':z['bbox'],'gap_lower_bound_mm':gap(q['bbox'],z['bbox'])}for z in objects if z is not q],key=lambda z:z['gap_lower_bound_mm']);q['nearest_apertures']=others[:3]
 assert min(q['nearest_apertures'][0]['gap_lower_bound_mm']for q in targets)>0
 return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'objects_parsed':len(objects),'target_apertures':targets,'minimum_target_to_any_other_aperture_conservative_bbox_gap_mm':min(q['nearest_apertures'][0]['gap_lower_bound_mm']for q in targets)}
r={n:parse(O/'artwork'/f'maru60-B_{n}.{ext}')for n,ext in [('Mask','gbs'),('Paste','gbp')]}
r.update({'candidate_sha256':'7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401','status':'PASS nominal generated aperture geometry; process qualification OFF','method':'Read generated KiCad Gerbers in mm 4.6. Explicit target rectangular aperture dimensions/centers checked; all plotted flashes and linear regions included in conservative axis-aligned bounding-box separation screen. Positive bounding-box gap is a guaranteed lower bound, not an asserted exact curved-aperture clearance. No registration or fabrication threshold invented.','effective_native_mask_expansion_mm':0,'effective_native_paste_margin_mm':[0,0],'paste_nominal_area_mm2_per_pad':{'R121':.12,'R125':.12,'C124':.25},'unqualified':['Solder-mask registration and dam capability','Stencil thickness, paste volume and transfer efficiency','Reflow/assembly process and tombstoning','Procurement and component drift equivalence','3D switch/socket/plate/case clearance']})
(O/'APERTURE_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v['minimum_target_to_any_other_aperture_conservative_bbox_gap_mm']for k,v in r.items()if k in ['Mask','Paste']}))
