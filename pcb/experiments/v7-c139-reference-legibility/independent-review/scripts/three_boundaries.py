from pathlib import Path
import json,collections,math
import native_ink as n
p=n.p;R=Path('/tmp/v7-c139-independent-review');BP=Path('/tmp/v7-buck-three-labels-4765/candidate/pcb/maru60.kicad_pcb');s=n.Scene(BP)
targets=[]
for r in ['C139']:
 box=n.effective(s.fields[r]).BBox();box.Inflate(1100000);targets.append((s.fields[r].GetLayer(),box))
raw={p.F_SilkS:[],p.B_SilkS:[]};nominal={p.F_SilkS:[],p.B_SilkS:[]};inventory=[];unsupported=[]
for ref,fp in s.fps.items():
 for layer,sl in [(p.F_CrtYd,p.F_SilkS),(p.B_CrtYd,p.B_SilkS)]:
  shapes=[q for q in fp.GraphicalItems()if q.GetLayer()==layer];edges=[];closed=[];native_by_uuid={n.UID(q):q for q in shapes}
  if not any(n.effective(q).BBox().Intersects(box)for q in shapes for targetsl,box in targets if sl==targetsl):continue
  for q in shapes:
   m=n.info(q,ref);m.update(stroke_width_nm=q.GetWidth(),shape_type=q.GetShape());raw[sl].append((m,n.effective(q)));t=q.GetShape()
   if t==p.SHAPE_T_RECT:closed.append(([n.XY(v)for v in q.GetRectCorners()],[m]))
   elif t==p.SHAPE_T_POLY:
    poly=p.SHAPE_POLY_SET(q.GetPolyShape());nominal[sl].append(({'reference':ref,'primitive_sources':[m],'method':'raw_closed_polygon'},poly))
   elif t in[p.SHAPE_T_SEGMENT,p.SHAPE_T_ARC]:edges.append((tuple(n.XY(q.GetStart())),tuple(n.XY(q.GetEnd())),m))
   else:unsupported.append(m)
  remaining=set(range(len(edges)))
  while remaining:
   start=next(iter(remaining));component={start};points=set(edges[start][:2]);changed=True
   while changed:
    changed=False
    for k in remaining-component:
     a,b,m=edges[k]
     if a in points or b in points:component.add(k);points.update([a,b]);changed=True
   remaining-=component;adj=collections.defaultdict(list)
   for k in component:a,b,m=edges[k];adj[a].append(b);adj[b].append(a)
   n.require(len(points)>=3 and all(len(v)==2 for v in adj.values()),'Open/ambiguous raw courtyard '+ref)
   first=min(points);ordered=[first];prev=None;cur=first
   while True:
    ns=adj[cur];nxt=ns[0]if ns[0]!=prev else ns[1]
    if nxt==first:break
    ordered.append(nxt);prev,cur=cur,nxt;n.require(len(ordered)<=len(points),'Invalid traversal')
   n.require(len(ordered)==len(points),'Incomplete traversal')
   chain=p.SHAPE_LINE_CHAIN();chain.Append(*ordered[0]);arc_count=0
   for i,a in enumerate(ordered):
    z=ordered[(i+1)%len(ordered)];edge=next(edges[k]for k in component if set(edges[k][:2])=={a,z});q=native_by_uuid[edge[2]['uuid']]
    if q.GetShape()==p.SHAPE_T_ARC:
     ax,ay=a;mx,my=n.XY(q.GetArcMid());zx,zy=z;den=2*(ax*(my-zy)+mx*(zy-ay)+zx*(ay-my));n.require(den!=0,'Collinear raw arc');aa=ax*ax+ay*ay;mm=mx*mx+my*my;zz=zx*zx+zy*zy;cx=(aa*(my-zy)+mm*(zy-ay)+zz*(ay-my))/den;cy=(aa*(zx-mx)+mm*(ax-zx)+zz*(mx-ax))/den;radius=math.hypot(ax-cx,ay-cy);ta=math.atan2(ay-cy,ax-cx);tm=math.atan2(my-cy,mx-cx);tz=math.atan2(zy-cy,zx-cx);ccw=(tz-ta)%(2*math.pi);turn=ccw if (tm-ta)%(2*math.pi)<=ccw else ccw-2*math.pi;steps=max(2,math.ceil(abs(turn)/(2*math.acos(1-0.25/radius))))
     for k in range(1,steps):t=ta+turn*k/steps;chain.Append(round(cx+radius*math.cos(t)),round(cy+radius*math.sin(t)))
     chain.Append(*z);arc_count+=1
    else:chain.Append(*z)
   chain.SetClosed(True);ps=p.SHAPE_POLY_SET();ps.AddOutline(chain)
   meta={'reference':ref,'primitive_sources':[edges[k][2]for k in component],'method':'raw integer closed centerline interior; raw 3-point arc chord sagitta <=0.25 nm plus <=0.708 nm integer rounding if present','endpoint_vertices_nm':ordered,'arc_count':arc_count};nominal[sl].append((meta,ps));inventory.append(meta)
  for pts,src in closed:
   meta={'reference':ref,'primitive_sources':src,'method':'exact_raw_integer_centerline_closed_interior','points_nm':pts};nominal[sl].append((meta,n.filled(pts)));inventory.append(meta)
n.require(not unsupported,'Unsupported courtyard shapes')
def row(ref):
 f=s.fields[ref];shape=n.effective(f);sl=f.GetLayer();normal=s.measure_ref(ref)['geometry'];ng=n.gap(shape,nominal[sl]);rg=n.gap(shape,raw[sl]);return {'reference':ref,'typography':n.typo(f),'normal_native_geometry':normal,'exact_nominal_centerline_gap':ng,'raw_stroke_envelope_gap':rg,'nominal_150um_pass':not n.hits(shape,nominal[sl],150000),'stroke_150um_pass':not n.hits(shape,raw[sl],150000),'nominal_200um_pass':not n.hits(shape,nominal[sl],200000),'stroke_200um_pass':not n.hits(shape,raw[sl],200000)}
refs=['C139'];before=[row(r)for r in refs]
proposed=[]
result={'source_trial_sha256':s.before,'status':'READ ONLY; actual C139-only 2b5787 and selected source unchanged','interpretation':'Three separately reported geometries: native cached filled courtyard, exact raw integer line/rectangle closed centerline interior; arc reconstruction bounded <1 nm, and actual drawn-stroke envelope. Stroked envelope is stricter optional audit, not a retroactive interpretation of earlier selected acceptance. Actual corrected poses target >=0.200 mm on both exact nominal and actual stroke envelope. No existing acceptance criterion is changed.','original_rows':before,'proposed_readonly_rows':proposed,'actual_corrected_fields_no_in_memory_mutation':True,'nominal_inventory':inventory,'unsupported':unsupported,'nominal_scope':'All footprints whose actual raw courtyard bounds enter any target actual ink bounding box expanded by 1.1 mm. Actual proposed shift <=0.1 mm, so every possible courtyard within 1.0 mm is included. Nearest reported gaps all <1.0 mm.','private_xdg':s.homes,'file_unchanged':n.SHA(BP)==s.before};(R/'qa/three-boundaries.json').write_text(json.dumps(result,indent=2)+'\n')
for rows in[before,proposed]:
 for r in rows:print(r['reference'],r['typography']['position_nm'],*[r[k]['lower_bound_nm']for k in['exact_nominal_centerline_gap','raw_stroke_envelope_gap']],r['normal_native_geometry']['courtyard_gap']['lower_bound_nm'],r['nominal_150um_pass'],r['stroke_200um_pass'],all(v for k,v in r['normal_native_geometry'].items()if k.endswith('_target_pass')or k=='whole_ink_inside_board'))
