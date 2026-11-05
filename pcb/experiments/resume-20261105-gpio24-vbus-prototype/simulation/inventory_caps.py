import pathlib,json,xml.etree.ElementTree as E
import pcbnew
D=pathlib.Path(__file__).resolve().parent; r=E.parse(D/'current.net.xml').getroot(); b=pcbnew.LoadBoard('/workspace/shared/maru60-resume/header-routing/frozen26b/pcb/maru60.kicad_pcb')
values={c.attrib['ref']:c.findtext('value') for c in r.findall('./components/comp')}; pins={}
for n in r.findall('./nets/net'):
 for p in n.findall('node'): pins.setdefault(p.attrib['ref'],{})[p.attrib['pin']]=n.attrib['name']
board={f.GetReference():{'value':f.GetValue(),'pins':{p.GetNumber():p.GetNetname() for p in f.Pads()}} for f in b.GetFootprints()}
nets=['VBUS_FUSED','VBUS_PROTECTED_RAW','+4V_REG','+4V_LED','+3V3']; inventory={}
for net in nets:
 inventory[net]=[]
 for ref,pp in sorted(pins.items()):
  if ref.startswith('C') and net in pp.values():
   assert values[ref]==board[ref]['value'] and pp==board[ref]['pins']
   inventory[net].append({'ref':ref,'value':values[ref],'pins':pp,'connection':'grounded' if 'GND' in pp.values() else 'between_non_ground_nets'})
(D/'capacitor-inventory.json').write_text(json.dumps(inventory,indent=2)); print(json.dumps(inventory,indent=2))
