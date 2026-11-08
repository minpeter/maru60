import os,sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;B=Path('/tmp/v7-buck-deadarm-trial-2c7e/filled/pcb/maru60.kicad_pcb');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f'
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 q=R/'obstacle-runtime'/k;q.mkdir(parents=True,mode=0o700,exist_ok=False);os.environ[k]=str(q)
import pcbnew as p
assert H(B)==expected and p.GetBuildVersion()=='9.0.2+dfsg-1';b=p.LoadBoard(str(B));uid=lambda q:q.m_Uuid.AsString();proof=json.loads((R/'boundary-envelope-proof.json').read_text());items=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];holes=[(uid(q),q.GetEffectiveHoleShape()) for q in items if isinstance(q,(p.PAD,p.PCB_VIA)) and q.HasHole()]
def hull(ps):
 ps=sorted(set(map(tuple,ps)));cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);lo=[];hi=[]
 for a in ps:
  while len(lo)>1 and cross(lo[-2],lo[-1],a)<=0:lo.pop()
  lo.append(a)
 for a in reversed(ps):
  while len(hi)>1 and cross(hi[-2],hi[-1],a)<=0:hi.pop()
  hi.append(a)
 z=lo[:-1]+hi[:-1];q=p.SHAPE_POLY_SET();line=p.SHAPE_LINE_CHAIN()
 for x,y in z:line.Append(p.VECTOR2I(x,y))
 line.SetClosed(True);q.AddOutline(line);return q,z
# Native collision call control: known point-distance cases, not CAD changes.
test,_=hull([(0,0),(100,0),(100,100),(0,100)]);assert test.Collide(p.SHAPE_CIRCLE(p.VECTOR2I(50,50),10),0);assert not test.Collide(p.SHAPE_CIRCLE(p.VECTOR2I(300,50),10),100);assert test.Collide(p.SHAPE_CIRCLE(p.VECTOR2I(300,50),10),200)
results=[]
for lp in proof['layers']:
 l={'In1.Cu':p.In1_Cu,'In2.Cu':p.In2_Cu}[lp['layer']];zone=next(z for z in b.Zones() if z.GetNetname()=='GND' and z.IsOnLayer(l));clearance=zone.GetLocalClearance();assert clearance==200000
 copper=[(uid(q),q.GetNetname(),p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2) if isinstance(q,p.PCB_VIA) else q.GetEffectiveShape(l)) for q in items if q.IsOnLayer(l) and q.GetNetname()!='GND'];records=[]
 for i,patch in enumerate(lp['patches']):
  h,vertices=hull(patch['old']+patch['new']);box=h.BBox();box.Inflate(clearance+2);checks=[];bad=[]
  for typ,objs in [('foreign_inner_copper',copper),('actual_drill_hole',[(u,'',sh) for u,sh in holes])]:
   for u,net,sh in objs:
    if not box.Intersects(sh.BBox()):continue
    coll=bool(h.Collide(sh,clearance));checks.append({'kind':typ,'uuid':u,'net':net,'collides_at_200000nm_clearance':coll})
    if coll:bad.append(checks[-1])
  records.append({'patch':i,'integer_convex_hull_covers_all_exact_difference_cells':vertices,'tested_nearby_obstacles':checks,'failure_count':len(bad)})
 results.append({'layer':lp['layer'],'zone_clearance_nm':clearance,'all_inner_foreign_objects_considered':len(copper),'all_actual_holes_considered':len(holes),'patch_count':len(records),'failures':sum(r['failure_count'] for r in records),'patches':records})
assert H(B)==expected
r={'candidate_sha256':expected,'source_sha256':proof['source_sha256'],'one_board_load_no_save_fill':True,'native_build':p.GetBuildVersion(),'native_coordinate_grid':{'PCB_IU_PER_MM':p.PCB_IU_PER_MM,'FromMM_1':p.FromMM(1),'ToMM_1_IU':p.ToMM(1),'VECTOR2I_doc':p.VECTOR2I.__doc__,'coordinate_type':type(p.VECTOR2I(1,2).x).__name__},'native_collision_controls_pass':True,'all_remote_patch_hulls_clear_all_actual_holes_and_foreign_inner_copper_at_normal_zone_clearance':all(x['failures']==0 for x in results),'layers':results,'limitation':'Native collision checks use a conservative integer convex hull around each exact rational change band. They cover both gain and loss; they are separate from the exact opposite-material-distance proof and do not waive source/contour gates or constitute analog qualification.'}
(R/'remote-obstacle-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='layers'},indent=2));print(json.dumps([{k:v for k,v in x.items() if k!='patches'} for x in results],indent=2))
