from screen_rules import *
pts={tuple(a)for a in json.loads((ROOT/'new-rules/qa/bridge-reach.json').read_text())};step=.0125;out=[]
for a in pts:
 if a[0]<105:continue
 for dx,dy in [(1,0),(0,-1),(0,1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
  z=(round(a[0]+dx*step,6),round(a[1]+dy*step,6))
  if z in pts:continue
  s=p.SHAPE_SEGMENT(V(*a),V(*z),150000);bb=s.BBox();keys=set()
  for x in range(bb.GetX()//1000000,bb.GetRight()//1000000+1):
   for y in range(bb.GetY()//1000000,bb.GetBottom()//1000000+1):keys.update(bins[p.B_Cu].get((x,y),()))
  hits=[]
  for k in keys:
   net,sh=shapes[k];gap=s.GetClearance(sh)
   if net!='EXT_GPIO25' and gap<150000:hits.append(dict(uuid=k[0],net=net,gap_mm=gap/1e6))
  out.append(dict(a=a,z=z,hits=hits))
summary=dict(edges=len(out),blockers=dict(collections.Counter(h['net']for r in out for h in r['hits'])),rows=out);(ROOT/'qa/bridge-frontier.json').write_text(json.dumps(summary,indent=2));print({k:v for k,v in summary.items()if k!='rows'})
idx={U(q):q for q in list(b.GetTracks())+pads};scope=json.loads((ROOT/'qa/joint-scope.json').read_text());details=[]
for r in scope['contacts']:
 for k in ['a','z']:
  uid=r[k].split(':')[1];q=idx[uid];entry=dict(uuid=uid,net=q.GetNetname(),type=q.GetClass(),xy=[q.GetPosition().x/1e6,q.GetPosition().y/1e6])
  if isinstance(q,p.PCB_TRACK):entry['end']=[q.GetEnd().x/1e6,q.GetEnd().y/1e6]
  details.append(entry)
(ROOT/'qa/retained-contact-details.json').write_text(json.dumps(details,indent=2));print(json.dumps(details,indent=2))
