import json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,'pcb/tools/signal_integrity')
import spice,sim_led
work=Path('build/mcu-near-usb/resume78-final-qa/si').resolve()
spice.DECKS=work/'convergence/decks';spice.OUT=work/'convergence/out'
spice.DECKS.mkdir(parents=True,exist_ok=True);spice.OUT.mkdir(parents=True,exist_ok=True)
original=(work/'numerical-failure/trapezoidal-aborted.cir').read_text()
lines=original.splitlines(); tiny_index=next(i for i,s in enumerate(lines) if s.startswith('Rt29 '))
assert lines[tiny_index:tiny_index+3]==['Rt29 p1 tm28 5.23772e-18','Lt29 tm28 p27 9.51656e-16n','Ct29 p27 0 2.74118e-16p']
lines[tiny_index:tiny_index+3]=['Rj29 p1 p27 1m']
base='\n'.join(lines)+'\n';results={}
for step in [0.2,0.1]:
 name=f'zero_length_fixed_{step:g}ns'
 deck=base.replace('0.1n 5000n 0 0.2n',f'0.1n 5000n 0 {step:g}n').replace('/out/led_hop19_weakp.txt',f'/out/{name}.txt')
 (spice.DECKS/f'{name}.cir').write_text(deck)
 wave=spice.run_deck(name)
 assert wave['time'][-1]>=5e-6
 results[str(step)]=sim_led.measure(wave['time'],wave['v(din)'],100e-9,30e-9)
a,b=results.values()
width_delta=max(abs(a[bit][key]-b[bit][key]) for bit in ['0','1'] for key in ['width_min_ns','width_max_ns'])
margin_delta=max(abs(a[key]-b[key]) for key in ['noise_margin_high_V','noise_margin_low_V'])
passed=width_delta<=0.1 and margin_delta<=0.005 and all(v>=0 for x in results.values() for v in x['budget_ns'].values()) and all(x[bit]['extra_threshold_crossings']==0 for x in results.values() for bit in ['0','1'])
out={'pass':passed,'method':'Trapezoidal integration, unchanged electrical route except numerical-zero LC section replaced by existing 1 mOhm junction convention','max_pulse_width_change_ns':width_delta,'max_noise_margin_change_V':margin_delta,'criteria':{'pulse_width_delta_ns':0.1,'noise_margin_delta_V':0.005,'positive_timing_budgets':True,'no_threshold_recrossings':True},'measurements':results}
(work/'convergence/results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert passed
