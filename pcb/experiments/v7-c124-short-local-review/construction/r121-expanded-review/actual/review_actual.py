import pcbnew as p,json,pathlib,hashlib,math,collections
D=pathlib.Path('/tmp/v7-c124-rebound-short/r121-expanded-review/actual');R=pathlib.Path('/tmp/v7-c124-rebound-short/isolated-v4');C=R/'filled/pcb/maru60.kicad_pcb';M=pathlib.Path('/tmp/v7-c124-rebound-short/main');sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();expected='8c45df3642599be269697ce9b225fe55ee6b886dce713b77f6ced533ea268fb6';assert sha(C)==expected
contract=json.loads((R/'BUILD_CONTRACT.json').read_text());ledger=json.loads((M/'counterfactual-v4-contact-reference.json').read_text());source=json.loads((D/'source_support_polygons.json').read_text());raw=json.loads((D/'raw_source_candidate_delta.json').read_text())
b=p.LoadBoard(str(C));fs={f.GetReference():f for f in b.GetFootprints()};obs=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in obs};xy=lambda v:[v.x/1e6,v.y/1e6]
def poly(shape,loc=p.ERROR_INSIDE):
 z=p.SHAPE_POLY_SET();shape.TransformToPolygon(z,1,loc);return z
def copper(q,loc=p.ERROR_INSIDE,l=p.B_Cu):
 z=poly(q.GetEffectiveShape(l),loc)
 if q.HasHole():z.BooleanSubtract(poly(q.GetEffectiveHoleShape(),p.ERROR_OUTSIDE if loc==p.ERROR_INSIDE else p.ERROR_INSIDE))
 return z
def inter(a,c):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(c);return z
def minus(a,c):
 z=p.SHAPE_POLY_SET(a);z.BooleanSubtract(c);return z
def rect(x,y,w,h):
 z=p.SHAPE_POLY_SET();z.NewOutline()
 for a,c in [(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)]:z.Append(round(a*1e6),round(c*1e6))
 return z
def loadpoly(rows):
 z=p.SHAPE_POLY_SET()
 for row in rows:
  i=z.NewOutline()
  for x,y in row['outer']:z.Append(x,y)
  for hh in row['holes']:
   k=z.NewHole(i)
   for x,y in hh:z.Append(x,y,i,k)
 return z
def court(f):
 pts=[]
 for s in f.GraphicalItems():
  if s.GetLayer()!=p.B_CrtYd:continue
  a,c=s.GetStart(),s.GetEnd()
  pp=[(a.x,a.y),(c.x,c.y)]
  if s.GetShape()==p.SHAPE_T_RECT:pp=[(a.x,a.y),(c.x,a.y),(c.x,c.y),(a.x,c.y)]
  for q in pp:
   if q not in pts:pts.append(q)
 assert len(pts)==4,(f.GetReference(),pts)
 cx=sum(x for x,y in pts)/4;cy=sum(y for x,y in pts)/4;pts.sort(key=lambda q:math.atan2(q[1]-cy,q[0]-cx));z=p.SHAPE_POLY_SET();z.NewOutline()
 for x,y in pts:z.Append(x,y)
 return z,[[x/1e6,y/1e6]for x,y in pts]
res={'candidate_sha256':sha(C),'source_sha256':source['source_sha256'],'version':p.GetBuildVersion(),'footprint_count':len(fs),'track_via_count':len(list(b.GetTracks())),'track_mismatches':[],'parts':{},'build_contract_stale_prefill_sha':contract['candidate_prefill_sha256']}
new={};newobj={};newuuids={r['uuid']for r in contract['added_tracks']}
for r in contract['added_tracks']:
 q=idx[r['uuid']];row={'name':r['name'],'uuid':uid(q),'start':xy(q.GetStart()),'end':xy(q.GetEnd()),'width':q.GetWidth()/1e6,'net':q.GetNetname(),'layer':b.GetLayerName(q.GetLayer())}
 for k in['start','end']:
  if [round(x*1e6)for x in row[k]]!=[round(x*1e6)for x in r[k]]:res['track_mismatches'].append([r['name'],k,row[k],r[k]])
 for k in['width','net']:
  if row[k]!=r[k]:res['track_mismatches'].append([r['name'],k,row[k],r[k]])
 if row['layer']!='B.Cu' or isinstance(q,p.PCB_VIA):res['track_mismatches'].append([r['name'],'not BCu track'])
 newobj[r['name']]=q;new[r['name']]=copper(q)
res['part_mismatches']=[];courts={}
for ref,spec in contract['parts'].items():
 f=fs[ref];cp,verts=court(f);courts[ref]=cp;expectedcourt=rect(*spec['at'],*spec['court']);part={'uuid':uid(f),'xy':xy(f.GetPosition()),'orientation_degrees':f.GetOrientationDegrees(),'fields':{x.GetName():x.GetText()for x in f.GetFields()},'court_vertices':verts,'court_extra_mm2':minus(cp,expectedcourt).Area()/1e12,'court_missing_mm2':minus(expectedcourt,cp).Area()/1e12,'reference_text_size':xy(f.Reference().GetTextSize()),'pads':[]}
 if part['xy']!=spec['at'] or part['uuid']!=spec['uuid'] or part['court_extra_mm2'] or part['court_missing_mm2']:res['part_mismatches'].append([ref,'pose/id/court mismatch'])
 for q in f.Pads():
  number=q.GetNumber();sp=next(x for x in spec['pads']if x[0]==number);want=[spec['at'][0]+sp[1],spec['at'][1]+sp[2]]
  pad={'number':number,'uuid':uid(q),'xy':xy(q.GetPosition()),'size':xy(q.GetSize()),'orientation_degrees':q.GetOrientationDegrees(),'shape':int(q.GetShape()),'net':q.GetNetname(),'layers':[b.GetLayerName(l)for l in [p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask,p.F_Paste,p.B_Paste]if q.IsOnLayer(l)],'paste_margin_mm':xy(q.GetSolderPasteMargin(p.B_Cu)),'mask_expansion_mm':q.GetSolderMaskExpansion(p.B_Cu)/1e6,'copper_area_mm2':copper(q).Area()/1e12,'native_paste_shape_area_mm2':poly(q.GetEffectiveShape(p.B_Paste)).Area()/1e12,'native_mask_shape_area_mm2':poly(q.GetEffectiveShape(p.B_Mask)).Area()/1e12}
  if [round(x*1e6)for x in pad['xy']]!=[round(x*1e6)for x in want] or pad['size']!=sp[3:5] or pad['net']!=sp[5] or q.GetShape()!=p.PAD_SHAPE_RECT:res['part_mismatches'].append([ref,number,'pad geometry/net'])
  if pad['layers']!=['B.Cu','B.Mask','B.Paste'] or pad['paste_margin_mm']!=[0,0] or pad['mask_expansion_mm']!=0:res['part_mismatches'].append([ref,number,'layer or mask/paste'])
  part['pads'].append(pad);new[ref+'.'+number]=copper(q);newobj[ref+'.'+number]=q
 res['parts'][ref]=part
print('ACTUAL_DIMENSIONS',res['track_mismatches'],res['part_mismatches'],flush=True)
bridge=p.SHAPE_POLY_SET(new['GROUND_BRIDGE_A']);bridge.BooleanAdd(new['GROUND_BRIDGE_B']);new['old-ground-bridge']=bridge
res['bridge_internal_contact_mm2']=inter(new['GROUND_BRIDGE_A'],new['GROUND_BRIDGE_B']).Area()/1e12
res['expected_contact_rechecks']=[]
for row in ledger['new_to_retained_contacts']:
 ar=inter(new[row['new']],copper(idx[row['old']])).Area()/1e12;res['expected_contact_rechecks'].append({'new':row['new'],'old':row['old'],'physical_area_mm2':ar,'expected_area_mm2':row['area_mm2'],'positive':ar>0})
res['new_contact_rechecks']=[{'a':r['a'],'b':r['b'],'area_mm2':inter(new[r['a']],new[r['b']]).Area()/1e12}for r in ledger['new_to_new_contacts']]
res['full_old_support_rechecks']=[]
for row in source['supports']:
 so=loadpoly(row['outside']['polygon_nm']);res['full_old_support_rechecks'].append({'old_contact_uuid':row['uuid'],'outside_old_support_area_mm2':so.Area()/1e12,'not_covered_by_actual_inside_bridge_mm2':minus(so,bridge).Area()/1e12})
# Bounded physical net partition: no copper bypass of the inserted resistor.
netobs={n:[q for q in obs if q.GetNetname()==n and q.IsOnLayer(p.B_Cu)]for n in['USB_DVDT','USB_DVDT_CAP']}
res['dvd_net_members']={n:[{'uuid':uid(q),'type':q.GetClass(),'ref':q.GetParentFootprint().GetReference()if isinstance(q,p.PAD)else None,'pin':q.GetNumber()if isinstance(q,p.PAD)else None}for q in qs]for n,qs in netobs.items()}
gaps=[]
for a in netobs['USB_DVDT']:
 for c in netobs['USB_DVDT_CAP']:
  gaps.append({'a':uid(a),'b':uid(c),'gap_mm':copper(a,p.ERROR_OUTSIDE).GetClearance(c.GetEffectiveShape(p.B_Cu))/1e6,'overlap_mm2':inter(copper(a),copper(c)).Area()/1e12})
res['input_output_min_gap']=min(gaps,key=lambda x:x['gap_mm']);res['input_output_overlap_count']=sum(x['overlap_mm2']>0 for x in gaps)
# Actual courtyard primitives, not cached erosion.
uc,_=court(fs['U8']);courts['U8']=uc
res['court_gaps_mm']={a+'_'+c:courts[a].GetClearance(courts[c])/1e6 for a,c in [('C124','R125'),('R121','C124'),('R121','R125'),('R125','U8')]}
# Process envelopes at actual part centers, verified poses above. Conservative integer rounding.
def envelope(ref,box):
 org=xy(fs[ref].GetPosition());pts=[]
 for x in[box[0],box[2]]:
  for y in[box[1],box[3]]:
   for a in[-math.pi/90,0,math.pi/90]:pts.append((org[0]+math.cos(a)*x-math.sin(a)*y,org[1]+math.sin(a)*x+math.cos(a)*y))
 x0=math.floor((min(x for x,y in pts)-.1)*1e6);x1=math.ceil((max(x for x,y in pts)+.1)*1e6);y0=math.floor((min(y for x,y in pts)-.1)*1e6);y1=math.ceil((max(y for x,y in pts)+.1)*1e6)
 return rect((x0+x1)/2e6,(y0+y1)/2e6,(x1-x0)/1e6,(y1-y0)/1e6)
envs={'C124.1':envelope('C124',[-.525,-.275,-.125,.275]),'R121.2':envelope('R121',[-.475,-.8,.475,-.25]),'R125.2':envelope('R125',[-.55,-.275,-.175,.275])}
critical=[('C124.1','OVLO0'),('C124.1','OVLO1'),('C124.1','ff31c038-3a4c-4c1b-880e-025462019509'),('R121.2','ff31c038-3a4c-4c1b-880e-025462019509'),('R125.2','OVLO3')]
res['actual_terminal_envelope_gaps']=[{'terminal':n,'obstacle':z,'gap_mm':envs[n].GetClearance((newobj[z]if z in newobj else idx[z]).GetEffectiveShape(p.B_Cu))/1e6}for n,z in critical]
res['r121_ground_pad_to_uvlo1_gap_mm']=new['R121.2'].GetClearance(newobj['UVLO1'].GetEffectiveShape(p.B_Cu))/1e6
brout=p.SHAPE_POLY_SET(copper(newobj['GROUND_BRIDGE_A'],p.ERROR_OUTSIDE));brout.BooleanAdd(copper(newobj['GROUND_BRIDGE_B'],p.ERROR_OUTSIDE));brrows=[]
for q in obs:
 if not q.IsOnLayer(p.B_Cu)or q.GetNetname()=='GND':continue
 brrows.append({'uuid':uid(q),'net':q.GetNetname(),'gap_mm':brout.GetClearance(q.GetEffectiveShape(p.B_Cu))/1e6})
res['bridge_foreign_min']=min(brrows,key=lambda x:x['gap_mm'])
print('CONTACTS',len(res['expected_contact_rechecks']),len(res['new_contact_rechecks']),'SUPPORT',res['full_old_support_rechecks'],'BYPASS',res['input_output_min_gap'],flush=True)
# Actual new signal projections: outside 1nm copper; actual filled GND minus outside physical drills.
signals={n:q for n,q in newobj.items()if q.GetNetname()!='GND'};projection=p.SHAPE_POLY_SET()
for q in signals.values():projection.BooleanAdd(copper(q,p.ERROR_OUTSIDE))
pbox=projection.BBox();res['reference_projection_signal_objects']=len(signals);res['actual_reference_coverage']=[];res['actual_plane_roots']=[]
for l in[p.In1_Cu,p.In2_Cu]:
 pl=p.SHAPE_POLY_SET()
 for z in b.Zones():
  if z.GetNetname()=='GND'and z.IsOnLayer(l):pl.BooleanAdd(z.GetFilledPolysList(l))
 for q in obs:
  if q.HasHole()and q.IsOnLayer(l)and q.GetBoundingBox().Intersects(pbox):pl.BooleanSubtract(poly(q.GetEffectiveHoleShape(),p.ERROR_OUTSIDE))
 loss=minus(projection,pl);res['actual_reference_coverage'].append({'layer':b.GetLayerName(l),'outside_projection_uncovered_mm2':loss.Area()/1e12,'uncovered_outlines':loss.OutlineCount()})
 for u in['efadf2be-e519-469f-a84c-2e7cbb60672a','763086b7-5549-4f5e-bb08-ce25387b3627','8e0fa85d-f2bc-543d-aae7-d8f6ff75061a']:
  ar=inter(copper(idx[u],p.ERROR_INSIDE,l),pl).Area()/1e12;res['actual_plane_roots'].append({'via':u,'layer':b.GetLayerName(l),'physical_annulus_overlap_mm2':ar})
res['source_zone_records_identical']=raw['zone']['source_hashes']==raw['zone']['candidate_hashes'];res['candidate_sha256_after']=sha(C);assert res['candidate_sha256_after']==expected
(D/'actual_native_review.json').write_text(json.dumps(res,indent=2)+'\n');print('FINAL',json.dumps({k:v for k,v in res.items()if k not in['parts','expected_contact_rechecks','dvd_net_members']},indent=2))
