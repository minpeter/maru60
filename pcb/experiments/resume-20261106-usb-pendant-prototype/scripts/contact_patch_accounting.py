from pathlib import Path
import runpy,json
D=Path('/workspace/shared/maru60-resume/continuation-fa96a7c/usb-stub');g=runpy.run_path(str(D/'scripts/inspect_junction.py'));p=g['p'];ix=g['ix'];poly=g['poly'];cu=g['copper'];inter=g['overlap'];u='b04e3a6d-1e98-43d1-9b10-58c23321ca28';v='ba0e0532-1586-4050-a390-d87dcee11d2c';f='cc183bf5-15f3-5270-ae14-886f402cad67';back='a963e830-796c-53b3-b9de-ef49be1314bc'
def raw(q,l):return poly(p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l))
def counts(z):return {'area_mm2':z.Area()/1e12,'contours':z.OutlineCount()}
rawstub=raw(ix[u],p.F_Cu);holes=[]
for q in ix.values():
 if isinstance(q,(p.PAD,p.PCB_VIA))and q.HasHole():
  z=inter(rawstub,poly(q.GetEffectiveHoleShape(),True))
  if z.Area()or z.OutlineCount():holes.append({'uuid':q.m_Uuid.AsString(),**counts(z)})
patches=[]
for a,c,l in [(u,f,p.F_Cu),(u,v,p.F_Cu),(f,v,p.F_Cu),(back,v,p.B_Cu)]:
 x,y=cu(ix[a],l),cu(ix[c],l);xx,yy=p.SHAPE_POLY_SET(x),p.SHAPE_POLY_SET(y);xx.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);yy.Deflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);patches.append({'a':a,'b':c,'layer':g['b'].GetLayerName(l),'raw':counts(inter(raw(ix[a],l),raw(ix[c],l))),'actual_after_all_holes':counts(inter(x,y)),'guarded_2nm_each':counts(inter(xx,yy))})
assert all(z['actual_after_all_holes']['area_mm2']>0 and z['guarded_2nm_each']['area_mm2']>0 for z in patches[2:]);assert patches[0]['actual_after_all_holes']['area_mm2']==0
out={'every_hole_scanned':True,'holes_intersecting_raw_stub':holes,'patches':patches,'source_hash':g['h'],'interpretation':'The historical raw stub-to-active-trace endpoint overlap lies in removed drill metal. After all holes the stub contacts only the via annulus. Retained F and B traces each independently have positive guarded annular contact. Deletion removes the stub primitive, not shared via or trace copper.'};(D/'qa/contact-patch-accounting.json').write_text(json.dumps(out,indent=2))
