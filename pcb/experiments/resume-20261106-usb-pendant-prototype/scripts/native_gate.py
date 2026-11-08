from pathlib import Path
import json,collections
R=Path('/workspace/shared/maru60-resume');S=R/'selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype';D=R/'continuation-fa96a7c/usb-stub';a=json.loads((S/'qa/drc.json').read_text());b=json.loads((D/'qa/drc.json').read_text());out={}
for k in ['violations','unconnected_items','schematic_parity']:
 old={json.dumps(x,sort_keys=True)for x in a[k]};new={json.dumps(x,sort_keys=True)for x in b[k]};out[k]={'before':len(a[k]),'after':len(b[k]),'removed':[json.loads(x)for x in sorted(old-new)],'added':[json.loads(x)for x in sorted(new-old)],'before_categories':dict(collections.Counter(x['severity']+':'+x['type']for x in a[k])),'after_categories':dict(collections.Counter(x['severity']+':'+x['type']for x in b[k]))}
v=out['violations'];out['severity_item_gate_pass']=not v['added'] and len(v['removed'])==1 and any(i['uuid']=='b04e3a6d-1e98-43d1-9b10-58c23321ca28'for i in v['removed'][0]['items']);out['open_count_unchanged']=len(a['unconnected_items'])==len(b['unconnected_items'])==9
out['physical_open_pair_gate']='Pending fresh corrected material graph; representative equality/count alone not sufficient.'
(D/'qa/native-gate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['severity_item_gate_pass']and out['open_count_unchanged']
