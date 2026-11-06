from screen import *
import copy
scope=json.loads((ROOT/'qa/FROZEN_STUDY.json').read_text());base=scope['fixed_gpio24'];ids=[base['via_uuid']]+base['retarget_tracks'];idx={U(q):q for q in b.GetTracks()}
for l in bins:
 for k in bins[l]:bins[l][k]=[key for key in bins[l][k]if key[0]not in ids]
keep=[]
for t in base['modified_tracks']:
 for a,z in [(t['start'],t['retain_to']),(t['retain_to'],t['new_end'])]:
  q=p.PCB_TRACK(b);q.SetStart(V(*a));q.SetEnd(V(*z));q.SetWidth(150000);q.SetLayer(b.GetLayerID(t['layer']));q.SetNetCode(idx[t['uuid']].GetNetCode());keep.append(q);addobs(q)
v=idx[base['via_uuid']].Duplicate();v.SetPosition(V(*base['via24_new']));keep.append(v);addobs(v)
out=[]
for i,a in enumerate(scope['sites_J3']):
 for j,z in enumerate(scope['sites_bridge']):
  plan=copy.deepcopy(base);plan['gpio25_vias']=[a,z];plan['J3'][-1]=a;plan['F'][0]=a;plan['F'][-1]=z;plan['B'][0]=z;name=f'j{i}-b{j}';row={'case':name,'sites_clear':[viaok('EXT_GPIO25',a),viaok('EXT_GPIO25',z)]};print(name,row,flush=True)
  if all(row['sites_clear']):
   failures=[]
   for key,l,box in [('J3',p.B_Cu,(92.5,38,95,41)),('F',p.F_Cu,(89,39,100,43.5)),('B',p.B_Cu,(95.5,36.5,108,42.2))]:
    if not all(edge('EXT_GPIO25',l,x,y)for x,y in zip(plan[key],plan[key][1:])):
     path=search('EXT_GPIO25',l,plan[key][0],plan[key][-1],box,step=.025)
     if path:plan[key]=path
     else:failures.append(key)
   row['route_failures']=failures
   if not failures:
    folder=ROOT/'variants'/name; (folder/'qa').mkdir(parents=True);(folder/'qa/FROZEN_SCOPE.json').write_text(json.dumps(plan,indent=2))
  out.append(row);(ROOT/'qa/PLANNING.json').write_text(json.dumps(out,indent=2))
