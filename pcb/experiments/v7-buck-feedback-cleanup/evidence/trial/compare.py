import os,pathlib,hashlib,json,sys
D=pathlib.Path(__file__).parent
for k in ['CONFIG','CACHE','DATA']:os.environ['XDG_'+k+'_HOME']=str(D/k.lower())
import pcbnew as p
B=pathlib.Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb/maru60.kicad_pcb');C=D/'filled/pcb/maru60.kicad_pcb';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before=sha(B);assert before=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373';b=p.LoadBoard(str(B));c=p.LoadBoard(str(C));uid=lambda q:q.m_Uuid.AsString();layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];obs=lambda b:list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];old=obs(b);new=obs(c);oi={uid(q):q for q in old};ni={uid(q):q for q in new};ledger=json.load(open(D/'qa/build.json'));expected={q['uuid']for q in ledger['new_objects']};retired={q['uuid']for q in ledger['retired_objects']};assert set(oi)-set(ni)==retired and set(ni)-set(oi)==expected

def poly(s):
 z=p.SHAPE_POLY_SET();s.TransformToPolygon(z,1,p.ERROR_OUTSIDE);return z
def sub(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanSubtract(b);return z
def intersect(a,b):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(b);return z
def dump(ps):
 def ring(r):return[[r.CPoint(i).x,r.CPoint(i).y]for i in range(r.PointCount())]
 return [dict(outline=ring(ps.COutline(i)),holes=[ring(ps.CHole(i,j))for j in range(ps.HoleCount(i))])for i in range(ps.OutlineCount())]
def fp(q):
 r=dict(net=q.GetNetname(),layers=[l for l in layers if q.IsOnLayer(l)],shape={l:dump(poly(q.GetEffectiveShape(l)))for l in layers if q.IsOnLayer(l)})
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():r['hole']=dump(poly(q.GetEffectiveHoleShape()))
 return r
changes=[]
for u,q in oi.items():
 if u in retired:continue
 if fp(q)!=fp(ni[u]):changes.append(u)
print('old geometry changed',changes,flush=True);assert not changes
zold={uid(z):z for z in b.Zones()};znew={uid(z):z for z in c.Zones()};assert set(zold)==set(znew);zd=[];lost={};gained={}
for u,z in zold.items():
 zz=znew[u];assert dump(z.Outline())==dump(zz.Outline());assert z.GetLocalClearance()==zz.GetLocalClearance()and z.GetMinThickness()==zz.GetMinThickness()
 for l in layers:
  if not z.IsOnLayer(l):continue
  a=z.GetFilledPolysList(l);aa=zz.GetFilledPolysList(l);loss=sub(a,aa);gain=sub(aa,a);item=dict(uuid=u,net=z.GetNetname(),layer=b.GetLayerName(l),lost_area_mm2=loss.Area()/1e12,gained_area_mm2=gain.Area()/1e12,loss=dump(loss),gain=dump(gain));zd.append(item)
  if z.GetNetname()=='GND'and l in [p.In1_Cu,p.In2_Cu]:
   lost.setdefault(l,p.SHAPE_POLY_SET()).BooleanAdd(loss);gained.setdefault(l,p.SHAPE_POLY_SET()).BooleanAdd(gain)
# Physical original-shadow loss excludes physical old holes, including same-net ground holes.
for q in old:
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
  h=q.GetEffectiveHoleShape()
  for l,ps in lost.items():
   if q.IsOnLayer(l)and ps.BBox().Intersects(h.BBox()):ps.BooleanSubtract(poly(h))
shadow=[]
for q in old:
 if q.GetNetname()=='GND':continue
 for l,rl in [(p.F_Cu,p.In1_Cu),(p.B_Cu,p.In2_Cu)]:
  if not q.IsOnLayer(l):continue
  s=q.GetEffectiveShape(l);loss=lost[rl]
  if not s.BBox().Intersects(loss.BBox()):continue
  hit=intersect(poly(s),loss)
  if hit.Area()>0:
   a=dict(uuid=uid(q),net=q.GetNetname(),type=q.GetClass(),outer_layer=b.GetLayerName(l),reference_layer=b.GetLayerName(rl),lost_actual_full_width_shadow_mm2=hit.Area()/1e12,loss=dump(hit))
   if isinstance(q,p.PAD):a['pad']=q.GetParentFootprint().GetReference()+'.'+q.GetNumber()
   shadow.append(a)
# Determine actual new reference gaps, without inventing a transition exemption.
newref=[]
for u in expected:
 q=ni[u]
 for l,rl in [(p.F_Cu,p.In1_Cu),(p.B_Cu,p.In2_Cu)]:
  if not q.IsOnLayer(l):continue
  g=p.SHAPE_POLY_SET()
  for z in c.Zones():
   if z.GetNetname()=='GND'and z.IsOnLayer(rl):g.BooleanAdd(z.GetFilledPolysList(rl))
  # Physical new drill already lies in non-GND via void, but subtract explicitly.
  for hq in new:
   if isinstance(hq,(p.PAD,p.PCB_VIA))and hq.HasHole()and hq.IsOnLayer(rl):
    hs=hq.GetEffectiveHoleShape()
    if hs.BBox().Intersects(q.GetBoundingBox()):g.BooleanSubtract(poly(hs))
  miss=sub(poly(q.GetEffectiveShape(l)),g);newref.append(dict(uuid=u,type=q.GetClass(),outer_layer=b.GetLayerName(l),reference_layer=b.GetLayerName(rl),missing_full_projection_mm2=miss.Area()/1e12,missing=dump(miss)))
# Canonical native serialization makes structural text comparison independent of source formatting.
p.SaveBoard(str(D/'qa/source-canonical.kicad_pcb'),b)
sys.path.insert(0,str(D/'tools'));from sexpr_spans import children,head,field
source_nodes=[t for _,_,t in children((D/'qa/source-canonical.kicad_pcb').read_text())if head(t)!='zone'and not any(('"'+u+'"')in t for u in retired)];candidate_nodes=[t for _,_,t in children(C.read_text())if head(t)!='zone'and not any(('"'+u+'"')in t for u in expected)];canonical_nonzone_exact=source_nodes==candidate_nodes
r=dict(status='UNSELECTED BUCK dead-arm actual native refill comparison; no adoption/analog claim',source_sha256=before,filled_sha256=sha(C),old_electrical_geometry_changed=changes,canonical_nonzone_nodes_exact=canonical_nonzone_exact,new_uuid_set=sorted(expected),retired_uuid_set=sorted(retired),zone_deltas=zd,affected_old_non_GND_shadows=shadow,all_retained_non_GND_shadow_loss_mm2=sum(a['lost_actual_full_width_shadow_mm2']for a in shadow),new_projection_reference_gaps=newref,outer_zone_delta_area_mm2=sum(a['lost_area_mm2']+a['gained_area_mm2']for a in zd if a['layer']in ['F.Cu','B.Cu']),notes=['Shadow loss is actual source saved inner fill minus actual candidate saved inner fill intersected with original full-width non-GND copper projections, with physical original holes removed.','No endpoint/transition exemption is assumed. New via and track projection gaps are reported in full.','Canonical nonzone comparison excludes declared retired/source and new/candidate UUIDs and all zone nodes; individual zone outlines/clearance/min-thickness are checked separately.']);(D/'qa/actual-reference-comparison.json').write_text(json.dumps(r,indent=2));assert sha(B)==before;print('RESULT',json.dumps({k:v for k,v in r.items()if k not in ['zone_deltas','new_projection_reference_gaps']},indent=2),flush=True)
