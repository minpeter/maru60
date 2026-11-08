import sys
sys.path.insert(0,'/workspace/shared/maru60-resume/mcu-routing/native-pylibs')
import pcbnew as p,shapely as s,numpy as np,json
from shapely.geometry import Polygon,Point,box
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-c782/mcu');b=p.LoadBoard(str(R/'source/pcb/maru60.kicad_pcb'));region=box(111,72.5,114,78)
def geom(ps):
 def pts(c):return [(c.CPoint(i).x/1e6,c.CPoint(i).y/1e6) for i in range(c.PointCount())]
 return s.union_all([Polygon(pts(ps.COutline(i)),[pts(ps.CHole(i,h)) for h in range(ps.HoleCount(i))]) for i in range(ps.OutlineCount())])
def shape(q,l):
 sh=p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2) if isinstance(q,p.PCB_VIA) else q.GetEffectiveShape(l);ps=p.SHAPE_POLY_SET();sh.TransformToPolygon(ps,100,p.ERROR_OUTSIDE);ps.Simplify();return geom(ps)
items=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];gs=[]
for q in items:
 if q.GetNetname()=='COL5':continue
 for l in [p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu]:
  if not q.IsOnLayer(l):continue
  g=shape(q,l)
  if g.intersects(region.buffer(1)):gs.append(g)
ob=s.union_all(gs).buffer(.456,quad_segs=32)
pts=[]
for y in np.arange(72.75,76.31,.025):
 for x in np.arange(112.1,112.801,.025):
  if not ob.intersects(Point(float(x),float(y))):pts.append([round(float(x),3),round(float(y),3)])
print('legal via screened sites',len(pts));print(pts[:100]);(R/'qa/col5-sites.json').write_text(json.dumps(pts,indent=2))
