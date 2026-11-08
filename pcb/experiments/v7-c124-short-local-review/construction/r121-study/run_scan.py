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

exec(open(ROOT+'/scan_tail.py').read())
