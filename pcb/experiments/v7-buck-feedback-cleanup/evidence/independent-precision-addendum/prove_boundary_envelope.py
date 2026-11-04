if not __debug__:
 raise RuntimeError('Optimized Python is unsupported for this proof')
import os,json,collections,difflib,math,hashlib
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parent;D=Path(os.environ.get('BUCK_STRICT_PACKET','/tmp/v7-buck-deadarm-independent-review/packet'));H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((D/'MANIFEST.json').read_text())['files']
for n in ['source-strip.json','candidate-strip.json']:assert H(D/n)==manifest[n]['sha256']
S=json.loads((D/'source-strip.json').read_text());C=json.loads((D/'candidate-strip.json').read_text())
def cycles(pts):
 es=collections.Counter(zip(pts,pts[1:]+pts[:1]));remain=es.copy()
 for edge,num in es.items():remain[edge]-=min(num,es[edge[::-1]])
 remain=+remain;assert all(n==1 for n in remain.values());adj={a:b for a,b in remain};assert len(adj)==len(remain) and set(adj)==set(adj.values());out={}
 while adj:
  start=min(adj);chain=[];u=start
  while True:
   chain.append(u);v=adj.pop(u);u=v
   if u==start:break
  assert start not in out;out[start]=chain
 assert sum(map(len,out.values()))==sum(remain.values())
 return out,es,remain
cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
dot=lambda a,b:a[0]*b[0]+a[1]*b[1]
minus=lambda a,b:(a[0]-b[0],a[1]-b[1])
area2=lambda ps:sum(cross(a,b) for a,b in zip(ps,ps[1:]+ps[:1]))
def interval_value(uv,u):
 for (a,b),(c,d) in zip(uv,uv[1:]):
  if a<=u<=c:return F(b)+F(d-b)*F(u-a,c-a)
 raise AssertionError('coverage missing')
def proof_chain(old,new):
 assert old[0]==new[0] and old[-1]==new[-1];A=old[0];d=minus(old[-1],A);L=dot(d,d);assert L>0
 def uv(ps):
  q=[(dot(minus(v,A),d),cross(d,minus(v,A))) for v in ps];assert q[0]==(0,0) and q[-1]==(L,0) and all(a[0]<b[0] for a,b in zip(q,q[1:]));return q
 a,b=uv(old),uv(new);knots=sorted({u for u,v in a+b});samples=[]
 for u in knots:
  v0,v1=interval_value(a,u),interval_value(b,u);diff=v1-v0;d2=diff*diff/L;assert d2<=1,('1 nm opposite-contour bound failed',old,new,u,d2)
  point=lambda v:(F(A[0])+F(d[0]*u-d[1]*v,L),F(A[1])+F(d[1]*u+d[0]*v,L))
  samples.append((F(u),v0,v1,d2,point(v0),point(v1)))
 # Split at all exact crossings, producing convex quadrilateral/triangle bands.
 extra=[]
 for left,right in zip(samples,samples[1:]):
  dl=left[2]-left[1];dr=right[2]-right[1]
  if dl*dr<0:extra.append(left[0]+(right[0]-left[0])*dl/(dl-dr))
 knots=sorted(set(knots+extra));cells=[]
 for ul,ur in zip(knots,knots[1:]):
  al,ar,bl,br=interval_value(a,ul),interval_value(a,ur),interval_value(b,ul),interval_value(b,ur)
  signed=(ur-ul)*((bl-al)+(br-ar))/(2*L)
  if signed==0:continue
  def point(u,v):return (F(A[0])+F(d[0]*u-d[1]*v,L),F(A[1])+F(d[1]*u+d[0]*v,L))
  ps=[point(ul,al),point(ur,ar),point(ur,br),point(ul,bl)];ps=list(dict.fromkeys(ps));assert len(ps)>=3
  assert abs(F(area2(ps),2))==abs(signed)
  if area2(ps)<0:ps.reverse()
  assert all(cross(minus(ps[(i+1)%len(ps)],ps[i]),minus(ps[(i+2)%len(ps)],ps[(i+1)%len(ps)]))>=0 for i in range(len(ps)))
  cells.append({'vertices':ps,'signed_band_area_nm2':signed})
 worst=max(samples,key=lambda v:v[3]);return {'old':old,'new':new,'basis_d':d,'L2':L,'maximum_distance_squared_nm2':worst[3],'witness_old':worst[4],'witness_new':worst[5],'breakpoints_tested':len(samples),'cells':cells}
def fraction_json(x):
 if isinstance(x,F):return str(x)
 if isinstance(x,dict):return {k:fraction_json(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [fraction_json(v) for v in x]
 return x
layers=[];globalmax=F(0)
for z in S['zones']:
 if z['net']!='GND' or z['layer']not in ('In1.Cu','In2.Cu'):continue
 v=next(x for x in C['zones'] if (x['uuid'],x['layer'])==(z['uuid'],z['layer']));assert len(z['fills'])==len(v['fills'])==1 and not z['fills'][0]['holes'] and not v['fills'][0]['holes'];a,ae,ac=cycles(list(map(tuple,z['fills'][0]['outline'])));b,be,bc=cycles(list(map(tuple,v['fills'][0]['outline'])));removed=set(a)-set(b);assert not(set(b)-set(a)) and len(removed)==1
 oldhole=a[next(iter(removed))];center=(178150000,85750000);r2=max(dot(minus(q,center),minus(q,center)) for q in oldhole);assert r2<=500000**2
 assert area2(oldhole)<0,'Expected a hole boundary, not removal of material island'
 patches=[]
 for anchor in sorted(a.keys()&b.keys()):
  old,new=a[anchor],b[anchor]
  if old==new:continue
  assert (area2(old)>0)==(area2(new)>0)
  for tag,i,j,k,l in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
   if tag=='equal':continue
   assert i>0 and j<len(old) and k>0 and l<len(new)
   p=proof_chain(old[i-1:j+1],new[k-1:l+1]);p['cycle_anchor']=anchor;patches.append(p);globalmax=max(globalmax,p['maximum_distance_squared_nm2'])
 layers.append({'layer':z['layer'],'source_cycles':len(a),'candidate_cycles':len(b),'all_raw_reverse_fracture_edges_cancelled_exactly':True,'all_residual_edges_partition_into_cycles_exactly':True,'only_removed_cycle_is_local_hole':oldhole,'local_hole_max_radius_squared_nm2':r2,'local_hole_area_nm2':F(-area2(oldhole),2),'remote_patch_count':len(patches),'remote_band_cell_count':sum(len(p['cells']) for p in patches),'patches':patches,'remote_band_area_sum_nm2':sum(abs(c['signed_band_area_nm2']) for p in patches for c in p['cells']),'proposed_one_nm_opposite_contour_band_bound_pass':True})
result={'source_sha256':S['board_sha256'],'candidate_sha256':C['board_sha256'],'status':'Intermediate exact boundary-chain envelope proof; material-boundary and cell-disjointness/control checks still required before proposed criterion report.','maximum_proved_opposite_chain_distance_squared_nm2':globalmax,'maximum_proved_opposite_chain_distance_nm':math.sqrt(float(globalmax)),'layers':layers}
(R/'boundary-envelope-proof.json').write_text(json.dumps(fraction_json(result),indent=2)+'\n');print(json.dumps({'max_distance_nm':result['maximum_proved_opposite_chain_distance_nm'],'max_distance_squared_exact':str(globalmax),'layers':[{k:fraction_json(x[k]) for k in ['layer','source_cycles','candidate_cycles','local_hole_max_radius_squared_nm2','local_hole_area_nm2','remote_patch_count','remote_band_cell_count','remote_band_area_sum_nm2']} for x in layers]},indent=2))
