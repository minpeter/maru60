import pcbnew as p
bp='build/mcu-near-usb/trial/pcb/maru60.kicad_pcb';b=p.LoadBoard(bp)
critical={'USB_DP','USB_DM','USB_DP_CONN','USB_DM_CONN','XIN','XOUT','XTAL_OUT','VREG_LX','VREG_AVDD','+1V1'}
for t in b.GetTracks():t.SetLocked(t.GetNetname() in critical)
p.SaveBoard(bp,b)
assert p.ExportSpecctraDSN(b,'build/mcu-near-usb/mcu.dsn')
print('DSN exported')
