import pcbnew as p

bp = "build/mcu-near-usb/l1-dot-move-check/pcb/maru60.kicad_pcb"
b = p.LoadBoard(bp)
f = b.FindFootprintByReference("L1")
hits = []
for g in f.GraphicalItems():
    c = g.GetCenter()
    if abs(c.x / 1e6 - 19.5) < .01 and abs(c.y / 1e6 - 35.6) < .01:
        hits.append(g)
assert len(hits) == 1, len(hits)
hits[0].Move(p.VECTOR2I(-500000,0))
b.BuildConnectivity()
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(bp,b)
print("translated L1 polarity dot 0.5 mm left")
