import sys,json,hashlib,shutil,time
from pathlib import Path
sys.path.insert(0,'/workspace/shared/maru60-resume/tools');from sexpr_spans import children,head,field
import pcbnew as p,re
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu');A=R/'source/pcb';B=R/'repair-D/pcb';h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();build=json.load(open(R/'qa/repair-D-build.json'));declared={r['uuid'] for r in build['modified']}
def topids(path):
 d={}
 for _,_,s in children(path.read_text()):
  f=field(s,'uuid')
  if f:d[json.loads(re.search(r'"[^"]+"',f).group())]=s
 return d
old=topids(A/'maru60.kicad_pcb');new=topids(B/'maru60.kicad_pcb');modified=[{'uuid':u,'type':head(s)} for u,s in old.items() if new.get(u)!=s];unexpected=[x for x in modified if x['type']!='zone' and x['uuid'] not in declared];assert not unexpected
companions=[f for f in A.rglob('*') if f.is_file() and f.name!='maru60.kicad_pcb'];assert all(h(f)==h(B/f.relative_to(A)) for f in companions)
b=p.LoadBoard(str(B/'maru60.kicad_pcb'));uid=lambda q:q.m_Uuid.AsString();names=lambda b:{uid(q):q.GetNetname() for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]}
counts={'tracks':sum(not isinstance(q,p.PCB_VIA) for q in b.GetTracks()),'vias':sum(isinstance(q,p.PCB_VIA) for q in b.GetTracks()),'footprints':len(list(b.GetFootprints())),'track_length_mm':sum(q.GetLength()/1e6 for q in b.GetTracks() if not isinstance(q,p.PCB_VIA))}
shutil.copytree(B,R/'cold-c/pcb',dirs_exist_ok=True);C=R/'cold-c/pcb/maru60.kicad_pcb';c=p.LoadBoard(str(C));before=h(C);nn=names(c);t=time.monotonic();c.BuildConnectivity();p.ZONE_FILLER(c).Fill(c.Zones());assert names(c)==nn;p.SaveBoard(str(C),c);cr={'before_sha256':before,'after_sha256':h(C),'byte_identical':before==h(C),'seconds':time.monotonic()-t};assert cr['byte_identical']
r={'source_sha256':h(A/'maru60.kicad_pcb'),'candidate_sha256':h(B/'maru60.kicad_pcb'),'declared_changed_source_objects':sorted(declared),'modified_raw_nodes':modified,'unexpected_changes':unexpected,'all_old_uuids_preserved':set(old)<=set(new),'all_57_companions_exact':len(companions)==57,'counts':counts,'cold_refill':cr};(R/'qa/repair-D-native-checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
