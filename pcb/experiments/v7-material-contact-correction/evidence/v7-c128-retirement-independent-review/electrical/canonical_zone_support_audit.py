from pathlib import Path
import os,json,hashlib,collections,sys
O=Path('/tmp/v7-c128-retirement-independent-review/electrical');os.environ['XDG_CONFIG_HOME']=str(O/'runtime/config')
import pcbnew as p
phase=sys.argv[1];D=Path('/tmp/v7-c128-stub-retirement-aead');g=json.load(open(D/'qa'/('source-physical-graph.json' if phase=='source' else 'candidate-physical-graph.json')));B=D/('source'if phase=='source'else'filled')/'pcb/maru60.kicad_pcb';b=p.LoadBoard(str(B));idx={q.m_Uuid.AsString():q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};cache={}
def poly(sh,out=False):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);return z
def cu(u,l):
 key=u,l
 if key not in cache:
  q=idx[u];z=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l))
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():z.BooleanSubtract(poly(q.GetEffectiveHoleShape(),True))
  cache[key]=z
 return cache[key]
drills=p.SHAPE_POLY_SET()
for q in idx.values():
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():drills.Append(poly(q.GetEffectiveHoleShape(),True))
drills.Simplify();wrong=[];lost=[];corrected=[];zoneidx={q.m_Uuid.AsString():q for q in b.Zones()}
for zr in g['zones']:
 z=zoneidx[zr['uuid']];l=b.GetLayerID(zr['layer']);physical=p.SHAPE_POLY_SET(z.GetFilledPolysList(l));physical.BooleanSubtract(drills)
 assert physical.OutlineCount()==zr['physical_outlines']
 for component in zr['components']:
  zid=component['id'];i=int(zid.split(':')[-1]);s=p.SHAPE_POLY_SET();s.AddOutline(physical.COutline(i))
  for h in range(physical.HoleCount(i)):s.AddHole(physical.CHole(i,h),0)
  assert s.Area()/1e12==component['area_mm2']
  for node,u,saved in g['zone_edges']:
   if node!=zid:continue
   overlap=p.SHAPE_POLY_SET();overlap.BooleanIntersection(cu(u,l),s);ar=overlap.Area()/1e12;corrected.append([node,u,ar])
   if ar!=saved:wrong.append(dict(zone=node,object=u,saved=saved,actual=ar,type=idx[u].GetClass()))
   if ar<=0:lost.append([node,u,saved])
 print(phase,zr['layer'],zr['uuid'],'DONE',flush=True)
r=dict(phase=phase,board_sha256=hashlib.sha256(B.read_bytes()).hexdigest(),saved_zone_edges=len(g['zone_edges']),checked_zone_edges=len(corrected),changed_support_count=len(wrong),changed_support_edges=wrong,lost_positive_edges=lost,scope='Recompute support for every existing saved zone-edge against exact saved filled polygons, after all canonical physical holes removed; no connectivity discovery, refill or new graph export.')
(O/('canonical-zone-support-'+phase+'.json')).write_text(json.dumps(r,indent=2));(O/('canonical-zone-edges-'+phase+'.json')).write_text(json.dumps(corrected,indent=2));print(json.dumps({k:v for k,v in r.items()if k!='changed_support_edges'},indent=2))
