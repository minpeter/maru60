import json,copy,math
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from shapely.affinity import rotate,translate
b=json.load(open('build/mcu-near-usb/base.json'));fs={f['ref']:f for f in b['fps']}
refs='U1 Y1 C110 C114 C106 C107 C104 C117 L1 C103 C112 C113 C116 R108 R104 R102 R103 C111 C199 C115 C108 C109 C102 TP5'.split()
ops=[]
for r in refs:
 f=fs[r];ops.append(dict(op='move_footprint',ref=r,x=137-f['x'],y=116.5-f['y'],rot=f['rot']+180))
# Flash plus local supply and CS pullup, independent placement.
for r in ['U3','C118','R105','C105']:
 f=fs[r]
 if r=='U3':x,y=10,35
 elif r=='C118':x,y=15.5,36.5
 elif r=='R105':x,y=15.5,35
 else:x,y=15.5,33.5
 ops.append(dict(op='move_footprint',ref=r,x=x,y=y,rot=f['rot']))
json.dump({'ops':ops},open('build/mcu-near-usb/placement-ops.json','w'),indent=2)
for op in ops:
 f=fs[op['ref']];angle=-(op['rot']-f['rot']);dx=op['x']-f['x'];dy=op['y']-f['y'];o=(f['x'],f['y'])
 def tx(g):return translate(rotate(g,angle,origin=o),xoff=dx,yoff=dy)
 f['courtyard']=[list(tx(Polygon(c)).exterior.coords) for c in f['courtyard']]
 for p in f['pads']:
  q=tx(Point(p['x'],p['y']));p['x'],p['y']=q.x,q.y;p['poly']=[list(tx(Polygon(c)).exterior.coords) for c in p['poly']]
 f.update(x=op['x'],y=op['y'],rot=op['rot'])
json.dump(b,open('build/mcu-near-usb/placed.json','w'))
# Quantify fixed footprint / drill collisions, not copper routing clearance.
moved={o['ref'] for o in ops};bad=[]
for r in moved:
 f=fs[r];g=unary_union([Polygon(c) for c in f['courtyard']])
 for other in b['fps']:
  if other['ref']==r:continue
  if other['layer']==f['layer']:
   a=g.intersection(unary_union([Polygon(c) for c in other['courtyard']])).area
   if a>1e-6:bad.append((r,other['ref'],'courtyard',round(a,6)))
  for p in other['pads']:
   if p['drill'][0] and g.intersects(Point(p['x'],p['y']).buffer(max(p['drill'])/2+.3)):bad.append((r,other['ref'],'hole',p['num']))
print(bad);json.dump(bad,open('build/mcu-near-usb/placement-collisions.json','w'),indent=2)
