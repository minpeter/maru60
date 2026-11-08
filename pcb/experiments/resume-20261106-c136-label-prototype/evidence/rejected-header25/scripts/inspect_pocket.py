from screen import *
pts=json.loads((ROOT/'qa/reach-last.json').read_text()); rows=[]
for xy in pts:
 if math.dist(xy,(107.1,37.325))<.45:continue
 s=p.SHAPE_CIRCLE(V(*xy),250000);keys=set();bb=s.BBox()
 for l in L:
  for x in range(bb.GetX()//1000000,bb.GetRight()//1000000+1):
   for y in range(bb.GetY()//1000000,bb.GetBottom()//1000000+1):keys.update(bins[l].get((x,y),()))
 hits=[]
 for k in keys:
  net,sh=shapes[k];c=s.GetClearance(sh)
  if net!='EXT_GPIO25'and c<(150000 if net in ['','GND']else 205000):hits.append({'uuid':k[0],'layer':b.GetLayerName(k[1]),'net':net,'gap_mm':c/1e6})
 rows.append({'xy':xy,'hits':hits,'score':len({q['uuid']for q in hits})})
rows.sort(key=lambda q:(q['score'],sum(.205-x['gap_mm']for x in q['hits'])));(ROOT/'qa/pocket-sites.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[:15],indent=2))
for uid in sorted({q['uuid']for r in rows[:10]for q in r['hits']}):
 q=next(x for x in b.GetTracks()if U(x)==uid);print(uid,q.GetNetname(),b.GetLayerName(q.GetLayer()),q.GetStart(),q.GetEnd())
