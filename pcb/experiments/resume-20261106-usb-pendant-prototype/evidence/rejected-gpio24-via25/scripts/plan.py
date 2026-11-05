from screen import *
idx={U(q):q for q in b.GetTracks()};vid='79e90551-63f2-4d3a-82a7-9d5d6259c3d6';tids=['b9d330ac-1b1c-42cf-989e-7a81dbfe810a','27d5bab5-97b2-409f-970d-ef67b5e0bc6a'];v=idx[vid];print('VIA',v.GetDrillValue(),[(b.GetLayerName(l),v.GetWidth(l))for l in L],flush=True)
for l in bins:
 for k in bins[l]:bins[l][k]=[key for key in bins[l][k]if key[0]not in [vid]+tids]
# retain source objects without mutation; add explicit replacement obstacle copies.
oldbins={l:{k:list(z)for k,z in bins[l].items()}for l in L};oldshapes=shapes.copy();candidates=[]
def via_site(a):
 s=p.SHAPE_CIRCLE(V(*a),v.GetWidth(p.F_Cu)//2)
 return all(net=='EXT_GPIO24' or s.GetClearance(sh)>=(150000 if net in['','GND']else 205000)for (uid,l),(net,sh)in shapes.items()if uid not in [vid]+tids)
for x in range(105300000,106300001,25000):
 for y in range(37000000,38000001,25000):
  a=(x/1e6,y/1e6)
  if math.dist(a,(105.8,37.5))<.1 or not via_site(a):continue
  if all(edge('EXT_GPIO24',idx[t].GetLayer(),(idx[t].GetStart().x/1e6,idx[t].GetStart().y/1e6),a,idx[t].GetWidth())for t in tids):candidates.append(a)
candidates.sort(key=lambda a:math.dist(a,(105.8,37.5)));print('SITES',candidates,flush=True);(ROOT/'qa/sites.json').write_text(json.dumps(candidates))
j=search('EXT_GPIO25',p.B_Cu,(93.5,39),goal=(93.925,40.175),box=(92,38,96,42),step=.025);f=search('EXT_GPIO25',p.F_Cu,(93.925,40.175),goal=(98.15,40.6),box=(89,38.8,100,44),step=.025)
plans=[]
for a in candidates[:40]:
 shapes.clear();shapes.update(oldshapes)
 for l in bins:bins[l]=collections.defaultdict(list,{k:list(z)for k,z in oldbins[l].items()})
 new=[]
 q=v.Duplicate();q.SetPosition(V(*a));new.append(q)
 for t in tids:q=idx[t].Duplicate();q.SetEnd(V(*a));new.append(q)
 for q in new:addobs(q)
 path=search('EXT_GPIO25',p.B_Cu,(98.15,40.6),goal=(107.1,37.325),box=(95.5,34,110,44),step=.025)
 plans.append({'via24':a,'path':path})
 if path:
  out={'via24_old':[105.8,37.5],'via24_new':a,'via_uuid':vid,'retarget_tracks':tids,'J3':j,'F':f,'B':path,'gpio25_vias':[(93.925,40.175),(98.15,40.6)]};(ROOT/'qa/PLAN.json').write_text(json.dumps(out,indent=2));print('PLAN',out,flush=True);break
(ROOT/'qa/attempts.json').write_text(json.dumps(plans,indent=2))
