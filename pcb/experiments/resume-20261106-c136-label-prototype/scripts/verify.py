from pathlib import Path
import json,hashlib,sys,collections,subprocess,shutil
import pcbnew as p
sys.path.insert(0,'/workspace/shared/maru60-resume/tools');import sexpr_spans as x
D=Path(__file__).resolve().parents[1];S=D.parent/'combined27fix2';B=D/'pcb/maru60.kicad_pcb';H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert p.GetBuildVersion()=='9.0.2+dfsg-1'
a=(S/'pcb/maru60.kicad_pcb').read_text();b=B.read_text();build=json.loads((D/'qa/build.json').read_text());assert b.count(build['new_form'])==1 and b.replace(build['new_form'],build['old_form'],1)==a
assert H(B)==build['candidate_sha256']
files={str(f.relative_to(D/'pcb')):H(f)for f in (D/'pcb').rglob('*')if f.is_file()};old={str(f.relative_to(S/'pcb')):H(f)for f in (S/'pcb').rglob('*')if f.is_file()};assert len(files)==len(old)==58
assert {k:v for k,v in files.items()if k!='maru60.kicad_pcb'}=={k:v for k,v in old.items()if k!='maru60.kicad_pcb'}
# Reversal of this single Reference form proves ALL electrical objects, fills and rules byte exact.
g=json.loads((S/'qa/material-graph.json').read_text());d=json.loads((D/'qa/drc.json').read_text());f=json.loads((S/'qa/drc.json').read_text())
def pairs(dr):
 rp=collections.defaultdict(list)
 for u in g['pad_inventory']:
  rs=g['object_material_roots'][u];assert len(rs)==1;rp[rs[0]].append(u)
 out=[]
 for row in dr['unconnected_items']:
  cs=[]
  for e in row['items']:
   rs=g['object_material_roots'][e['uuid']];assert len(rs)==1 and rp[rs[0]];cs.append(tuple(sorted(rp[rs[0]])))
  assert len(set(cs))==2;out.append(tuple(sorted(cs)))
 return collections.Counter(out)
assert pairs(d)==pairs(f) and len(d['unconnected_items'])==9
ca=collections.Counter(json.dumps(x,sort_keys=True)for x in f['violations']);cb=collections.Counter(json.dumps(x,sort_keys=True)for x in d['violations']);assert not(cb-ca) and len(d['violations'])==40 and not d['schematic_parity'] and all(v['severity']=='warning' for v in d['violations'])
subprocess.run([sys.executable,str(D/'portable-tools/verify_net_identity.py'),str(B),str(D/'portable-tools/netlist.xml'),str(D/'qa/net-identity.json')],check=True)
C=D/'cold/pcb';shutil.copytree(D/'pcb',C);board=p.LoadBoard(str(C/'maru60.kicad_pcb'));board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones());p.SaveBoard(str(C/'maru60.kicad_pcb'),board);assert files=={str(q.relative_to(C)):H(q)for q in C.rglob('*')if q.is_file()}
result={'candidate_sha256':H(B),'changed_reference_fields':['C136'],'raw_reference_reversal_exact':True,'all57_companions_exact':True,'all58_cold_exact':True,'warnings':40,'open_pairs':9,'parity':0,'pin_net_identity':True,'material_evidence':'Inherited from exact combined27fix2 graph, not freshly recomputed. Raw reversal proves all electrical/fill forms byte exact.','semantic_physical_open_pair_preservation':True,'no_physical_visibility_or_fabrication_qualification':True}
(D/'qa/verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
