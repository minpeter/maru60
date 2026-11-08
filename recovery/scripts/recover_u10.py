from pathlib import Path
import re,json,hashlib
base=Path(__file__).resolve().parent;arc=base.parent/'extracted/v7-si-advanced-20261104/return_geometry'
a=json.loads((arc/'baseline_native.json').read_text());b=json.loads((arc/'candidate_native.json').read_text());s=(base/'baseline3663.kicad_pcb').read_text();assert hashlib.sha256(s.encode()).hexdigest()==a['sha256']
x={v['id']:v for v in a['tracks']};y={v['id']:v for v in b['tracks']};assert all(x[k]==y[k] for k in x.keys()&y.keys());assert all(a[k]==b[k] for k in ['vias','pads','planes','zone_settings'])
pat=r'\n\t\(segment\n.*?\n\t\)';blocks=list(re.finditer(pat,s,re.S));netids={n:int(i)for i,n in re.findall(r'\(net (\d+) "([^"]*)"\)',s)}
for uid in x.keys()-y.keys():
 found=[m.group()for m in blocks if f'(uuid "{uid}")'in m.group()];assert len(found)==1;s=s.replace(found[0],'',1)
def fmt(v):return f'{v:.6f}'.rstrip('0').rstrip('.')
def make(t):
 return '\n\t(segment\n\t\t(start '+ ' '.join(map(fmt,t['a']))+')\n\t\t(end '+' '.join(map(fmt,t['b']))+')\n\t\t(width '+fmt(t['width'])+')\n\t\t(layer "'+t['layer']+'")\n\t\t(net '+str(netids[t['net']])+')\n\t\t(uuid "'+t['id']+'")\n\t)'
for uid in sorted(y.keys()-x.keys()):
 t=y[uid];matches=[m for m in re.finditer(pat,s,re.S)if f'(net {netids[t["net"]]})'in m.group() and f'(layer "{t["layer"]}")'in m.group()];assert matches
 later=[m for m in matches if re.search(r'\(uuid "([^"]+)"',m.group()).group(1)>uid]
 pos=later[0].start() if later else matches[-1].end();s=s[:pos]+make(t)+s[pos:]
out=base/'u10-reconstructed.kicad_pcb';out.write_text(s);h=hashlib.sha256(s.encode()).hexdigest();r={'source_sha256':a['sha256'],'reconstructed_sha256':h,'expected_sha256':b['sha256'],'exact_match':h==b['sha256'],'removed_ids':sorted(x.keys()-y.keys()),'added_ids':sorted(y.keys()-x.keys()),'method':'Raw existing board preserved; archived native track delta serialized using exact existing segment grammar and order. No save or refill.'};(base/'u10-reconstruction.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
