from screen import *
pts=json.loads((ROOT/'qa/u11-reach.json').read_text());rows=[]
for xy in pts:
 s=p.SHAPE_CIRCLE(V(*xy),250000);keys=set();bb=s.BBox()
 for l in L:
  for x in range(bb.GetX()//1000000-1,bb.GetRight()//1000000+2):
   for y in range(bb.GetY()//1000000-1,bb.GetBottom()//1000000+2):keys.update(bins[l].get((x,y),()))
 hits=[]
 for k in keys:
  net,sh=shapes[k];gap=s.GetClearance(sh)
  if net!='EXT_GPIO25' and gap<150000:hits.append(dict(uuid=k[0],layer=b.GetLayerName(k[1]),net=net,gap_mm=gap/1e6))
 rows.append(dict(xy=xy,hits=hits))
rows.sort(key=lambda r:(len(r['hits']),sum(.15-h['gap_mm']for h in r['hits'])));out=dict(rule_mm=.15,diameter_mm=.5,sites=len(rows),clear_sites=[r['xy']for r in rows if not r['hits']],blockers=dict(collections.Counter((h['net']+' '+h['layer'])for r in rows for h in r['hits'])),rows=rows)
(ROOT/'qa/u11-rule-blockers.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items()if k!='rows'});print(json.dumps(rows[:8],indent=2))
# Closest inter-region edge: native collisions, no conductor removed.
back=json.loads((ROOT/'qa/reach-last.json').read_text())
