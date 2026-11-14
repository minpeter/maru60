import json,sys,math,hashlib
from pathlib import Path
sys.path.insert(0,'pcb/tools/signal_integrity')
import geom,sim_led,spice
root=Path('build/mcu-near-usb/resume79-final-qa/led-damping').resolve();spice.OUT=root/'out';spice.DECKS=root/'decks';root.mkdir(parents=True,exist_ok=True)
gpath=Path('build/mcu-near-usb/resume79-final-qa/geometry.json');board=geom.Board(gpath)
si=Path('build/mcu-near-usb/resume79-final-qa/si/out');table=json.loads((si/'lines.json').read_text());geo=json.loads((si/'geometry.json').read_text())
labels=[];jobs=[];routes={}
for net in ['KEY_RGB_CHAIN_28','KEY_RGB_CHAIN_29','UG_LED_6']:
 h=next(h for h in geo['led']['key']+geo['led']['underglow'] if h['net']==net);ser=h['series_at_source'];pre=ser['source_side'];pr=board.route(pre['net'],tuple(pre['from'].split('.')),tuple(pre['to'].split('.')))
 for pop,near in ([('window',(16.49,42.22)),('stepped',(19.99,38.22))] if net.endswith('29') else [('default',None)]):
  pick=None if near is None else lambda p:p['ref']!='LED30' or math.hypot(p['x']-near[0],p['y']-near[1])<=1.5
  route=board.route(net,tuple(h['from'].split('.')),tuple(h['to'].split('.')),pick)
  routes[net+'/'+pop]={'resistor':ser['ref'],'ohm':ser['ohm'],'source_side_mm':pr['length_mm'],'downstream_mm':route['length_mm'],'source_vias':pr['vias'],'downstream_vias':route['vias']}
  for i,drv in enumerate([{'r':rr,'edge':ee*1e-9,'cin':cap*1e-12} for rr,ee,cap in [(10,1,5),(10,2,5),(20,1,5),(20,2,5),(10,1,15),(1000,30,15)]]):
   label=f'{net}_{pop}_{i}';labels.append((label,drv));jobs.append((label,route,table,drv,(pr,ser['ohm'])))
rows=[]
for (label,drv),m in zip(labels,sim_led.run_hops(jobs)):
 passed=bool(m.get('budget_ns')) and min(m['budget_ns'].values())>=0 and m['noise_margin_high_V']>=0 and m['noise_margin_low_V']>=0 and all(m[b].get('extra_threshold_crossings',1)==0 for b in ['0','1'])
 rows.append({'case':label,'driver':drv,'pass':passed,'measurement':m});print(label,passed,flush=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'pass':all(r['pass'] for r in rows),'board_sha256':sha(Path('build/mcu-near-usb/resume78-led-damped/pcb/maru60.kicad_pcb')),'geometry_sha256':sha(gpath),'scope':'Actual routed resistor circuits, both exclusive LED30 sites; assumed output and load corners.','routes':routes,'cases':rows}
(root/'results.json').write_text(json.dumps(result,indent=2)+'\n');assert result['pass']
