import pcbnew as p,json,hashlib,math
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-c782/mcu');S=R/'source/pcb/maru60.kicad_pcb';B=R/'north-escape-c/pcb/maru60.kicad_pcb';a=p.LoadBoard(str(S));b=p.LoadBoard(str(B));uid=lambda q:q.m_Uuid.AsString();h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();mid='14d35ed0-d9e6-45a6-a698-4e8b482aba5f';build=json.load(open(R/'qa/north-escape-c-build.json'));newids=[mid]+[r['uuid'] for r in build['added'] if r['net']=='+1V1'];old=next(q for q in a.GetTracks() if uid(q)==mid);new=[q for q in b.GetTracks() if uid(q) in newids]
def poly(sh):
 z=p.SHAPE_POLY_SET();sh.TransformToPolygon(z,1,p.ERROR_INSIDE);z.Simplify();return z
def union(qs):
 z=p.SHAPE_POLY_SET()
 for q in qs:z.Append(poly(q.GetEffectiveShape(p.F_Cu)))
 z.Simplify();return z
def physical(z,board):
 cuts=[]
 for q in list(board.GetTracks())+[q for f in board.GetFootprints() for q in f.Pads()]:
  if isinstance(q,(p.PAD,p.PCB_VIA)) and q.HasHole() and q.GetEffectiveHoleShape().BBox().Intersects(z.BBox()):
   hp=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(hp,1,p.ERROR_OUTSIDE);hp.Simplify();z.BooleanSubtract(hp);cuts.append(uid(q))
 return z,cuts
def diff(x,y):z=p.SHAPE_POLY_SET(x);z.BooleanSubtract(y);return z
def inter(x,y):z=p.SHAPE_POLY_SET();z.BooleanIntersection(x,y);return z
og,oc=physical(union([old]),a);ng,nc=physical(union(new),b);srcidx={uid(q):q for q in a.GetTracks()};dstidx={uid(q):q for q in b.GetTracks()};endpoints=[]
for u in ['2df4c211-ae72-4021-a11a-f400d90108b2','a3dac412-9c4c-48cf-81b8-b7016c33b879']:
 q=srcidx[u];z,_=physical(poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(p.F_Cu)//2)),a);qa=dstidx[u];unchanged=q.GetPosition()==qa.GetPosition() and q.GetDrillValue()==qa.GetDrillValue() and all(q.GetWidth(l)==qa.GetWidth(l) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]);oldover=inter(og,z);newover=inter(ng,z);missing=diff(oldover,newover)
 endpoints.append({'uuid':u,'position_mm':[q.GetPosition().x/1e6,q.GetPosition().y/1e6],'unchanged_native_geometry':unchanged,'old_physical_power_overlap_mm2':oldover.Area()/1e12,'new_physical_power_overlap_mm2':newover.Area()/1e12,'lost_original_endpoint_contact_mm2':missing.Area()/1e12})
oldlen=old.GetLength()/1e6;newlen=math.fsum(q.GetLength()/1e6 for q in new);r={'source_sha256':h(S),'candidate_sha256':h(B),'declared_modified_power_uuid':mid,'new_power_track_uuids':newids,'net':'+1V1','all_track_widths_mm':[q.GetWidth()/1e6 for q in new],'old_length_mm':oldlen,'new_length_mm':newlen,'length_delta_mm':newlen-oldlen,'old_physical_power_area_mm2':og.Area()/1e12,'new_physical_power_area_mm2':ng.Area()/1e12,'removed_physical_power_area_mm2':diff(og,ng).Area()/1e12,'added_physical_power_area_mm2':diff(ng,og).Area()/1e12,'source_nearby_drill_ids':oc,'candidate_nearby_drill_ids':nc,'endpoints':endpoints,'limits':'Only nominal geometry and endpoint contact coverage. Full named-pad/decoupler partition comparison is separate. No impedance, ripple, regulator stability, current capability or hardware qualification.'};(R/'qa/north-escape-c-power-geometry.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
