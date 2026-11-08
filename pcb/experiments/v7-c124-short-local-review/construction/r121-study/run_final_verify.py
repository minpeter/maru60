import pcbnew as p, json, hashlib, math, os, code
ROOT='/tmp/v7-c124-rebound-short/r121-study'
SRC='/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104/selected-recovered/pcb/maru60.kicad_pcb'
assert hashlib.sha256(open(SRC,'rb').read()).hexdigest()=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'
b=p.LoadBoard(SRC)
FPS={f.GetReference():f for f in b.GetFootprints()}
r=FPS['R121']
def mm(x):return x/1e6
def vxy(v):return [mm(v.x),mm(v.y)]
def bbox(item):
 q=item.GetBoundingBox(); return [mm(q.GetX()),mm(q.GetY()),mm(q.GetRight()),mm(q.GetBottom())]
def uid(i):return str(i.m_Uuid.AsString())
def poly(item, loc=p.ERROR_OUTSIDE):
 out=p.SHAPE_POLY_SET(); item.TransformShapeToPolygon(out,p.B_Cu,0,1,loc); return out
def base(i):return {'uuid':uid(i),'net':i.GetNetname(),'box':bbox(i),'type':i.GetClass()}
def pinfo(x):return {**base(x),'n':x.GetNumber(),'xy':vxy(x.GetPosition()),'size':vxy(x.GetSize()),'angle':x.GetOrientationDegrees(),'shape':x.GetShape(),'radius':mm(x.GetRoundRectCornerRadius(p.B_Cu))}
localp=[]; localt=[]
for f in b.GetFootprints():
 for x in f.Pads():
  q=x.GetPosition()
  if x.IsOnLayer(p.B_Cu) and 9e6<q.x<21e6 and 13e6<q.y<25e6:localp.append((f,x))
for t in b.GetTracks():
 bb=bbox(t)
 if t.IsOnLayer(p.B_Cu) and bb[0]<21 and bb[2]>9 and bb[1]<25 and bb[3]>13:localt.append(t)

def bbshape(s):
 q=s.BBox();return [mm(q.GetX()),mm(q.GetY()),mm(q.GetRight()),mm(q.GetBottom())]
def rect(x0,y0,x1,y1):
 s=p.SHAPE_POLY_SET();s.NewOutline()
 for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:s.Append(round(x*1e6),round(y*1e6))
 return s
def sep(a,b,hi=2000000):
 if a.Collide(b,0):return [-1,0]
 if not a.Collide(b,hi):return [hi,None]
 lo=0
 while hi-lo>1:
  mid=(lo+hi)//2
  if a.Collide(b,mid):hi=mid
  else:lo=mid
 return [lo,hi]
allobs=[]
for f,x in localp:
 if f.GetReference() not in ['R121','C124']:allobs.append((f.GetReference()+'.'+x.GetNumber(),x,x.GetEffectiveShape(p.B_Cu)))
for t in localt:
 if t.GetNetname()!='USB_OVLO':allobs.append((uid(t),t,t.GetEffectiveShape(p.B_Cu)))
ps=list(r.Pads()); orig=p.VECTOR2I(r.GetPosition())
original_pads=[(q,p.VECTOR2I(q.GetPosition()),q.GetOrientationDegrees()) for q in ps]
original_shapes=[(s,p.VECTOR2I(s.GetStart()),p.VECTOR2I(s.GetEnd())) for s in r.GraphicalItems() if hasattr(s,'GetStart')]
def pos(dx=0,dy=0,a=90):
 # Restore exact original pad and courtyard primitives before each trial.
 # KiCad repeated incremental rotations otherwise accumulate integer-nm rounding.
 r.SetOrientationDegrees(90);r.SetPosition(orig)
 for q,xy,ang in original_pads:q.SetPosition(xy);q.SetOrientationDegrees(ang)
 for s,st,en in original_shapes:s.SetStart(st);s.SetEnd(en)
 r.SetOrientationDegrees(a);r.SetPosition(p.VECTOR2I(round(14e6+dx*1e6),round(18.5e6+dy*1e6)));r.BuildCourtyardCaches()
def check(details=False):
 ans=[]
 for pad in ps:
  sh=pad.GetEffectiveShape(p.B_Cu)
  for lab,o,shape in allobs:
   if pad.GetNetCode()!=o.GetNetCode() and sh.Collide(shape,150000):
    ans.append([pad.GetNumber(),lab,o.GetNetname(),sep(sh,shape)] if details else [pad.GetNumber(),lab])
 return ans
def contacts():
 ans=[]
 for pad in ps:
  sh=pad.GetEffectiveShape(p.B_Cu)
  for t in localt:
   if sh.Collide(t.GetEffectiveShape(p.B_Cu),0):ans.append([pad.GetNumber(),uid(t),t.GetNetname()])
 return ans

exec(open(ROOT+'/refine_clipping.py').read().split('rp=rect(')[0])
def intersection(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(b);return z
tm={uid(t):t for t in localt}
spur=tm['abcd4fb1-881b-43f9-906e-39d93366692e'];via=tm['763086b7-5549-4f5e-bb08-ce25387b3627']
pos();old={pad.GetNumber():[poly(pad,loc) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]] for pad in ps}
res={'old_ground_support':{'pad2_to_via_gap_nm':sep(ps[1].GetEffectiveShape(p.B_Cu),via.GetEffectiveShape(p.B_Cu)),'spur_via_overlap_inside_outside_mm2':[intersection(poly(spur,loc),poly(via,loc)).Area()/1e12 for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]]},'cases':[]}
rp=rect(14.695,19.575,16.495,20.625);cp=rect(14.8,18.520,16.4,19.570)
for dx,dy,ang in [(0,0,88),(0,-.025,88),(-.035001,0,90)]:
 pos(dx,dy,ang);c={'center':vxy(r.GetPosition()),'angle':ang,'copper_bad':check(True),'R125court_gap_nm':sep(exactrectcourt(r),rp,100000),'C124court_gap_nm':sep(exactrectcourt(r),cp,200000),'contacts':contacts(),'areas':[]}
 for pad in ps:
  key='05a0b97d-79af-50e5-b191-fe26b55d2c02' if pad.GetNumber()=='1' else 'abcd4fb1-881b-43f9-906e-39d93366692e'
  vals=[]
  for loc,oldp in zip([p.ERROR_INSIDE,p.ERROR_OUTSIDE],old[pad.GetNumber()]):
   tp=poly(tm[key],loc);oi=intersection(oldp,tp);ni=intersection(poly(pad,loc),tp);common=intersection(oi,ni)
   vals.append({'old':oi.Area()/1e12,'new':ni.Area()/1e12,'lost':(oi.Area()-common.Area())/1e12,'gained':(ni.Area()-common.Area())/1e12})
  oldi,oldo=[intersection(old[pad.GetNumber()][j],poly(tm[key],loc)) for j,loc in enumerate([p.ERROR_INSIDE,p.ERROR_OUTSIDE])]
  newi,newo=[intersection(poly(pad,loc),poly(tm[key],loc)) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]]
  def subarea(a,b):
   z=p.SHAPE_POLY_SET(a);z.BooleanSubtract(b);return z.Area()/1e12
  c['areas'].append({'pad':pad.GetNumber(),'track':key,'inside_outside_mm2':vals,'lost_area_bounds_mm2':[subarea(oldi,newo),subarea(oldo,newi)],'gained_area_bounds_mm2':[subarea(newi,oldo),subarea(newo,oldi)]})
 res['cases'].append(c)
pos();res['source_sha256_after']=hashlib.sha256(open(SRC,'rb').read()).hexdigest();assert res['source_sha256_after']=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'
json.dump(res,open(ROOT+'/final_verify.json','w'),indent=2);print(json.dumps(res,indent=2))
