import os
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-kicad-config'
import pcbnew as p,json,hashlib,sys,math,collections
from pathlib import Path
sys.path.insert(0,'/workspace/shared/maru60-kicad-linux/pcb/tools');import sexp
D=Path(__file__).parent;H=Path('/workspace/shared/maru-a4l-P3-S3-3V3-bridge-worker-0334/handoff-3V3-source-repair-0357');BASE=Path('/workspace/shared/maru-a4l-P3-S1-reconstruction-0236/handoff-P3-S1-netcorrect-0303');S=H/'candidate.kicad_pcb';F=D/'candidate.kicad_pcb';h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();s=sexp.parse(S.read_text());c=sexp.parse(F.read_text());g=sexp.get;uidraw=lambda q:str(g(q,'uuid')[1]);sel=lambda tree,ks:{uidraw(q):q for q in tree if isinstance(q,list)and str(q[0])in ks};st=sel(s,{'segment','arc','via'});ct=sel(c,{'segment','arc','via'});sf=sel(s,{'footprint'});cf=sel(c,{'footprint'});sz=sel(s,{'zone'});cz=sel(c,{'zone'});strip=lambda q:[n for n in q if not(isinstance(n,list)and str(n[0])in ['filled_polygon','fill_segments'])];ledger=json.load(open(D/'addition-ledger.json'));adds={r['uuid']for r in ledger['additions2']};assert ct.keys()-st.keys()==adds and not st.keys()-ct.keys();assert all(st[u]==ct[u]for u in st);assert sf==cf;assert all(strip(sz[u])==strip(cz[u])for u in sz);assert S.with_suffix('.kicad_pro').read_bytes()==F.with_suffix('.kicad_pro').read_bytes()
a=p.LoadBoard(str(S));b=p.LoadBoard(str(F));b.BuildConnectivity();con=b.GetConnectivity();uid=lambda q:q.m_Uuid.AsString();xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)];fs={f.GetReference():f for f in b.GetFootprints()};tracks={uid(q):q for q in b.GetTracks()};eps=[q for q in fs['U1'].Pads()if q.GetNumber()=='61'];via_proofs=[]
for r in ledger['additions2']:
 if r['kind']!='via':continue
 v=tracks[r['uuid']];proof=[]
 for l in[p.In1_Cu,p.In2_Cu]:
  common=[]
  for z in b.Zones():
   if z.GetNetname()!='GND'or not z.IsOnLayer(l):continue
   for i in range(z.GetFilledPolysList(l).OutlineCount()):
    ps=z.GetFilledPolysList(l).UnitSet(i)
    if ps.Collide(v.GetEffectiveShape(l),0)and any(ps.Collide(q.GetEffectiveShape(l),0)for q in eps):common.append({'zone':uid(z),'island':i})
  assert common;proof.append({'layer':b.GetLayerName(l),'same_GND_island_as_EP':common})
 via_proofs.append({'uuid':uid(v),'at':xy(v.GetPosition()),'proof':proof})
def comp(q):
 todo=[q];seen=set()
 while todo:
  q=todo.pop()
  if uid(q)in seen:continue
  seen.add(uid(q));todo+=list(con.GetConnectedTracks(q))+list(con.GetConnectedPads(q))
 return seen
controls=[];old=json.load(open(BASE/'S1-audit.json'))
for r in old['local_control_witnesses']:
 q=next(q for q in fs['U1'].Pads()if q.GetNumber()==str(r['pin']));seen=comp(q);local=[u for u in json.load(open(BASE/'raw-intended-ledger.json'))['added166_coupon_derived_uuids']if tracks[u].GetNetname()==r['net']];assert set(local)<=seen;controls.append({'net':r['net'],'pin':r['pin'],'all_local_items_exact_and_connected':True})
def details(ps):
 rows=[]
 for i in range(ps.OutlineCount()):
  q=ps.COutline(i);pts=[xy(q.CPoint(k))for k in range(q.PointCount())];rows.append({'bbox':[min(x[k]for x in pts)for k in[0,1]]+[max(x[k]for x in pts)for k in[0,1]],'outline':pts})
 return rows
fills=[];bz={uid(z):z for z in b.Zones()}
for z in a.Zones():
 if z.GetIsRuleArea():continue
 for l in[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
  if not z.IsOnLayer(l):continue
  x=z.GetFilledPolysList(l);y=bz[uid(z)].GetFilledPolysList(l);lost=p.SHAPE_POLY_SET();lost.BooleanSubtract(x,y);gain=p.SHAPE_POLY_SET();gain.BooleanSubtract(y,x)
  if lost.Area()or gain.Area():fills.append({'uuid':uid(z),'net':z.GetNetname(),'layer':b.GetLayerName(l),'lost_mm2':lost.Area()/1e12,'gained_mm2':gain.Area()/1e12,'lost':details(lost),'gained':details(gain)})
source=[]
for f in sorted((D/'witnesses').glob('*.json')):
 oldj=json.load(open(H/'witnesses'/f.name));j=json.load(open(f));ends=lambda v:{tuple(q)for x in v['unreached_components']for q in x['pads']};oldends,newends=ends(oldj),ends(j);lost=newends-oldends;assert not lost;source.append({'name':f.stem,'physical_pad_count':j.get('rail_pad_count',j.get('ground_pad_count')),'old_unreached_components':len(oldj['unreached_components']),'new_unreached_components':len(j['unreached_components']),'new_unreached_physical_endpoints':[q for x in j['unreached_components']for q in x['pads']],'restored_endpoints':sorted(oldends-newends),'lost_endpoints':sorted(lost)})
drc=json.load(open(D/'native-drc.json'));erc=json.load(open(D/'native-erc.json'));ref=json.load(open(D/'collateral-return-regression.json'));assert not ref['affected_tracks'];native={'opens':len(drc['unconnected_items']),'hard':sum(x['severity']=='error'for x in drc['violations']),'warnings':sum(x['severity']=='warning'for x in drc['violations']),'warning_types':dict(collections.Counter(x['type']for x in drc['violations'])),'parity':len(drc['schematic_parity']),'ERC':sum(len(x['violations'])for x in erc['sheets'])};assert native['hard']==native['parity']==native['ERC']==0
q1=next(q for q in fs['C105'].Pads()if q.GetNumber()=='1');q2=next(q for q in fs['U3'].Pads()if q.GetNumber()=='8');positive=uid(q2)in comp(q1);assert positive
qg=next(q for q in fs['C105'].Pads()if q.GetNumber()=='2');gv=next(q for q in tracks.values()if isinstance(q,p.PCB_VIA)and q.GetNetname()=='GND'and xy(q.GetPosition())==[19.31,14.1]);ground=uid(gv)in comp(qg);assert ground
r={'source_sha256':h(S),'candidate_sha256':h(F),'status':'P3_SOURCE_BRIDGE_PLUS_C105_GROUND_COMPLETE_PARTIAL_RAILS_NOT_A25_PROGRESS','exact2_C105_ground_positive_arm_additions_only':True,'retained9051_source_copper_exact':True,'all340_footprints_and_1275pads_exact':True,'all13_zone_definitions_exact':True,'project_bytes_exact':True,'all27_local_control_witnesses':controls,'no_new_vias':True,'C105_direct_positive_to_U3_8_track_component':positive,'C105_direct_ground_to_existing_via_track_component':ground,'fill_deltas':fills,'source_endpoint_comparison':source,'native':native,'all7958_retained_outer_tracks_new_reference_loss_mm':ref['totals_mm'],'scope_limits':['All215 GND physical pads now source-reached topologically; not loop/PDN/SI/assembly qualification.','All positive/source stage opens remain unchanged, as do LX and downstreamLED connectivity caveats.','C105 positive/GND arms1.843199mm/2.832402mm, two-via innerreturn chord13.602007mm, U3GNDarm1.492542mm are geometric context, not a predicted current path or complete qualified bypassloop.','No footprint/pose/newhole change; original-case/tool/body sensitivities remain conditional.','S3 regression repaired by exact terminal bridge; no TP5 move and no A25 KEY16 merge.']};(D/'audit.json').write_text(json.dumps(r,indent=2));print({'native':native,'sha':h(F),'fills':[(v['net'],v['layer'],v['lost_mm2'],v['gained_mm2'])for v in fills]})
