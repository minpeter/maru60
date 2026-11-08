from pathlib import Path
import json,collections
R=Path('/workspace/shared/maru60-resume');S=R/'selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype';D=R/'continuation-fa96a7c/usb-stub';x=json.loads((S/'qa/material-graph.json').read_text());ns=x['material_nodes'];retired={'b04e3a6d-1e98-43d1-9b10-58c23321ca28'};keep={n for n,v in ns.items()if v.get('uuid') not in retired}
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
via='ba0e0532-1586-4050-a390-d87dcee11d2c'
r=dict(source_sha256=x['board_sha256'],proposed_retired=sorted(retired),retained_nodes=len(keep),retained_components=len(a),exact_retained_partition_unchanged=True,pad_inventory_untouched=True,incident_edges=incident,incident_guard_failures=guards,via_barrel_proof=next(z for z in x['barrel_joins']if z['uuid']==via),limits='Source graph pruning only; no candidate, refill, plane no-loss, native warning, or electromagnetic proof.')
r['boundary_contacts']=[e for e in incident if sum(ns[n].get('uuid')in retired for n in e[:2])==1]
r['boundary_contact_nodes']={n:ns[n]for e in r['boundary_contacts']for n in e[:2]}
def padparts(comps):
 return sorted(tuple(sorted({ns[n].get('uuid')for n in comp if ns[n].get('uuid')in x['pad_inventory']}))for comp in comps if any(ns[n].get('uuid')in x['pad_inventory']for n in comp))
r['pad_partitions_before']=padparts(a);r['pad_partitions_after']=padparts(b);assert r['pad_partitions_before']==r['pad_partitions_after']
(D/'qa/full-graph-prune.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

active={'cc183bf5-15f3-5270-ae14-886f402cad67','a963e830-796c-53b3-b9de-ef49be1314bc'}
patches=[e for e in x['material_edges']if set(ns[n].get('uuid')for n in e[:2]) in [{via,u} for u in active]]
assert len(patches)==2
assert all(e[2]>0 and e[3]>0 for e in patches)
r['retained_active_patches']=patches
r['finite_scope_authorized_for_candidate']=len(r['boundary_contacts'])==1 and not guards
(D/'qa/full-graph-prune.json').write_text(json.dumps(r,indent=2)+'\n')
