if not __debug__:
 raise RuntimeError('Optimized Python is unsupported for this proof')
import json,math,collections,hashlib
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parent;code=R/'prove_boundary_envelope.py';ns={'__file__':str(code)};exec(code.read_text().split('layers=[];globalmax=')[0],ns)
S,C,cycles,area2,cross,minus=[ns[k] for k in ['S','C','cycles','area2','cross','minus']]
proof=json.loads((R/'boundary-envelope-proof.json').read_text());GRID=1000000

def point_material(x,y,pts):
 d=math.lcm(x.denominator,y.denominator);xn=x.numerator*(d//x.denominator);yn=y.numerator*(d//y.denominator);yl=yn//d;yh=-(-yn//d);hit=False
 for (ax,ay),(bx,by) in zip(pts,pts[1:]+pts[:1]):
  if max(ay,by)<yl or min(ay,by)>yh:continue
  cr=(bx-ax)*(yn-ay*d)-(by-ay)*(xn-ax*d)
  if cr==0 and min(ax,bx)*d<=xn<=max(ax,bx)*d and min(ay,by)*d<=yn<=max(ay,by)*d:return None
  if (ay*d>yn)!=(by*d>yn):
   v=ax*d*(by-ay)+(bx-ax)*(yn-ay*d)-xn*(by-ay)
   if (v>0 and by>ay) or (v<0 and by<ay):hit=not hit
 return hit

def edge_bbox(e):
 a,b=e;return min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])
def overlap(a,b):return not(a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])
def integer_box(ps):return tuple([math.floor(min(p[0] for p in ps)),math.floor(min(p[1] for p in ps)),math.ceil(max(p[0] for p in ps)),math.ceil(max(p[1] for p in ps))])
def index_edges(es):
 idx=collections.defaultdict(list);records=[]
 for e in es:
  bb=edge_bbox(e);i=len(records);records.append((e,bb))
  for x in range(bb[0]//GRID,bb[2]//GRID+1):
   for y in range(bb[1]//GRID,bb[3]//GRID+1):idx[x,y].append(i)
 return idx,records

def query(index,bb):
 idx,rec=index;seen=set()
 for x in range(bb[0]//GRID,bb[2]//GRID+1):
  for y in range(bb[1]//GRID,bb[3]//GRID+1):seen.update(idx.get((x,y),()))
 return [rec[i][0] for i in seen if overlap(bb,rec[i][1])]

def touch_only_shared_endpoints(e,f):
 if e==f:return True
 a,b=e;c,d=f;o1=cross(minus(b,a),minus(c,a));o2=cross(minus(b,a),minus(d,a));o3=cross(minus(d,c),minus(a,c));o4=cross(minus(d,c),minus(b,c))
 if o1*o2<0 and o3*o4<0:return False
 if o1==o2==o3==o4==0:
  axis=0 if a[0]!=b[0] else 1;lo=max(min(a[axis],b[axis]),min(c[axis],d[axis]));hi=min(max(a[axis],b[axis]),max(c[axis],d[axis]));return hi<lo or (hi==lo and bool(set(e)&set(f)))
 def on(v,u,w):return min(u[0],w[0])<=v[0]<=max(u[0],w[0]) and min(u[1],w[1])<=v[1]<=max(u[1],w[1])
 for val,pt,seg in [(o1,c,e),(o2,d,e),(o3,a,f),(o4,b,f)]:
  if val==0 and on(pt,*seg) and pt not in set(e)&set(f):return False
 return True

def edge_enters_open_cell(e,ps):
 a,b=e;delta=minus(b,a);lo,hi=F(0),F(1)
 for u,v in zip(ps,ps[1:]+ps[:1]):
  dv=minus(v,u);k=cross(dv,minus(a,u));m=cross(dv,delta)
  if m==0:
   if k<=0:return False
  elif m>0:lo=max(lo,-F(k,m))
  else:hi=min(hi,-F(k,m))
  if lo>=hi:return False
 return lo<hi

def cells_overlap_interior(a,b):
 for ps in [a,b]:
  for u,v in zip(ps,ps[1:]+ps[:1]):
   dv=minus(v,u);pa=[cross(dv,minus(q,u)) for q in a];pb=[cross(dv,minus(q,u)) for q in b]
   if max(pa)<=min(pb) or max(pb)<=min(pa):return False
 return True

def point_segment_distance2(c,a,b):
 d=minus(b,a);v=minus(c,a);den=d[0]*d[0]+d[1]*d[1];u=F(v[0]*d[0]+v[1]*d[1],den)
 if u<0:q=a
 elif u>1:q=b
 else:q=(a[0]+u*d[0],a[1]+u*d[1])
 return (q[0]-c[0])**2+(q[1]-c[1])**2

def distance_cell2(c,ps):
 if all(cross(minus(b,a),minus(c,a))>=0 for a,b in zip(ps,ps[1:]+ps[:1])):return F(0)
 return min(point_segment_distance2(c,a,b) for a,b in zip(ps,ps[1:]+ps[:1]))

results=[]
for lp in proof['layers']:
 layer=lp['layer'];sr=next(z for z in S['zones'] if z['net']=='GND' and z['layer']==layer)['fills'][0]['outline'];cr=next(z for z in C['zones'] if z['net']=='GND' and z['layer']==layer)['fills'][0]['outline'];points={'source':list(map(tuple,sr)),'candidate':list(map(tuple,cr))};cycle_maps={};indices={}
 for label,ps in points.items():
  cm,es,remaining=cycles(ps);cycle_maps[label]=cm;indices[label]=index_edges(list(remaining))
 localhole=[tuple(v) for v in lp['only_removed_cycle_is_local_hole']];localbox=integer_box(localhole);localedges=set(zip(localhole,localhole[1:]+localhole[:1]))
 assert all(e in localedges for e in query(indices['source'],localbox))
 assert not query(indices['candidate'],localbox)
 assert point_material(F(178150000),F(85750000),points['source']) is False and point_material(F(178150000),F(85750000),points['candidate']) is True
 # Each changed segment is a genuine material boundary: no nonadjacent crossing/overlap and exact sided membership.
 boundary_records=[]
 for label,key in [('source','old'),('candidate','new')]:
  edge_set={tuple(map(tuple,e)) for patch in lp['patches'] for e in zip(patch[key],patch[key][1:])}
  for edge in sorted(edge_set):
   possible=query(indices[label],edge_bbox(edge));assert edge in possible
   for other in possible:assert touch_only_shared_endpoints(edge,other),('Not an isolated material boundary',label,edge,other)
   a,b=edge;dx,dy=b[0]-a[0],b[1]-a[1];max_other_length2=max((v[0][1][0]-v[0][0][0])**2+(v[0][1][1]-v[0][0][1])**2 for v in indices[label][1]);assert 4*(dx*dx+dy*dy)*max_other_length2<10**60;x=F(a[0]+b[0],2);y=F(a[1]+b[1],2);eps=F(1,10**30)
   left=point_material(x-dy*eps,y+dx*eps,points[label]);right=point_material(x+dy*eps,y-dx*eps,points[label]);assert left is True and right is False,('Boundary orientation/material not proved',label,edge,left,right)
   boundary_records.append({'version':label,'edge':edge,'material_left_exact':left,'material_right_exact':right,'nonadjacent_boundary_crossings':0})
 cells=[]
 for patchid,patch in enumerate(lp['patches']):
  for cellid,cell in enumerate(patch['cells']):
   ps=[tuple(F(v) for v in q) for q in cell['vertices']];bb=integer_box(ps)
   # Complete exact index candidate filtering; any other true boundary entering the cell would invalidate its constant classification.
   for label in ['source','candidate']:
    for edge in query(indices[label],bb):assert not edge_enters_open_cell(edge,ps),('Boundary cuts band cell',label,patchid,cellid,edge)
   x=sum(q[0] for q in ps)/len(ps);y=sum(q[1] for q in ps)/len(ps);insideS=point_material(x,y,points['source']);insideC=point_material(x,y,points['candidate']);assert insideS is not None and insideC is not None and insideS!=insideC
   assert distance_cell2((F(178150000),F(85750000)),ps)>500000**2,'Remote band enters allowed local circle'
   cells.append({'patch':patchid,'cell':cellid,'vertices':ps,'bbox':bb,'area_nm2':F(area2(ps),2),'classification':'source_only_loss' if insideS else 'candidate_only_gain','no_other_boundary_inside':True})
 # All material-difference cells disjoint; exact signed areas therefore sum once.
 pair_checks=0
 for i,a in enumerate(cells):
  for b in cells[i+1:]:
   if not overlap(a['bbox'],b['bbox']):continue
   pair_checks+=1;assert not cells_overlap_interior(a['vertices'],b['vertices']),('Overlapping bands',a['patch'],a['cell'],b['patch'],b['cell'])
 loss=sum(c['area_nm2'] for c in cells if c['classification']=='source_only_loss');gain=sum(c['area_nm2'] for c in cells if c['classification']=='candidate_only_gain');local=F(lp['local_hole_area_nm2']);raw_signed=F(area2(points['candidate'])-area2(points['source']),2);assert gain-loss+local==raw_signed
 results.append({'layer':layer,'exact_boundary_segment_tests':len(boundary_records),'boundary_tests':boundary_records,'all_opposite_chains_proved_actual_material_boundaries':True,'normal_witness_offset_below_exact_integer_midpoint_line_separation_bound':True,'local_removed_hole_contains_no_other_saved_material_boundary':True,'all_remote_difference_cells_have_constant_material_classification':True,'all_remote_cells_pairwise_interior_disjoint':True,'intersecting_bbox_cell_pairs_checked':pair_checks,'all_remote_cells_outside_unchanged_0_50mm_local_circle':True,'remote_loss_nm2_exact':loss,'remote_gain_nm2_exact':gain,'local_gain_nm2_exact':local,'raw_signed_area_delta_nm2_exact':raw_signed,'complete_difference_area_identity_exact':True,'cells':cells})
# Focused controls use the exact same predicates as the proof.
controls=[]
def reject(name,fn):
 try:fn()
 except (AssertionError,ValueError,ZeroDivisionError):controls.append({'name':name,'rejected':True});return
 raise AssertionError('Control did not reject '+name)
chain=ns['proof_chain'];reject('same-endpoint_two_nm_gain',lambda:chain([(0,0),(100,0)],[(0,0),(50,2),(100,0)]));reject('same-endpoint_two_nm_loss',lambda:chain([(0,0),(50,2),(100,0)],[(0,0),(100,0)]));reject('thin_translated_strip_different_endpoints',lambda:chain([(0,0),(100,0)],[(0,2),(100,2)]));reject('nonmonotone_chain',lambda:chain([(0,0),(70,0),(50,0),(100,0)],[(0,0),(100,0)]))
assert chain([(0,0),(100,0)],[(0,0),(50,1),(100,0)])['maximum_distance_squared_nm2']==1;controls.append({'name':'exact_one_nm_limit_positive','passed':True})
square=[(F(0),F(0)),(F(10),F(0)),(F(10),F(10)),(F(0),F(10))];assert edge_enters_open_cell(((-1,5),(11,5)),square) and not edge_enters_open_cell(((0,0),(10,0)),square);assert cells_overlap_interior(square,[(x+5,y) for x,y in square]) and not cells_overlap_interior(square,[(x+10,y) for x,y in square]);controls.extend([{'name':'crossing_boundary_detected','passed':True},{'name':'boundary_only_not_interior','passed':True},{'name':'overlapping_cell_detected','passed':True},{'name':'touching_cells_not_overlap','passed':True}])
assert not touch_only_shared_endpoints(((0,0),(10,0)),((5,-1),(5,1))) and not touch_only_shared_endpoints(((0,0),(10,0)),((5,0),(15,0)));controls.extend([{'name':'proper_segment_crossing_detected','passed':True},{'name':'collinear_overlap_detected','passed':True}])
out={'source_sha256':S['board_sha256'],'candidate_sha256':C['board_sha256'],'candidate_specific_proposed_1_nm_criterion_pass':True,'strict_global_no_loss_result_unchanged':'FAIL','maximum_exact_opposite_material_distance_squared_nm2':proof['maximum_proved_opposite_chain_distance_squared_nm2'],'maximum_distance_bound_nm':proof['maximum_proved_opposite_chain_distance_nm'],'layers':results,'controls':controls,'qualification':'Mathematical saved-material representation bound for this exact candidate only; not a manufacturing tolerance, electrical/noise/stability guarantee, general validated checker, or adoption authorization.'}
(R/'material-coverage-proof.json').write_text(json.dumps(ns['fraction_json'](out),indent=2)+'\n');print(json.dumps({'bound_nm':out['maximum_distance_bound_nm'],'controls':len(controls),'layers':[{k:str(x[k]) for k in ['layer','exact_boundary_segment_tests','remote_loss_nm2_exact','remote_gain_nm2_exact','local_gain_nm2_exact','raw_signed_area_delta_nm2_exact']} for x in results]},indent=2))
