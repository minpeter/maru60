from pathlib import Path
import os,json,time,collections,sys
D=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected_v2');os.environ['XDG_CONFIG_HOME']=str(D/'inventory/config');Path(os.environ['XDG_CONFIG_HOME']).mkdir(parents=True,exist_ok=True)
import pcbnew as p
b=p.LoadBoard('/tmp/v7-c128-stub-retirement-aead/source/pcb/maru60.kicad_pcb');layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];idx={q.m_Uuid.AsString():q for q in items};uid=lambda q:q.m_Uuid.AsString()
def poly(sh,out=False):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);z.Simplify();return z
def box(r):
 b=r.BBox();return b.GetX(),b.GetY(),b.GetRight(),b.GetBottom()
def hit(a,b):return a[0]<=b[2]and a[2]>=b[0]and a[1]<=b[3]and a[3]>=b[1]
drills=[];types=collections.Counter()
for q in items:
 if isinstance(q,p.PCB_VIA):
  assert q.GetViaType()==p.VIATYPE_THROUGH and all(q.IsOnLayer(l)for l in layers);types['through_vias']+=1
 if isinstance(q,p.PAD)and q.HasHole():
  assert q.GetAttribute()in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH];types['PTH'if q.GetAttribute()==p.PAD_ATTRIB_PTH else'NPTH']+=1
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
  ps=poly(q.GetEffectiveHoleShape(),True);drills.append((uid(q),box(ps),ps))
start=time.monotonic();zero=[];multi=[];counts=collections.Counter();barrelissues=[]
for q in items:
 for l in layers:
  if not q.IsOnLayer(l):continue
  s=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l));bb=box(s);holes=[]
  for u,hb,h in drills:
   if hit(bb,hb):s.BooleanSubtract(h);holes.append(u)
  areas=[]
  for i in range(s.OutlineCount()):
   z=p.SHAPE_POLY_SET();z.AddOutline(s.COutline(i))
   for h in range(s.HoleCount(i)):z.AddHole(s.CHole(i,h),0)
   if z.Area()>0:areas.append(z.Area()/1e12)
  r=dict(uuid=uid(q),type=q.GetClass(),net=q.GetNetname(),layer=b.GetLayerName(l),positive_components=len(areas),areas_mm2=areas,overlapping_holes=holes)
  if isinstance(q,p.PAD):r.update(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber(),attribute=int(q.GetAttribute()))
  counts['object_layers']+=1
  if not areas:zero.append(r)
  if len(areas)>1:multi.append(r)
  if isinstance(q,p.PCB_VIA)or isinstance(q,p.PAD)and q.GetAttribute()==p.PAD_ATTRIB_PTH:
   if len(areas)!=1:barrelissues.append(r)
print('DONE seconds',time.monotonic()-start,flush=True);out=dict(actual_hole_type_counts=dict(types),native_item_types=dict(collections.Counter(q.GetClass()for q in items)),object_layers=counts['object_layers'],zero_object_layers=zero,multiple_component_object_layers=multi,plated_barrel_component_issues=barrelissues,zero_count=len(zero),multi_count=len(multi));(D/'source-material-inventory.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items()if k not in ['zero_object_layers','multiple_component_object_layers']},indent=2))
