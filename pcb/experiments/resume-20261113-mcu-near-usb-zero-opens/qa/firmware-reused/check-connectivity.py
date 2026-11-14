import json,hashlib,xml.etree.ElementTree as E
from pathlib import Path
old=Path('build/final22-native/netlist.xml');new=Path('build/mcu-near-usb/resume79-silk-native/netlist.xml')
a,b=[E.parse(p).getroot() for p in (old,new)]
def nets(e):return {n.get('name'):{(x.get('ref'),x.get('pin')) for x in n.findall('node')} for n in e.findall('./nets/net')}
def comps(e):return {c.get('ref'):c.findtext('value') for c in e.findall('./components/comp')}
na,nb=nets(a),nets(b);ca,cb=comps(a),comps(b)
assert set(cb)-set(ca)=={'R192','R193'} and not set(ca)-set(cb)
assert {k:(ca[k],cb[k]) for k in ca if ca[k]!=cb[k]}=={'R115':('100 1%','150 1%')}
assert nb['KEY_RGB_CHAIN_28_SRC']=={('LED17','3'),('R192','1')}
assert nb['KEY_RGB_CHAIN_29_SRC']=={('LED16','3'),('R193','1')}
assert ('R192','2') in nb['KEY_RGB_CHAIN_28'] and ('R193','2') in nb['KEY_RGB_CHAIN_29']
normalized={}
for n,ps in nb.items():
 target=n[:-4] if n in ['KEY_RGB_CHAIN_28_SRC','KEY_RGB_CHAIN_29_SRC'] else n
 normalized.setdefault(target,set()).update(p for p in ps if p[0] not in ['R192','R193'])
assert normalized==na
mcu=lambda ns:{p[1]:n for n,ps in ns.items() for p in ps if p[0]=='U1'}
assert mcu(na)==mcu(nb)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fwroot=Path('pcb/experiments/resume-20261112-mcu-near-usb-prototype/qa/qmk-build');images={p.name:sha(p) for p in fwroot.glob('*.uf2')};assert len(images)==2
r={'pass':True,'netlist_names_and_pins_identical':False,'baseline_nets':len(na),'candidate_nets':len(nb),'mcu_pin_bindings_identical':True,'all_original_pin_bindings_identical_after_contracting_added_resistors':True,'allowed_topology_changes':{'R192':'LED17.3 -> KEY_RGB_CHAIN_28_SRC -> R192.1 / R192.2 -> KEY_RGB_CHAIN_28 -> LED16.1','R193':'LED16.3 -> KEY_RGB_CHAIN_29_SRC -> R193.1 / R193.2 -> KEY_RGB_CHAIN_29 -> LED30.1 (both sites)'},'allowed_value_changes':{'R115':{'from':'100 1%','to':'150 1%'}},'baseline_netlist':str(old),'baseline_netlist_sha256':sha(old),'candidate_netlist_sha256':sha(new),'board_sha256':sha(Path('build/mcu-near-usb/resume79-final/pcb/maru60.kicad_pcb')),'firmware_images':images,'note':'Existing firmware bytes reused: MCU pins and original connectivity match after explicitly contracting only R192/R193. LED order preserved; firmware timing unchanged. No new build, flash or hardware test.'}
Path('build/mcu-near-usb/resume79-final-qa/firmware-reuse.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
