import pcbnew
p='build/mcu-near-usb/resume78-led-damped/pcb/maru60.kicad_pcb'
b=pcbnew.LoadBoard(p);f=next(f for f in b.GetFootprints() if f.GetReference()=='R193');t=f.Reference()
t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(15.6),pcbnew.FromMM(31.0)));t.SetTextAngle(pcbnew.EDA_ANGLE(0,pcbnew.DEGREES_T));pcbnew.SaveBoard(p,b)
