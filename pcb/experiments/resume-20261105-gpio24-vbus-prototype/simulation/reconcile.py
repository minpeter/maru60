import pathlib,hashlib,json,xml.etree.ElementTree as E
import pcbnew
D=pathlib.Path(__file__).resolve().parent; P=pathlib.Path('/workspace/shared/maru60-resume/header-routing/frozen26b/pcb'); b=pcbnew.LoadBoard(str(P/'maru60.kicad_pcb')); e=E.parse(D/'current.net.xml').getroot()
refs=['C100','C120','C125','C126','R125','F1','D100','U2','U8','R120','R121','R122','R123','R124','C124','U18','L2','C136','C137','C138','C139','C140','C141','R159','R160','U7','R112','C128','C129']
sch={x.attrib['ref']:x for x in e.findall('./components/comp')}; pads={}; nets={}
for n in e.findall('./nets/net'):
 for node in n.findall('node'):nets.setdefault(node.attrib['ref'],{})[node.attrib['pin']]=n.attrib['name']
for f in b.GetFootprints():
 if f.GetReference() in refs:pads[f.GetReference()]={'value':f.GetValue(),'pads':{p.GetNumber():p.GetNetname() for p in f.Pads()}}
r={}
for ref in refs:
 x=sch.get(ref); r[ref]={'schematic_value':x.findtext('value') if x is not None else None,'schematic_pins':nets.get(ref), 'native_board':pads.get(ref)}
report={'current_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.glob('*') if p.suffix in ['.kicad_sch','.kicad_pcb']},'exported_netlist_sha256':hashlib.sha256((D/'current.net.xml').read_bytes()).hexdigest(),'components':r}
assert all(x['schematic_value']==x['native_board']['value'] and all(x['native_board']['pads'].get(pin)==net for pin,net in x['schematic_pins'].items()) for x in r.values())
(D/'current-source-crosscheck.json').write_text(json.dumps(report,indent=2));print(json.dumps(r,indent=2))
