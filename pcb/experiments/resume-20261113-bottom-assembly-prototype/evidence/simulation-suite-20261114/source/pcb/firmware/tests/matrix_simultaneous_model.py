#!/usr/bin/env python3
"""Actual netlist ideal-diode scan model; not switch/diode/USB hardware testing."""
from pathlib import Path
import xml.etree.ElementTree as E,json,collections,itertools,hashlib
P=Path(__file__).resolve().parents[2];reports=[]
def verify(xml,config):
 refs=collections.defaultdict(dict)
 for net in E.parse(xml).findall('nets/net'):
  for n in net.findall('node'):refs[n.get('ref')][n.get('pin')]=net.get('name')
 diodes={v['2']:v['1'] for ref,v in refs.items() if ref.startswith('D') and v.get('1','').startswith('ROW') and v.get('2','').startswith('KEY_')}
 switches={}
 for ref,pins in refs.items():
  if not ref.startswith('SW') or not any(v.startswith('COL') for v in pins.values()):continue
  for i in range(1,len(pins)+1,2):
   a,b=pins[str(i)],pins[str(i+1)]
   assert a.startswith('COL') and b in diodes,(ref,i,a,b)
   key=(int(diodes[b][3:]),int(a[3:]));switches.setdefault(key,[]).append((a,b,ref))
 def scan(pressed,reverse_one=False):
  graph=collections.defaultdict(set)
  for j,key in enumerate(pressed):
   col,anode,_=switches[key][0];row=diodes[anode]
   graph[col].add(anode);graph[anode].add(col)
   graph[row if reverse_one and j==0 else anode].add(anode if reverse_one and j==0 else row)
  sensed=set()
  for col in {switches[k][0][0] for k in pressed}:
   seen=set();todo=[col]
   while todo:
    node=todo.pop()
    if node in seen:continue
    seen.add(node);todo.extend(graph[node]-seen)
   sensed.update((int(n[3:]),int(col[3:])) for n in seen if n.startswith('ROW'))
  return sensed
 for name,layout in json.loads(config.read_text())['layouts'].items():
  keys=[tuple(k['matrix']) for k in layout['layout']];assert len(keys)==len(set(keys));assert all(k in switches for k in keys)
  counts={}
  for n in [1,2,3]:
   count=0
   for pressed in itertools.combinations(keys,n):
    assert scan(pressed)==set(pressed),(name,pressed);count+=1
   counts[str(n)]=count
  assert scan(keys)==set(keys) and scan([])==set()
  assert scan([keys[0]],True)!=set([keys[0]]) # polarity-negative fixture must fail
  reports.append({'layout':name,'keys':len(keys),'exhaustive_pressed_subsets':counts,'all_pressed_and_all_released':'PASS','reversed_diode_negative_fixture':'detected','duplicate_matrix_coordinates':False,'ideal_model_no_missing_or_ghost_keys':'PASS','netlist_sha256':hashlib.sha256(xml.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256(config.read_bytes()).hexdigest()})
verify(P/'validation/maru60.xml',P/'firmware/qmk/keyboards/maru60/rp2350/keyboard.json')
verify(P/'variants/bs65/validation/maru60.xml',P/'variants/bs65/firmware/qmk/keyboards/maru60/rp2350/keyboard.json')
r={'scope':'Actual exported switch-pair/diode net topology; ideal forward diodes and digital levels. Exhaustive subsets up to3 plus allpressed/released, not exhaustive2^60. Does not prove physical diode orientation/leakage, scan timing/bounce, analog voltage margins, USB NKRO/host acceptance or mechanically compatible population.','results':reports}
out=P/'validation/matrix-simultaneous-model.json';out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
