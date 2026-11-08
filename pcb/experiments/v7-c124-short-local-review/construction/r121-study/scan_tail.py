# Source-line shape, not cached courtyard.
exec(open(ROOT+'/refine_clipping.py').read().split('rp=rect(')[0])
rp=rect(14.695,19.575,16.495,20.625)
cp=rect(14.8,18.520,16.4,19.570)
uc=exactrectcourt(FPS['U8'])
rows=[]
for dy in [-.2,-.15,-.1,-.075,-.05,-.025,0,.025,.05,.075,.1,.15,.2]:
 for a in [85,86,87,88,89,90,91,92,93,94,95]:
  pos(0,dy,a)
  if check():continue
  rc=exactrectcourt(r)
  if rc.Collide(rp,0) or rc.Collide(cp,0):continue
  courtgap=sep(rc,rp,200000)
  if courtgap[0]<0:continue
  near=[]
  for pad in ps:
   sh=pad.GetEffectiveShape(p.B_Cu)
   for lab,o,s in allobs:
    if pad.GetNetCode()!=o.GetNetCode() and sh.Collide(s,250000):near.append([pad.GetNumber(),lab,o.GetNetname(),sep(sh,s,250000)])
  near.sort(key=lambda x:x[3][0])
  rows.append({'dy':dy,'angle':a,'min_gap_nm':near[0],'R125court_gap_nm':courtgap,'contacts':contacts()})
# Native inside/outside positive local copper check for preferred candidates.
proof=[];areas=[]
pos();oldpolys={pad.GetNumber():[poly(pad,loc) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]] for pad in ps}
tps={uid(t):(t,[poly(t,loc) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]]) for t in localt if uid(t)[:8] in ['05a0b97d','abcd4fb1','763086b7']}
def inter(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(b);return z
def area(z):return z.Area()/1e12
for dy,ang in [(-.025,87),(-.05,86),(-.075,85),(-.05,87),(-.025,88)]:
 pos(0,dy,ang)
 for pad in ps:
  pin,pout=[poly(pad,loc) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]]
  exp=[]
  for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]:
   z=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(z,p.B_Cu,150000,1,loc);exp.append(z)
  for lab,o,sh in allobs:
   if pad.GetNetCode()==o.GetNetCode() or not pad.GetEffectiveShape(p.B_Cu).Collide(sh,250000):continue
   tin,tout=[poly(o,loc) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]]
   ii,oo=inter(exp[0],tin),inter(exp[1],tout)
   proof.append({'dy':dy,'angle':ang,'pad':pad.GetNumber(),'obstacle':lab,'gap_effective_nm':sep(pad.GetEffectiveShape(p.B_Cu),sh,250000),'inside150_overlap_nm2':ii.Area(),'outside150_overlap_nm2':oo.Area()})
  for key,(t,tpolys) in tps.items():
   vals=[]
   for old,new,tp in zip(oldpolys[pad.GetNumber()],[pin,pout],tpolys):
    oi,ni=inter(old,tp),inter(new,tp);common=inter(oi,ni)
    vals.append({'old':area(oi),'new':area(ni),'lost':area(oi)-area(common),'gained':area(ni)-area(common)})
   if any(x['old']>0 or x['new']>0 for x in vals):areas.append({'dy':dy,'angle':ang,'pad':pad.GetNumber(),'track':key,'inside_outside_mm2':vals})
 # local neighboring actual court intersections excluding retired C124
 courts=[]
 for f in {f.GetReference():f for f,x in localp}.values():
  if f.GetReference() in ['R121','C124','SW16']:continue
  try:c=exactrectcourt(f)
  except ValueError:c=f.GetCourtyard(p.B_CrtYd)
  if exactrectcourt(r).Collide(c,0):courts.append(f.GetReference())
 print('CANDIDATE',dy,ang,check(True),'R125',sep(exactrectcourt(r),rp,200000),'C124',sep(exactrectcourt(r),cp,200000),'courts',courts,'pads',[pinfo(x) for x in ps],flush=True)
pos()
json.dump({'R125_center':[15.595,20.1],'C124_center':[15.6,19.045],'R125_U8_gap_nm':sep(rp,uc,100000),'R125_C124_gap_nm':sep(rp,cp,100000),'grid_passes':rows,'preferred_1nm_proof':proof,'contact_areas':areas},open(ROOT+'/scan.json','w'),indent=2)
print('DONE',len(rows),len(proof),flush=True)
