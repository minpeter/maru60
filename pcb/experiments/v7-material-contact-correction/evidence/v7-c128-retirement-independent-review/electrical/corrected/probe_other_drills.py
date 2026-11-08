from pathlib import Path
import os,json
D=Path('/tmp/v7-c128-retirement-independent-review/electrical/corrected');os.environ['XDG_CONFIG_HOME']=str(D/'probe/config');Path(os.environ['XDG_CONFIG_HOME']).mkdir(parents=True,exist_ok=True)
import pcbnew as p
b=p.LoadBoard('/tmp/v7-c128-stub-retirement-aead/filled/pcb/maru60.kicad_pcb');idx={q.m_Uuid.AsString():q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};g=json.load(open(D/'cafa/physical-graph.json'));bad=json.load(open(D.parent/'canonical-direct-support-audit.json'))['lost_positive_edges'];short={x[0]for x in bad};layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
def poly(sh):
 r=p.SHAPE_POLY_SET();sh.TransformToPolygon(r,1,p.ERROR_OUTSIDE);return r
drills=[]
for q in idx.values():
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():drills.append((q.m_Uuid.AsString(),q.GetEffectiveHoleShape(),q))
def physical_copper(q,l):
 r=p.SHAPE_POLY_SET();shape=p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l);shape.TransformToPolygon(r,1,p.ERROR_INSIDE);removed=[]
 for uid,h,owner in drills:
  if owner.IsOnLayer(l)and r.BBox().Intersects(h.BBox()):r.BooleanSubtract(poly(h));removed.append(uid)
 return r,removed
records=[]
for a,c,saved in g['direct_edges']:
 if not set([a,c])&short:continue
 support=[];subtracted={}
 for l in layers:
  if idx[a].IsOnLayer(l)and idx[c].IsOnLayer(l):
   ap,ah=physical_copper(idx[a],l);bp,bh=physical_copper(idx[c],l);t=p.SHAPE_POLY_SET();t.BooleanIntersection(ap,bp);ar=t.Area()/1e12
   if ar>0:support.append([b.GetLayerName(l),ar])
   subtracted[b.GetLayerName(l)]=dict(a_holes=ah,b_holes=bh,a_physical_area=ap.Area()/1e12,b_physical_area=bp.Area()/1e12)
 records.append(dict(a=a,b=c,a_type=idx[a].GetClass(),b_type=idx[c].GetClass(),canonical_own_hole_support=saved,all_overlapping_hole_support=support,details=subtracted))
shortdata=[]
for u in short:
 q=idx[u];l=q.GetLayer();cu,holes=physical_copper(q,l);shortdata.append(dict(uuid=u,net=q.GetNetname(),start=[q.GetStart().x/1e6,q.GetStart().y/1e6],end=[q.GetEnd().x/1e6,q.GetEnd().y/1e6],width_mm=q.GetWidth()/1e6,length_mm=q.GetLength()/1e6,physical_area_after_all_drills_mm2=cu.Area()/1e12,overlapping_holes=holes))
out=dict(status='FOCUSED COUNTEREXAMPLE AUDIT; completed v1 corrected exports unchanged',shorttracks=shortdata,incident_edges=records,new_zero_contact_count=sum(not x['all_overlapping_hole_support']for x in records),changed_support_count=sum(x['canonical_own_hole_support']!=x['all_overlapping_hole_support']for x in records),scope='Only incident saved direct contacts of the three observed false track-via shorttracks. Subtracts every overlapping physical hole from each object shape on the tested layer. Not a global corrected export.');(D/'other-drill-probe.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
