import os,sys,json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 d=W/'support-runtime'/k.lower();d.mkdir(parents=True,mode=0o700);os.environ[k]=str(d)
import pcbnew as p
H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();D=Path('/tmp/v7-c124-d-actual');BP=Path('/tmp/v7-support-endpoint-trial/filled/pcb/maru60.kicad_pcb');bh=H(BP);assert bh=='abdbf4c80e11cadc525389060d2215b73fc3cbcc85b2bff6ddb0e8d2581e052d';b=p.LoadBoard(str(BP));assert p.GetBuildVersion()=='9.0.2+dfsg-1';U=lambda q:q.m_Uuid.AsString();items=list(b.GetTracks())+[q for fp in b.GetFootprints()for q in fp.Pads()];changed={'abcd4fb1-881b-43f9-906e-39d93366692e','ae94ea04-2d21-5f84-8952-7f8960275e00','f41eeb49-8180-5bac-bccf-c1a0b3b4c547'}
def polygon(shape,out=False):
 q=p.SHAPE_POLY_SET();shape.TransformToPolygon(q,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);q.Simplify();return q
def decode(rows):
 q=p.SHAPE_POLY_SET()
 for row in rows:
  c=p.SHAPE_LINE_CHAIN()
  for pt in row['outer']:c.Append(*pt)
  c.SetClosed(True);i=q.AddOutline(c)
  for pts in row['holes']:
   c=p.SHAPE_LINE_CHAIN()
   for pt in pts:c.Append(*pt)
   c.SetClosed(True);q.AddHole(c,i)
 return q
holes=[polygon(q.GetEffectiveHoleShape(),True)for q in items if isinstance(q,(p.PCB_VIA,p.PAD))and q.HasHole()];assert len(holes)==1270
source_paths={'original':D/'qa/source-local-material.json','C':Path('/tmp/v7-c124-c-actual/qa/actual-local-material.json')};src={k:{r['uuid']:decode(r['metal_B'])for r in json.loads(v.read_text())['nodes']}for k,v in source_paths.items()};rows=json.loads((D/'qa/actual-strong-support-reference.json').read_text())['all_original_external_plus_C_boundary_support'];reports=[]
for row in rows:
 old=src['original'if row['source']=='original'else'C'];patch=p.SHAPE_POLY_SET();patch.BooleanIntersection(old[row['old']],old[row['target']]);bb=patch.BBox();bb.Inflate(10);union=p.SHAPE_POLY_SET();ids=[]
 for q in items:
  if not q.IsOnLayer(p.B_Cu)or q.GetNetname()!=row['net']or U(q)==row['target']:continue
  sh=q.GetEffectiveShape(p.B_Cu)
  if not sh.BBox().Intersects(bb):continue
  poly=polygon(sh)
  for hole in holes:
   if hole.BBox().Intersects(poly.BBox()):poly.BooleanSubtract(hole)
  union.BooleanAdd(poly);ids.append(U(q))
 loss=p.SHAPE_POLY_SET(patch);loss.BooleanSubtract(union);assert loss.OutlineCount()==0 and loss.Area()==0
 patch.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);union.Inflate(-2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);loss=p.SHAPE_POLY_SET(patch);loss.BooleanSubtract(union);assert loss.OutlineCount()==0 and loss.Area()==0
 reports.append({'source':row['source'],'old':row['old'],'target':row['target'],'net':row['net'],'actual_direct_native_object_contributors':ids,'exact_support_loss_mm2':0,'outward2nm_old_vs_inward2nm_actual_support_loss_mm2':0})
refs=[]
for lid in [p.In1_Cu,p.In2_Cu]:
 plane=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.IsOnLayer(lid)and z.GetNetname()=='GND':plane.BooleanAdd(z.GetFilledPolysList(lid))
 for hole in holes:
  if hole.BBox().Intersects(plane.BBox()):plane.BooleanSubtract(hole)
 for q in b.GetTracks():
  if U(q)not in changed or q.GetNetname()=='GND':continue
  shadow=polygon(q.GetEffectiveShape(p.B_Cu),True);shadow.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);shadow.BooleanSubtract(plane);assert shadow.OutlineCount()==0 and shadow.Area()==0;refs.append({'uuid':U(q),'plane':b.GetLayerName(lid),'outward2nm_projection_loss_mm2':0})
assert len(reports)==14 and len(refs)==4 and H(BP)==bh
out={'status':'PASS independent native reconstruction of actual support union and all-hole reference','board_sha256':bh,'source_material_files':{str(v):H(v)for v in source_paths.values()},'source_support_ledger_sha256':H(D/'qa/actual-strong-support-reference.json'),'actual_through_hole_count':len(holes),'supports':reports,'new_reference_projections':refs,'all_actual_support_geometry_reloaded_from_candidate':True,'cached_baseline_actual_object_material_not_used':True,'no_area_tolerance':True};(W/'SUPPORT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'pass':True,'support_patches':len(reports),'reference_projections':len(refs),'all_holes':len(holes)}))
