from pathlib import Path
import os, re, json, hashlib, collections, math
O=Path('/tmp/v7-c128-retirement-independent-review/electrical')
for key in ['CONFIG','CACHE','DATA','STATE','RUNTIME']:
 d=O/'runtime'/key.lower(); d.mkdir(parents=True,exist_ok=True);os.environ['XDG_'+key+'_HOME']=str(d)
import pcbnew as p
D=Path('/tmp/v7-c128-stub-retirement-aead'); Q=D/'qa'; P=Path('/tmp/v7-c128-deadbranch-readonly-aead'); H=Path('/tmp/v7-buck-deadarm-final-recheck')
S=D/'source/pcb'; C=D/'filled/pcb'; SB=S/'maru60.kicad_pcb'; CB=C/'maru60.kicad_pcb'; PB=D/'prefill/pcb/maru60.kicad_pcb'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();load=lambda f:json.loads(f.read_text());canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'))
expected_s='aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f';expected_c='cafa92133d336fef0b8236b8eafb2071bd6535cb991e95223a4b3fc233c4c4cb';expected_contract='4feb4ba2be91888a12f14524b2137537bd5a9e46aadad826e84be6bb26de3f6b'
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,pass_=bool(ok),detail=detail)); print(name, 'PASS' if ok else 'FAIL',flush=True)
 if not ok: raise AssertionError((name,detail))
check('board and contract SHA256 bindings', [sha(SB),sha(CB),sha(P/'RETIREMENT_CONTRACT.json'),sha(D/'RETIREMENT_CONTRACT.json')]==[expected_s,expected_c,expected_contract,expected_contract])
plan=load(P/'RETIREMENT_CONTRACT.json');ret={x['uuid'] for x in plan['retire']};check('contract exactly nine tracks one via and adds nothing',len(ret)==10 and collections.Counter(x['type']for x in plan['retire'])=={'PCB_TRACK':9,'PCB_VIA':1} and plan['add']==[])
files=lambda root:{str(f.relative_to(root)):sha(f)for f in root.rglob('*')if f.is_file()}
sf=files(S);cf=files(C);manifest=[dict(path=k,source_sha256=v,candidate_sha256=cf.get(k),identical=v==cf.get(k))for k,v in sf.items()]
check('all 54 source and candidate file paths; 53 nonboard files byte exact',len(sf)==len(cf)==54 and sf.keys()==cf.keys() and [k for k in sf if sf[k]!=cf[k]]==['maru60.kicad_pcb'])
(O/'file-manifest.json').write_text(json.dumps(manifest,indent=2))
# Independent balanced form scan, preserving raw source spans and quoted strings.
def forms(t):
 depth=0; quoted=False;esc=False;start=None;out=[]
 for i,ch in enumerate(t):
  if quoted:
   if esc:esc=False
   elif ch=='\\':esc=True
   elif ch=='"':quoted=False
  elif ch=='"':quoted=True
  elif ch=='(':
   depth+=1
   if depth==2:start=i
  elif ch==')':
   if depth==2:out.append((start,i+1,t[start:i+1]))
   depth-=1
   assert depth>=0
 assert depth==0 and not quoted
 return out
head=lambda t:re.match(r'\(\s*([^\s()]+)',t).group(1)
tok=lambda t:tuple(re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',t))
def uid(t):
 field=next((s for _,_,s in forms(t)if head(s)=='uuid'),None)
 return re.search(r'"([^"]+)"',field).group(1) if field else None
st=SB.read_text(); ct=CB.read_text(); ss=forms(st); cc=forms(ct);si={uid(t):(head(t),t)for _,_,t in ss if uid(t)};ci={uid(t):(head(t),t)for _,_,t in cc if uid(t)}
check('raw object UUID removal set exact; no UUID additions',set(si)-set(ci)==ret and not set(ci)-set(si))
check('raw removed object kinds',collections.Counter(si[u][0] for u in ret)=={'segment':9,'via':1})
prefill_expected=st
for a,b,t in sorted([z for z in ss if uid(z[2]) in ret],reverse=True):prefill_expected=prefill_expected[:a]+prefill_expected[b:]
check('prefill raw bytes exactly source minus declared ten spans',prefill_expected.encode()==PB.read_bytes())
retained_changes=[u for u in si.keys()&ci.keys()if si[u][0]!='zone'and tok(si[u][1])!=tok(ci[u][1])]
nonzone_s=[tok(t)for _,_,t in ss if head(t)!='zone'and uid(t)not in ret];nonzone_c=[tok(t)for _,_,t in cc if head(t)!='zone']
check('all retained nonzone forms token exact in original order',not retained_changes and nonzone_s==nonzone_c)
def zone_static(t):return [tok(s)for _,_,s in forms(t)if head(s)not in ['filled_polygon','fill_segments']]
zs={u:t for u,(h,t)in si.items()if h=='zone'};zc={u:t for u,(h,t)in ci.items()if h=='zone'}
check('all zone definitions/configuration exact after excluding saved fill payloads',zs.keys()==zc.keys() and all(zone_static(zs[u])==zone_static(zc[u])for u in zs))
changed_zone_fills=[u for u in zs if tok(zs[u])!=tok(zc[u])];check('only two inner plane saved fill forms differ',set(changed_zone_fills)=={'7a0e11fe-4433-4b0d-914b-0fa7262b6aa2','3a23a46c-3272-47d8-86cd-03a9240b82af'})
# Fresh native load only: no refill, SaveBoard, DRC, or full graph re-export.
boards=[p.LoadBoard(str(SB)),p.LoadBoard(str(CB))]; uidn=lambda o:o.m_Uuid.AsString();layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
items=[{uidn(q):q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]}for b in boards]
check('native object removal set exactly contract',set(items[0])-set(items[1])==ret and not set(items[1])-set(items[0]))
for r in plan['retire']+[plan['preserve_attachment_track']]:
 q=items[0][r['uuid']];native=dict(type=q.GetClass(),net=q.GetNetname(),layers=[boards[0].GetLayerName(l)for l in layers if q.IsOnLayer(l)],start=[q.GetStart().x/1e6,q.GetStart().y/1e6],end=[q.GetEnd().x/1e6,q.GetEnd().y/1e6],width_mm=(q.GetWidth(p.F_Cu) if isinstance(q,p.PCB_VIA) else q.GetWidth())/1e6,length_mm=q.GetLength()/1e6)
 if isinstance(q,p.PCB_VIA):native['drill_mm']=q.GetDrillValue()/1e6
 check('native contract object '+r['uuid'], all(native[k]==r[k]for k in native),native)
retired_length=math.fsum(items[0][u].GetLength()/1e6 for u in ret if not isinstance(items[0][u],p.PCB_VIA));check('native retired centerline length',retired_length==plan['declared_retired_track_centerline_mm'],retired_length)
g=[load(Q/'source-physical-graph.json'),load(Q/'candidate-physical-graph.json')]
check('saved native graph board SHA bindings',g[0]['board_sha256']==sha(SB) and g[1]['board_sha256']==sha(CB))
roots=[];repartitions=[];edge_counts=[];direct_maps=[];zone_maps=[]
for n,(gr,its,b)in enumerate(zip(g,items,boards)):
 pads={u:dict(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber(),net=q.GetNetname())for u,q in its.items()if isinstance(q,p.PAD)and q.GetNetname()}
 check('graph '+str(n)+' inventory matches native pads exactly',pads==gr['pad_inventory'],dict(named_pads=len(pads),total_native_pads=sum(isinstance(q,p.PAD)for q in its.values())))
 parent={u:u for u in its};znet={};zcnt={}
 for z in gr['zones']:
  nz=next(q for q in b.Zones() if uidn(q)==z['uuid']);assert nz.GetNetname()==z['net'] and nz.IsOnLayer(b.GetLayerID(z['layer']))
  for component in z['components']:parent[component['id']]=component['id'];znet[component['id']]=z['net'];zcnt[component['id']]=component['contact_count']
 def root(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(a,c):parent[root(c)]=root(a)
 dm={};zm={};zactual=collections.Counter()
 for a,c,support in gr['direct_edges']:
  assert a in its and c in its and a!=c and its[a].GetNetname()==its[c].GetNetname()
  assert all(v>0 and its[a].IsOnLayer(b.GetLayerID(l)) and its[c].IsOnLayer(b.GetLayerID(l))for l,v in support)
  key=tuple(sorted((a,c)));assert key not in dm;dm[key]=support;union(a,c)
 for a,c,area in gr['zone_edges']:
  assert a in znet and c in its and znet[a]==its[c].GetNetname() and area>0
  key=(a,c);assert key not in zm;zm[key]=area;zactual[a]+=1;union(a,c)
 assert dict(zactual)=={k:v for k,v in zcnt.items() if v}
 bynet=collections.defaultdict(lambda:collections.defaultdict(list))
 for u,data in pads.items():bynet[data['net']][root(u)].append(u)
 partitions={net:sorted(sorted(part)for part in bins.values())for net,bins in bynet.items()}
 check('graph '+str(n)+' recomputed full pad partitions from actual positive edges',partitions==gr['pad_partitions_by_net'] and len(partitions)==245)
 check('graph '+str(n)+' native counts/length',gr['tracks']==sum(not isinstance(q,p.PCB_VIA)for q in b.GetTracks())and gr['vias']==sum(isinstance(q,p.PCB_VIA)for q in b.GetTracks())and gr['footprints']==len(b.GetFootprints())and gr['track_length_mm']==math.fsum(q.GetLength()/1e6 for q in b.GetTracks()if not isinstance(q,p.PCB_VIA)))
 roots.append({u:root(u)for u in parent});repartitions.append(partitions);direct_maps.append(dm);zone_maps.append(zm);edge_counts.append(dict(direct=len(dm),zone=len(zm),physical_zone_components=len(znet)))
check('all 245 pad partitions source/candidate exactly preserved',repartitions[0]==repartitions[1])
retained_dm={k:v for k,v in direct_maps[0].items()if not set(k)&ret};retained_zm={k:v for k,v in zone_maps[0].items()if k[1]not in ret}
check('all retained direct contacts AND exact support areas equal',retained_dm==direct_maps[1],edge_counts)
check('all retained zone contacts AND exact support areas equal',retained_zm==zone_maps[1])
boundary=[dict(retired=next(u for u in k if u in ret),retained=next(u for u in k if u not in ret),support=v)for k,v in direct_maps[0].items()if len(set(k)&ret)==1]
check('removed branch has exactly declared single live attachment and no zone contact',len(boundary)==1 and boundary[0]['retired']=='0858c392-ee59-5350-bcaf-d8762f658a08'and boundary[0]['retained']=='f578f80d-52bb-500f-b3df-4fe97eccdb4e'and not [k for k in zone_maps[0]if k[1]in ret],boundary)
# Native positive-copper recomputation restricted to all witness edges (not a duplicate full graph export).
cache={}
def poly(shape,out=False):
 r=p.SHAPE_POLY_SET();shape.TransformToPolygon(r,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);return r
def copper(q,l):
 key=uidn(q),l
 if key not in cache:
  ps=poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l))
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():ps.BooleanSubtract(poly(q.GetEffectiveHoleShape(),True))
  cache[key]=ps
 return cache[key]
def overlap(a,b):
 t=p.SHAPE_POLY_SET();t.BooleanIntersection(a,b);return t.Area()/1e12
witnesses=[]
for w in plan['live_witnesses']:
 route=w['native_positive_copper_witness'];ep=[g[1]['pad_inventory'][u]['ref']+'.'+g[1]['pad_inventory'][u]['pad']for u in [route[0],route[-1]]]
 assert ep==w['endpoints'] and not ret.intersection(route)
 witnesses.append(dict(label=' to '.join(ep),route=route))
aw=load(P/'ATTACHMENT_TO_C128_JOIN.json');route=[x['uuid']for x in aw['objects']];assert route[0]==plan['preserve_attachment_track']['uuid'] and route[-1]==aw['target_track']=='1d4427cb-95fe-5142-8c69-bbae765376e7';witnesses.append(dict(label='attachment to C128 supply join',route=route))
# Validate attachment lies on retained track, C128.1 reaches stated join by first two edges.
q=items[1][route[0]];ax,ay=[round(v*1e6)for v in aw['attachment_xy_mm']];x0,y0=q.GetStart().x,q.GetStart().y;x1,y1=q.GetEnd().x,q.GetEnd().y
assert (ax-x0)*(y1-y0)==(ay-y0)*(x1-x0) and min(x0,x1)<=ax<=max(x0,x1) and min(y0,y1)<=ay<=max(y0,y1)
assert plan['live_witnesses'][0]['native_positive_copper_witness'][2]==aw['target_track']
positive_native_edges={};zone_witnesses=[]
for w in witnesses:
 ev=[]
 for a,c in zip(w['route'],w['route'][1:]):
  key=tuple(sorted((a,c)))
  if key in direct_maps[1]:
   support=[]
   for l in layers:
    if items[1][a].IsOnLayer(l)and items[1][c].IsOnLayer(l):
     ar=overlap(copper(items[1][a],l),copper(items[1][c],l))
     if ar>0:support.append([boards[1].GetLayerName(l),ar])
   assert support;positive_native_edges[key]=support;ev.append(dict(a=a,b=c,kind='direct',actual_native_support=support,original_saved_support=direct_maps[1][key]))
  else:
   z,u=(a,c)if a.startswith('zone:')else(c,a);assert (z,u)in zone_maps[1];zone_witnesses.append((z,u));ev.append(dict(a=a,b=c,kind='zone',area_mm2=zone_maps[1][z,u]))
 w['edges']=ev
# Zone witnesses: reproduce physical hole-subtracted full saved fill for the one referenced zone.
zone_cache={}
for z,u in set(zone_witnesses):
 _,zid,layerid,outlineid=z.split(':');l=int(layerid);oi=int(outlineid)
 if z not in zone_cache:
  zone=next(q for q in boards[1].Zones()if uidn(q)==zid);ps=p.SHAPE_POLY_SET(zone.GetFilledPolysList(l));drills=p.SHAPE_POLY_SET()
  for q in items[1].values():
   if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():drills.Append(poly(q.GetEffectiveHoleShape(),True))
  drills.Simplify();ps.BooleanSubtract(drills);sub=p.SHAPE_POLY_SET();sub.AddOutline(ps.COutline(oi))
  for h in range(ps.HoleCount(oi)):sub.AddHole(ps.CHole(oi,h),0)
  zone_cache[z]=sub
 ar=overlap(copper(items[1][u],l),zone_cache[z]);assert ar>0
check('all four live paths and attachment path with native positive support recomputation',len(witnesses)==5,dict(unique_direct_edges=len(positive_native_edges),unique_zone_edges=len(set(zone_witnesses)),hops=[len(w['route'])-1 for w in witnesses]))
(O/'verified-witnesses.json').write_text(json.dumps(witnesses,indent=2))
# DRC compares full records, retaining multiplicities, not merely endpoint sets/counts.
sd=load(Q/'source-drc.json');cd=load(Q/'drc.json');erc=load(Q/'erc.json');a=collections.Counter(map(canon,sd['violations']));b=collections.Counter(map(canon,cd['violations']));removed=[json.loads(x)for x in (a-b).elements()];added=[json.loads(x)for x in (b-a).elements()]
check('DRC 67 to 66 exact one named dangling warning removal and no other changes',len(sd['violations'])==67 and len(cd['violations'])==66 and len(removed)==1 and removed[0]['type']=='track_dangling' and removed[0]['severity']=='warning' and [x['uuid']for x in removed[0]['items']]==['53e7b99f-308f-57ae-9e47-9e779e6b3272']and not added,removed)
check('all 12 complete open records exactly equal, not just pairs',len(sd['unconnected_items'])==len(cd['unconnected_items'])==12 and collections.Counter(map(canon,sd['unconnected_items']))==collections.Counter(map(canon,cd['unconnected_items'])))
endpoint_evidence=[]
for v in cd['unconnected_items']:
 ep=[]
 for e in v['items']:
  u=e['uuid'];q=items[1][u];q0=items[0][u];pos=dict(x=q.GetPosition().x/1e6,y=q.GetPosition().y/1e6);assert pos==e['pos'] and q.GetPosition()==q0.GetPosition() and q.GetNetname()==q0.GetNetname() and ('['+q.GetNetname()+']') in e['description']
  if isinstance(q,p.PAD):
   prefix='Pad '+q.GetNumber()+' ['+q.GetNetname()+'] of '+q.GetParentFootprint().GetReference()+' on ';assert e['description'].startswith(prefix);reported_layer=e['description'][len(prefix):];assert q.IsOnLayer(boards[1].GetLayerID(reported_layer))
  else:assert e['description']=='Track ['+q.GetNetname()+'] on '+boards[1].GetLayerName(q.GetLayer())+', length '+format(q.GetLength()/1e6,'.4f')+' mm'
  ep.append(dict(uuid=u,description=e['description'],position_mm=pos,native_net=q.GetNetname(),source_root=roots[0][u],candidate_root=roots[1][u]))
 assert ep[0]['native_net']==ep[1]['native_net'] and ep[0]['source_root']!=ep[1]['source_root']and ep[0]['candidate_root']!=ep[1]['candidate_root'];endpoint_evidence.append(ep)
check('24 open endpoint occurrences native UUID/type/ref/pad/net/layer/position/length sanity and disconnected roots',len(endpoint_evidence)==12)
check('zero other DRC errors and parity/ERC empty',all(x['severity']=='warning'for x in cd['violations'])and sd['schematic_parity']==cd['schematic_parity']==[] and all(sh['violations']==[]for sh in erc['sheets']),dict(ERC_sheets=len(erc['sheets'])))
(O/'verified-open-endpoints.json').write_text(json.dumps(endpoint_evidence,indent=2))
# Provenance across actual commands, existing logs, named outputs, board hashes, and reused-source chain.
commands=load(Q/'commands.json');histcommands=load(H/'qa/commands.json');bindings=[]
for command_name,out,log,input_path in [('graph','candidate-physical-graph.json','graph.log',CB),('drc','drc.json','drc.log',CB),('erc','erc.json','erc.log',C/'maru60.kicad_sch')]:
 command=next(r for r in commands if str(Q/out) in r['command']);assert command['exit_code']==0 and str(input_path) in command['command'];logtext=(Q/log).read_text();assert str(Q/out)in logtext
 if command_name=='graph':assert 'DIRECT '+str(edge_counts[1]['direct'])in logtext and 'DONE '+str(Q/out)in logtext
 if command_name=='drc':assert '--schematic-parity'in command['command'] and 'Found 66 violations'in logtext and 'Found 12 unconnected items'in logtext and 'Found 0 schematic parity issues'in logtext
 if command_name=='erc':assert 'Found 0 violations'in logtext
 bindings.append(dict(kind=command_name,command=command,output_sha256=sha(Q/out),log_sha256=sha(Q/log),input_sha256=sha(input_path)))
check('candidate commands-output-log-input bindings',len(bindings)==3)
check('reused source graph/DRC bytes exactly original historical artifacts',sha(Q/'source-physical-graph.json')==sha(H/'qa/candidate-physical-graph.json') and sha(Q/'source-drc.json')==sha(H/'qa/candidate-drc.json')and sha(H/'candidate/pcb/maru60.kicad_pcb')==sha(SB))
for out,log in [('candidate-physical-graph.json','candidate-graph.log'),('candidate-drc.json','candidate-drc.log')]:
 cmd=next(r for r in histcommands if str(H/'qa'/out)in r['command']);assert cmd['exit_code']==0 and str(H/'candidate/pcb/maru60.kicad_pcb')in cmd['command'];assert str(H/'qa'/out)in (H/'qa'/log).read_text()
check('reused source historical commands/logs bind correct source board',True)
check('same native graph checker source used for source/candidate',sha(D/'tools/export_native_physical_graph.py')==sha(Path('/tmp/v7-buck-deadarm-trial-2c7e/tools/export_native_physical_graph.py')))
build=load(Q/'build.json');fill=load(Q/'fill.json');check('build/fill hash chain and emitted logs',build['source_board_sha256']==sha(SB)and build['source_contract_sha256']==expected_contract and build['prefill_sha256']==sha(PB)==fill['prefill_sha256']and fill['filled_sha256']==sha(CB)and canon(fill)==canon(json.loads((Q/'fill.log').read_text()))and canon(build)==canon(json.loads((Q/'build.log').read_text()[(Q/'build.log').read_text().index('{'):])))
check('actual-results log exactly machine report',load(Q/'ACTUAL_RESULTS.json')==json.loads((Q/'actual-results.log').read_text()))
check('checks log complete graph DRC ERC sequence',(Q/'checks.log').read_text()=='graph DONE\ndrc DONE\nerc DONE\n')
selected=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-buck-feedback-cleanup/candidate/pcb')
check('all 54 selected source files match isolated source snapshot',files(selected)==sf)
check('all inputs unchanged by this audit',files(S)==sf and files(C)==cf)
report=dict(status='RAW_FILES_DRC_AND_WITNESS_CHECKS_PASS; original graph support claims invalid due wrapper bug; corrected full graph audit separate; not global acceptance',source_sha256=sha(SB),candidate_sha256=sha(CB),contract_sha256=expected_contract,checks=checks,file_manifest='file-manifest.json',all_54_file_count=len(sf),retired_uuids=sorted(ret),retired_track_length_mm=retired_length,changed_zone_fill_uuids=changed_zone_fills,graph_edge_counts=edge_counts,pad_nets=245,pad_inventory_count=len(g[0]['pad_inventory']),native_total_pads=1437,witness_artifact='verified-witnesses.json',open_endpoints_artifact='verified-open-endpoints.json',removed_DRC_records=removed,command_bindings=bindings,strict_global_plane_gate='Separate parent review; the supplied strict native loss of 3.1345e-9 mm2 per plane remains a FAIL, not waived; BUCK-only 1nm criterion does not apply.',script_review=dict(graph='FAULT FOUND: GetConnectedTracks via neighbors are Python PCB_TRACK wrappers; isinstance-based hole subtraction can be skipped and cached. Original recorded support equality does not prove accurate physical support. Canonical direct support audit found 1042 changed areas and 3 redundant zero-area false edges; corrected full exports and controls are separate artifacts. All five path witnesses independently retain positive drill-aware copper.',comparison='Original compare_graphs.py uses booleans and set-based deltas and compares open pairs only. This audit strengthens those to independently reconstructed graph partitions, multiplicity-preserving full DRC/open-record comparisons and native endpoint sanity.',provenance='DRC/ERC JSON does not embed input SHA; binding is command/log plus byte-identical source chain, recorded graph hashes, unchanged 54-file input inventory, and build/refill hash chain. No claim of cryptographic execution attestation.',limits='No new full native graph exports or DRC/ERC executions. Existing native outputs were audited as requested. Native source and candidate loads and restricted witness geometry recomputation only. Not an impedance/stability/PDN performance analysis.'))
(O/'ELECTRICAL_AUDIT.json').write_text(json.dumps(report,indent=2));print('DONE',O/'ELECTRICAL_AUDIT.json')
