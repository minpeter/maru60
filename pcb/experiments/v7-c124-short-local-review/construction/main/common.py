import pcbnew as p,json,pathlib,hashlib,math
D=pathlib.Path('/tmp/v7-c124-rebound-short/main');BP=pathlib.Path('/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104/selected-recovered/pcb/maru60.kicad_pcb');sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();assert sha(BP)=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'
b=p.LoadBoard(str(BP));fs={f.GetReference():f for f in b.GetFootprints()};obs=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in obs};vec=lambda a:p.VECTOR2I(*(round(x*1e6)for x in a))
def poly(s,bound=p.ERROR_INSIDE):
 o=p.SHAPE_POLY_SET();s.TransformToPolygon(o,1,bound);o.Simplify();return o
def shape(q,l):return p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l)
def copper(q,l):
 o=poly(shape(q,l))
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():o.BooleanSubtract(poly(q.GetEffectiveHoleShape(),p.ERROR_OUTSIDE))
 return o
def cross(a,b):
 o=p.SHAPE_POLY_SET();o.BooleanIntersection(a,b);return o
def dump(q):
 def ring(r):return [[r.CPoint(i).x/1e6,r.CPoint(i).y/1e6]for i in range(r.PointCount())]
 return [dict(o=ring(q.COutline(i)),h=[ring(q.CHole(i,j))for j in range(q.HoleCount(i))])for i in range(q.OutlineCount())]
def rect(x,y,w,h):
 q=p.SHAPE_POLY_SET();q.NewOutline()
 for a,z in [(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)]:q.Append(round(a*1e6),round(z*1e6))
 return q
def seg(a,z,w=.15):return poly(p.SHAPE_SEGMENT(vec(a),vec(z),round(w*1e6)))
def transform(q,old,new,angle=0):
 co,si=math.cos(angle),math.sin(angle);r=p.SHAPE_POLY_SET()
 def point(xy):
  x,y=xy[0]-old[0],xy[1]-old[1];return round((new[0]+co*x-si*y)*1e6),round((new[1]+si*x+co*y)*1e6)
 for row in dump(q):
  i=r.NewOutline()
  for xy in row['o']:r.Append(*point(xy))
  for h in row['h']:
   j=r.NewHole(i)
   for xy in h:r.Append(*point(xy),i,j)
 return r
def clearance(s,net,l=p.B_Cu,exclude=()):
 rows=[]
 for q in obs:
  if uid(q)in exclude or not q.IsOnLayer(l)or q.GetNetname()==net:continue
  rows.append(dict(uuid=uid(q),net=q.GetNetname(),gap_mm=s.GetClearance(shape(q,l))/1e6))
 return sorted(rows,key=lambda x:x['gap_mm'])[:8]
def envelope(org,box):
 pts=[]
 for x in[box[0],box[2]]:
  for y in[box[1],box[3]]:
   for a in[-math.pi/90,0,math.pi/90]:
    dx,dy=x-org[0],y-org[1];pts.append([org[0]+math.cos(a)*dx-math.sin(a)*dy,org[1]+math.sin(a)*dx+math.cos(a)*dy])
 x0,y0=min(q[0]for q in pts)-.1,min(q[1]for q in pts)-.1;x1,y1=max(q[0]for q in pts)+.1,max(q[1]for q in pts)+.1
 return rect((x0+x1)/2,(y0+y1)/2,x1-x0,y1-y0)
compact=seg([15.5,17.725],[14.9,17.275],.28);compact.BooleanAdd(seg([15.5,17.85],[15.5,17.25],.20))
capids={uid(q)for q in fs['C124'].Pads()};rids={uid(q)for q in fs['R121'].Pads()}
ret={x for x in idx if x.startswith(('6e2e82bf','e218cfe4','eb147f3b','05a0b97d','18d72adc','3aa399c7','3dce1fa7','5b54e93a','c69210ed'))}
