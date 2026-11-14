#!/usr/bin/env python3
"""Plan LED-pad escape vias, with explicit minimal trace rip-up when required.

No CAD mutation. Critical USB/QSPI/oscillator/VREG copper and all pads/vias are
fixed obstacles. Every removed track is recorded; rerouting and native DRC are
required. Existing populated pad centers are obtained from native components.
"""
import argparse,json,math,re,itertools
from pathlib import Path
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
import local_router as LR

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('geometry',type=Path);ap.add_argument('components',type=Path);ap.add_argument('output',type=Path)
ap.add_argument('--refs',default='^LED',help='Reference regular expression; defaults to LEDs')
ap.add_argument('--nets',default=None,help='Optional net regular expression')
ap.add_argument('--small-components',action='store_true',help='Also escape small B.Cu-only components')
a=ap.parse_args();g=json.loads(a.geometry.read_text());entries=json.loads(a.components.read_text());L=LR.Layout(g)
critical=lambda n:n.startswith(('USB_','QSPI_','VREG_')) or n in ('XIN','XOUT','XTAL_OUT','+1V1')
centers={tuple(pt) for e in entries for group in e['groups'] if len(group)==1 or (a.small_components and len(group)<12 and all(pt[0]=='B.Cu' for pt in group)) for pt in group}
targets=[(f,p) for f in g['fps'] if re.search(a.refs,f['ref']) for p in f['pads'] if any((layer,round(p['x'],6),round(p['y'],6)) in centers for layer in p['layers'])]
targets=[(f,p) for f,p in targets if a.nets is None or re.search(a.nets,p['net'])]
removed,tracks,vias,report=[],[],[],[]
original_ids={id(t) for t in g['tracks']}
for f,p in targets:
 net=p['net'];layer=f['layer'];sx,sy=p['x'],p['y'];start=(sx,sy);best=None
 # Nearby trees avoid exact comparisons against the entire PCB per candidate.
 window=Point(sx,sy).buffer(4)
 nearby={ly:[c for c in L.cu[ly] if c[0].intersects(window) and c[1]!=net and not(c[2]=='zone' and c[1] in ('GND','+3V3'))] for ly in LR.OUTER}
 smd=[s for s,_ in L.smd if s.intersects(window)];holes=[h for h in L.pad_holes+L.via_holes if h.intersects(window)]
 inner=[(s,n) for s,n in L.inner if n!=net and s.intersects(window)]
 edge=L.outline.buffer(-.505)
 for ix,iy,offset in itertools.product(range(-26,27),range(-26,27),[(0,0),(.7,0),(-.7,0),(0,.7),(0,-.7)]):
   x,y=round(sx+ix*.1,6),round(sy+iy*.1,6);distance=math.hypot(x-sx,y-sy)
   if distance<.65 or distance>2.6:continue
   path=[start]+([(sx+offset[0],sy+offset[1])] if offset!=(0,0) else [])+[(x,y)]
   ann=Point(x,y).buffer(.25,24);drill=Point(x,y).buffer(.125,24);trace=LineString(path).buffer(.075,24)
   if not edge.contains(ann) or not edge.contains(trace):continue
   if any(s.distance(drill)<.105 for s in smd) or any(h.distance(drill)<.355 for h in holes):continue
   if any(s.distance(ann)<.185 for s,n in inner):continue
   if net=='GND' and not all(any(s.contains(Point(x,y).buffer(.35,24)) for s in shapes) for shapes in L.gnd_planes.values()):continue
   rip=[];invalid=False
   for ly in LR.OUTER:
    shape=ann.union(trace) if ly==layer else ann
    for c in nearby[ly]:
     if c[0].distance(shape)>=.185:continue
     if c[2]!='track' or critical(c[1]) or id(c[3]) not in original_ids:invalid=True;break
     if c[3] not in rip:rip.append(c[3])
    if invalid:break
   if invalid:continue
   # Cut only the obstructing interval of a long track. Preserve its distant
   # validated sections, and make the resulting open explicit for rerouting.
   leftovers=[];length=0
   for t in rip:
    line=LineString([(t['x1'],t['y1']),(t['x2'],t['y2'])])
    shape=ann.union(trace) if t['layer']==layer else ann
    remain=line.difference(shape.buffer(t['w']/2+.20,24))
    length+=line.length-remain.length
    for piece in getattr(remain,'geoms',[remain]):
     if piece.is_empty or piece.length<.05:continue
     aa,bb=piece.coords[0],piece.coords[-1]
     leftovers.append(dict(t,x1=aa[0],y1=aa[1],x2=bb[0],y2=bb[1]))
   if length>25:continue
   score=20*len(rip)+length+LineString(path).length
   if best is None or score<best[0]:best=(score,x,y,rip,leftovers,path)
 if best is None:
  report.append({'ref':f['ref'],'pad':p['num'],'net':net,'status':'no-local-escape'});continue
 _,x,y,rip,leftovers,path=best
 for t in rip:
  L.remove_track(t);removed.append(t)
 for t in leftovers:
  L.add_track(t);tracks.append(t)
 for aa,bb in zip(path,path[1:]):
  if math.dist(aa,bb)<1e-6:continue
  t=dict(x1=aa[0],y1=aa[1],x2=bb[0],y2=bb[1],w=.15,layer=layer,net=net);tracks.append(t);L.add_track(t)
 v=dict(x=x,y=y,d=.5,drill=.25,net=net);vias.append(v);L.add_via(x,y,net)
 report.append({'ref':f['ref'],'pad':p['num'],'net':net,'status':'planned','via':[x,y],'removed_tracks':len(rip),'removed_nets':sorted({t['net'] for t in rip})})
 print(report[-1],flush=True)
a.output.write_text(json.dumps({'status':'escape plan; rerouting and native DRC required','ops':[{'op':'remove_tracks','tracks':removed},{'op':'add_tracks','tracks':tracks},{'op':'add_vias','vias':vias}],'report':report},indent=2)+'\n')
