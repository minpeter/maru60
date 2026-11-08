exec((__import__('pathlib').Path(__file__).parent/'inspect.py').read_text().split('rows=[]')[0])
from fractions import Fraction
L=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];assert b.GetCopperLayerCount()==4
uid=lambda q:q.m_Uuid.AsString();xy=lambda v:(v.x,v.y);via=[];pads=[];native=[]
for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]:
 if not(isinstance(q,p.PCB_VIA)or isinstance(q,p.PAD)and q.GetAttribute()==p.PAD_ATTRIB_PTH):continue
 assert q.HasHole()and all(q.IsOnLayer(l)for l in L);hc=q.GetEffectiveHoleShape();assert isinstance(hc,p.SHAPE_SEGMENT);seg=hc.GetSeg();a=xy(seg.A);z=xy(seg.B);cx,cy=xy(q.GetPosition());assert(a[0]+z[0],a[1]+z[1])==(2*cx,2*cy)
 if isinstance(q,p.PCB_VIA):
  assert q.GetViaType()==p.VIATYPE_THROUGH and a==z==(cx,cy);drill=q.GetDrillValue();assert hc.GetWidth()==drill;rows=[]
  for l in L:
   width=q.GetWidth(l);assert width>drill>0;rows.append(dict(layer=b.GetLayerName(l),outer_diameter_nm=width,drill_nm=drill,exact_radial_margin_nm=str(Fraction(width-drill,2))))
  via.append(dict(uuid=uid(q),layers=rows,hole_center_nm=[cx,cy],through=True));continue
 drill=xy(q.GetDrillSize());assert min(drill)>0 and hc.GetWidth()==min(drill);rows=[]
 for l in L:
  size=xy(q.GetSize(l));shape=q.GetShape(l);assert xy(q.GetOffset(l))==(0,0)
  if shape==p.PAD_SHAPE_CIRCLE:
   assert size[0]==size[1]and drill[0]==drill[1]and a==z==(cx,cy);margin=Fraction(size[0]-drill[0],2);method='concentric circles'
  elif shape==p.PAD_SHAPE_RECT:
   assert drill[0]==drill[1]and a==z==(cx,cy);margin=Fraction(min(size)-drill[0],2);method='centered circle inside rectangle; minimum half-side minus radius'
  elif shape==p.PAD_SHAPE_OVAL:
   assert q.GetOrientationDegrees()==0 and size[1]>=size[0]and drill[1]>=drill[0];assert size[1]-size[0]==drill[1]-drill[0];d=drill[1]-drill[0];assert d%2==0 and set([a,z])=={(cx,cy-d//2),(cx,cy+d//2)};margin=Fraction(size[0]-drill[0],2);method='concentric same-spine capsules; radius difference'
  else:raise AssertionError(('unsupported PTH shape',uid(q),shape))
  assert margin>0;rows.append(dict(layer=b.GetLayerName(l),shape=int(shape),size_nm=size,drill_nm=drill,offset_nm=[0,0],exact_minimum_hole_enclosure_margin_nm=str(margin),proof=method))
 pads.append(dict(uuid=uid(q),ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber(),layers=rows,hole_endpoints_nm=[a,z],through=True))
assert len(via)==918 and len(pads)==16
vm=min(Fraction(z['exact_radial_margin_nm'])for q in via for z in q['layers']);pm=min(Fraction(z['exact_minimum_hole_enclosure_margin_nm'])for q in pads for z in q['layers']);after=hashlib.sha256(B.read_bytes()).hexdigest();assert after==before
r=dict(status='PASS exact source-specific own-hole enclosure; not an all-drill graph replay',board_path=str(B),source_sha256=before,native_version=p.GetBuildVersion(),copper_layer_count=4,copper_layers=[b.GetLayerName(l)for l in L],vias=via,PTH=pads,via_count=len(via),PTH_count=len(pads),plated_layer_checks=(len(via)+len(pads))*4,min_via_radial_margin_nm=str(vm),min_PTH_hole_enclosure_margin_nm=str(pm),exceptions=[],source_unchanged=True,method='Exact integer/Fraction center, circle, rectangle and equal-spine capsule invariants from actual canonical native dimensions on every copper layer, including native hole segment endpoints and width. Unknown shape/span/offset fails closed. Positive enclosure makes each own-hole material a connected annulus touching the full physical hole boundary.',limits='Own-hole enclosure only. Foreign-drill cuts and final contact topology remain the corrected checker responsibility; no manufacturing, plating-process or SI qualification.')
(D/'ENCLOSURE_PROOF.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items()if k not in['vias','PTH']},indent=2))
