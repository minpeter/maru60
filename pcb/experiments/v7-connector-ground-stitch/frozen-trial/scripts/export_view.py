import os,pathlib,json,hashlib
D=pathlib.Path('/tmp/v7-connector-gnd-stitch-c770')
# Private standard XDG homes supplied by native_run.sh.
import pcbnew as p
win=p.BOX2I(p.VECTOR2I(14000000,7000000),p.VECTOR2I(7500000,6500000))
def poly(s):
 o=p.SHAPE_POLY_SET();s.TransformToPolygon(o,100,p.ERROR_OUTSIDE);o.Simplify();return o
def dump(q):
 def ring(r):return[[r.CPoint(i).x/1e6,r.CPoint(i).y/1e6]for i in range(r.PointCount())]
 return[dict(o=ring(q.COutline(i)),h=[ring(q.CHole(i,j))for j in range(q.HoleCount(i))])for i in range(q.OutlineCount())]
out={}
for phase in ['source','filled']:
 B=D/phase/'pcb/maru60.kicad_pcb';before=hashlib.sha256(B.read_bytes()).hexdigest();b=p.LoadBoard(str(B));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];result=dict(board_sha256=before,layers={})
 for l in [p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu]:
  holes=p.SHAPE_POLY_SET()
  for q in items:
   if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()and q.GetBoundingBox().Intersects(win):holes.BooleanAdd(poly(q.GetEffectiveHoleShape()))
  rows=[]
  for z in b.Zones():
   if z.IsOnLayer(l) and z.GetNetname()=='GND':
    shape=p.SHAPE_POLY_SET(z.GetFilledPolysList(l));shape.BooleanSubtract(holes);rows.append(dict(uuid=z.m_Uuid.AsString(),net='GND',type='ZONE',poly=dump(shape)))
  for q in items:
   if not q.IsOnLayer(l)or not q.GetBoundingBox().Intersects(win):continue
   s=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l));s.BooleanSubtract(holes);row=dict(uuid=q.m_Uuid.AsString(),net=q.GetNetname(),type=q.GetClass(),poly=dump(s))
   if isinstance(q,p.PAD):row['pad']=q.GetParentFootprint().GetReference()+'.'+q.GetNumber()
   rows.append(row)
  result['layers'][b.GetLayerName(l)]=rows
 out[phase]=result;assert hashlib.sha256(B.read_bytes()).hexdigest()==before
(D/'qa/local-native-view.json').write_text(json.dumps(out))
