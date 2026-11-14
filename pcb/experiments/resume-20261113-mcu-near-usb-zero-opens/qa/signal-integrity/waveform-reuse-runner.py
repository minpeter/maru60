"""Recompute metrics; reuse only completed waveforms of byte-identical electrical decks.

Only the first comment/title and wrdata output filename are normalized. Circuit,
solver settings, stimuli, loading, requested vectors and stop time must match.
Historical failures remain failures; no outcome-based cache selection is made.
"""
import hashlib,json,re,runpy,shutil,sys,threading
from pathlib import Path
import numpy as np
sys.path.insert(0,'pcb/tools/signal_integrity');import spice
root=Path('build/mcu-near-usb/resume79-final-qa').resolve();dst=root/'si-cached';dst.mkdir(exist_ok=True)
base=root/'si';archive=Path('build/mcu-near-usb/resume78-final-qa/si-final').resolve()
for folder in ['out','decks','plots']:(dst/folder).mkdir(exist_ok=True)
for p in (base/'out').glob('*.json'):shutil.copy2(p,dst/'out'/p.name)
for p in base.glob('*-provenance.json'):shutil.copy2(p,dst/p.name)
for folder in ['decks','out','plots']:
 for p in (base/folder).glob('*'):
  if p.is_file() and not p.name.startswith('led_'):shutil.copy2(p,dst/folder/p.name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(s):
 lines=s.splitlines();assert lines[0].startswith('*')
 return '\n'.join(re.sub(r'^(wrdata) /out/[^ ]+\.txt ',r'\1 /out/WAVEFORM.txt ',line) for line in lines[1:])
def key(p):return hashlib.sha256(canonical(p.read_text()).encode()).hexdigest()
cache={}
for src in [archive,base,root/'led-damping',root/'si-fresh-cache']:
 for deck in (src/'decks').glob('*.cir'):
  if not deck.stem.startswith(('led_','KEY_RGB','UG_LED')):continue
  log=src/'out'/(deck.stem+'.log');wave=src/'out'/(deck.stem+'.txt')
  if not log.exists() or not wave.exists():continue
  text=log.read_text()
  if 'simulation(s) aborted' in text.lower() or 'No. of Data Rows' not in text:continue
  cache[key(deck)]=(deck,log,wave)
original=spice.run_deck;receipts=[];lock=threading.Lock()
def run(name):
 deck=spice.DECKS/(name+'.cir');k=key(deck);hit=cache.get(k)
 if hit is None:
  answer=original(name);record={'case':name,'action':'new_ngspice_run','canonical_deck_sha256':k}
 else:
  prior,log,wave=hit
  assert canonical(prior.read_text())==canonical(deck.read_text())
  with wave.open() as f:
   columns=f.readline().split();data=np.loadtxt(f,ndmin=2)
  assert data.size and np.isfinite(data).all() and columns[0]=='time'
  stop=re.search(r'^\.tran\s+\S+\s+([0-9.eE+-]+)([munp]?)',deck.read_text(),re.M)
  assert stop is not None
  stop_time=float(stop[1])*{'':1,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12}[stop[2]]
  # wrdata numdgt=7 can print equal adjacent adaptive timestamps.
  assert data[-1,0]>=stop_time*(1-1e-7) and np.all(np.diff(data[:,0])>=0), (name, data[-1,0], np.diff(data[:,0]).min())
  target=spice.OUT/(name+'.txt')
  if target.exists() or target.is_symlink():target.unlink()
  target.symlink_to(wave)
  shutil.copy2(log,spice.OUT/(name+'.log'))
  answer={n:data[:,i] for i,n in enumerate(columns)}
  record={'case':name,'action':'identical_deck_waveform_reuse','canonical_deck_sha256':k,'source_deck':str(prior),'source_deck_sha256':sha(prior),'source_waveform_sha256':sha(wave),'source_log_sha256':sha(log)}
 with lock:
  receipts.append(record)
  (dst/'waveform-reuse.json').write_text(json.dumps({'scope':__doc__,'source_ngspice_image':spice.IMAGE,'cases':sorted(receipts,key=lambda r:r['case'])},indent=2)+'\n')
 return answer
spice.run_deck=run
sys.argv=['run_candidate.py',str(root/'geometry.json'),'build/mcu-near-usb/resume78-led-damped/pcb/maru60.kicad_pcb',str(dst),'sim_led']
runpy.run_path('pcb/tools/signal_integrity/run_candidate.py',run_name='__main__')
print('Completed',len(receipts),'cases;',sum(r['action']=='new_ngspice_run' for r in receipts),'new runs',flush=True)
