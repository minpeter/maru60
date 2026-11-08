from optimistic_screen import *
front={tuple(x)for x in json.loads((ROOT/'qa/reach-last.json').read_text())};back={tuple(x)for x in json.loads((ROOT/'qa/B-reach.json').read_text())}
rows=[]
for a in sorted(front & back):
 s=p.SHAPE_CIRCLE(V(*a),250000);hits=[]
 for (uid,l),(net,sh)in shapes.items():
  if net=='EXT_GPIO24':continue
  gap=s.GetClearance(sh);need=150000 if net in['','GND']else 205000
  if gap<need:hits.append({'uuid':uid,'net':net,'layer':b.GetLayerName(l),'clearance_mm':gap/1e6,'required_screen_mm':need/1e6})
 rows.append({'xy':a,'hits':hits})
out={'overlap_sites':len(rows),'all_sites_have_blockers':all(x['hits']for x in rows),'blocker_counts':dict(collections.Counter((h['net'],h['layer']).__repr__()for r in rows for h in r['hits'])),'rows':rows}
(ROOT/'qa/bridge-blockers.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items()if k!='rows'})
