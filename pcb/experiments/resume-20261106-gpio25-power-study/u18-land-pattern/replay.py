#!/usr/bin/python3
"""Read-only U18 geometry extraction; never saves CAD. Run with run-kicad.sh."""
import pcbnew, hashlib, json, pathlib, math, subprocess
R=pathlib.Path('/workspace/shared/maru60-resume')
D=R/'selected-repo/pcb/experiments/resume-20261106-usb-pendant-prototype/pcb'
O=pathlib.Path(__file__).resolve().parent
board=D/'maru60.kicad_pcb'; vendor=R/'continuation-fa96a7c/power-audit/tps62932.pdf'
lib=pathlib.Path('/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-583-8.kicad_mod')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def mm(v): return round(pcbnew.ToMM(v),9)
def xy(v): return [mm(v.x),mm(v.y)]
b=pcbnew.LoadBoard(str(board)); f=next(f for f in b.GetFootprints() if f.GetReference()=='U18')
l=pcbnew.FootprintLoad(str(lib.parent),'SOT-583-8')
pads=[]
for p in sorted(f.Pads(),key=lambda p:int(p.GetNumber())):
 q=p.GetFPRelativePosition(); canonical=[mm(q.x),-mm(q.y)]
 lp=next(v for v in l.Pads() if v.GetNumber()==p.GetNumber())
 n=int(p.GetNumber()); expected=[-.74 if n<=4 else .74,(-.75+.5*(n-1)) if n<=4 else (.75-.5*(n-5))]
 mask=mm(p.GetSolderMaskExpansion(pcbnew.B_Mask)); paste=xy(p.GetSolderPasteMargin(pcbnew.B_Paste))
 row={'number':n,'net':p.GetNetname(),'inline_relative_mm':xy(q),'board_xy_mm':xy(p.GetPosition()),'canonical_component_top_view_mm':canonical,'size_mm':xy(p.GetSize()),'rotation_deg':p.GetOrientationDegrees(),'shape':p.ShowPadShape(pcbnew.B_Cu),'radius_mm':mm(p.GetRoundRectCornerRadius()),'layers':[b.GetLayerName(v) for v in p.GetLayerSet().Seq()], 'effective_mask_expansion_per_side_mm':mask,'effective_paste_margin_per_side_mm':paste,'pad_mask_override':p.GetLocalSolderMaskMargin(),'pad_paste_override':p.GetLocalSolderPasteMargin(),'pad_paste_ratio_override':p.GetLocalSolderPasteMarginRatio(),'matches_vendor_position':all(abs(a-c)<1e-8 for a,c in zip(canonical,expected)),'matches_installed_library_position_and_size':canonical==xy(lp.GetFPRelativePosition()) and xy(p.GetSize())==xy(lp.GetSize())}
 assert row['matches_vendor_position'] and row['matches_installed_library_position_and_size']
 assert row['size_mm']==[.67,.3] and abs(row['radius_mm']-.05)<1e-8
 pads.append(row)
graphics=[]
for g in f.GraphicalItems():
 if hasattr(g,'GetStart'): graphics.append({'layer':g.GetLayerName(),'start_board_mm':xy(g.GetStart()),'end_board_mm':xy(g.GetEnd()),'width_mm':mm(g.GetWidth())})
sources={str(p):sha(p) for p in [board,D/'maru60.kicad_pro',vendor,lib]}
assert sources[str(board)]=='41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5'
assert sources[str(vendor)]=='16ec2eac43c7374eb9e7edd7df7bdb24de6862f695e1582c68716ced4820e5f6'
result={'tool_version':pcbnew.Version(),'source_hashes':sources,'vendor_url':'https://www.ti.com/lit/ds/symlink/tps62932.pdf','drawing':'DRL0008A, 4224486/G 11/2024; physical PDF pages 48-50, visually reviewed','footprint':str(f.GetFPID().GetLibItemName()),'reference':f.GetReference(),'value':f.GetValue(),'position_mm':xy(f.GetPosition()),'angle_deg':f.GetOrientationDegrees(),'flipped':f.IsFlipped(),'transform':'Canonical top-view (x,y) -> inline (x,-y); board=(179.25-y,84.25-x) at 90 deg B.Cu','pads':pads,'graphics':graphics,'derived_mm':{'pitch':.5,'row_center_spacing':1.48,'same_row_edge_gap':.2,'opposing_pad_edge_gap':.81,'outer_copper_span':2.15,'row_end_span':1.8},'footprint_overrides':{'mask':f.GetLocalSolderMaskMargin(),'paste':f.GetLocalSolderPasteMargin(),'paste_ratio':f.GetLocalSolderPasteMarginRatio()},'board_settings':{k:getattr(b.GetDesignSettings(),k) for k in ['m_SolderMaskExpansion','m_SolderMaskMinWidth','m_SolderPasteMargin','m_SolderPasteMarginRatio']},'status':'CAD copper matches example; mask fabrication and stencil/assembly/thermal/hardware qualification remain provisional; no CAD changes'}
(O/'geometry.json').write_text(json.dumps(result,indent=2)+'\n')
(O/'source-hashes.json').write_text(json.dumps(sources,indent=2)+'\n')
print(json.dumps({'pads_checked':len(pads),'vendor_match':True,'library_match':True,'mask_mm':pads[0]['effective_mask_expansion_per_side_mm'],'paste_margin_mm':pads[0]['effective_paste_margin_per_side_mm']}))
