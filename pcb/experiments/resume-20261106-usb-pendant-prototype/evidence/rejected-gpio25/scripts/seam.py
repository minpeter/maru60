from screen_rules import *
A=json.loads((ROOT/'new-rules/qa/u11-reach.json').read_text());Z=json.loads((ROOT/'new-rules/qa/bridge-reach.json').read_text());B=collections.defaultdict(list)
for z in Z:B[math.floor(z[0]*2),math.floor(z[1]*2)].append(z)
best=(1e9,None,None)
for a in A:
 ix,iy=math.floor(a[0]*2),math.floor(a[1]*2)
 for x in range(ix-2,ix+3):
  for y in range(iy-2,iy+3):
   for z in B[x,y]:
    d=math.dist(a,z)
    if d<best[0]:best=(d,a,z)
d,a,z=best;s=p.SHAPE_SEGMENT(V(*a),V(*z),150000);hits=[]
for (uid,l),(net,sh)in shapes.items():
 if l!=p.B_Cu or net=='EXT_GPIO25':continue
 gap=s.GetClearance(sh)
 if gap<150000:hits.append(dict(uuid=uid,net=net,gap_mm=gap/1e6))
out=dict(distance_mm=d,u11_point=a,bridge_point=z,blocked_shortcut=hits);(ROOT/'qa/seam.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
