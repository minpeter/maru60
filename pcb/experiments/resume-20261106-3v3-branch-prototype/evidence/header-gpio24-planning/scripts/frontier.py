from optimistic_screen import *
pts=json.loads((ROOT/'qa/reach-last.json').read_text())
goal=(92.35,37.75);pts.sort(key=lambda xy:math.dist(xy,goal))
rows=[]
for a in pts[:20]:
 z=(a[0],round(a[1]-.05,6));s=p.SHAPE_SEGMENT(V(*a),V(*z),150000)
 hits=[]
 for (uid,l),(net,sh) in shapes.items():
  if l==p.F_Cu and net!='EXT_GPIO24':
   gap=s.GetClearance(sh)
   if gap<(205000 if uid in drilled_signal_uuids else C):hits.append({'uuid':uid,'net':net,'clearance_mm':gap/1e6})
 rows.append({'from':a,'to':z,'distance_to_target_mm':math.dist(a,goal),'hits':hits})
(ROOT/'qa/frontier-obstacles.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows[:8],indent=2))
