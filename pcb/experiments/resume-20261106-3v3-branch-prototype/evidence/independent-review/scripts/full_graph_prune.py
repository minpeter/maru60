from pathlib import Path
import json,collections
R=Path('/workspace/shared/maru60-resume');S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype';D=R/'continuation-97d9eb7/stub3v3-independent';x=json.loads((S/'qa/material-graph.json').read_text());ns=x['material_nodes'];retired={'53e7b99f-308f-57ae-9e47-9e779e6b3272','f9815195-95ae-5029-9575-af5b562417f2','0826a4b6-5567-52ab-a787-b898d20d23ac','fba8f2b5-a5de-578b-a107-ce7c9d080fb6','9f355e92-2386-5d9a-b330-367e9a6d6370','7ffc8178-bb79-51de-b57d-c5c6afb0ad28','872bfd37-a607-537a-a7fa-650d69bca58e','19fee20c-f24a-5570-9d2d-8ed9371d42bb','cbe6ef4b-6ae2-561c-89a1-59cf696150b8','0858c392-ee59-5350-bcaf-d8762f658a08'};keep={n for n,v in ns.items()if v.get('uuid') not in retired}
def components(prune):
 adj=collections.defaultdict(set)
 edges=[e[:2] for e in x['material_edges']]
 for bar in x['barrel_joins']:edges.extend(zip(bar['nodes'],bar['nodes'][1:]))
 for a,b in edges:
  if prune and (a not in keep or b not in keep):continue
  adj[a].add(b);adj[b].add(a)
 todo=set(keep);out=[]
 while todo:
  start=next(iter(todo));seen={start};queue=[start]
  while queue:
   for n in adj[queue.pop()]:
    if n not in seen:seen.add(n);queue.append(n)
  remain=seen&keep;todo-=remain;out.append(tuple(sorted(remain)))
 return sorted(out)
a=components(False);b=components(True);assert a==b
incident=[e for e in x['material_edges']if any(ns[n].get('uuid')in retired for n in e[:2])]
guards=[e for e in x['guard_failing_material_edges']if any(ns[n].get('uuid')in retired for n in[e['a'],e['b']])]
assert not guards;assert not(retired&set(x['pad_inventory']))
via='0826a4b6-5567-52ab-a787-b898d20d23ac'
r=dict(source_sha256=x['board_sha256'],proposed_retired=sorted(retired),retained_nodes=len(keep),retained_components=len(a),exact_retained_partition_unchanged=True,pad_inventory_untouched=True,incident_edges=incident,incident_guard_failures=guards,via_barrel_proof=next(z for z in x['barrel_joins']if z['uuid']==via),limits='Source graph pruning only; no candidate, refill, plane no-loss, native warning, or electromagnetic proof.')
r['boundary_contacts']=[e for e in incident if sum(ns[n].get('uuid')in retired for n in e[:2])==1]
r['boundary_contact_nodes']={n:ns[n]for e in r['boundary_contacts']for n in e[:2]}
def padparts(comps):
 return sorted(tuple(sorted({ns[n].get('uuid')for n in comp if ns[n].get('uuid')in x['pad_inventory']}))for comp in comps if any(ns[n].get('uuid')in x['pad_inventory']for n in comp))
r['pad_partitions_before']=padparts(a);r['pad_partitions_after']=padparts(b);assert r['pad_partitions_before']==r['pad_partitions_after']
(D/'qa/full-graph-prune.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
