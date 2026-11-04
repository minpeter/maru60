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

exec(open(ROOT+'/evaluate.py').read())
exec(open(ROOT+'/refine_clipping.py').read())
