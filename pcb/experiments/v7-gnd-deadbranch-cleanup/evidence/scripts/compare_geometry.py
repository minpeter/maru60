from pathlib import Path
import hashlib,json,re,pcbnew as p
from sexpr_spans import children,head,field
R=Path('/tmp/v7-gnd-tail-cleanup-aead'); A=R/'source/pcb/maru60.kicad_pcb';B=R/'filled/pcb/maru60.kicad_pcb'
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();c=json.loads((R/'BUILD_CONTRACT.json').read_text());assert H(A)==c['source_sha256'];before=H(B)
ret=set(c['retired_uuids']);uid=lambda q:q.m_Uuid.AsString()
def raw_nodes(P):return[t for a,z,t in children(P.read_text())]
def uuid(t):
 f=field(t,'uuid')
 return re.search(r'"([^"]+)"',f).group(1) if f else None
old=raw_nodes(A);new=raw_nodes(B)
kept=[t for t in old if head(t)!='zone' and uuid(t) not in ret]
new_nonzone=[t for t in new if head(t)!='zone']
assert kept==new_nonzone,'unexpected non-zone record changes'
oldz={uuid(t):t for t in old if head(t)=='zone'};newz={uuid(t):t for t in new if head(t)=='zone'};assert oldz.keys()==newz.keys()
configs=[]
for u,t in oldz.items():
 ca=[q for _,_,q in children(t)if head(q)!='filled_polygon'];cb=[q for _,_,q in children(newz[u])if head(q)!='filled_polygon'];assert ca==cb,('zone config',u);configs.append(u)
manifest=json.loads((R/'SOURCE_TREE_MANIFEST.json').read_text());changed_companions=[]
for rel,d in manifest.items():
 if rel=='maru60.kicad_pcb':continue
 if H(R/'filled/pcb'/rel)!=d['sha256']:changed_companions.append(rel)
assert not changed_companions
a=p.LoadBoard(str(A));b=p.LoadBoard(str(B));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
def dump(ps):
 def ring(r):return[[r.CPoint(i).x,r.CPoint(i).y]for i in range(r.PointCount())]
 return[{'outline':ring(ps.COutline(i)),'holes':[ring(ps.CHole(i,j))for j in range(ps.HoleCount(i))]}for i in range(ps.OutlineCount())]
def diff(x,y):
 r=p.SHAPE_POLY_SET(x);r.BooleanSubtract(y);return r
az={uid(z):z for z in a.Zones()};bz={uid(z):z for z in b.Zones()};zd=[]
for u,z in az.items():
 for l in layers:
  if not z.IsOnLayer(l):continue
  op=z.GetFilledPolysList(l);np=bz[u].GetFilledPolysList(l);loss=diff(op,np);gain=diff(np,op)
  zd.append({'uuid':u,'net':z.GetNetname(),'layer':a.GetLayerName(l),'raw_zone_record_identical':oldz[u]==newz[u],'native_loss_estimate_mm2':loss.Area()/1e12,'native_gain_estimate_mm2':gain.Area()/1e12,'loss':dump(loss),'gain':dump(gain)})
oi={uid(q):q for q in list(a.GetTracks())+[q for f in a.GetFootprints()for q in f.Pads()]};ni={uid(q):q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};assert set(oi)-set(ni)==ret and not set(ni)-set(oi)
holes=lambda idx:{u:q for u,q in idx.items() if q.GetClass() in ('PAD','PCB_VIA') and q.HasHole()}
oh=holes(oi);nh=holes(ni);assert set(oh)==set(nh)
for u in nh:
 assert dump((lambda z:(nh[u].GetEffectiveHoleShape().TransformToPolygon(z,1,p.ERROR_OUTSIDE),z)[1])(p.SHAPE_POLY_SET()))==dump((lambda z:(oh[u].GetEffectiveHoleShape().TransformToPolygon(z,1,p.ERROR_OUTSIDE),z)[1])(p.SHAPE_POLY_SET()))
report={'status':'UNSELECTED native/serialized delta screen; strict raw-contour reviewer governs acceptance','source_sha256':H(A),'candidate_sha256':before,'retired_uuids':sorted(ret),'retained_nonzone_records_byte_identical':True,'zone_configs_byte_identical':True,'companions_byte_identical':True,'companion_files':len(manifest)-1,'source_drills':len(oh),'candidate_drills':len(nh),'only_removed_drill':c['removed_via'],'all_retained_drill_shapes_exact':True,'retained_copper_material_inclusion_argument':'Every retained raw copper shape and every through-drill are identical, so each retained object material is identical. Saved-plane inclusion is separately checked against exact serialized zone records.','zone_deltas':zd,'limitations':['Native integer polygon Boolean areas are preliminary estimates, not substitutes for exact serialized-contour classification.','No inherited global hardware, stability, SI, EMC or manufacturing qualification.']}
assert H(A)==c['source_sha256'] and H(B)==before
(R/'qa/geometry-delta.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='zone_deltas'},indent=2));print('ZONE_DELTAS',json.dumps([{k:v for k,v in r.items()if k not in ('loss','gain')}for r in zd],indent=2))
