from pathlib import Path
import json,collections,hashlib
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-9d787/stub4v';S=R/'continuation-c782/combined27fix2';a=json.loads((S/'qa/drc.json').read_text());b=json.loads((D/'qa/drc.json').read_text());out={}
for k in ['violations','unconnected_items','schematic_parity']:
 old={json.dumps(x,sort_keys=True)for x in a[k]};new={json.dumps(x,sort_keys=True)for x in b[k]};out[k]={'before':len(a[k]),'after':len(b[k]),'removed':[json.loads(x)for x in sorted(old-new)],'added':[json.loads(x)for x in sorted(new-old)],'before_categories':dict(collections.Counter(x['severity']+':'+x['type']for x in a[k])),'after_categories':dict(collections.Counter(x['severity']+':'+x['type']for x in b[k]))}
out['pass']=not out['violations']['added'];out['decision']='REJECTED: a new dangling warning appears on retained active rail 05a61be2; severity/category totals alone hide replacement of the warned object. Stop before deeper checks.';out['open_pair_limit']='Native representative items differ in four pre-existing open-pair reports. No fresh material/partition validation run after failed gate; count equality is not accepted as physical proof.'
(D/'qa/native-gate.json').write_text(json.dumps(out,indent=2)+'\n');assert not out['pass'];print(out['decision'])
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert h(S/'pcb/maru60.kicad_pcb')=='9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed'
changed=[]
for f in (S/'pcb').rglob('*'):
 if f.is_file() and h(f)!=h(D/'pcb'/f.relative_to(S/'pcb')):changed.append(str(f.relative_to(S/'pcb')))
assert changed==['maru60.kicad_pcb'];manifest={'source_sha256':h(S/'pcb/maru60.kicad_pcb'),'rejected_candidate_sha256':h(D/'pcb/maru60.kicad_pcb'),'only_changed_project_file':changed,'sha256':{str(f.relative_to(D)):h(f)for f in D.rglob('*')if f.is_file()}};(D/'HASHES.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in manifest.items()if k!='sha256'},indent=2))
