import sys,glob
sys.path[:0]=glob.glob('/tmp/maru-assembly-uv/archive-v0/*')
import sys,glob,json,math,hashlib

from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
D=Path(__file__).parent;j=json.load(open(D/'identity-reference-export.json'));grounds={k:unary_union([Polygon(q['exterior'],q['holes'])for q in v])for k,v in j['GND_planes'].items()};out=[]
for t in j['new_reference_tracks']:
 a,z=t['start'],t['end'];length=math.dist(a,z)
 if not length:continue
 inner='In1.Cu'if t['layer']=='F.Cu'else'In2.Cu';v=[x for x in j['signal_vias']if x['net']==t['net']];excepts=unary_union([Point(x['start']).buffer(.55,quad_segs=64)for x in v]);n=(-(z[1]-a[1])/length,(z[0]-a[0])/length);result={}
 for name,off in [('left',-t['width']/2),('center',0),('right',t['width']/2)]:
  line=LineString([(a[0]+n[0]*off,a[1]+n[1]*off),(z[0]+n[0]*off,z[1]+n[1]*off)]);miss=line.difference(grounds[inner]).difference(excepts);result[name]={'missing_length_mm':miss.length,'intervals':list(miss.coords)if miss.geom_type=='LineString'else[list(x.coords)for x in getattr(miss,'geoms',[])if x.geom_type=='LineString']}
 out.append({'uuid':t['uuid'],'net':t['net'],'layer':t['layer'],'reference':inner,'start':a,'end':z,**result})
by={}
for net in sorted({r['net']for r in out}):by[net]={k:sum(r[k]['missing_length_mm']for r in out if r['net']==net)for k in['left','center','right']}
returns=[]
newids={t['uuid']for t in j['added']}
for v in j['signal_vias']:
 if v['uuid']not in newids and v['net']!='XIN':continue
 nearest=sorted(j['GND_vias'],key=lambda g:math.dist(v['start'],g['start']))[:3];returns.append({'signal_via':v,'nearest_GND':[{**g,'center_distance_mm':math.dist(v['start'],g['start']),'filled_annulus_intersection_mm2':{l:grounds[l].intersection(Point(g['start']).buffer(.25,quad_segs=64).difference(Point(g['start']).buffer(.125,quad_segs=64))).area for l in grounds}}for g in nearest]})
r={'candidate_sha256':j['candidate_sha256'],'method':'Continuous Shapely intersections of native filled GND polygons with each new non-power/non-ground outer track center and parallel copper edges. Only same-net signal-via radius0.55mm launch disks excluded. Does not qualify impedance or oscillator startup.','totals_by_net_mm':by,'tracks':out,'source_return_vias':returns,'source_validation':'Full native protected-net opens zero and all215GND pads source-reached, together with actual nearest GNDvia annulus/filled-polygon area; center distance not full return-loop length.'};(D/'continuous-new-reference.json').write_text(json.dumps(r,indent=2));print(by);print([(v['signal_via']['net'],v['signal_via']['start'],v['nearest_GND'][0]['center_distance_mm'])for v in returns])
