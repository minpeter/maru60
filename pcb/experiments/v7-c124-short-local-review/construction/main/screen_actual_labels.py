import pcbnew as p, math,json,pathlib
R=pathlib.Path('/tmp/v7-c124-rebound-short/isolated-v4');b=p.LoadBoard(str(R/'pcb/maru60.kicad_pcb'));fs={f.GetReference():f for f in b.GetFootprints()};v=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6))
def poly(s):
 a=p.SHAPE_POLY_SET();s.TransformToPolygon(a,100,p.ERROR_OUTSIDE);return a
def textpoly(t):
 a=p.SHAPE_POLY_SET();t.TransformTextToPolySet(a,0,100,p.ERROR_OUTSIDE);return a
obs=[]
for f in fs.values():
 for q in f.Pads():
  if q.IsOnLayer(p.B_Cu)or q.HasHole():obs.append((f.GetReference()+'.'+q.GetNumber(),poly(q.GetEffectiveShape(p.B_Cu))))
 for q in list(f.GraphicalItems())+list(f.GetFields()):
  if q.GetLayer()!=p.B_SilkS or(hasattr(q,'IsVisible')and not q.IsVisible()):continue
  if f.GetReference()in ['R121','C124']and q==f.Reference():continue
  try:s=textpoly(q)if isinstance(q,p.PCB_TEXT)else poly(q.GetEffectiveShape())
  except TypeError:continue
  obs.append((f.GetReference()+' silk',s))
for q in b.GetTracks():
 if isinstance(q,p.PCB_VIA):obs.append(('via',poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(p.B_Cu)//2))))
for q in b.GetDrawings():
 if q.GetLayer()==p.B_SilkS:obs.append(('board silk',textpoly(q)if isinstance(q,p.PCB_TEXT)else poly(q.GetEffectiveShape())))
# Clip obstacle list to bounded label search rectangle. Far mask/ink cannot govern.
bb=p.BOX2I(v(6,12),v(14,13));obs=[(n,s)for n,s in obs if s.BBox().Intersects(bb)]
sol={}
for ref in ['R121','C124']:
 t=fs[ref].Reference(); rows=[]
 for xi in range(80,176,2):
  for yi in range(140,226,2):
   x,y=xi/10,yi/10;t.SetPosition(v(x,y));s=textpoly(t);near=[(n,s.GetClearance(q)/1e6)for n,q in obs];n,d=min(near,key=lambda a:a[1])
   if d<.10:continue
   o=fs[ref].GetPosition();rows.append(dict(at=[x,y],min_gap=d,nearest=n,distance=math.hypot(x-o.x/1e6,y-o.y/1e6)))
 rows.sort(key=lambda r:r['distance']);sol[ref]=rows[:20]
 if rows:
  t.SetPosition(v(*rows[0]['at']));obs.append((ref+' chosen reference',textpoly(t)))
print(json.dumps(sol,indent=2));(R/'qa/reference-ink-screen.json').write_text(json.dumps(sol,indent=2))
