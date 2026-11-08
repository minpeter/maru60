"""Independent negative-check review. Reads CAD only; never edits a board."""
from pathlib import Path
from fractions import Fraction as F
import pcbnew as p, json, hashlib
R=Path('/workspace/shared/maru60-resume');O=Path(__file__).resolve().parent
S=R/'selected-repo/pcb/experiments/resume-20261106-usb-pendant-prototype/pcb/maru60.kicad_pcb'
H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert H(S)=='41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5'
def points(r):return [(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
def winding(r,c):
 x,y=c;w=0
 for a,b in zip(r,r[1:]+r[:1]):
  cross=(b[0]-a[0])*(y-a[1])-(x-a[0])*(b[1]-a[1])
  assert not(cross==0 and min(a[0],b[0])<=x<=max(a[0],b[0]) and min(a[1],b[1])<=y<=max(a[1],b[1])), 'boundary witness'
  if a[1]<=y<b[1] and cross>0:w+=1
  elif b[1]<=y<a[1] and cross<0:w-=1
 return w!=0
def cover(s,c):
 return any(winding(points(s.COutline(i)),c) and not any(winding(points(s.CHole(i,h)),c)for h in range(s.HoleCount(i)))for i in range(s.OutlineCount()))
def plane(b,l):
 zs=[z for z in b.Zones()if z.GetNetname()=='GND' and z.IsOnLayer(l) and not z.GetIsRuleArea()];assert len(zs)==1
 return zs[0].GetFilledPolysList(l)
def strict_capsule(q,c):
 a=(q.GetStart().x,q.GetStart().y);b=(q.GetEnd().x,q.GetEnd().y);d=(b[0]-a[0],b[1]-a[1]);v=(c[0]-a[0],c[1]-a[1]);den=d[0]**2+d[1]**2;assert den>0
 t=max(F(0),min(F(1),(v[0]*d[0]+v[1]*d[1])/den));dist2=(v[0]-t*d[0])**2+(v[1]-t*d[1])**2;rad=F(q.GetWidth(),2)
 assert dist2<rad**2
 return str(dist2),float(rad)-(float(dist2)**.5)
def holes(b):
 out=[]
 for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]:
  if isinstance(q,(p.PCB_VIA,p.PAD))and q.HasHole():
   s=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(s,1,p.ERROR_OUTSIDE)
   out.append((s.BBox(),s))
 return out
source=p.LoadBoard(str(S));source_tracks={q.m_Uuid.AsString():q for q in source.GetTracks()};source_holes=holes(source)
rows=[]
for name in ['j2-b2','j1-b1','j0-b0']:
 D=O/'gpio25-transition/resume-runs'/name
 if not D.exists():D=O/'gpio25-transition/variants'/name
 evidence=D/'qa/FOREIGN_REFERENCE.json'
 if not evidence.exists():continue
 E=json.loads(evidence.read_text());assert E['verdict']=='REJECT_EXACT_FOREIGN_REFERENCE_LOSS'
 C=D/'candidate/pcb/maru60.kicad_pcb';candidate=p.LoadBoard(str(C));ct={q.m_Uuid.AsString():q for q in candidate.GetTracks()};hs=source_holes+holes(candidate)
 for e in E['exact_foreign_reference_loss_witnesses']:
  c=tuple(F(v)for v in e['point_nm']);q=source_tracks[e['uuid']];z=ct[e['uuid']]
  sig=lambda t:(t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetWidth(),t.GetLayer(),t.GetNetname())
  assert sig(q)==sig(z);assert q.GetNetname()=='COL14'
  dist2,margin=strict_capsule(q,c);l=source.GetLayerID(e['reference'])
  assert cover(plane(source,l),c) and not cover(plane(candidate,l),c)
  for bb,h in hs:
   if bb.GetX()<=c[0]<=bb.GetRight() and bb.GetY()<=c[1]<=bb.GetBottom():assert not cover(h,c)
  rows.append({'case':name,'candidate_sha256':H(C),'track_uuid':e['uuid'],'point_nm':e['point_nm'],'exact_squared_distance_to_track_center_nm2':dist2,'analytic_track_interior_margin_nm':margin,'source_plane_interior':True,'candidate_plane_exterior':True,'all_drills_excluded':len(hs),'method':'Independent nonzero winding + exact analytic track capsule; conservative hole polygons.'})
assert rows
(O/'independent-negative-witnesses.json').write_text(json.dumps({'source_sha256':H(S),'rows':rows,'scope':'Independent exact rejection witnesses only. No full acceptance or hardware test.'},indent=2)+'\n')
print(json.dumps(rows,indent=2))
