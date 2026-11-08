import pcbnew as p,json,hashlib,pathlib
R=pathlib.Path('/tmp/v7-c124-rebound-short/r121-study')
SRC=pathlib.Path('/workspace/scratch/edd9a5be63e7/v7-recovered-library-20261104/selected-recovered/pcb/maru60.kicad_pcb')
expected='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(SRC)==expected
retained={str(q.name):sha(q) for q in R.iterdir() if q.is_file() and q.suffix in ['.json','.log'] and not q.name.startswith('drill_annulus')}
b=p.LoadBoard(str(SRC))
tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
t=tracks['abcd4fb1-881b-43f9-906e-39d93366692e'];v=tracks['763086b7-5549-4f5e-bb08-ce25387b3627']
def xy(q):return [q.x/1e6,q.y/1e6]
def copper(obj,loc):
 out=p.SHAPE_POLY_SET();obj.TransformShapeToPolygon(out,p.B_Cu,0,1,loc);return out
def hole(obj,loc):
 out=p.SHAPE_POLY_SET();obj.GetEffectiveHoleShape().TransformToPolygon(out,1,loc);return out
def sub(a,b):
 out=p.SHAPE_POLY_SET(a);out.BooleanSubtract(b);return out
def intersect(a,b):
 out=p.SHAPE_POLY_SET(a);out.BooleanIntersection(b);return out
area=lambda q:q.Area()/1e12
ti,to=[copper(t,loc) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]]
vi,vo=[copper(v,loc) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]]
hi,ho=[hole(v,loc) for loc in [p.ERROR_INSIDE,p.ERROR_OUTSIDE]]
# Physical lower approximation removes OUTSIDE hole from INSIDE outer copper.
# Physical upper approximation removes INSIDE hole from OUTSIDE outer copper.
ai,ao=sub(vi,ho),sub(vo,hi)
ci,co=intersect(ti,ai),intersect(to,ao)
# Independent set ordering check: outer overlap then subtract actual drilled hole.
di,do=sub(intersect(ti,vi),ho),sub(intersect(to,vo),hi)
res={
 'source':str(SRC),'source_sha256_before':expected,'pcbnew_version':p.GetBuildVersion(),
 'track':{'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'start_mm':xy(t.GetStart()),'end_mm':xy(t.GetEnd()),'width_mm':t.GetWidth()/1e6},
 'via':{'uuid':v.m_Uuid.AsString(),'net':v.GetNetname(),'center_mm':xy(v.GetPosition()),'outer_diameter_BCu_mm':v.GetWidth(p.B_Cu)/1e6,'actual_drill_mm':v.GetDrillValue()/1e6,'stored_drill_mm':v.GetDrill()/1e6,'has_drilled_hole':v.HasDrilledHole(),'hole_shape':v.GetEffectiveHoleShape().GetClass() if hasattr(v.GetEffectiveHoleShape(),'GetClass') else str(type(v.GetEffectiveHoleShape()))},
 'polygon_error_nm':1,
 'outer_disk_overlap_inside_outside_mm2':[area(intersect(ti,vi)),area(intersect(to,vo))],
 'actual_hole_overlap_inside_outside_mm2':[area(intersect(ti,hi)),area(intersect(to,ho))],
 'annulus_area_lower_upper_mm2':[area(ai),area(ao)],
 'physical_annular_contact_area_lower_upper_mm2':[area(ci),area(co)],
 'physical_annular_contact_positive_both':area(ci)>0 and area(co)>0,
 'independent_intersection_then_hole_subtraction_mm2':[area(di),area(do)],
 'contact_polygons_lower_upper':{'outline_counts':[ci.OutlineCount(),co.OutlineCount()],'hole_counts':[[ci.HoleCount(k) for k in range(ci.OutlineCount())],[co.HoleCount(k) for k in range(co.OutlineCount())]]},
 'correction_scope':'Supersedes only the reported spur-to-via full-disk contact area. R121-pad/track overlap values have no via or hole. No other nonzero track/via overlap areas were reported. Via-based clearances used conservative outer-copper envelopes; tested R121 pads lie outside those disks, so their nearest annular outer edge is unchanged.',
 'retained_raw_file_sha256':retained,
 'source_sha256_after':sha(SRC),
}
assert res['source_sha256_after']==expected
assert all(sha(R/q)==v for q,v in retained.items())
res['retained_raw_files_unchanged']=True
(R/'drill_annulus_correction.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
