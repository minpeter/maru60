from pathlib import Path
import json,collections,math,pcbnew as p
R=Path('/workspace/shared/maru60-resume/continuation-c782/header');D=R/'qa';A=json.loads(Path('/workspace/shared/maru60-resume/combined-trial/qa/material-graph.json').read_text());B=json.loads((D/'material-graph.json').read_text());a=json.loads(Path('/workspace/shared/maru60-resume/combined-trial/qa/drc.json').read_text());b=json.loads((D/'drc.json').read_text());build=json.loads((D/'BUILD.json').read_text())
assert A['pad_inventory']==B['pad_inventory']
def keys(g,d):
 rp=collections.defaultdict(list)
 for u,meta in g['pad_inventory'].items():
  roots=g['object_material_roots'][u];assert len(roots)==1;rp[roots[0]].append(u)
 out=[];records=[]
 for row in d['unconnected_items']:
  roots=[];nets=[];ends=[]
  for item in row['items']:
   u=item['uuid'];rs=g['object_material_roots'][u];assert len(rs)==1;r=rs[0];assert rp[r];nodes=[n for ns in g['object_nodes_by_layer'][u].values()for n in ns];net={g['material_nodes'][n]['net']for n in nodes};assert len(net)==1;net=next(iter(net));roots.append(r);nets.append(net);ends.append({'uuid':u,'native_description':item['description'],'native_position':item['pos'],'complete_pad_component':sorted(rp[r])})
  assert len(set(nets))==1 and len(set(roots))==2
  k=(nets[0],tuple(sorted(tuple(x['complete_pad_component'])for x in ends)));out.append(k);records.append({'net':nets[0],'endpoints':ends})
 return collections.Counter(out),records
ak,ar=keys(A,a);bk,br=keys(B,b);removed=ak-bk;added=bk-ak;assert sum(removed.values())==1 and not added and next(iter(removed))[0]=='EXT_GPIO27'
(D/'open-component-pairs.json').write_text(json.dumps({'source_sha256':A['board_sha256'],'candidate_sha256':B['board_sha256'],'all_pad_inventory_exact':True,'only_closed_component_pair_net':'EXT_GPIO27','all_other_complete_open_pad_component_pairs_exact':True,'before_native_records':a['unconnected_items'],'after_native_records':b['unconnected_items'],'source_component_pairs':ar,'candidate_component_pairs':br,'pass':True},indent=2))
changes=[]
for k,v in A['material_nodes'].items():
 if v['kind']=='object'and v!=B['material_nodes'].get(k):changes.append({'id':k,'before':v,'after':B['material_nodes'].get(k)})
assert all(q['before']['uuid']in build['modified_source_uuids']for q in changes)
(D/'material-declared-changes.json').write_text(json.dumps({'all_undeclared_object_material_nodes_exact':True,'declared_object_changes':changes,'GND_pad_count':sum(x['net']=='GND'for x in B['pad_inventory'].values()),'GND_pad_partitions_exact':A['pad_partitions_by_net']['GND']==B['pad_partitions_by_net']['GND']},indent=2))
board=p.LoadBoard(str(R/'trial27/pcb/maru60.kicad_pcb'));zones={c['id']:z for z in B['zones']for c in z['components']};zc=collections.defaultdict(dict)
for zn,u,area in B['zone_edges']:
 z=zones[zn]
 if z['net']=='GND':zc[u][z['layer']]=area
barrels={x['uuid']:x for x in B['barrel_joins']};ground=[]
for x in board.GetTracks():
 u=x.m_Uuid.AsString()
 if isinstance(x,p.PCB_VIA)and x.GetNetname()=='GND'and u in barrels and all(zc[u].get(l,0)>0 for l in ['In1.Cu','In2.Cu']):
  ground.append({'uuid':u,'xy_mm':[x.GetPosition().x/1e6,x.GetPosition().y/1e6],'zone_contacts_mm2':zc[u],'barrel_verified':True})
rows=[]
for name,xy in [('new_GPIO27',[96.925,40.175]),('existing_GPIO27',[92.9,42.5]),('moved_GPIO26',[96.65,41.625]),('source_GPIO26',[96.8,41.775])]:
 vals=[dict(q,center_distance_mm=math.dist(xy,q['xy_mm']))for q in ground];vals.sort(key=lambda x:x['center_distance_mm']);rows.append({'transition':name,'xy_mm':xy,'nearest_three_grounded_through_vias':vals[:3]})
metrics={}
for net in ['EXT_GPIO10','EXT_GPIO26','EXT_GPIO27']:
 lens=[]
 for path in ['/workspace/shared/maru60-resume/combined-trial/pcb/maru60.kicad_pcb',str(R/'trial27/pcb/maru60.kicad_pcb')]:
  b2=p.LoadBoard(path);q=[x for x in b2.GetTracks()if x.GetNetname()==net];lens.append({'track_segments':sum(not isinstance(x,p.PCB_VIA)for x in q),'vias':sum(isinstance(x,p.PCB_VIA)for x in q),'length_mm':sum(x.GetLength()/1e6 for x in q if not isinstance(x,p.PCB_VIA))})
 metrics[net]={'before':lens[0],'after':lens[1],'length_delta_mm':lens[1]['length_mm']-lens[0]['length_mm']}
(D/'transition-evidence.json').write_text(json.dumps({'transitions':rows,'net_route_metrics':metrics,'no_new_GND_stitch_added':True,'limitation':'Distances and positive native material contacts establish nominal grounded return alternatives, not inductance, edge-rate suitability, impedance, SI, EMI, or physical validation.'},indent=2));print(json.dumps(rows,indent=2));print(json.dumps(metrics,indent=2))
