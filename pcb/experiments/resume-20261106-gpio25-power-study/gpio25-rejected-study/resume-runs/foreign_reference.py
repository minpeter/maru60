from pathlib import Path
from fractions import Fraction as F
import pcbnew as p,json,sys
D=Path(sys.argv[1]);S=Path('/workspace/shared/maru60-resume/selected-repo/pcb/experiments/resume-20261106-usb-pendant-prototype/pcb/maru60.kicad_pcb');a=p.LoadBoard(str(S));b=p.LoadBoard(str(D/'candidate/pcb/maru60.kicad_pcb'))
def pts(r):return [(r.CPoint(i).x,r.CPoint(i).y)for i in range(r.PointCount())]
def box(r):return min(x for x,y in r),min(y for x,y in r),max(x for x,y in r),max(y for x,y in r)
def ring(r):return r,box(r)
def state(rr,c):
 r,bb=rr;x,y=c
 if not(bb[0]<=x<=bb[2]and bb[1]<=y<=bb[3]):return False,False
 v=False
 for aa,z in zip(r,r[1:]+r[:1]):
  if min(aa[0],z[0])<=x<=max(aa[0],z[0])and min(aa[1],z[1])<=y<=max(aa[1],z[1])and(x-aa[0])*(z[1]-aa[1])==(y-aa[1])*(z[0]-aa[0]):return False,True
  if(aa[1]>y)!=(z[1]>y)and x<F(aa[0])+F(y-aa[1],z[1]-aa[1])*(z[0]-aa[0]):v=not v
 return v,False
def rings(s):return [(ring(pts(s.COutline(i))),[ring(pts(s.CHole(i,h)))for h in range(s.HoleCount(i))])for i in range(s.OutlineCount())]
def covered(rs,c):
 boundary=any(state(r,c)[1]for o,hs in rs for r in[o]+hs)
 return any(state(o,c)[0]and not any(state(h,c)[0]for h in hs)for o,hs in rs),boundary
def poly(sh):
 s=p.SHAPE_POLY_SET();sh.TransformToPolygon(s,1,p.ERROR_INSIDE);return s
holes=[]
for board in[a,b]:
 for q in list(board.GetTracks())+[q for f in board.GetFootprints()for q in f.Pads()]:
  if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
   s=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(s,1,p.ERROR_OUTSIDE);holes.extend(ring(pts(s.COutline(i)))for i in range(s.OutlineCount()))
planes={};losses={}
for l in[p.In1_Cu,p.In2_Cu]:
 ss=[next(z for z in board.Zones()if z.GetNetname()=='GND'and z.IsOnLayer(l)).GetFilledPolysList(l)for board in[a,b]];planes[l]=[rings(s)for s in ss];loss=p.SHAPE_POLY_SET(ss[0]);loss.BooleanSubtract(ss[1]);losses[l]=loss
idx={q.m_Uuid.AsString():q for q in b.GetTracks()};rows=[];witnesses=[];scanned=0
for q in a.GetTracks():
 if isinstance(q,p.PCB_VIA)or q.GetLayer()not in[p.F_Cu,p.B_Cu]or q.GetNetname()in['GND','','EXT_GPIO24','EXT_GPIO25']:continue
 u=q.m_Uuid.AsString();z=idx.get(u)
 if z is None:continue
 sig=lambda t:(t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetWidth(),t.GetLayer(),t.GetNetname())
 if sig(q)!=sig(z):continue
 scanned+=1;l=p.In1_Cu if q.GetLayer()==p.F_Cu else p.In2_Cu;cu=poly(q.GetEffectiveShape(q.GetLayer()));hit=p.SHAPE_POLY_SET();hit.BooleanIntersection(cu,losses[l])
 if not hit.OutlineCount():continue
 row=dict(uuid=u,net=q.GetNetname(),layer=a.GetLayerName(q.GetLayer()),reference=a.GetLayerName(l),native_loss_area_nm2=hit.Area(),native_loss_contours=hit.OutlineCount());rows.append(row)
 for i in range(hit.OutlineCount()):
  vv=pts(hit.COutline(i));c=tuple(sum(F(v[j])for v in vv)/len(vv)for j in[0,1]);old,ob=covered(planes[l][0],c);new,nb=covered(planes[l][1],c);tc,tb=covered(rings(cu),c);hh=any(any(state(h,c))for h in holes)
  if old and not new and not ob and not nb and tc and not tb and not hh:witnesses.append(dict(**row,point_nm=[str(v)for v in c],source_copper=True,candidate_copper=False,boundary=False,retained_trace_interior=True,inside_any_drill=False))
 # Early exact counterexample is sufficient for rejection; no assertion of full-scan pass.
 if witnesses:break
# Independently validate remote rational witnesses against every source/candidate drill polygon.
remote=[]
for row in json.loads((D/'qa/rational-loss-strict.json').read_text()):
 for w in row['witnesses']:
  c=tuple(F(v)for v in w['point_nm']);remote.append(dict(layer=row['layer'],**w,inside_or_on_any_drill=any(any(state(h,c))for h in holes)))
out=dict(scanned_retained_foreign_tracks=scanned,all_drill_shapes_checked=len(holes),native_intersections=rows,exact_foreign_reference_loss_witnesses=witnesses,remote_witnesses_all_drill_checked=remote,full_scan_completed=not bool(witnesses),verdict='REJECT_EXACT_FOREIGN_REFERENCE_LOSS'if witnesses else'NO_EXACT_FOREIGN_WITNESS_FOUND_NOT_ACCEPTANCE');(D/'qa/FOREIGN_REFERENCE.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
