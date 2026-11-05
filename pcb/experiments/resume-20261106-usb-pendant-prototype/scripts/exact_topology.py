from pathlib import Path
import json,hashlib,sys,collections,pcbnew as p
R=Path('/workspace/shared/maru60-resume');S=R/'selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype';D=R/'continuation-fa96a7c/usb-stub';U='b04e3a6d-1e98-43d1-9b10-58c23321ca28';sys.path.insert(0,str(R/'tools'));from sexpr_spans import children,head,field
sa=(S/'pcb/maru60.kicad_pcb').read_text();sb=(D/'pcb/maru60.kicad_pcb').read_text();ca=[s for _,_,s in children(sa)if not(head(s)=='segment' and U in s)];cb=[s for _,_,s in children(sb)];assert ca==cb
# This exact whole-top-level assertion also covers all serialized zone boundaries,
# all retained primitive input shapes, every drill, rules, mask and stack setup.
bs=[p.LoadBoard(str(x/'pcb/maru60.kicad_pcb'))for x in [S,D]];layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
def capture(b):
 out={}
 for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]:
  if 'USB_D' not in q.GetNetname():continue
  uid=q.m_Uuid.AsString();row={'uuid':uid,'kind':q.GetClass(),'net':q.GetNetname(),'layers':[b.GetLayerName(l)for l in layers if q.IsOnLayer(l)],'position_nm':[q.GetPosition().x,q.GetPosition().y]}
  if isinstance(q,p.PCB_VIA):row.update(widths_nm={b.GetLayerName(l):q.GetWidth(l)for l in layers if q.IsOnLayer(l)},drill_nm=q.GetDrillValue())
  elif isinstance(q,p.PCB_TRACK):row.update(start_nm=[q.GetStart().x,q.GetStart().y],end_nm=[q.GetEnd().x,q.GetEnd().y],width_nm=q.GetWidth(),length_mm=q.GetLength()/1e6)
  elif isinstance(q,p.PAD):row.update(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber())
  out[uid]=row
 return out
a,b=map(capture,bs);assert set(a)-set(b)=={U};assert all(a[u]==b[u]for u in b)
summary={}
for n in sorted({v['net']for v in a.values()}):
 def metrics(rows):
  rows=[v for v in rows if v['net']==n];return {'segments':sum('length_mm'in v for v in rows),'centerline_length_mm':sum(v.get('length_mm',0)for v in rows),'widths_mm':sorted({v['width_nm']/1e6 for v in rows if 'width_nm'in v}),'via_transitions':[v for v in rows if v['kind']=='PCB_VIA'],'pads':[v for v in rows if v['kind']=='PAD']}
 summary[n]={'before_including_dangling_stub':metrics(a.values()),'after':metrics(b.values()),'retained_active_geometry_exact':True}
# Only live geometry is unchanged; whole-net length metric is explicitly not an active path metric.
res={'source_sha256':hashlib.sha256(sa.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(sb.encode()).hexdigest(),'entire_board_top_level_exact_except_one_segment':True,'removed_segments':[U],'changed_retained_primitives':0,'changed_holes':0,'changed_zone_serializations':0,'changed_zone_filled_contours':0,'exact_retained_material_proof':'Every raw copper primitive and every drill serialization unchanged, hence all-hole-subtracted retained material is exactly equal. Every complete filled zone serialization unchanged and holes unchanged, hence complete all-hole GND planes exactly equal, including remote edges. Reference intersection is therefore exactly unchanged for every retained row.','usb_by_net':summary,'before_objects':a,'after_objects':b,'historical_signal_quality_inputs':'Stub copper changed on USB_DM_CONN. Older-hash reduced models are not validated for this candidate and may omit pendant branches. No older SI result is reused. No field/IBIS/eye result or USB certification is claimed.'}
(D/'qa/exact-topology.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps({n:{k:v for k,v in d.items()if k=='retained_active_geometry_exact'}for n,d in summary.items()}))
