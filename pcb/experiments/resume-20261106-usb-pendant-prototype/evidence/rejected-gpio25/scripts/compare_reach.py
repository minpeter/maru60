from screen_rules import *
import hashlib
N='EXT_GPIO25';out={'source':str(SRC),'sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'step_mm':.0125,'trace_width_mm':.15,'clearance_mm':.15}
for name,start,box in [('u11',(107.1,37.325),(95.5,29,115,46)),('bridge',(98.15,40.6),(95.5,29,115,46))]:
 search(N,p.B_Cu,start,box=box,step=.0125);pts=json.loads((ROOT/'qa/reach-last.json').read_text());(ROOT/f'qa/{name}-reach.json').write_text(json.dumps(pts));out[name]={'sites':len(pts),'bbox':[min(a[0]for a in pts),min(a[1]for a in pts),max(a[0]for a in pts),max(a[1]for a in pts)]}
 if name=='u11':
  rows=[]
  for a in pts:
   s=p.SHAPE_CIRCLE(V(*a),250000);keys=set();bb=s.BBox()
   for l in L:
    for x in range(bb.GetX()//1000000-1,bb.GetRight()//1000000+2):
     for y in range(bb.GetY()//1000000-1,bb.GetBottom()//1000000+2):keys.update(bins[l].get((x,y),()))
   hits=[]
   for k in keys:
    net,sh=shapes[k];gap=s.GetClearance(sh)
    if net!=N and gap<150000:hits.append({'uuid':k[0],'net':net,'layer':b.GetLayerName(k[1]),'gap_mm':gap/1e6})
   rows.append({'xy':a,'hits':hits})
  out[name]['clear_via_sites']=[r['xy']for r in rows if not r['hits']];out[name]['via_blocker_counts']=dict(collections.Counter(h['net']+' '+h['layer']for r in rows for h in r['hits']));(ROOT/'qa/via-blockers.json').write_text(json.dumps(rows))
a={tuple(x)for x in json.loads((ROOT/'qa/u11-reach.json').read_text())};z={tuple(x)for x in json.loads((ROOT/'qa/bridge-reach.json').read_text())};out['intersection_count']=len(a&z)
(ROOT/'qa/SUMMARY.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
