import pcbnew as p

bp = "build/mcu-near-usb/gnd-cut-check/pcb/maru60.kicad_pcb"
b = p.LoadBoard(bp)
for name, x0, y0, x1, y1 in [
    ("GND neck cut A", 24.9745, 39.385, 25.1745, 39.415),
    ("GND neck cut B", 13.9703, 36.7728, 14.0303, 36.8328),
]:
    z = p.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetDoNotAllowTracks(False)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetLayer(p.F_Cu)
    z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)):
        o.Append(round(x*1e6),round(y*1e6))
    b.Add(z)
b.BuildConnectivity()
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(bp,b)
print("added two pour-only GND neck cuts")
