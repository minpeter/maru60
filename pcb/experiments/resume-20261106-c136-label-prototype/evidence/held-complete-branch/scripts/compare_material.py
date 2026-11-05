from pathlib import Path
import json,collections,hashlib,sys
R=Path('/workspace/shared/maru60-resume');S=R/'continuation-c782/combined27fix2';D=R/'continuation-9d787/branch4v';a=json.loads((S/'qa/material-graph.json').read_text());b=json.loads((D/'qa/material-graph.json').read_text());removed=set(json.loads((D/'qa/build.json').read_text())['removed']);fails=[]
def check(name,v):
 if not v:fails.append(name)
check('complete_pad_inventory',a['pad_inventory']==b['pad_inventory']);check('complete_pad_partitions',a['pad_partitions_by_net']==b['pad_partitions_by_net'])
def de(g):return {(x,y,l):area for x,y,ls in g['direct_edges']for l,area in ls if x not in removed and y not in removed}
def ze(g):return {(z,u):area for z,u,area in g['zone_edges']if u not in removed}
records={}
for name,fn in [('direct',de),('zone',ze)]:
 aa,bb=fn(a),fn(b);missing=[k for k in aa if k not in bb];reduced=[{'edge':k,'before':v,'after':bb[k]}for k,v in aa.items()if k in bb and bb[k]<v];added=[k for k in bb if k not in aa];records[name]={'old':len(aa),'new':len(bb),'missing':missing,'area_reduced':reduced,'added':added};check(name+'_contacts_preserved',not missing);check(name+'_overlap_areas_not_reduced',not reduced)
check('inherited_guard_failures_unchanged',a['guard_failing_material_edges']==b['guard_failing_material_edges']);check('51_guard_failures_explicit',len(b['guard_failing_material_edges'])==51)
# Native ratsnest representatives resolved to complete material pad components.
def mapped(g,drc):
 roots=collections.defaultdict(set)
 for u in g['pad_inventory']:
  rr=g['object_material_roots'][u];assert len(rr)==1;roots[rr[0]].add(u)
 out=[]
 for row in drc['unconnected_items']:
  pp=[]
  for i in row['items']:
   rr=g['object_material_roots'][i['uuid']];assert len(rr)==1;pp.append(tuple(sorted(roots[rr[0]])))
  out.append(tuple(sorted(pp)))
 return sorted(out)
check('native_open_complete_pad_pairs',mapped(a,json.loads((S/'qa/drc.json').read_text()))==mapped(b,json.loads((D/'qa/drc.json').read_text())))
# Raw serialized retained tracks/pads/footprints identical, not only connectivity.
sys.path.insert(0,str(R/'tools'));from sexpr_spans import children,head,field
ra=(S/'pcb/maru60.kicad_pcb').read_text();rb=(D/'pcb/maru60.kicad_pcb').read_text()
def primitives(raw):
 out={}
 for _,_,s in children(raw):
  if head(s)in('segment','arc','via','footprint'):
   u=json.loads(field(s,'uuid').split(' ',1)[1][:-1]);out[u]=s
 return out
pa,pb=primitives(ra),primitives(rb);check('only_declared_primitives_removed',set(pa)-set(pb)==removed and not set(pb)-set(pa));changed=[u for u in pb if pb[u]!=pa[u]];check('all_retained_primitive_serialization_identical',not changed)
res={'pass':not fails,'failures':fails,'contacts':records,'changed_retained_primitives':changed,'pad_inventory_equal':a['pad_inventory']==b['pad_inventory'],'pad_partitions_equal':a['pad_partitions_by_net']==b['pad_partitions_by_net'],'guard_failures':len(b['guard_failing_material_edges']),'native_open_complete_pad_pairs_equal':mapped(a,json.loads((S/'qa/drc.json').read_text()))==mapped(b,json.loads((D/'qa/drc.json').read_text()))};(D/'qa/material-comparison.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2));assert not fails
