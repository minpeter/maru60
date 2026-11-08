import pcbnew as p,sys,html
from pathlib import Path
b=p.LoadBoard(sys.argv[1]); items=list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]
for l in [p.F_Cu,p.B_Cu,p.In1_Cu]:
 out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="84 30 30 18" width="1500" height="900"><rect x="84" y="30" width="30" height="18" fill="#181818"/>']
 colors={'EXT_GPIO24':'#ff4949','EXT_GPIO25':'#ffc241','EXT_GPIO26':'#41ffc2','EXT_GPIO27':'#417eff','EXT_GPIO10':'#d983ff','GND':'#585858'}
 for q in items:
  if not q.IsOnLayer(l):continue
  bb=q.GetBoundingBox()
  if bb.GetRight()<84e6 or bb.GetX()>114e6 or bb.GetBottom()<30e6 or bb.GetY()>48e6:continue
  shape=p.SHAPE_CIRCLE(q.GetPosition(),q.GetWidth(l)//2)if isinstance(q,p.PCB_VIA)else q.GetEffectiveShape(l)
  ps=p.SHAPE_POLY_SET();shape.TransformToPolygon(ps,5000,p.ERROR_OUTSIDE); ps.Simplify()
  for i in range(ps.OutlineCount()):
   c=ps.COutline(i);points=' '.join(f'{c.CPoint(j).x/1e6},{c.CPoint(j).y/1e6}'for j in range(c.PointCount()));out.append(f'<polygon points="{points}" fill="{colors.get(q.GetNetname(),"#b0b0b0")}"/>')
  if isinstance(q,p.PAD):
   x,y=q.GetPosition().x/1e6,q.GetPosition().y/1e6;out.append(f'<text x="{x}" y="{y+.05}" font-size=".18" fill="white" text-anchor="middle">{html.escape(q.GetParentFootprint().GetReference()+"."+q.GetNumber())}</text>')
 for x in range(84,115):out.append(f'<text x="{x}" y="30.3" font-size=".22" fill="white">{x}</text>')
 for y in range(31,49):out.append(f'<text x="84" y="{y}" font-size=".22" fill="white">{y}</text>')
 out.append('</svg>');Path(sys.argv[2]+'-'+b.GetLayerName(l)+'.svg').write_text('\n'.join(out))
