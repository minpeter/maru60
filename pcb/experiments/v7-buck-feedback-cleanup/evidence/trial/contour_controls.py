import os,pathlib,json,hashlib,collections,math,sys,re,decimal
D=pathlib.Path(__file__).parent
for k in ['CONFIG','CACHE','DATA']:os.environ['XDG_'+k+'_HOME']=str(D/k.lower())
import pcbnew as p
A=D/'source/pcb/maru60.kicad_pcb';B=D/'filled/pcb/maru60.kicad_pcb';a=p.LoadBoard(str(A));b=p.LoadBoard(str(B));uid=lambda q:q.m_Uuid.AsString()
def ring(r):return tuple((r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount()))
def canonical(r):
 if r[0]==r[-1]:r=r[:-1]
 m=min(r);inds=[i for i,x in enumerate(r)if x==m];f=min(r[i:]+r[:i]for i in inds);rr=tuple(reversed(r));inds=[i for i,x in enumerate(rr)if x==m];z=min(rr[i:]+rr[:i]for i in inds);return min(f,z)
def rings(ps):
 return[dict(type='outline',xy=ring(ps.COutline(i)))for i in range(ps.OutlineCount())]+[dict(type='hole',xy=ring(ps.CHole(i,j)))for i in range(ps.OutlineCount())for j in range(ps.HoleCount(i))]
def bounds(r):return[min(x for x,y in r)/1e6,min(y for x,y in r)/1e6,max(x for x,y in r)/1e6,max(y for x,y in r)/1e6]
def desc(row):return dict(type=row['type'],vertex_count=len(row['xy']),bounds_mm=bounds(row['xy']),vertices_nm=row['xy'])
def key(row):return(row['type'],canonical(row['xy']))
def sub(x,y):
 z=p.SHAPE_POLY_SET(x);z.BooleanSubtract(y);return z
out=[]
for l in [p.In1_Cu,p.In2_Cu]:
 z=next(z for z in a.Zones()if z.GetNetname()=='GND'and z.IsOnLayer(l));zz=next(q for q in b.Zones()if uid(q)==uid(z));ps=z.GetFilledPolysList(l);qs=zz.GetFilledPolysList(l);rs=rings(ps);rr=rings(qs);cs=collections.Counter(map(key,rs));ct=collections.Counter(map(key,rr));removed=[];added=[]
 for k,n in(cs-ct).items():removed.extend([desc(next(r for r in rs if key(r)==k))]*n)
 for k,n in(ct-cs).items():added.extend([desc(next(r for r in rr if key(r)==k))]*n)
 loss=sub(ps,qs);gain=sub(qs,ps);loss_parts=[]
 for i in range(loss.OutlineCount()):
  r=ring(loss.COutline(i));part=p.SHAPE_POLY_SET();part.AddOutline(loss.COutline(i));bb=bounds(r);loss_parts.append(dict(area_mm2=part.Area()/1e12,bounds_mm=bb,axis_min_width_mm=min(bb[2]-bb[0],bb[3]-bb[1]),vertices_nm=r))
 # Omit source's one removed hole from copied raw contour topology. This is an independent identity control, not saving a board.
 rebuilt=p.SHAPE_POLY_SET()
 for i in range(ps.OutlineCount()):
  oi=rebuilt.AddOutline(ps.COutline(i))
  for j in range(ps.HoleCount(i)):
   row=dict(type='hole',xy=ring(ps.CHole(i,j)))
   if(cs-ct)[key(row)]:continue
   rebuilt.AddHole(ps.CHole(i,j),oi)
 proof=collections.Counter(map(key,rings(rebuilt)))==ct
 out.append(dict(zone_uuid=uid(z),layer=a.GetLayerName(l),source_outline_count=ps.OutlineCount(),source_hole_count=sum(ps.HoleCount(i)for i in range(ps.OutlineCount())),candidate_outline_count=qs.OutlineCount(),candidate_hole_count=sum(qs.HoleCount(i)for i in range(qs.OutlineCount())),raw_native_removed_contours=removed,raw_native_added_contours=added,source_minus_self_area_mm2=sub(ps,ps).Area()/1e12,candidate_minus_self_area_mm2=sub(qs,qs).Area()/1e12,source_minus_candidate_area_mm2=loss.Area()/1e12,candidate_minus_source_area_mm2=gain.Area()/1e12,loss_parts=loss_parts,candidate_exactly_equals_source_with_removed_contours_omitted=proof,rebuilt_minus_candidate_area_mm2=sub(rebuilt,qs).Area()/1e12,candidate_minus_rebuilt_area_mm2=sub(qs,rebuilt).Area()/1e12))
# Exact serialized XY vertex multisets, before any polygon Boolean operation.
sys.path.insert(0,str(D/'tools'));from sexpr_spans import children,head,field
raw=[]
for P in [A,B]:
 zs=[t for _,_,t in children(P.read_text())if head(t)=='zone'];r={}
 for z in zs:
  u=field(z,'uuid');u=re.search(r'"([^"]+)"',u).group(1)
  if u not in [x['zone_uuid']for x in out]:continue
  fs=[t for _,_,t in children(z)if head(t)=='filled_polygon'];pts=[(int(decimal.Decimal(x)*1000000),int(decimal.Decimal(y)*1000000))for f in fs for x,y in re.findall(r'\(xy\s+([-\d.]+)\s+([-\d.]+)\)',f)];r[u]=collections.Counter(pts)
 raw.append(r)
for x in out:
 u=x['zone_uuid'];removed=raw[0][u]-raw[1][u];added=raw[1][u]-raw[0][u];x['serialized_vertex_multiset_delta']=dict(removed_count=sum(removed.values()),added_count=sum(added.values()),removed_bounds_mm=bounds(tuple(removed))if removed else[],added_bounds_mm=bounds(tuple(added))if added else[],removed=[dict(xy_nm=k,count=n)for k,n in removed.items()],added=[dict(xy_nm=k,count=n)for k,n in added.items()])
r=dict(source_sha256=hashlib.sha256(A.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256(B.read_bytes()).hexdigest(),controls=out,note='Raw contour matching ignores only cyclic start and winding reversal, not vertices or distances. All tiny Boolean losses retained in evidence. No rounding tolerance or preservation waiver.');(D/'qa/contour-controls.json').write_text(json.dumps(r,indent=2));print(json.dumps([{k:v for k,v in x.items()if k not in ['raw_native_removed_contours','raw_native_added_contours','loss_parts','serialized_vertex_multiset_delta']}for x in out],indent=2))
