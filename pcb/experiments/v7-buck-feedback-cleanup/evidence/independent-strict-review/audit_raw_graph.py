import json,hashlib,collections,re,sys,math
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;D=Path('/tmp/v7-buck-deadarm-trial-2c7e');J=Path('/tmp/v7-j3-unselected-closure-2c7e/qa');B=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/candidate-four/pcb');C=D/'filled/pcb';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());V='d382de57-3476-43c4-ac26-0a72b21acf7c';T='2c0aa2c5-bec8-4dff-bff7-2e823d3e36fa';N='6ffab701-7688-4850-9aad-8ab86bd0f04a';ret={V,T}
def nodes(s):
 depth=0;quote=False;esc=False;start=0;out=[]
 for i,c in enumerate(s):
  if quote:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c=='"':quote=False
  elif c=='"':quote=True
  elif c=='(':
   if depth==1:start=i
   depth+=1
  elif c==')':
   depth-=1
   if depth==1:out.append(s[start:i+1])
 assert depth==0 and not quote;return out
head=lambda n:n.split(None,1)[0][1:].rstrip(')');uid=lambda n:re.search(r'\(uuid "([^"]+)"',n).group(1)
ns=nodes((B/'maru60.kicad_pcb').read_text());nc=nodes((C/'maru60.kicad_pcb').read_text())
def eligible(n,skip):return head(n)!='zone' and not(head(n) in ('segment','via') and uid(n) in skip)
assert [n for n in ns if eligible(n,ret)]==[n for n in nc if eligible(n,{N})]
z0={uid(n):n for n in ns if head(n)=='zone'};z1={uid(n):n for n in nc if head(n)=='zone'};assert z0.keys()==z1.keys()
for u,z in z0.items():assert [q for q in nodes(z) if head(q) not in ('filled_polygon','fill_segments')]==[q for q in nodes(z1[u]) if head(q) not in ('filled_polygon','fill_segments')]
filemaps={}
for name,path in [('selected',B),('copied_source',D/'source/pcb'),('prefill',D/'prefill/pcb'),('candidate',C)]:
 filemaps[name]={str(p.relative_to(path)):H(p) for p in sorted(path.rglob('*')) if p.is_file()};assert len(filemaps[name])==54
assert filemaps['selected']==filemaps['copied_source']
for name in ['prefill','candidate']:assert {k:v for k,v in filemaps[name].items() if k!='maru60.kicad_pcb'}=={k:v for k,v in filemaps['selected'].items() if k!='maru60.kicad_pcb'}
gs=read(J/'source-physical-graph.json');gc=read(D/'qa/candidate-physical-graph.json');assert gs['board_sha256']==H(B/'maru60.kicad_pcb') and gc['board_sha256']==H(C/'maru60.kicad_pcb');assert gs['pad_inventory']==gc['pad_inventory'];assert gs['native_version']==gc['native_version']=='9.0.2+dfsg-1';assert gs['native_pairs_without_positive_copper']==gc['native_pairs_without_positive_copper']
def edgekeys(g):return {tuple(sorted((a,b))):s for a,b,s in g['direct_edges']}
e0=edgekeys(gs);e1=edgekeys(gc);assert {k:v for k,v in e0.items() if not(set(k)&ret)}=={k:v for k,v in e1.items() if N not in k}
removed={k:v for k,v in e0.items() if set(k)&ret};added={k:v for k,v in e1.items() if N in k};assert len(removed)==4 and len(added)==3
assert {next(iter(set(k)-{N})) for k in added}=={'3c804add-ee74-5104-b471-73062ffcaeb9','d20e66e3-44fb-4535-81e2-9bc53c5f6519','37c51a69-ea1f-42e2-b356-72426fc3b1b2'}
z0={(a,b):s for a,b,s in gs['zone_edges']};z1={(a,b):s for a,b,s in gc['zone_edges']};assert z0.keys()==z1.keys();changed_support=[{'zone_object':k,'before_mm2':v,'after_mm2':z1[k],'delta_mm2':z1[k]-v} for k,v in z0.items() if z1[k]!=v]
def partition(g):
 parents={u:u for u in g['pad_inventory']}
 def find(u):
  parents.setdefault(u,u)
  while parents[u]!=u:parents[u]=parents[parents[u]];u=parents[u]
  return u
 def join(u,v):parents[find(v)]=find(u)
 for a,b,s in g['direct_edges']:assert s and all(x[1]>0 for x in s);join(a,b)
 for a,b,s in g['zone_edges']:assert s>0;join(a,b)
 out=collections.defaultdict(lambda:collections.defaultdict(list))
 for u,meta in g['pad_inventory'].items():out[meta['net']][find(u)].append(u)
 ans={n:sorted(sorted(ids) for ids in v.values()) for n,v in out.items()};assert ans==g['pad_partitions_by_net'];return ans
assert partition(gs)==partition(gc) and len(partition(gc))==245
# Prove source-root membership exact for all GND pads, not only GND flag/count.
p0=partition(gs)['GND'];p1=partition(gc)['GND'];root='186082bb-d1d7-429b-b059-389234bbb320';root0=next(v for v in p0 if root in v);root1=next(v for v in p1 if root in v);assert root0==root1
src=read(J/'fresh-source-drc.json');cand=read(D/'qa/drc.json');canon=lambda x:json.dumps(dict(x,items=sorted(x['items'],key=lambda q:q['uuid'])),sort_keys=True);a=collections.Counter(map(canon,src['violations']));b=collections.Counter(map(canon,cand['violations']));assert not(b-a) and sum((a-b).values())==1;warning=json.loads(next(iter(a-b)));assert warning['type']=='via_dangling' and warning['items'][0]['uuid']==V and len(warning['items'])==1;assert all(v['severity']=='warning' for v in cand['violations']);assert not cand['schematic_parity'];assert len(src['unconnected_items'])==len(cand['unconnected_items'])==12
opens_exact=collections.Counter(map(canon,src['unconnected_items']))==collections.Counter(map(canon,cand['unconnected_items']))
erc=read(D/'qa/erc.json');assert all(not s['violations'] for s in erc['sheets'])
r={'pass_raw_graph_and_diagnostic_review':True,'source_sha256':gs['board_sha256'],'candidate_sha256':gc['board_sha256'],'complete_filemaps':filemaps,'raw_all_unchanged_nonzone_nodes_exact':True,'raw_zone_settings_exact':True,'all_original_native_direct_support_exact_except_four_retired_edges':True,'four_retired_edges':[[list(k),v] for k,v in removed.items()],'three_new_replacement_edges':[[list(k),v] for k,v in added.items()],'zone_contact_identities_exact':True,'zone_contact_support_changes':changed_support,'all_245_pad_net_partitions_reconstructed_and_exact':True,'all_ground_pad_root_membership_exact':True,'ground_pads_in_J1_A1_root':len(root0),'native_20_unproven_direct_pairs_exact':True,'native_DRC':{'warnings':len(cand['violations']),'hard_errors':0,'opens':12,'parity':0,'removed_exact_warning':warning,'unconnected_records_exact':opens_exact},'native_ERC_violations':0,'source_graph_sha256':H(J/'source-physical-graph.json'),'candidate_graph_sha256':H(D/'qa/candidate-physical-graph.json'),'scope':'Observed source-bound native physical graph rechecked/reconstructed, not an independently rerun full graph. Independent native FB direct contacts and geometry were exported separately. Strict global plane loss remains a separate gate.'}
(R/'raw-graph-review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='complete_filemaps'},indent=2))
