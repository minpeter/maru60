import hashlib,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path('pcb/tools/signal_integrity').resolve()))
import spice
from sim_mixed_led import measure,PROFILES
base=Path('build/bottom-sim-20261114').resolve();sup=base/'supplement';out=base/'first-refinement';out.mkdir(exist_ok=True);spice.OUT=out/'raw';spice.DECKS=out/'decks';spice.DECKS.mkdir(exist_ok=True)
rows=[]
for r in json.loads((sup/'results.json').read_text())['first_hop']:
 if r['measurement']['meets_assumed_corner']:continue
 name=r['case']+'_dt025';original=sup/'decks'/(r['case']+'.cir');d=spice.Deck(name);d.lines=original.read_text().split('.tran')[0].splitlines();d.add('.options reltol=1e-4 abstol=1e-12 vntol=1e-7')
 w=d.run(name,['v(din)'],tran='0.025n 5000n 0 0.025n');np.savez_compressed(spice.OUT/(name+'.npz'),**w);(spice.OUT/(name+'.txt')).unlink()
 rows.append(dict(case=name,original_deck_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),measurement=measure(w['time']*1e9,w['v(din)'],PROFILES['SK6812MINI-E-012'])))
(out/'results.json').write_text(json.dumps({'scope':'Two flagged full first-hop cases: tighter time step/tolerance; same spatial ladder and behavioral buffer model.','tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':rows},indent=2)+'\n')
print([(r['case'],r['measurement']['meets_assumed_corner']) for r in rows])
