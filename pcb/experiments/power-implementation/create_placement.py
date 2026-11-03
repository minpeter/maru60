"""Placement-only isolated five-part LDO tile, not a routed/fabrication board."""
from pathlib import Path
import pcbnew as k,json
P=Path(__file__).parent;O=P/'native-max38902a';b=k.BOARD()
net={}
for n in ['GND','+4V_REG','+3V3','LDO_BYP']:
 x=k.NETINFO_ITEM(b,n);b.Add(x);net[n]=x
spec=json.loads((P/'bom.json').read_text())
positions={'U2':(12,10,0),'C100':(7.5,9.25,180),'C101':(16.5,9.25,0),'C142':(15.2,12.25,180),'R163':(12,14,0)}
pins={'U2':{'1':'+4V_REG','2':'GND','3':'+4V_REG','4':'GND','6':'+3V3','7':'LDO_BYP','8':'+3V3','9':'GND'},'C100':{'1':'+4V_REG','2':'GND'},'C101':{'1':'+3V3','2':'GND'},'C142':{'1':'+3V3','2':'LDO_BYP'},'R163':{'1':'+3V3','2':'GND'}}
for s in spec:
 ref=s['reference'];lib,name=s['footprint'].split(':');libpath=O/'MaruStudy.pretty' if lib=='MaruStudy' else Path('/usr/share/kicad/footprints')/(lib+'.pretty')
 f=k.FootprintLoad(str(libpath),name);assert f
 f.SetReference(ref);f.SetValue(s['mpn']);f.SetFPID(k.LIB_ID(lib,name));b.Add(f)
 x,y,rot=positions[ref];f.SetPosition(k.VECTOR2I(k.FromMM(x),k.FromMM(y)));f.SetOrientationDegrees(rot)
 f.Reference().SetTextSize(k.VECTOR2I(k.FromMM(.8),k.FromMM(.8)));f.Reference().SetTextThickness(k.FromMM(.12));f.Value().SetVisible(False)
 for pad in f.Pads():
  if pad.GetNumber() in pins[ref]:pad.SetNet(net[pins[ref][pad.GetNumber()]])
  elif ref=='U2' and pad.GetNumber()=='5':pad.SetPadName('5')
for a,z in [((3,4),(21,4)),((21,4),(21,18)),((21,18),(3,18)),((3,18),(3,4))]:
 line=k.PCB_SHAPE();line.SetShape(k.SHAPE_T_SEGMENT);line.SetStart(k.VECTOR2I(k.FromMM(a[0]),k.FromMM(a[1])));line.SetEnd(k.VECTOR2I(k.FromMM(z[0]),k.FromMM(z[1])));line.SetLayer(k.Edge_Cuts);line.SetWidth(k.FromMM(.05));b.Add(line)
for text,y in [('ISOLATED PLACEMENT ONLY',5),('UNROUTED / NOT FOR FAB',17)]:
 t=k.PCB_TEXT(b);t.SetText(text);t.SetPosition(k.VECTOR2I(k.FromMM(12),k.FromMM(y)));t.SetTextSize(k.VECTOR2I(k.FromMM(.8),k.FromMM(.8)));t.SetTextThickness(k.FromMM(.12));t.SetLayer(k.F_SilkS);b.Add(t)
k.SaveBoard(str(O/'ldo-placement-only.kicad_pcb'),b)
print('Placement-only tile; no tracks, vias, thermal copper or reset circuitry claimed implemented.')
