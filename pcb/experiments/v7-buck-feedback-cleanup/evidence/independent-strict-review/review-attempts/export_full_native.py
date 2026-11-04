import os,sys,json,hashlib,math
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent; B=Path(sys.argv[1]);tag=sys.argv[2];expected=sys.argv[3]
for k in ('XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR'):
 d=R/('runtime-'+tag)/k;d.mkdir(parents=True,mode=0o700,exist_ok=False);os.environ[k]=str(d)
import pcbnew as p
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert H(B)==expected and p.GetBuildVersion()=='9.0.2+dfsg-1'
b=p.LoadBoard(str(B));uid=lambda x:x.m_Uuid.AsString();L=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
window=p.BOX2I(p.VECTOR2I(-100000000,-100000000),p.VECTOR2I(600000000,600000000))
def bounds(s):
 q=s.BBox();return [q.GetLeft(),q.GetTop(),q.GetRight(),q.GetBottom()]
def rings(q):
 def ring(r):return [[r.CPoint(i).x,r.CPoint(i).y] for i in range(r.PointCount())]
 return [{'outline':ring(q.COutline(i)),'holes':[ring(q.CHole(i,j)) for j in range(q.HoleCount(i))]} for i in range(q.OutlineCount())]
def poly(s):
 q=p.SHAPE_POLY_SET();s.TransformToPolygon(q,1,p.ERROR_OUTSIDE);return q
def copy(q):return p.SHAPE_POLY_SET(q)
items=list(b.GetTracks())+[x for f in b.GetFootprints() for x in f.Pads()];by={uid(x):x for x in items};objects={};holes={};fbshape={}
for x in items:
 u=uid(x);m={'class':x.GetClass(),'net':x.GetNetname(),'net_code':x.GetNetCode(),'layers':[b.GetLayerName(l) for l in L if x.IsOnLayer(l)],'position_nm':[x.GetPosition().x,x.GetPosition().y]}
 if isinstance(x,p.PAD):m.update(ref=x.GetParentFootprint().GetReference(),pin=x.GetNumber(),attribute=x.GetAttribute())
 elif isinstance(x,p.PCB_VIA):m.update(diameter_nm=x.GetWidth(p.F_Cu),drill_nm=x.GetDrill(),via_type=x.GetViaType())
 else:m.update(start_nm=[x.GetStart().x,x.GetStart().y],end_nm=[x.GetEnd().x,x.GetEnd().y],width_nm=x.GetWidth(),length_mm=x.GetLength()/1e6)
 if isinstance(x,(p.PAD,p.PCB_VIA)) and x.HasHole():
  assert (isinstance(x,p.PCB_VIA) and x.GetViaType()==p.VIATYPE_THROUGH and x.TopLayer()==p.F_Cu and x.BottomLayer()==p.B_Cu) or (isinstance(x,p.PAD) and x.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH))
  h=x.GetEffectiveHoleShape();holes[u]={'bbox':bounds(h),'through_layers':[b.GetLayerName(l) for l in L]}
  if window.Intersects(h.BBox()):holes[u]['shape']=rings(poly(h))
 m['copper']={}
 for l in L:
  if not x.IsOnLayer(l):continue
  sh=p.SHAPE_CIRCLE(x.GetPosition(),x.GetWidth(l)//2) if isinstance(x,p.PCB_VIA) else x.GetEffectiveShape(l)
  rec={'bbox':bounds(sh)}
  if window.Intersects(sh.BBox()) or x.GetNetname()=='BUCK_FB':rec['shape']=rings(poly(sh))
  m['copper'][b.GetLayerName(l)]=rec
  if x.GetNetname()=='BUCK_FB':
   q=poly(sh)
   if isinstance(x,(p.PAD,p.PCB_VIA)) and x.HasHole():q.BooleanSubtract(poly(x.GetEffectiveHoleShape()))
   fbshape[(u,l)]=q
 objects[u]=m
zones=[]
for z in b.Zones():
 for l in L:
  if z.IsOnLayer(l):zones.append({'uuid':uid(z),'net':z.GetNetname(),'layer':b.GetLayerName(l),'settings':{'outline':rings(z.Outline()),'clearance_nm':z.GetLocalClearance(),'minimum_thickness_nm':z.GetMinThickness()},'fills':rings(z.GetFilledPolysList(l))})
fb=sorted(u for u,m in objects.items() if m['net']=='BUCK_FB');edges=[]
for i,a in enumerate(fb):
 for v in fb[i+1:]:
  contacts=[]
  for l in L:
   if (a,l) not in fbshape or (v,l) not in fbshape:continue
   q=copy(fbshape[a,l]);q.BooleanIntersection(fbshape[v,l])
   if q.Area()>0:contacts.append({'layer':b.GetLayerName(l),'overlap_mm2':q.Area()/1e12})
  if contacts:edges.append({'a':a,'b':v,'contacts':contacts})
assert H(B)==expected
out={'source_board':str(B),'board_sha256':expected,'project_sha256':H(B.with_suffix('.kicad_pro')),'native_build':p.GetBuildVersion(),'one_board_load_no_save_fill':True,'window_nm':[-100000000,-100000000,500000000,500000000],'objects':objects,'holes':holes,'zones':zones,'FB_edges':edges,'counts':{'tracks':sum(isinstance(x,p.PCB_TRACK) and not isinstance(x,p.PCB_VIA) for x in items),'vias':sum(isinstance(x,p.PCB_VIA) for x in items),'pads':sum(isinstance(x,p.PAD) for x in items),'holes':len(holes),'all_track_centerline_mm':math.fsum(x.GetLength()/1e6 for x in items if isinstance(x,p.PCB_TRACK) and not isinstance(x,p.PCB_VIA))}}
(R/(tag+'.json')).write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps({'sha':expected,'counts':out['counts'],'FB_objects':len(fb),'FB_edges':len(edges)},indent=2))
