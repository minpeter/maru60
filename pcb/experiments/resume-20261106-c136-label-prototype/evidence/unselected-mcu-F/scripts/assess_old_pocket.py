import sys,json,hashlib
sys.path.insert(0,'/workspace/shared/maru60-resume/mcu-routing/native-pylibs')
import pcbnew as p,shapely as s,numpy as np
from shapely.geometry import Polygon,Point,box
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu-led-repair');C=Path('/workspace/shared/maru60-resume/continuation-c782/mcu/frozen-C/pcb/maru60.kicad_pcb');F=R/'candidate-F/pcb/maru60.kicad_pcb';H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();V=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6));bb=[111.81,76.5,116.06,78.5];expanded=[110.81,75.5,117.06,79.5];nbox=p.BOX2I(V(*expanded[:2]),V(expanded[2]-expanded[0],expanded[3]-expanded[1]));clip=p.SHAPE_POLY_SET();clip.NewOutline()
for x,y in [(expanded[0],expanded[1]),(expanded[2],expanded[1]),(expanded[2],expanded[3]),(expanded[0],expanded[3])]:clip.Append(round(x*1e6),round(y*1e6))
def geom(ps):
 def pts(c):return [(c.CPoint(i).x/1e6,c.CPoint(i).y/1e6) for i in range(c.PointCount())]
 gs=[]
 for i in range(ps.OutlineCount()):
  q=s.make_valid(Polygon(pts(ps.COutline(i)),[pts(ps.CHole(i,h)) for h in range(ps.HoleCount(i))]));gs.extend(x for x in s.get_parts(q) if x.geom_type in ['Polygon','MultiPolygon'])
 return s.union_all(gs)
def poly(sh):z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,100,p.ERROR_OUTSIDE);z.Simplify();return z
def capture(path):
 b=p.LoadBoard(str(path));items=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()];obs=[[],[]];vobs=[];holes=[];own=[];signature={}
 for q in items:
  if not q.GetBoundingBox().Intersects(nbox):continue
  for i,l in enumerate([p.F_Cu,p.B_Cu]):
   if not q.IsOnLayer(l):continue
   g=geom(poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2) if isinstance(q,p.PCB_VIA) else q.GetEffectiveShape(l)));vobs.append(g)
   if q.GetNetname()!='MCU_GPIO27':obs[i].append(g)
  if isinstance(q,(p.PAD,p.PCB_VIA)) and q.HasHole():holes.append(geom(poly(q.GetEffectiveHoleShape())))
  if isinstance(q,p.PCB_VIA) and q.GetNetname()=='MCU_GPIO27':own.append(Point(q.GetPosition().x/1e6,q.GetPosition().y/1e6).buffer(q.GetWidth(p.F_Cu)/2e6+.205,resolution=64))
  if isinstance(q,p.PCB_TRACK):signature[q.m_Uuid.AsString()]={'net':q.GetNetname(),'layer':b.GetLayerName(q.GetLayer()),'start_mm':[q.GetStart().x/1e6,q.GetStart().y/1e6],'end_mm':[q.GetEnd().x/1e6,q.GetEnd().y/1e6],'width_mm':q.GetWidth(p.F_Cu)/1e6 if isinstance(q,p.PCB_VIA) else q.GetWidth()/1e6}
 planes=[]
 for l in [p.In1_Cu,p.In2_Cu]:
  polys=[]
  for z in b.Zones():
   if z.GetNetname()=='GND' and not z.GetIsRuleArea() and z.IsOnLayer(l):pp=p.SHAPE_POLY_SET();pp.BooleanIntersection(z.GetFilledPolysList(l),clip);polys.append(geom(pp))
  planes.append(s.union_all(polys).difference(s.union_all(holes)))
 ob=[s.union_all(x).buffer(.2251,resolution=32) for x in obs];vob=s.union_all(vobs).buffer(.456,resolution=32);ref=[s.union_all([pl,s.union_all(own)]).buffer(-.0751,resolution=32) for pl in planes];return ob,vob,ref,planes,signature
xs=111.81+np.arange(86)*.05;ys=76.5+np.arange(41)*.05;X,Y=np.meshgrid(xs,ys);rows=[];allm=[];sig=[];gs=[]
for label,path in [('rejected_C',C),('candidate_F',F)]:
 ob,vob,ref,planes,signature=capture(path);mask=np.stack([~s.intersects_xy(ob[i],X,Y)&s.intersects_xy(ref[i],X,Y) for i in range(2)]);ordinary=~s.intersects_xy(vob,X,Y)&mask[0]&mask[1];strong=ordinary.copy()
 for pl in planes:strong&=s.intersects_xy(pl.buffer(-.655,resolution=32),X,Y)
 rows.append({'label':label,'sha256':H(path),'allowed_track_grid_cells_F_B':mask.sum(axis=(1,2)).tolist(),'ordinary_via_cells':int(ordinary.sum()),'strong_plane_screen_via_cells':int(strong.sum())});allm.append((mask,ordinary,strong));sig.append(signature);gs.append((ob,vob,ref,planes))
changes={'newly_allowed_track_cells_F_B':((~allm[0][0])&allm[1][0]).sum(axis=(1,2)).tolist(),'newly_blocked_track_cells_F_B':(allm[0][0]&~allm[1][0]).sum(axis=(1,2)).tolist(),'ordinary_via_mask_changed_cells':int((allm[0][1]!=allm[1][1]).sum()),'strong_via_mask_changed_cells':int((allm[0][2]!=allm[1][2]).sum())};region=box(*bb);geometry=[]
for i,name in enumerate(['F','B']):geometry.append({'layer':name,'obstacle_symmetric_difference_inside_old_pocket_mm2':gs[0][0][i].symmetric_difference(gs[1][0][i]).intersection(region).area,'track_reference_mask_geometry_difference_mm2':gs[0][2][i].symmetric_difference(gs[1][2][i]).intersection(region).area,'physical_nearest_plane_geometry_difference_mm2':gs[0][3][i].symmetric_difference(gs[1][3][i]).intersection(region).area})
unchanged=[]
for u in ['d04bedc3-787f-4dd8-9a83-dc804564f50f','56cd01e8-ffb4-4d10-83b6-47e65b8fbc6a','5bcc3e01-7bf7-4484-aa21-f12e24210539']:
 unchanged.append({'uuid':u,'exact_primitive_signature_unchanged':sig[0].get(u)==sig[1].get(u),'geometry':sig[1].get(u)})
r={'candidate_sha256':H(F),'prior_C_sha256':H(C),'read_only_no_search_or_CAD_save':True,'region_mm':bb,'geometry_capture_region_with_1mm_margin':expanded,'grid_mm':.05,'samples_per_layer':len(xs)*len(ys),'prior_search_limits':'C search visited1842 F cells, no B cells, no reachable via sites; reached its y78.5 southern boundary. A bounding box is not a claim that every cell inside was reachable.','same_screen_parameters_as_prior':{'signal_width_mm':.15,'combined_trace_radius_clearance_mm':.2251,'trace_reference_erosion_mm':.0751,'via_old_shadow_buffer_mm':.456,'via_plane_boundary_buffer_mm':.655},'rows':rows,'mask_changes':changes,'candidate_strong_screen_via_sites_mm':[[round(float(xs[x]),6),round(float(ys[y]),6)] for y,x in zip(*np.nonzero(allm[1][2]))],'geometric_difference_within_old_pocket':geometry,'blocking_primitives':unchanged,'interpretation':'Static geometry/mask comparison only, no flood fill or route search. Equal masks inside the formerly bounded pocket do not prove the unbounded exterior inaccessible. The LED shift is farther north-west; the diagonal LED barrier, nearby GND vias and crystal-related plane boundary are not refactored here. A materially different next step would inspect the unsearched southern exterior or a specific local blocker/transition corridor, not count this rail-clearance repair as an escape from the pocket.','limits':'These screening margins are not DRC rules or SI qualification; actual future native fill and return checks remain necessary.'};(R/'qa/read-only-old-pocket-assessment.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
