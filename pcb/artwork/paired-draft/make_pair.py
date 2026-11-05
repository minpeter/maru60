import pcbnew,pathlib,json
p=pathlib.Path(__file__).parent;lib=p/'Maru60_Art.pretty';polys=[];offset=0
for n in ['OSHW_Generic_Gear_6mm_Silk_DRAFT','Minpeter_Character_10mm_Silk_DRAFT']:
 fp=pcbnew.FootprintLoad(str(lib),n);groups=[]
 for g in fp.GraphicalItems():
  if g.GetLayer()!=pcbnew.F_SilkS:continue
  ps=g.GetPolyShape()
  for i in range(ps.OutlineCount()):
   o=ps.Outline(i);groups.append([(o.CPoint(k).x/1e6,o.CPoint(k).y/1e6) for k in range(o.PointCount())])
 xs=[x for a in groups for x,y in a];ys=[y for a in groups for x,y in a];scale=6/(max(ys)-min(ys));w=(max(xs)-min(xs))*scale
 for a in groups:polys.append([((x-min(xs))*scale+offset,(y-min(ys))*scale) for x,y in a])
 offset+=w+1.5
name='OSHW_then_Minpeter_H6_Gap1p5_Silk_DRAFT'
s=f'(footprint "{name}" (version 20241229) (generator "pcbnew") (layer "F.Cu") (descr "Generic gear LEFT, actual minpeter character RIGHT; equal 6mm height, 1.5mm gap. DRAFT not certified") (attr board_only exclude_from_pos_files exclude_from_bom)\n'
for a in polys:s+='(fp_poly (pts '+' '.join(f'(xy {x:.6f} {y:.6f})' for x,y in a)+') (stroke (width 0) (type solid)) (fill solid) (layer "F.SilkS"))\n'
s+=')';(lib/(name+'.kicad_mod')).write_text(s);assert pcbnew.FootprintLoad(str(lib),name)
(p/'pair-polygons.json').write_text(json.dumps(polys));print('pair width',offset-1.5,'height6 gap1.5')
