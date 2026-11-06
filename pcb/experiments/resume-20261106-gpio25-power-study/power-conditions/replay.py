#!/usr/bin/env python3
"""Portable evidence validation only; not a fresh native CAD audit."""
import hashlib,json,pathlib,xml.etree.ElementTree as ET
p=pathlib.Path(__file__).resolve().parent
x=json.loads((p/'EVIDENCE.json').read_text())
assert hashlib.sha256((p/'netlist-fresh.xml').read_bytes()).hexdigest()==x['fresh_netlist_sha256']
r=ET.parse(p/'netlist-fresh.xml').getroot()
nets={n.get('name'):sorted([v.get('ref'),v.get('pin')] for v in n.findall('node')) for n in r.findall('./nets/net')}
for n,ns in x['nets'].items():assert nets[n]==ns
for ref,c in x['components'].items():
 for pin,net in c['native_pins'].items():assert [ref,pin] in nets[net]
assert x['nets']['USB_INPUT_FAULT_N']==[['R126','1'],['U8','4']]
assert x['nets']['GPIO_ISOLATE']==[['R128','1'],['U11','19'],['U12','2']]
assert x['components_checked']==36 and x['native_pins_checked']==181
assert all(v=='PASS' for v in x['checks'].values())
print('PASS: portable snapshot parity, 36 components / 181 numbered pads; no dynamic or hardware claim.')
