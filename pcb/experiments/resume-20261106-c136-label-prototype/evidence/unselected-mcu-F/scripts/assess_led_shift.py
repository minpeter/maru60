import sys,json,hashlib,math
sys.path.insert(0,'/workspace/shared/maru60-resume/mcu-routing/native-pylibs')
import pcbnew as p,shapely as s
from shapely.geometry import Polygon,box
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu-led-repair');S=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu/source/pcb/maru60.kicad_pcb');E=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu/repair-E/pcb/maru60.kicad_pcb');H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert H(S)=='9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed';b=p.LoadBoard(str(S));e=p.LoadBoard(str(E));uid=lambda q:q.m_Uuid.AsString();V=lambda a:p.VECTOR2I(round(a[0]*1e6),round(a[1]*1e6));xy=lambda a:[a.x/1e6,a.y/1e6]
def poly(sh,out=True):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);z.Simplify();return z
def geom(ps):
 def pts(c):return [(c.CPoint(i).x/1e6,c.CPoint(i).y/1e6) for i in range(c.PointCount())]
 gs=[]
 for i in range(ps.OutlineCount()):
  q=s.make_valid(Polygon(pts(ps.COutline(i)),[pts(ps.CHole(i,h)) for h in range(ps.HoleCount(i))]));gs.extend(x for x in s.get_parts(q) if x.geom_type in ['Polygon','MultiPolygon'])
 return s.union_all(gs)
def sh(q,l):return poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2) if isinstance(q,p.PCB_VIA) else q.GetEffectiveShape(l))
def desc(q):
 d={'uuid':uid(q),'class':q.GetClass(),'net':q.GetNetname(),'layers':[b.GetLayerName(l) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu] if q.IsOnLayer(l)]}
 if isinstance(q,p.PAD):d.update(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber(),pos_mm=xy(q.GetPosition()))
 elif isinstance(q,p.PCB_VIA):d.update(pos_mm=xy(q.GetPosition()),diameter_mm=q.GetWidth(p.F_Cu)/1e6,drill_mm=q.GetDrillValue()/1e6)
 else:d.update(start_mm=xy(q.GetStart()),end_mm=xy(q.GetEnd()),width_mm=q.GetWidth()/1e6)
 return d
idx={uid(q):q for q in b.GetTracks()};proposal=[('97c06ea9-3805-4713-8c88-adc1818c3258',[110.9,75.35],[110.7,75.45]),('b995c2c7-f443-497b-bb80-da0d3312d10d',[110.7,75.45],[110.7,75.95]),('f6f5406e-c528-4d4f-a9d3-6a7ddc1ae774',[110.7,75.95],[110.6,76.05]),('6673dcb6-419c-4720-a5a5-19baa7afaec4',[110.6,76.05],[110.7,76.149999])];changed={u for u,_,_ in proposal};plans=[]
for u,a,c in proposal:
 q=idx[u];assert q.GetNetname()=='LED_FAULT_N' and q.GetLayer()==p.F_Cu and q.GetWidth()==150000;t=p.PCB_TRACK(b);t.SetStart(V(a));t.SetEnd(V(c));t.SetWidth(q.GetWidth());t.SetLayer(p.F_Cu);plans.append((q,t,desc(q)))
region=box(109.7,74.7,111.9,76.8);nregion=p.BOX2I(V([109.7,74.7]),V([2.2,2.1]));near=[];items=list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]
for q in items:
 if not q.GetBoundingBox().Intersects(nregion):continue
 layers=[]
 for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if q.IsOnLayer(l) and geom(sh(q,l)).intersects(region):layers.append(b.GetLayerName(l))
 if layers:d=desc(q);d['intersects_region_on_layers']=layers;near.append(d)
# Full prospective copper clearance to every other-net F object, replacing just rail with E's exact outer geometry.
eidx={uid(q):q for q in e.GetTracks()};oldrail='14d35ed0-d9e6-45a6-a698-4e8b482aba5f';eb=json.load(open(E.parents[2]/'qa/repair-E-build.json'));powerids={oldrail}|{r['uuid'] for r in eb['added'] if r['net']=='+1V1'};foreign=[q for q in items if q.GetBoundingBox().Intersects(nregion) and q.IsOnLayer(p.F_Cu) and q.GetNetname()!='LED_FAULT_N' and uid(q)!=oldrail]+[eidx[u] for u in powerids];obs=[(q,geom(sh(q,p.F_Cu))) for q in foreign]
rows=[]
for old,t,d in plans:
 g=geom(sh(t,p.F_Cu));dists=sorted([(g.distance(gg),q) for q,gg in obs],key=lambda x:x[0]);rows.append({'source':d,'proposed_start_mm':xy(t.GetStart()),'proposed_end_mm':xy(t.GetEnd()),'width_mm':.15,'nearest_foreign_F_copper':[dict(clearance_mm=dist,**desc(q)) for dist,q in dists[:8]],'screen_all_foreign_clearance_ge_0p150':dists[0][0]>=.15})
# Native full-shadow reference check against source and launch/rail E's actual filled In1; no own-window exception is needed for these signal segments.
refs=[]
for label,board in [('source',b),('hypothetical_escape_fill',e)]:
 holes=p.SHAPE_POLY_SET()
 for q in list(board.GetTracks())+[q for f in board.GetFootprints() for q in f.Pads()]:
  if isinstance(q,(p.PAD,p.PCB_VIA)) and q.HasHole():holes.Append(poly(q.GetEffectiveHoleShape()))
 holes.Simplify();plane=p.SHAPE_POLY_SET()
 for z in board.Zones():
  if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(p.In1_Cu):plane.Append(z.GetFilledPolysList(p.In1_Cu))
 plane.Simplify();plane.BooleanSubtract(holes);rr=[]
 for old,t,d in plans:
  q=sh(t,p.F_Cu);q.BooleanSubtract(holes);q.BooleanSubtract(plane);rr.append({'uuid':uid(old),'unsupported_mm2':q.Area()/1e12})
 refs.append({'plane_source':label,'proposed_F_tracks_against_In1':rr})
# Existing endpoint branches: report every object that intersects original four tracks.
connections=[]
for old,t,d in plans:
 g=geom(sh(old,p.F_Cu));contacts=[]
 for q in items:
  if uid(q)==uid(old) or not q.IsOnLayer(p.F_Cu) or not q.GetBoundingBox().Intersects(old.GetBoundingBox()):continue
  gg=geom(sh(q,p.F_Cu));ar=g.intersection(gg).area
  if ar>0:contacts.append(dict(overlap_mm2=ar,**desc(q)))
 connections.append({'uuid':uid(old),'original_contacts':contacts})
r={'source_sha256':H(S),'existing_failed_E_sha256':H(E),'scope':'Read-only in-memory assessment; no board saved or connectivity/fill mutation. Source untouched. Four LED_FAULT_N F.Cu tracks only; intermediate staircase vertices move left0.10mm, two outer endpoint positions retained. E rail/launch geometry used as known proposed context, not accepted source.','inventory_region_mm':[109.7,74.7,111.9,76.8],'broad_phase':'Conservative native object bounding boxes prune shapes outside this region, which encloses all proposed copper with more than 0.15 mm margin. Zones are handled separately by refill verification, not treated as immutable obstacle copper.','nearby_actual_source_objects':near,'proposal':rows,'reference_checks':refs,'original_contact_inventory':connections,'screen_pass':all(x['screen_all_foreign_clearance_ge_0p150'] for x in rows) and all(y['unsupported_mm2']==0 for x in refs for y in x['proposed_F_tracks_against_In1']),'limits':'Analytical read-only screen, not native DRC. Native fill may change after saving; all source-bound contact/plane/return gates remain required. No SI claim.'};(R/'qa/read-only-assessment.json').write_text(json.dumps(r,indent=2));print('SCREEN',r['screen_pass']);print('nearby_objects',len(near));print('minimums',[(x['source']['uuid'],x['nearest_foreign_F_copper'][0]) for x in rows]);print('refs',refs);print('contacts',connections)
