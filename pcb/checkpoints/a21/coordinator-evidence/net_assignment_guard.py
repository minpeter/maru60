"""Fail-closed raw/native net-name guard. Never repairs assignments or saves CAD.
Usage: /usr/bin/python3 net_assignment_guard.py board.kicad_pcb report.json [--refill]
"""
import os,sys,json,hashlib
from pathlib import Path
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-kicad-config'
import pcbnew as p
sys.path.insert(0,'/workspace/shared/maru60-kicad-linux/pcb/tools')
import sexp as s
B=Path(sys.argv[1]);O=Path(sys.argv[2]);pro=B.with_suffix('.kicad_pro');sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();bh=sha(B);ph=sha(pro)
r=s.parse(B.read_text());net={int(q[1]):str(q[2])for q in r if isinstance(q,list) and q and q[0]=='net'};net.setdefault(0,'')
uuid=lambda q:str(s.get(q,'uuid')[1]);expected={};kind={}
for q in r:
 if not isinstance(q,list) or not q:continue
 if q[0] in ['segment','arc','via','zone']:
  n=s.get(q,'net');expected[uuid(q)]=net[int(n[1])] if n else '';kind[uuid(q)]=str(q[0])
 if q[0]=='footprint':
  for a in q:
   if isinstance(a,list) and a and a[0]=='pad':
    n=s.get(a,'net');expected[uuid(a)]=net[int(n[1])] if n else '';kind[uuid(a)]='pad'
steps=[]
def check(label,b):
 actual={x.m_Uuid.AsString():str(x.GetNetname())for x in list(b.GetTracks())+list(b.Zones())}
 for f in b.GetFootprints():
  for q in f.Pads():actual[q.m_Uuid.AsString()]=str(q.GetNetname())
 missing=sorted(set(expected)-set(actual));extra=sorted(set(actual)-set(expected));delta=[{'uuid':u,'kind':kind[u],'intended_net':expected[u],'actual_net':actual[u]}for u in sorted(set(actual)&set(expected))if actual[u]!=expected[u]]
 state={'stage':label,'object_count':len(actual),'mismatches':delta,'missing_uuids':missing,'unexpected_uuids':extra,'pcb_hash_unchanged':sha(B)==bh,'project_hash_unchanged':sha(pro)==ph};steps.append(state)
 out={'source_pcb':str(B),'pcb_sha256':bh,'project_sha256':ph,'raw_expected_net_names':expected,'steps':steps,'pass':not any(x['mismatches']or x['missing_uuids']or x['unexpected_uuids']or not x['pcb_hash_unchanged']or not x['project_hash_unchanged']for x in steps),'scope':'Exact per-UUID semantic net-name assignment including pads, tracks, vias, arcs, zones. This does not substitute physical short/source/refill/reference/DRC/assembly checks. No net repair or SaveBoard.'};O.write_text(json.dumps(out,indent=2));assert out['pass'],f'{label}: assignment/hash failure; see {O}'
b=p.LoadBoard(str(B));check('after_LoadBoard',b);b.BuildConnectivity();check('after_BuildConnectivity',b)
if '--refill' in sys.argv[3:]:p.ZONE_FILLER(b).Fill(b.Zones());check('after_in_memory_refill',b)
print(json.dumps({'board':str(B),'objects':len(expected),'stages':[x['stage']for x in steps],'pass':True}))
