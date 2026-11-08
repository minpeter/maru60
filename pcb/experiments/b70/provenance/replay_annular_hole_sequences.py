from pathlib import Path
import os,sys,json,hashlib,time
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-b2l-native'
import pcbnew as p
import annular_source_hole_safe as h
D=Path(__file__).parent;f=D/(sys.argv[1]+'.kicad_pcb');out=D/(sys.argv[1]+'-hole-replay.json');sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before={str(f):sha(f),str(f.with_suffix('.kicad_pro')):sha(f.with_suffix('.kicad_pro'))};b=p.LoadBoard(str(f));allobjs=list(b.GetTracks())+[q for fp in b.GetFootprints()for q in fp.Pads()];drilled=[q for q in allobjs if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole()];cache={};rows=[];begin=time.time()
def stats(ps):return {'outlines':ps.OutlineCount(),'holes':sum(ps.HoleCount(i)for i in range(ps.OutlineCount())),'area_mm2':ps.Area()/1e12}
def compare(ps):
 other=p.SHAPE_POLY_SET(ps);other.Unfracture();minus=p.SHAPE_POLY_SET();plus=p.SHAPE_POLY_SET();minus.BooleanSubtract(ps,other);plus.BooleanSubtract(other,ps);return {'before':stats(ps),'after_Unfracture':stats(other),'lost_area_mm2':minus.Area()/1e12,'added_area_mm2':plus.Area()/1e12,'exact_area_equivalent':minus.Area()==0 and plus.Area()==0}
for z in b.Zones():
 if z.GetIsRuleArea()or z.GetNetname()not in h.ROOTS:continue
 for layer in h.LAYERS:
  if not z.IsOnLayer(layer):continue
  ps=z.GetFilledPolysList(layer)
  for ix in range(ps.OutlineCount()):
   island=ps.UnitSet(ix);clipped=[]
   for q in drilled:
    if not q.IsOnLayer(layer)or not q.GetBoundingBox().Intersects(island.BBox()):continue
    hs=q.GetEffectiveHoleShape()
    if not island.Collide(hs,0):continue
    u=h.uid(q)
    if u not in cache:
     hp=p.SHAPE_POLY_SET();hs.TransformToPolygon(hp,1,p.ERROR_OUTSIDE);cache[u]=hp
    island.BooleanSubtract(cache[u]);clipped.append(u)
   normalized=p.SHAPE_POLY_SET();normalized.BooleanAdd(island)
   rows.append({'net':z.GetNetname(),'zone_uuid':h.uid(z),'layer':b.GetLayerName(layer),'native_outline':ix,'actual_drills_subtracted':clipped,'physical_island_step':compare(island),'boundary_edges_normalization_step':compare(normalized)})
  print(z.GetNetname(),b.GetLayerName(layer),'cumulative',len(rows),'elapsed',round(time.time()-begin,2),flush=True)
assert before=={str(f):sha(f),str(f.with_suffix('.kicad_pro')):sha(f.with_suffix('.kicad_pro'))}
r={'board_sha256':sha(f),'source_project_sha256':sha(f.with_suffix('.kicad_pro')),'method':'Read-only exact original annular helper sequence replay on actual saved filled islands, identical physical drill subtraction and one-nanometer ERROR_OUTSIDE drill polygons. Compare omitted Unfracture against original call at both drilled-island and normalized-boundary stages using two directed native Boolean differences. This verifies geometry semantics, not final graph equivalence.','rows':rows,'changed_islands':[i for i,x in enumerate(rows)if not x['physical_island_step']['exact_area_equivalent']],'changed_boundary_geometries':[i for i,x in enumerate(rows)if not x['boundary_edges_normalization_step']['exact_area_equivalent']],'elapsed_seconds':time.time()-begin,'complete':True};out.write_text(json.dumps(r,indent=2));print('COMPLETE',len(rows),r['changed_islands'],r['changed_boundary_geometries'])
