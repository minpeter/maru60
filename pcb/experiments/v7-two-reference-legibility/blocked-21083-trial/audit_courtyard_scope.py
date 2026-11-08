import sys,os,json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));sys.dont_write_bytecode=True
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 d=W/'court-audit-runtime'/k.lower();d.mkdir(parents=True,exist_ok=True,mode=0o700);os.environ[k]=str(d)
from native_ink import *
S=W/'source/pcb/maru60.kicad_pcb';s=Scene(S);old=json.load(open('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-four-reference-logo/qa/candidate-four-ink.json'));refs=list(dict.fromkeys([r['reference']for r in old['rows']]+['R125','U18','L2']))
raw={p.F_CrtYd:[],p.B_CrtYd:[]}
for x,ref in [(x,r)for r,fp in s.fps.items()for x in fp.GraphicalItems()]+[(x,None)for x in s.board.GetDrawings()]:
 if x.GetLayer()in raw:
  m=info(x,ref);m['width_nm']=x.GetWidth() if hasattr(x,'GetWidth')else None;raw[x.GetLayer()].append((m,effective(x)))
rows=[]
for r in refs:
 x=s.fields[r];side=x.GetLayer();cy=p.F_CrtYd if side==p.F_SilkS else p.B_CrtYd;shape=effective(x);g=gap(shape,s.buckets[side]['courtyard']);j=gap(shape,s.buckets[side]['courtyard']+raw[cy]);hit=hits(shape,s.buckets[side]['courtyard']+raw[cy],150000);rows.append({'reference':r,'old_filled_cache_gap':g,'full_raw_stroke_plus_filled_gap':j,'full_target_pass':not hit,'hit_partners':hit})
 print(r,g['lower_bound_nm'],j['lower_bound_nm'],j['partner'],not hit,flush=True)
assert SHA(S)==s.before
(W/'COURTYARD_SCOPE_AUDIT.json').write_text(json.dumps({'source_sha256':s.before,'scope':'Existing measured fields on exact currently selected source; no CAD edits. Raw courtyard stroke shapes supplement filled cache, not replace interiors.','rows':rows,'board_unchanged':True},indent=2)+'\n')
