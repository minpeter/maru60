import pcbnew as p,json,hashlib,pathlib,math,collections
D=pathlib.Path('/tmp/v7-c124-rebound-short/r121-expanded-review')
S=pathlib.Path('/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104/selected-recovered/pcb/maru60.kicad_pcb')
M=pathlib.Path('/tmp/v7-c124-rebound-short/main')
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(S)=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'
g=json.loads((M/'counterfactual-uvlo-r121-ipc-v4.json').read_text());j=json.loads((M/'counterfactual-v4-contact-reference.json').read_text())
res={'source_sha256':sha(S),'input_sha256':{n:sha(M/n)for n in ['counterfactual-uvlo-r121-ipc-v4.json','counterfactual-v4-contact-reference.json']},'version':p.GetBuildVersion()}
b=p.LoadBoard(str(S));fs={f.GetReference():f for f in b.GetFootprints()};obs=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()];uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in obs}
vec=lambda a:p.VECTOR2I(*(round(v*1e6)for v in a));xy=lambda v:[v.x/1e6,v.y/1e6]
def poly(s,loc=p.ERROR_INSIDE):
 z=p.SHAPE_POLY_SET();s.TransformToPolygon(z,1,loc);return z
def objpoly(q,loc=p.ERROR_INSIDE):
 z=poly(q.GetEffectiveShape(p.B_Cu),loc)
 if q.HasHole():z.BooleanSubtract(poly(q.GetEffectiveHoleShape(),p.ERROR_OUTSIDE if loc==p.ERROR_INSIDE else p.ERROR_INSIDE))
 return z
def inter(a,c):
 z=p.SHAPE_POLY_SET(a);z.BooleanIntersection(c);return z
def minus(a,c):
 z=p.SHAPE_POLY_SET(a);z.BooleanSubtract(c);return z
def seg(a,c,w,loc=p.ERROR_INSIDE):return poly(p.SHAPE_SEGMENT(vec(a),vec(c),round(w*1e6)),loc)
def rect(x,y,w,h):
 z=p.SHAPE_POLY_SET();z.NewOutline()
 for a,c in [(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)]:z.Append(round(a*1e6),round(c*1e6))
 return z

ret={x['uuid']for x in j['retired_tracks']};moved={x['uuid']for x in j['old_moved_pads']}
bridge_in=seg([15.5,17.725],[14.9,17.275],.28);bridge_in.BooleanAdd(seg([15.5,17.85],[15.5,17.25],.20))
bridge_out=seg([15.5,17.725],[14.9,17.275],.28,p.ERROR_OUTSIDE);bridge_out.BooleanAdd(seg([15.5,17.85],[15.5,17.25],.20,p.ERROR_OUTSIDE))
rows=[]
for q in obs:
 if uid(q)in(ret|moved)or not q.IsOnLayer(p.B_Cu)or q.GetNetname()=='GND':continue
 si=bridge_in.GetClearance(q.GetEffectiveShape(p.B_Cu))/1e6;so=bridge_out.GetClearance(q.GetEffectiveShape(p.B_Cu))/1e6
 rows.append({'uuid':uid(q),'net':q.GetNetname(),'gap_inside_mm':si,'gap_outside_mm':so})
res['bridge_retained_foreign']=sorted(rows,key=lambda x:x['gap_outside_mm'])[:12]
res['bridge_clearance_violation_count']=sum(x['gap_outside_mm']<.15 for x in rows)
# Each source primitive bounding box includes its entire stroked shape.
# Their enclosing box also encloses the courtyard interior: nonintersection proves separation.
rc=rect(13.68,18.65,1.5,3);near=[]
for f in fs.values():
 if f.GetReference()in['R121','C124']:continue
 parts=[z.GetBoundingBox()for z in f.GraphicalItems()if z.GetLayer()==p.B_CrtYd]
 if not parts:continue
 x0=min(z.GetX()for z in parts);y0=min(z.GetY()for z in parts);x1=max(z.GetRight()for z in parts);y1=max(z.GetBottom()for z in parts)
 q=rect((x0+x1)/2e6,(y0+y1)/2e6,(x1-x0)/1e6,(y1-y0)/1e6)
 gap=rc.GetClearance(q)/1e6
 near.append({'ref':f.GetReference(),'actual_source_primitive_enclosing_box_mm':[x0/1e6,y0/1e6,x1/1e6,y1/1e6],'conservative_box_gap_mm':gap,'overlap_mm2':inter(rc,q).Area()/1e12})
res['r121_retained_actual_courtyard_box_nearest']=sorted(near,key=lambda x:x['conservative_box_gap_mm'])[:10]
res['r121_retained_actual_courtyard_box_overlap_count']=sum(x['overlap_mm2']>0for x in near)
res['source_after_sha256']=sha(S);assert res['source_after_sha256']==res['source_sha256']
(D/'additional_native.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
