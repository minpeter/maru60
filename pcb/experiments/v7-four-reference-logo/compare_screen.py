"""Read-only actual-trial comparison. Association review and acceptance replay remain separate."""
import sys,json,hashlib,copy,collections,math
from pathlib import Path
sys.dont_write_bytecode=True
if not __debug__:raise RuntimeError('Optimized execution forbidden')
import sexp as sx
W=Path(__file__).resolve().parent;Q=W/'qa';read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,m):
 if not x:raise RuntimeError(m)
def files(root):return {str(p.relative_to(root)):sha(p)for p in sorted(root.rglob('*'))if p.is_file()}
plan=read(W/'PLAN-four.json');sr=read(W/'SOURCE.json');base=W/'input';candidate=W/'candidate-four/pcb';sf=files(base);cf=files(candidate);need(sf==sr['files_sha256']and len(sf)==53,'Exact53 source members');need(cf==plan['candidate_file_map']and len(cf)==54,'Exact declared54 candidate map');need(set(cf)==set(sf)|{'maru60.kicad_prl'},'Only declared native metadata extra');need(cf['maru60.kicad_prl']=='8c0a828ce6c58ebd31b8835a9bd58efb04385897813f3e5d51b961410868af58','Exact2057-byte local metadata');need((candidate/'maru60.kicad_prl').stat().st_size==2057,'Metadata length');need([r for r in sf if sf[r]!=cf[r]]==['maru60.kicad_pcb'],'Only board among source files differs');need(sf['maru60.kicad_pcb']==plan['source_board_sha256']and cf['maru60.kicad_pcb']==plan['candidate_board_sha256'],'Bound source/candidate boards')
a=sx.parse((base/'maru60.kicad_pcb').read_text());b=sx.parse((candidate/'maru60.kicad_pcb').read_text());restored=copy.deepcopy(b);af=sx.fields(a);bf=sx.fields(b);rf=sx.fields(restored);wanted={x['reference']for x in plan['reference_changes']};need(wanted=={'C100','R140','R160','R134'},'Exact four targets')
for r in wanted:
 need(sx.get(sx.get(sx.get(bf[r],'effects'),'font'),'size')==['size','0.8','0.8'],'Exact new font')
 sx.get(sx.get(sx.get(rf[r],'effects'),'font'),'size')[:]=copy.deepcopy(sx.get(sx.get(sx.get(af[r],'effects'),'font'),'size'));sx.get(rf[r],'at')[:]=copy.deepcopy(sx.get(af[r],'at'))
def logo(t):return next(fp for fp in sx.all(t,'footprint')if any(x[1]=='Reference'and x[2]=='LOGO1'for x in sx.all(fp,'property')))
need(len(sx.all(logo(a),'fp_poly'))==2 and sx.all(logo(a),'fp_poly')==sx.all(logo(b),'fp_poly'),'Both intact local polygons');sx.get(logo(restored),'at')[:]=copy.deepcopy(sx.get(logo(a),'at'));need(restored==a,'Every other raw object/field/rule/copper/plane unchanged')
ni=read(Q/'source-native.json');nc=read(Q/'candidate-four-native.json');need(ni['board_sha256']==plan['source_board_sha256']and nc['board_sha256']==plan['candidate_board_sha256'],'Native board binding');fp0=ni['footprint_placement'];fp1=nc['footprint_placement'];need(set(fp0)==set(fp1),'All native footprints')
for r in fp0:
 if r=='LOGO1':
  expect=dict(fp0[r],position_nm=plan['logo_after']['position_nm']);need(fp1[r]==expect,'Only LOGO native placement')
 else:need(fp0[r]==fp1[r],'Electrical footprint native placement '+r)
for k in set(ni)-{'board_sha256','private_xdg','footprint_placement'}:need(ni[k]==nc[k],'Complete native electrical equivalence '+k)
def owners(n):
 ds=n['diagnostic_items'];ids=n['net_identity'];need(set(ds)==set(n['track_geometry'])|set(n['pad_geometry']),'Complete native diagnostic object inventory');par={u:u for u in ds}
 def find(u):
  while par[u]!=u:par[u]=par[par[u]];u=par[u]
  return u
 es=n['edges'];need(es==sorted(map(list,set(map(tuple,es)))),'Canonical complete unique edges')
 for e in es:
  need(type(e)is list and len(e)==2,'Edge shape');u,v=e;need(u<v and u in ds and v in ds and ids[u]==ids[v],'Valid same-net edge');par[find(v)]=find(u)
 groups={}
 for u in ds:
  if ids[u]:groups.setdefault((ids[u],find(u)),[]).append(u)
 derived={(net,tuple(sorted(us)))for(net,_),us in groups.items()};reported={(c['net'],tuple(c['object_uuids']))for c in n['native_components']};need(len(reported)==len(n['native_components'])and reported==derived,'All reported components match fresh edge-derived memberships');return {u:g for g in derived for u in g[1]},derived
o0,p0=owners(ni);o1,p1=owners(nc);need(p0==p1,'Complete fresh native component partitions exact')
def openpairs(d,n,owner):
 need(d['coordinate_units']=='mm'and d['kicad_version']=='9.0.2','Native DRC version/units');rs=d['unconnected_items'];need(len(rs)==12,'Exactly twelve existing opens');out={}
 for r in rs:
  need(set(r)=={'description','items','severity','type'}and r['description']=='Missing connection between items'and r['type']=='unconnected_items'and r['severity']=='error'and len(r['items'])==2,'Exact open record schema');pair=[]
  for i in r['items']:
   need(set(i)=={'description','pos','uuid'},'Exact endpoint schema');u=i['uuid'];need(u in owner and u in n['diagnostic_items'],'Known open endpoint');v=n['diagnostic_items'][u];need(i['description']==v['description'],'Actual native endpoint description');need(set(i['pos'])=={'x','y'}and all(type(x)in(int,float)and math.isfinite(x)for x in i['pos'].values()),'Finite endpoint positions');need([i['pos']['x'],i['pos']['y']]in v['positions_mm'],'Actual native endpoint position');pair.append(owner[u])
  need(pair[0][0]==pair[1][0]and pair[0]!=pair[1],'Two different same-net components');key=tuple(sorted(pair));need(key not in out,'Unique complete open pair');out[key]=r
 return out
sd=read(Q/'source-drc.json');cd=read(Q/'candidate-four-drc.json');sop=openpairs(sd,ni,o0);cop=openpairs(cd,nc,o1);need(sop.keys()==cop.keys(),'Exact12 native open-component pairs unchanged')
normalize=lambda x:json.dumps(dict(x,items=sorted(x['items'],key=lambda i:i['uuid'])),sort_keys=True);sw=collections.Counter(map(normalize,sd['violations']));cw=collections.Counter(map(normalize,cd['violations']));need(not(cw-sw),'No new or altered warning record');removed=[json.loads(k)for k,count in(sw-cw).items()for _ in range(count)];need(len(sd['violations'])==92 and len(cd['violations'])==68 and len(removed)==24,'Exact warning delta');need(not sd['schematic_parity']and not cd['schematic_parity'],'Zero parity issues');need(all(r['severity']=='warning'for r in sd['violations']+cd['violations']),'No hard DRC beyond recorded existing opens')
si=read(Q/'source-ink.json');ci=read(Q/'candidate-four-ink.json');need(si['board_sha256']==plan['source_board_sha256']and ci['board_sha256']==plan['candidate_board_sha256'],'Ink board binding');need(si['native_board_loads']==ci['native_board_loads']==1 and si['native_build']==ci['native_build']=='9.0.2+dfsg-1','One native load per ink run');need(si['complete_mask_aperture_inventory']==ci['complete_mask_aperture_inventory']and len(ci['complete_mask_aperture_inventory'])==1759,'Complete actual1759 mask objects unchanged');need(si['mask_silk_zones']==ci['mask_silk_zones']==[],'No silently unsupported mask/silk zones');need(len(si['all382_reference_typography'])==len(ci['all382_reference_typography'])==382,'All382 fields');expected=copy.deepcopy(si['all382_reference_typography'])
for row in plan['reference_changes']:need(expected[row['reference']]==row['before'],'Exact original native typography');expected[row['reference']]=row['after']
delta=[b-a for a,b in zip(plan['logo_before']['position_nm'],plan['logo_after']['position_nm'])];expected['LOGO1']['position_nm']=[a+b for a,b in zip(expected['LOGO1']['position_nm'],delta)];need(expected==ci['all382_reference_typography'],'Only declared four native field changes plus whole-logo reference translation');rows={r['reference']:r for r in ci['rows']};need(len(rows)==len(ci['rows'])==23,'Unique23 inspected references');accepted='R120 R144 J3 D100 R124 C142 C141 R163 C137 C126 C129 U2 R126 U10 C101'.split()
def valid_gap(g,target):
 lo=g['lower_bound_nm'];hi=g['upper_bound_nm'];need(type(lo)is int and lo>=target and g['lower_noncollision_verified']is True,'Measured lower bound meets target')
 if g['capped_lower_bound']:need(hi is None and lo==g['cap_nm']and g['upper_collision_verified']is False and g['partner']is None,'Capped bound semantics')
 else:need(type(hi)is int and hi==lo+1 and g['upper_collision_verified']is True and type(g['partner'])is dict,'Exact integer native bracket')
def check_geometry(g,strict_proxies):
 need(g['whole_ink_inside_board']is True,'Whole ink contained')
 for k in ['mask','silk','courtyard','fab','unreconstructed_fab','edge']:
  need(g[k+'_intersections']==[],'No '+k+' intersection')
  if k in ['mask','silk','edge']or strict_proxies:need(g[k+'_target_pass']is True,'Target clearance '+k);valid_gap(g[k+'_gap'],250000 if k=='edge'else 150000)
for r in wanted:need(rows[r]['typography']==expected[r],'Actual proposed field row');check_geometry(rows[r]['geometry'],True)
for r in accepted:need(rows[r]['typography']==si['all382_reference_typography'][r],'Accepted reference unchanged');check_geometry(rows[r]['geometry'],False)
lg=ci['whole_LOGO1'];need(lg['footprint']['position_nm']==[85326786,82100000]and lg['angle_deg']==180 and len(lg['polygons'])==2,'Complete desired artwork pose')
for row in lg['polygons']:check_geometry(row['geometry'],True)
minimums={k:min((rows[r]['geometry'][k+'_gap']['lower_bound_nm'],rows[r]['geometry'][k+'_gap']['upper_bound_nm'])for r in wanted)for k in ['mask','silk','courtyard','fab','edge']};logo_min={k:min((row['geometry'][k+'_gap']['lower_bound_nm'],row['geometry'][k+'_gap']['upper_bound_nm'])for row in lg['polygons'])for k in ['mask','silk','courtyard','fab','unreconstructed_fab','edge']}
result={'passed_scoped_geometry_and_no_regression_checks':True,'source_board_sha256':plan['source_board_sha256'],'candidate_board_sha256':plan['candidate_board_sha256'],'warnings_before_after':[92,68],'exact_warning_records_removed':removed,'new_warning_records':[],'remaining_warning_types':dict(collections.Counter(r['type']for r in cd['violations'])),'native_open_pair_count':12,'open_representatives_changed':sum(sop[k]!=cop[k]for k in sop),'complete_open_pairs':[{'net':k[0][0],'components':[list(x[1])for x in k],'source_record':sop[k],'candidate_record':cop[k]}for k in sorted(sop)],'complete_native_component_count':len(p0),'complete_native_electrical_and_copper_saved_plane_raw_geometry_unchanged':True,'native_counts':nc['counts'],'length_fsum_mm':nc['length_fsum_mm'],'all53_recovered_source_files_preserved':True,'declared_native_generated_local_metadata':plan['declared_native_generated_metadata'],'new_four_reference_minimum_brackets_nm':minimums,'whole_logo_minimum_brackets_nm':logo_min,'all1759_mask_apertures_checked':True,'accepted15_and_reserved_C124_R121_U8_and_R131_unchanged':True,'R131_dropped_due_to_unmoved_U12_label_dependency':True,'association_review_status':'Pending independent actual-candidate review; not implied by geometric pass.','full_acceptance_replay_or_new_simulation_performed':False,'historical_QA_packets_restored':False,'manufacturing_or_actual_3D_visibility_qualified':False,'selected':False};(Q/'SCREEN_COMPARISON.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['exact_warning_records_removed','complete_open_pairs']},indent=2))
