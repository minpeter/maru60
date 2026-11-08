import pcbnew as p,pathlib,json,hashlib
R=pathlib.Path('/tmp/v7-c124-rebound-short/isolated-v4');BP=R/'filled/pcb/maru60.kicad_pcb';b=p.LoadBoard(str(BP));uid=lambda q:q.m_Uuid.AsString();win=p.BOX2I(p.VECTOR2I(6000000,14000000),p.VECTOR2I(18000000,11000000));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]
def poly(s):
 o=p.SHAPE_POLY_SET();s.TransformToPolygon(o,100,p.ERROR_OUTSIDE);return o
def dump(q):
 def ring(r):return [[r.CPoint(i).x/1e6,r.CPoint(i).y/1e6]for i in range(r.PointCount())]
 return [dict(o=ring(q.COutline(i)),h=[ring(q.CHole(i,j))for j in range(q.HoleCount(i))])for i in range(q.OutlineCount())]
out={'sha256':hashlib.sha256(BP.read_bytes()).hexdigest(),'layers':{},'note':'Actual native geometry,100nm display polygons only; no mechanical or manufacturing qualification.'}
for l,sl,fa,cy in [(p.F_Cu,p.F_SilkS,p.F_Fab,p.F_CrtYd),(p.B_Cu,p.B_SilkS,p.B_Fab,p.B_CrtYd)]:
 rows=[]
 for q in items:
  if not q.IsOnLayer(l)or not q.GetBoundingBox().Intersects(win):continue
  s=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l))
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():s.BooleanSubtract(poly(q.GetEffectiveHoleShape()))
  rows.append(dict(type='copper',net=q.GetNetname(),uuid=uid(q),poly=dump(s)))
 for f in b.GetFootprints():
  for q in list(f.GraphicalItems())+list(f.GetFields()):
   if q.GetLayer()not in[sl,fa,cy]or not q.GetBoundingBox().Intersects(win):continue
   if hasattr(q,'IsVisible')and not q.IsVisible():continue
   if isinstance(q,p.PCB_TEXT)and q.GetLayer()!=sl:continue
   s=poly(q.GetEffectiveTextShape()if isinstance(q,p.PCB_TEXT)else q.GetEffectiveShape());rows.append(dict(type='silk'if q.GetLayer()==sl else'fab'if q.GetLayer()==fa else'court',ref=f.GetReference(),poly=dump(s)))
 out['layers'][b.GetLayerName(l)]=rows
(R/'qa/local-native-view.json').write_text(json.dumps(out))
