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
report={'version':p.GetBuildVersion(),'R121':{'xy':vxy(r.GetPosition()),'angle':r.GetOrientationDegrees(),'value':r.GetValue(),'attributes':{f.GetName():f.GetText() for f in r.GetFields()},'pads':[pinfo(x) for x in r.Pads()]},'footprints':[],'tracks':[]}
for f in {f.GetReference():f for f,x in localp}.values():
 f.BuildCourtyardCaches(); c=f.GetCourtyard(p.B_CrtYd)
 report['footprints'].append({'ref':f.GetReference(),'xy':vxy(f.GetPosition()),'angle':f.GetOrientationDegrees(),'value':f.GetValue(),'court_count':c.OutlineCount(),'court_box':bbox(c) if hasattr(c,'GetBoundingBox') else str(c.BBox()),'pads':[pinfo(x) for x in f.Pads()]})
for t in localt:report['tracks'].append({**base(t),'start':vxy(t.GetStart()),'end':vxy(t.GetEnd()),'width':mm(t.GetWidth()),'layer':t.GetLayer()})
json.dump(report,open(ROOT+'/initial.json','w'),indent=2)
print('READY',len(localp),len(localt),flush=True)
code.interact(local=globals())
