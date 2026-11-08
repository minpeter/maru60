from pathlib import Path
import pcbnew as p,json,hashlib
R=Path('/tmp/v7-support-endpoint-trial');D=Path('/tmp/v7-c124-d-actual');BP=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-c124-series-with-connector-ground/candidate/pcb/maru60.kicad_pcb');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sha=H(BP);assert sha=='7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401';b=p.LoadBoard(str(BP));b.BuildConnectivity();cn=b.GetConnectivity();items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];U=lambda q:q.m_Uuid.AsString();idx={U(q):q for q in items};V=lambda a:p.VECTOR2I(round(a[0]*1e6),round(a[1]*1e6));xy=lambda q:[q.x/1e6,q.y/1e6]
plan=[('GND','abcd4fb1-881b-43f9-906e-39d93366692e','start',[14.54,17.435],'f58bc791-8a08-55a5-ada7-19575bcd7e75'),('USB_OVLO','ae94ea04-2d21-5f84-8952-7f8960275e00','end',[20.0725,20.9785],'cc1282fe-f0b3-5fea-9d45-66eea8068d66'),('USB_UVLO','f41eeb49-8180-5bac-bccf-c1a0b3b4c547','start',[14.1,16.45],'d4be2091-cd02-51f1-b2e5-0505e7ec1e8a')]
def poly(sh,out=False):
 r=p.SHAPE_POLY_SET();sh.TransformToPolygon(r,1,p.ERROR_OUTSIDE if out else p.ERROR_INSIDE);r.Simplify();return r
def load(rows):
 q=p.SHAPE_POLY_SET()
 for row in rows:
  c=p.SHAPE_LINE_CHAIN()
  for x,y in row['outer']:c.Append(x,y)
  c.SetClosed(True);n=q.AddOutline(c)
  for ring in row['holes']:
   c=p.SHAPE_LINE_CHAIN()
   for x,y in ring:c.Append(x,y)
   c.SetClosed(True);q.AddHole(c,n)
 return q
def cross(a,z):
 q=p.SHAPE_POLY_SET();q.BooleanIntersection(a,z);return q
def diff(a,z):
 q=p.SHAPE_POLY_SET(a);q.BooleanSubtract(z);return {'area_mm2':q.Area()/1e12,'contours':q.OutlineCount()}
A=json.loads((D/'qa/actual-local-material.json').read_text());S=json.loads((D/'qa/source-local-material.json').read_text());C=json.loads(Path('/tmp/v7-c124-c-actual/qa/actual-local-material.json').read_text());SS=json.loads((D/'qa/actual-strong-support-reference.json').read_text());SM={q['uuid']:load(q['metal_B'])for q in S['nodes']};CM={q['uuid']:load(q['metal_B'])for q in C['nodes']};AM={q['uuid']:load(q['metal_B'])for q in A['nodes']};AN={q['uuid']:q for q in A['nodes']};planes={l:load(v)for l,v in A['inner_planes'].items()};holes=[poly(q.GetEffectiveHoleShape(),True)for q in items if isinstance(q,(p.PCB_VIA,p.PAD))and q.HasHole()];before={};after={};rows=[]
for net,u,which,point,support in plan:
 q=idx[u];before[u]=p.SHAPE_POLY_SET(AM[u]);row={'uuid':u,'net':net,'old_start':xy(q.GetStart()),'old_end':xy(q.GetEnd()),'old_length_mm':q.GetLength()/1e6,'which':which,'point':point,'support_uuid':support,'native_support_dangling_before':cn.TestTrackEndpointDangling(idx[support],True)}
 if which=='start':q.SetStart(V(point))
 else:q.SetEnd(V(point))
 ps=poly(q.GetEffectiveShape(p.B_Cu))
 for h in holes:
  if ps.BBox().Intersects(h.BBox()):ps.BooleanSubtract(h)
 AM[u]=ps;after[u]=ps;row.update({'new_start':xy(q.GetStart()),'new_end':xy(q.GetEnd()),'new_length_mm':q.GetLength()/1e6});rows.append(row)
b.BuildConnectivity();cn=b.GetConnectivity();terms=json.loads((D/'qa/actual-clearance-envelope.json').read_text())['terminal_to_actual_copper'];clear=[]
for row in rows:
 u=row['uuid'];q=idx[u];row['native_support_dangling_after']=cn.TestTrackEndpointDangling(idx[row['support_uuid']],True);row['native_main_dangling_after']=cn.TestTrackEndpointDangling(q,True);foreign=sorted([{'uuid':U(z),'net':z.GetNetname(),'gap_mm':q.GetEffectiveShape(p.B_Cu).GetClearance(z.GetEffectiveShape(p.B_Cu))/1e6}for z in items if z.IsOnLayer(p.B_Cu)and z.GetNetname()!=q.GetNetname()],key=lambda v:v['gap_mm']);te=[]
 for t in terms:
  if t['net']==q.GetNetname():continue
  x0,y0,x1,y1=t['bounds'];shape=p.SHAPE_RECT(V([x0,y0]),round((x1-x0)*1e6),round((y1-y0)*1e6));te.append({'ref':t['ref'],'pad':t['pad'],'gap_mm':q.GetEffectiveShape(p.B_Cu).GetClearance(shape)/1e6})
 te.sort(key=lambda v:v['gap_mm']);clear.append({'uuid':u,'nearest_foreign':foreign[:3],'nearest_terminals':te[:3]})
 # Full local same-net union delta, rather than pairwise object identity.
 old=p.SHAPE_POLY_SET();new=p.SHAPE_POLY_SET()
 for v,ps in AM.items():
  if AN[v]['net']==q.GetNetname():new.BooleanAdd(ps);old.BooleanAdd(before[v]if v in before else ps)
 row['same_net_union_old_minus_new']=diff(old,new);row['same_net_union_new_minus_old']=diff(new,old)
supp=[]
for old in SS['all_original_external_plus_C_boundary_support']:
 source=SM if old['source']=='original'else CM;patch=cross(source[old['old']],source[old['target']]);new=p.SHAPE_POLY_SET()
 for u,ps in AM.items():
  if AN[u]['net']==old['net']and u!=old['target']:new.BooleanAdd(ps)
 strict=diff(patch,new);patch.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);new.Inflate(-2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);strong=diff(patch,new);supp.append({'old':old['old'],'target':old['target'],'net':old['net'],'exact':strict,'strong':strong})
refs=[]
for row in rows:
 q=idx[row['uuid']]
 if q.GetNetname()=='GND':continue
 ps=poly(q.GetEffectiveShape(p.B_Cu),True);ps.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 for l,pl in planes.items():refs.append({'uuid':row['uuid'],'plane':l,**diff(ps,pl)})
fail={'dangling':[r for r in rows if r['native_support_dangling_after']or r['native_main_dangling_after']],'clearance':[r for r in clear if r['nearest_foreign'][0]['gap_mm']<.15 or r['nearest_terminals'][0]['gap_mm']<.15],'support':[r for r in supp if r['exact']['area_mm2']or r['exact']['contours']or r['strong']['area_mm2']or r['strong']['contours']],'reference':[r for r in refs if r['area_mm2']or r['contours']]}
assert H(BP)==sha
out={'source_sha256':sha,'status':'READ ONLY in-memory natural serial-route screen, no board save','plans':rows,'clearance':clear,'all14_original_strong_supports':supp,'new_outward2nm_reference':refs,'failures':fail,'no_extra_objects_or_drills':True,'source_unchanged':True};(R/'qa/serial-route-screen.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'plans':rows,'clearance':clear,'failures':fail},indent=2))
