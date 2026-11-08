#!/usr/bin/env python3
"""NEW bounded netlist/GPIO check, not restoration of the lost integration verifier."""
import sys
if not __debug__:raise SystemExit('Assertions required; do not use optimized Python')
sys.dont_write_bytecode=True
import argparse,ast,copy,hashlib,json,re,xml.etree.ElementTree as E
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--netlist',type=Path,required=True);p.add_argument('--expected-sha256',required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--matrix-script',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
N=a.netlist.resolve();S=a.source.resolve();M=a.matrix_script.resolve();O=a.output.resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists() and O!=N and not O.is_relative_to(S)
assert sha(N)==a.expected_sha256,'Wrong netlist hash'
before={str(f.relative_to(S)):sha(f) for f in S.rglob('*') if f.is_file()};model_before=sha(M)
k=json.loads((S/'keyboard.json').read_text());assert k['diode_direction']=='COL2ROW'
pads={0:2,1:3,2:4,4:7,5:8,6:9,7:10,8:12,9:13,11:15,12:16,13:17,14:18,15:19,16:27,17:28,18:29,19:31,20:32,21:33,22:34,23:35,28:42,29:43}
expected={}
for kind,key in [('ROW','rows'),('COL','cols')]:
 for i,g in enumerate(k['matrix_pins'][key]):
  assert re.fullmatch(r'GP\d+',g);expected[int(g[2:])]=f'{kind}{i}'
for file,macro,net,gpio in [('maru_key_transport.c','WS2812_DI_PIN','KEY_RGB',20),('maru_ug_transport.c','WS2812_DI_PIN','UNDERGLOW',21),('maru_rgb.c','MARU_LED_ENABLE','LED_ENABLE',22),('maru_rgb.c','MARU_LED_FAULT_N','LED_FAULT_N',23)]:
 assert re.search(r'^#define\s+'+macro+r'\s+GP'+str(gpio)+r'\s*$',(S/file).read_text(),re.M);expected[gpio]=net
assert len(expected)==24
root=E.parse(N).getroot()
def mapping(tree):
 seen={};used_pins=set()
 for net in tree.findall('nets/net'):
  for node in net.findall('node'):
   if node.get('ref')!='U1':continue
   m=re.fullmatch(r'GPIO(\d+)(?:_ADC\d+)?',node.get('pinfunction',''))
   if not m:continue
   gpio=int(m[1]);pin=int(node.get('pin'))
   assert gpio not in seen and pin not in used_pins,'Duplicate MCU GPIO node/pin'
   seen[gpio]={'net':net.get('name'),'physical_pin':pin};used_pins.add(pin)
 for gpio,net in expected.items():
  assert seen[gpio]=={'net':net,'physical_pin':pads[gpio]},(gpio,seen.get(gpio),net,pads[gpio])
 return {str(g):seen[g] for g in sorted(expected)}
actual=mapping(root);negatives=[]
for name in ['wrong_gpio_function','wrong_led_net','duplicate_selected_gpio']:
 r=copy.deepcopy(root);net=next(n for n in r.findall('nets/net') if n.get('name')=='KEY_RGB');node=next(n for n in net.findall('node') if n.get('ref')=='U1')
 if name=='wrong_gpio_function':node.set('pinfunction','GPIO21')
 elif name=='wrong_led_net':net.set('name','WRONG_KEY_RGB')
 else:net.append(copy.deepcopy(node))
 try:mapping(r)
 except AssertionError:negatives.append({'case':name,'rejected':True})
 else:raise AssertionError('Negative mutation was not rejected: '+name)
# Execute original pure model definitions only; omit its historical main/BS65
# calls and source-tree writes, then supply the CURRENT hash-bound V7 netlist.
tree=ast.parse(M.read_text());nodes=[]
for n in tree.body:
 if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef)) or (isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and t.id in ['P','reports'] for t in n.targets)):nodes.append(n)
ns={'__file__':str(M)};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(M),'exec'),ns);ns['verify'](N,S/'keyboard.json')
assert sha(N)==a.expected_sha256 and sha(M)==model_before and before=={str(f.relative_to(S)):sha(f) for f in S.rglob('*') if f.is_file()}
report={'pass':True,'scope':'NEW bounded current-V7 schematic-netlist/GPIO and ideal-matrix check. Not the lost 362-file verifier or routed PCB/hardware qualification.','netlist_path':str(N),'netlist_sha256':sha(N),'source_hashes':before,'matrix_model_sha256':model_before,'checked_gpio_bindings':actual,'binding_count':len(actual),'negative_controls':negatives,'matrix_results':ns['reports'],'inputs_unchanged':True,'limits':['Schematic netlist labels and symbol pin functions do not prove PCB routing continuity or physical wiring','Ideal forward diodes/digital levels; exhaustive key subsets only through3 plus all/none, not all2^60 combinations','No physical diode orientation/leakage, switch bounce, scan timing, analog margins, USB NKRO, MCU register/driver waveform or LED-rail qualification','No original full integration verifier, Git history or historical receipts restored']}
O.parent.mkdir(parents=True,exist_ok=True);O.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'pass':True,'bindings':len(actual),'matrix_results':ns['reports'],'negative_controls':negatives,'report':str(O)},indent=2))
