def exactrectcourt(f):
 pts=[]
 for s in f.GraphicalItems():
  if s.GetLayer()==p.B_CrtYd:
   for v in [s.GetStart(),s.GetEnd()]:
    q=(v.x,v.y)
    if q not in pts:pts.append(q)
 if len(pts)==2:
  (x0,y0),(x1,y1)=pts;pts=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
 if len(pts)!=4:raise ValueError('not simple rectangle '+f.GetReference())
 cx=sum(x for x,y in pts)/4;cy=sum(y for x,y in pts)/4
 pts.sort(key=lambda q:math.atan2(q[1]-cy,q[0]-cx))
 z=p.SHAPE_POLY_SET();z.NewOutline()
 for x,y in pts:z.Append(x,y)
 return z
rp=rect(14.7,19.575,16.5,20.625)
cp=rect(14.8,18.525,16.4,19.575)
u8=exactrectcourt(FPS['U8'])
pos();rc=exactrectcourt(r)
print('EXACTCOURTS',{s:bbshape(z) for s,z in [('R121',rc),('U8',u8),('R125',rp),('C124_new',cp)]},'R125U8',sep(rp,u8,100000),'R125C124',sep(rp,cp,100000),flush=True)
# Bounded translation and angle study: minimal clearance of courtyard centerline, not stroke bbox.
checks=[]
for dx in [0,-.03,-.030001,-.035,-.037699,-.037700,-.037701,-.037702]:
 pos(dx)
 checks.append({'dx':dx,'dy':0,'angle':90,'copper_bad':check(True),'R125court_gap_nm':sep(exactrectcourt(r),rp,100000),'contacts':contacts()})
# Rotation no centroid displacement, reduce angle just enough to get positive court gap.
lo=0;hi=5
for i in range(35):
 mid=(lo+hi)/2;pos(a=90-mid)
 if exactrectcourt(r).Collide(rp,0):lo=mid
 else:hi=mid
angle_bound=[lo,hi]
for a in [90-hi,88.3,88.2,88,87.5,87]:
 pos(a=a)
 checks.append({'dx':0,'dy':0,'angle':a,'copper_bad':check(True),'R125court_gap_nm':sep(exactrectcourt(r),rp,100000),'contacts':contacts()})
# Native 1 nm inside/outside positivity proof by clipping expanded pad against track polygon.
# Boolean intersection avoids quadratic high-resolution polygon Collide tests.
critical={uid(t):t for t in localt if uid(t)[:8] in ['3a13a9a0','4174a692','a621cda3','db0f565d','0bf33e40','ff31c038']}
critpoly={key:[poly(t,loc) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]] for key,t in critical.items()}
def padexpanded(pad,loc):
 z=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(z,p.B_Cu,150000,1,loc);return z
def intersection(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(b);return z
proof=[]
for dx,ang in [(0,90),(-.030001,90),(-.035,90),(-.037699,90),(-.037700,90),(-.037701,90),(-.037702,90),(0,88.3),(0,88.2),(0,88)]:
 pos(dx,a=ang)
 for pad in ps:
  pin,pout=padexpanded(pad,p.ERROR_INSIDE),padexpanded(pad,p.ERROR_OUTSIDE)
  for key,t in critical.items():
   if pad.GetNetCode()==t.GetNetCode():continue
   tin,tout=critpoly[key]
   ii,oo=intersection(pin,tin),intersection(pout,tout)
   proof.append({'dx':dx,'angle':ang,'pad':pad.GetNumber(),'obstacle':key,'clear150_inside':ii.Area()==0,'clear150_outside':oo.Area()==0,'overlap_inside_nm2':ii.Area(),'overlap_outside_nm2':oo.Area()})
# Preserve both original terminal-to-track contacts; quantify polygon overlap and changes.
pos(); oldpolys={pad.GetNumber():poly(pad,p.ERROR_INSIDE) for pad in ps}
trackpolys={uid(t):poly(t,p.ERROR_INSIDE) for t in localt if uid(t)[:8] in ['05a0b97d','abcd4fb1','763086b7']}
def intersection(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(b);return z
area=lambda x:x.Area()/1e12
areas=[]
for dx,ang in [(0,90),(-.030001,90),(-.035,90),(0,88.3),(0,88.2),(0,88)]:
 pos(dx,a=ang)
 for pad in ps:
  newpoly=poly(pad,p.ERROR_INSIDE)
  for key,tp in trackpolys.items():
   old=intersection(oldpolys[pad.GetNumber()],tp);new=intersection(newpoly,tp);common=intersection(old,new)
   if area(old)>0 or area(new)>0:
    areas.append({'dx':dx,'angle':ang,'pad':pad.GetNumber(),'track':key,'old_overlap_mm2':area(old),'new_overlap_mm2':area(new),'lost_overlap_mm2':area(old)-area(common),'gained_overlap_mm2':area(new)-area(common)})
res={'angle_delta_transition_deg':angle_bound,'checks':checks,'polygon_1nm_proof':proof,'contact_areas':areas,'exact_source_courtyards':{'R121':bbshape(rc),'U8':bbshape(u8),'R125':bbshape(rp),'C124_new':bbshape(cp)},'caution':'Native cached courtyard vertices lie 5um inside actual source-line rectangles. Use source line vertices. Actual R121 MPN/terminals unknown, copper-only screening not assembly proof.'}
json.dump(res,open(ROOT+'/refine.json','w'),indent=2)
print('REFINE_DONE',json.dumps({'angle_bound':angle_bound,'checks':checks,'contact_areas':areas},indent=2),flush=True)
pos()
