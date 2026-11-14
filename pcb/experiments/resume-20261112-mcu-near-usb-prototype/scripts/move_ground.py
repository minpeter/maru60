import pcbnew as p
bp='build/mcu-near-usb/trial/pcb/maru60.kicad_pcb';b=p.LoadBoard(bp)
for z in b.Zones():
 bb=z.GetBoundingBox();x,y=bb.GetX()/1e6,bb.GetY()/1e6
 if z.GetNetname()=='GND' and 96<=x<120 and 72<=y<90:
  z.Rotate(p.VECTOR2I(111000000,81500000),p.EDA_ANGLE(180,p.DEGREES_T));z.Move(p.VECTOR2I(-85000000,-46500000))
p.SaveBoard(bp,b);b=p.LoadBoard(bp);b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(bp,b)
