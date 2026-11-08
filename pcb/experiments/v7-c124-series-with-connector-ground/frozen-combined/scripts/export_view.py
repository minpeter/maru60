import pcbnew as p,pathlib,json,hashlib,sys
R=pathlib.Path('/tmp/v7-c124-d-plus-connector-gnd');mode=sys.argv[1] if len(sys.argv)>1 else 'filled';assert mode in ('source','filled');BP=R/mode/'pcb/maru60.kicad_pcb';b=p.LoadBoard(str(BP));uid=lambda q:q.m_Uuid.AsString();win=p.BOX2I(p.VECTOR2I(6000000,7000000),p.VECTOR2I(18000000,18000000));items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]
def poly(s):
 o=p.SHAPE_POLY_SET();s.TransformToPolygon(o,100,p.ERROR_OUTSIDE);return o
def dump(q):
 def ring(r):return [[r.CPoint(i).x/1e6,r.CPoint(i).y/1e6]for i in range(r.PointCount())]
 return [dict(o=ring(q.COutline(i)),h=[ring(q.CHole(i,j))for j in range(q.HoleCount(i))])for i in range(q.OutlineCount())]
holes=[poly(q.GetEffectiveHoleShape())for q in items if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()]
out={'sha256':hashlib.sha256(BP.read_bytes()).hexdigest(),'layers':{},'note':'Actual native geometry,100nm display polygons only; no mechanical or manufacturing qualification.'}
for l,sl,fa,cy in [(p.F_Cu,p.F_SilkS,p.F_Fab,p.F_CrtYd),(p.B_Cu,p.B_SilkS,p.B_Fab,p.B_CrtYd)]:
 rows=[]
 for q in items:
  if not q.IsOnLayer(l)or not q.GetBoundingBox().Intersects(win):continue
  s=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l))
  for h in holes:
   if s.BBox().Intersects(h.BBox()):s.BooleanSubtract(h)
  rows.append(dict(type='copper',net=q.GetNetname(),uuid=uid(q),poly=dump(s)))
 for f in b.GetFootprints():
  for q in list(f.GraphicalItems())+list(f.GetFields()):
   if q.GetLayer()not in[sl,fa,cy]or not q.GetBoundingBox().Intersects(win):continue
   if hasattr(q,'IsVisible')and not q.IsVisible():continue
   if isinstance(q,p.PCB_TEXT)and q.GetLayer()!=sl:continue
   s=poly(q.GetEffectiveTextShape()if isinstance(q,p.PCB_TEXT)else q.GetEffectiveShape());rows.append(dict(type='silk'if q.GetLayer()==sl else'fab'if q.GetLayer()==fa else'court',ref=f.GetReference(),poly=dump(s)))
 out['layers'][b.GetLayerName(l)]=rows
OP=R/('qa/source-local-native-view.json' if mode=='source' else 'qa/local-native-view.json');OP.write_text(json.dumps(out));print(OP, out['sha256'])
