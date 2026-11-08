import json,hashlib,collections,re
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parent;J=Path('/tmp/v7-j3-unselected-closure-2c7e/qa');D=Path('/tmp/v7-buck-deadarm-trial-2c7e/qa');read=lambda p:json.loads(p.read_text())
def check(ob,g,dr):
 parents={u:u for u in ob['objects']}
 def find(u):
  parents.setdefault(u,u)
  while parents[u]!=u:parents[u]=parents[parents[u]];u=parents[u]
  return u
 def join(a,b):parents[find(a)]=find(b)
 for a,b,s in g['direct_edges']:assert s and all(v[1]>0 for v in s);join(a,b)
 for a,b,s in g['zone_edges']:assert s>0;join(a,b)
 groups=collections.defaultdict(list)
 for u in list(parents):groups[find(u)].append(u)
 groups={k:sorted(v) for k,v in groups.items()};pairs=[];records=[]
 assert dr['coordinate_units']=='mm' and dr['kicad_version']=='9.0.2'
 for rec in dr['unconnected_items']:
  assert set(rec)=={'description','items','severity','type'} and rec['description']=='Missing connection between items' and rec['severity']=='error' and rec['type']=='unconnected_items' and len(rec['items'])==2
  parts=[];net=[]
  for item in rec['items']:
   assert set(item)=={'description','pos','uuid'} and set(item['pos'])=={'x','y'};u=item['uuid'];m=ob['objects'][u];net.append(m['net']);actualpos=[int(Decimal(str(item['pos'][a]))*1000000) for a in ('x','y')];assert actualpos==m['position_nm'];assert len(m['layers'])==1
   if m['class']=='PAD':expected=f"Pad {m['pin']} [{m['net']}] of {m['ref']} on {m['layers'][0]}"
   elif m['class']=='PCB_TRACK':expected=f"Track [{m['net']}] on {m['layers'][0]}, length {m['length_mm']:.4f} mm"
   else:raise AssertionError('unsupported endpoint type')
   assert item['description']==expected
   parts.append(groups[find(u)])
  assert net[0]==net[1] and parts[0]!=parts[1];parts.sort();pairs.append(json.dumps(parts,separators=(',',':')));records.append({'net':net[0],'endpoint_uuids':sorted(x['uuid'] for x in rec['items']),'complete_components':parts})
 assert len(set(pairs))==len(pairs)==12
 return pairs,records
S=read(R/'source-strip.json');C=read(R/'candidate-strip.json');a,ar=check(S,read(J/'source-physical-graph.json'),read(J/'fresh-source-drc.json'));b,br=check(C,read(D/'candidate-physical-graph.json'),read(D/'drc.json'));assert collections.Counter(a)==collections.Counter(b)
old={json.dumps(q['complete_components'],separators=(',',':')):q for q in ar};changes=[]
for q in br:
 p=old[json.dumps(q['complete_components'],separators=(',',':'))]
 if p['endpoint_uuids']!=q['endpoint_uuids']:changes.append({'net':q['net'],'before':p['endpoint_uuids'],'after':q['endpoint_uuids'],'complete_component_pair_exact':True})
out={'source_sha256':S['board_sha256'],'candidate_sha256':C['board_sha256'],'pass_exact_twelve_complete_component_pairs':True,'all48_endpoints_UUID_native_position_description_validated':True,'unique_component_pairs':12,'representative_changes':changes,'source_records':ar,'candidate_records':br,'method':'Independent union-find from all positive direct/zone edges; exact full UUID member sets per endpoint pair, not count or same-net equivalence. Native exported type/net/position/layer/ref/pin/length validate every observed endpoint.'}
(R/'open-pair-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['source_records','candidate_records']},indent=2))
