import os
os.environ['XDG_CONFIG_HOME']='/tmp/v7-c128-retirement-independent-review/electrical/runtime/config'
import pcbnew as p,json
b=p.LoadBoard('/tmp/v7-c128-stub-retirement-aead/filled/pcb/maru60.kicad_pcb');ids=['cdcdaf62-0d7e-520a-9821-934ef8e04931','2a8005ba-8cc3-5ec3-bf91-40e20122da23'];idx={q.m_Uuid.AsString():q for q in b.GetTracks()}
def poly(sh,out=False):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);return z
for connected in [False,True]:
 if connected:b.BuildConnectivity()
 ps=[]
 for u in ids:
  q=idx[u];print('CONNECT',connected,'id',u,'class',q.GetClass(),'pos',q.GetPosition(),'hasHole',q.HasHole(),'width',q.GetWidth())
  a=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(p.F_Cu)//2) if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(p.F_Cu));print('Cu',a.Area()/1e12)
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
   hole=poly(q.GetEffectiveHoleShape(),True);print('hole',hole.Area()/1e12);a.BooleanSubtract(hole)
  print('net copper',a.Area()/1e12);ps.append(a)
 for a,c in [ps,ps[::-1]]:
  t=p.SHAPE_POLY_SET();t.BooleanIntersection(a,c);print('overlap',t.Area()/1e12)
g=json.load(open('/tmp/v7-c128-stub-retirement-aead/qa/candidate-physical-graph.json'))
print('saved',[e for e in g['direct_edges']if set(e[:2])==set(ids)])
