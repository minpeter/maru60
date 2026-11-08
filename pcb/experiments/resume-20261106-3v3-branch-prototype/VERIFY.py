"""Recheck the frozen candidate without modifying its CAD. Use Python with pcbnew.
Optional --material recomputes the corrected material graph (several minutes).
These are nominal CAD checks, not fabrication or active stability approval.
"""
from pathlib import Path
import argparse, tempfile, os, subprocess, sys, json, hashlib, shutil, collections
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--material',action='store_true');args=ap.parse_args()
O=Path(tempfile.mkdtemp(prefix='verification-',dir=P));env=os.environ.copy()
for var,name in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data'),('XDG_STATE_HOME','state'),('XDG_RUNTIME_DIR','runtime'),('TMPDIR','tmp')]:
 q=O/name;q.mkdir(mode=0o700);env[var]=str(q)
env['QT_QPA_PLATFORM']='offscreen';os.environ.update(env)
import pcbnew as p
assert p.GetBuildVersion()=='9.0.2+dfsg-1','This exact evidence set uses KiCad9.0.2+dfsg-1. Re-review version changes rather than bypassing this guard.'
H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();BP=P/'pcb/maru60.kicad_pcb';expected='88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e';assert H(BP)==expected
T=P/'portable-tools'
def run(name,cmd):
 with(O/(name+'.log')).open('w')as log:subprocess.run([str(c)for c in cmd],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
run('drc',['kicad-cli','pcb','drc','--format','json','--schematic-parity','-o',O/'drc.json',BP]);run('erc',['kicad-cli','sch','erc','--format','json','-o',O/'erc.json',P/'pcb/maru60.kicad_sch'])
d=json.loads((O/'drc.json').read_text());f=json.loads((P/'qa/drc.json').read_text());assert len(d['unconnected_items'])==9 and not d['schematic_parity'];assert collections.Counter(json.dumps(x,sort_keys=True)for x in d['violations'])==collections.Counter(json.dumps(x,sort_keys=True)for x in f['violations']);erc=json.loads((O/'erc.json').read_text());assert not any(s.get('violations')for s in erc['sheets'])
run('net-identity',[sys.executable,T/'verify_net_identity.py',BP,T/'netlist.xml',O/'net-identity.json'])
C=O/'cold/pcb';shutil.copytree(P/'pcb',C);before={str(f.relative_to(C)):H(f)for f in C.rglob('*')if f.is_file()};b=p.LoadBoard(str(C/'maru60.kicad_pcb'));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(C/'maru60.kicad_pcb'),b);after={str(f.relative_to(C)):H(f)for f in C.rglob('*')if f.is_file()};assert before==after and len(before)==58
result={'candidate_sha256':expected,'native_DRC_open_pairs':9,'native_DRC_warnings':39,'ERC':0,'schematic_parity':0,'all58_cold_files_byte_identical':True,'raw_native_pin_identity':True,'material_recomputed':False,'qualification':'Nominal CAD checks only. Prior strict exact-no-loss failure remains; no active stability, SI, physical or manufacturing qualification.'}
if args.material:
 run('material-graph',[sys.executable,T/'export_material_graph.py',BP,O/'material-graph.json']);new=json.loads((O/'material-graph.json').read_text());old=json.loads((P/'qa/material-graph.json').read_text());assert new['pad_inventory']==old['pad_inventory']and new['pad_partitions_by_net']==old['pad_partitions_by_net'];de=lambda g:{(x,y,l):a for x,y,ls in g['direct_edges']for l,a in ls};ze=lambda g:{(z,u):a for z,u,a in g['zone_edges']};assert de(new)==de(old)and ze(new)==ze(old);assert new['guard_failing_material_edges']==old['guard_failing_material_edges']
 def pairs(g,dr):
  rp=collections.defaultdict(list)
  for u in g['pad_inventory']:
   rs=g['object_material_roots'][u];assert len(rs)==1;rp[rs[0]].append(u)
  out=[]
  for row in dr['unconnected_items']:
   components=[]
   for e in row['items']:
    rs=g['object_material_roots'][e['uuid']];assert len(rs)==1 and rp[rs[0]];components.append(tuple(sorted(rp[rs[0]])))
   assert len(set(components))==2;out.append(tuple(sorted(components)))
  return collections.Counter(out)
 assert pairs(new,d)==pairs(old,f);result['material_recomputed']=True;result['all9_physical_open_component_pairs_match']=True
assert H(BP)==expected;(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));print('Evidence:',O)
