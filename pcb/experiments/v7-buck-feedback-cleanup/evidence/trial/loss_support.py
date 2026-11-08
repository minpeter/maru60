import os,pathlib,json,hashlib
D=pathlib.Path(__file__).parent
for k in ['CONFIG','CACHE','DATA']:os.environ['XDG_'+k+'_HOME']=str(D/k.lower())
import pcbnew as p
A=D/'source/pcb/maru60.kicad_pcb';B=D/'filled/pcb/maru60.kicad_pcb';a=p.LoadBoard(str(A));b=p.LoadBoard(str(B));uid=lambda q:q.m_Uuid.AsString();obs=list(a.GetTracks())+[q for f in a.GetFootprints()for q in f.Pads()]
def poly(s):
 z=p.SHAPE_POLY_SET();s.TransformToPolygon(z,1,p.ERROR_OUTSIDE);return z
def cross(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(b);return z
cut=poly(p.SHAPE_SEGMENT(p.VECTOR2I(178150000,85750000),p.VECTOR2I(181000000,85750000),150000));cut.BooleanAdd(poly(p.SHAPE_CIRCLE(p.VECTOR2I(178150000,85750000),450500)));rows=[]
for l in [p.In1_Cu,p.In2_Cu]:
 z=next(z for z in a.Zones()if z.GetNetname()=='GND'and z.IsOnLayer(l));zz=next(q for q in b.Zones()if uid(q)==uid(z));loss=p.SHAPE_POLY_SET(z.GetFilledPolysList(l));loss.BooleanSubtract(zz.GetFilledPolysList(l));hits=[];tested=[]
 for q in obs:
  if q.GetNetname()!='GND'or not q.IsOnLayer(l):continue
  s=q.GetEffectiveShape(l)
  if not s.BBox().Intersects(loss.BBox()):continue
  cu=poly(s)
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():cu.BooleanSubtract(poly(q.GetEffectiveHoleShape()))
  support=cross(cu,z.GetFilledPolysList(l));hit=cross(support,loss);tested.append(uid(q))
  if hit.Area()>0:hits.append(dict(uuid=uid(q),type=q.GetClass(),lost_contact_support_mm2=hit.Area()/1e12))
 rows.append(dict(layer=a.GetLayerName(l),reported_loss_mm2=loss.Area()/1e12,overlap_authorized_removed_arm_and_via_cut_region_mm2=cross(loss,cut).Area()/1e12,source_GND_contact_support_hits=hits,source_GND_objects_bbox_tested=tested,all_source_GND_on_layer_count=sum(q.GetNetname()=='GND'and q.IsOnLayer(l)for q in obs)))
r=dict(source_sha256=hashlib.sha256(A.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256(B.read_bytes()).hexdigest(),layers=rows,scope='Tests positive area of each actual old inner-plane GND copper/annular contact support against raw native loss polygons. No polygon discarded. Cut region is exact retired deadarm copper plus old via nominal .4505mm clearance envelope. Existing full-board non-GND shadow proof is separate. Strict global no-loss remains failed irrespective of zero support overlap.');(D/'qa/loss-support.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
