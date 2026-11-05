import pcbnew,json,pathlib,shutil
p=pathlib.Path(__file__).parent;lib=p/'Maru60_Art.pretty'
cs=json.loads((p/'character-contours.json').read_text())
for w in [10,12]:
 poly=pcbnew.SHAPE_POLY_SET();poly.NewOutline()
 for j,pts in enumerate(cs):
  h=poly.NewHole() if j else -1
  for x,y in pts:poly.Append(round((x-59)*w/118*1e6),round((y-52)*w/118*1e6),0,h)
 poly.Fracture()
 name=f'Minpeter_Character_{w}mm_Silk_DRAFT'
 text=f'(footprint "{name}" (version 20241229) (generator "pcbnew") (layer "F.Cu") (descr "User-authorized signature-mark.svg; draft artwork only; no pads/copper") (attr board_only exclude_from_pos_files exclude_from_bom)\n'
 for i in range(poly.OutlineCount()):
  o=poly.Outline(i);pts=' '.join(f'(xy {o.CPoint(k).x/1e6:.6f} {o.CPoint(k).y/1e6:.6f})' for k in range(o.PointCount()))
  text+=f'(fp_poly (pts {pts}) (stroke (width 0) (type solid)) (fill solid) (layer "F.SilkS"))\n'
 text+=')\n';(lib/f'{name}.kicad_mod').write_text(text)
 fp=pcbnew.FootprintLoad(str(lib),name);assert fp and len(list(fp.Pads()))==0
 print(name,fp.GetBoundingBox().GetWidth()/1e6,fp.GetBoundingBox().GetHeight()/1e6)
src=pathlib.Path('/usr/share/kicad/footprints/Symbol.pretty/OSHW-Symbol_6.7x6mm_SilkScreen.kicad_mod')
name='OSHW_Generic_Gear_6mm_Silk_DRAFT';s=src.read_text().replace('OSHW-Symbol_6.7x6mm_SilkScreen',name).replace('(attr board_only','(attr board_only')
(lib/f'{name}.kicad_mod').write_text(s)
fp=pcbnew.FootprintLoad(str(lib),name);assert fp and len(list(fp.Pads()))==0
b=pcbnew.BOARD()
for x,name in [(10,'Minpeter_Character_10mm_Silk_DRAFT'),(25,'Minpeter_Character_12mm_Silk_DRAFT'),(39,'OSHW_Generic_Gear_6mm_Silk_DRAFT')]:
 fp=pcbnew.FootprintLoad(str(lib),name);fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(10)));b.Add(fp)
pcbnew.SaveBoard(str(p/'artwork-proof-only.kicad_pcb'),b)
