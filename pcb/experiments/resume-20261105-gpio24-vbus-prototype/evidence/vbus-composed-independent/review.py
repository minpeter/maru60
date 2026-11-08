from pathlib import Path
import pcbnew as p,json,hashlib
R=Path('/workspace/shared/maru60-resume');O=R/'combined-vbus-independent'
def poly(s,out=False):
 q=p.SHAPE_POLY_SET();s.TransformToPolygon(q,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);q.Simplify();return q
def diff(a,b):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(b);return q
def inter(a,b):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,b);return q
def contour(q):
 def ring(r):
  v=[(r.CPoint(i).x,r.CPoint(i).y) for i in range(r.PointCount())];low=min(v);return min(tuple(v[i:]+v[:i])for i,x in enumerate(v)if x==low)
 return sorted((ring(q.COutline(i)),sorted(ring(q.CHole(i,h))for h in range(q.HoleCount(i))))for i in range(q.OutlineCount()))
rows=[];zones=[]
for path in [R/'header-routing/frozen24move/pcb/maru60.kicad_pcb',R/'combined-trial/pcb/maru60.kicad_pcb']:
 b=p.LoadBoard(str(path));its=list(b.GetTracks())+[x for f in b.GetFootprints() for x in f.Pads()];via=next(x for x in its if x.m_Uuid.AsString().startswith('30f42945'));ann=diff(poly(p.SHAPE_CIRCLE(via.GetPosition(),via.GetWidth(p.In1_Cu)//2)),poly(via.GetEffectiveHoleShape(),True));allholes=p.SHAPE_POLY_SET();near=p.SHAPE_POLY_SET();ids=[]
 for x in its:
  if isinstance(x,(p.PAD,p.PCB_VIA))and x.HasHole():
   h=poly(x.GetEffectiveHoleShape(),True);allholes.Append(h)
   if h.BBox().Intersects(ann.BBox()):near.Append(h);ids.append(x.m_Uuid.AsString())
 allholes.Simplify();near.Simplify();zs={};rr=[]
 for z in b.Zones():
  for l in [p.In1_Cu,p.In2_Cu]:
   if not z.IsOnLayer(l) or z.GetIsRuleArea():continue
   raw=p.SHAPE_POLY_SET(z.GetFilledPolysList(l));zs[l]=raw
   # Local-first clipping versus global-hole clipping, mathematically equivalent.
   direct=inter(raw,ann);local=diff(direct,near);glob=inter(diff(raw,allholes),ann)
   rr.append(dict(layer=b.GetLayerName(l),direct_raw_annulus_area=direct.Area()/1e12,local_holes_contact_area=local.Area()/1e12,global_holes_contact_area=glob.Area()/1e12,annulus_area=ann.Area()/1e12,direct_contact_contour=contour(direct),local_contact_contour=contour(local),local_drill_ids=ids))
 rows.append(dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),contacts=rr));zones.append(zs)
summary=[]
for l in zones[0]:
 loss=diff(zones[0][l],zones[1][l]);gain=diff(zones[1][l],zones[0][l]);summary.append(dict(layer=l,raw_fill_loss_mm2=loss.Area()/1e12,raw_fill_gain_mm2=gain.Area()/1e12,raw_loss_contours=contour(loss)))
for i in range(2):print('CONTACT',rows[i]['sha256'],[{k:v for k,v in rr.items()if 'contour'not in k}for rr in rows[i]['contacts']])
print('RAW FILL',summary)
result=dict(boards=rows,raw_fills=summary,local_contact_contours_equal=all(rows[0]['contacts'][i]['local_contact_contour']==rows[1]['contacts'][i]['local_contact_contour']for i in range(2)))
(O/'independent-local-contact.json').write_text(json.dumps(result,indent=2)+'\n')
