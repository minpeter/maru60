import pcbnew as p,json,hashlib,shutil
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu');O=R/'repair-E/pcb';assert not O.exists();shutil.copytree(R/'repair-D/pcb',O);B=O/'maru60.kicad_pcb';b=p.LoadBoard(str(B));uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in b.GetTracks()};V=lambda xy:p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6));j=json.load(open(R/'qa/repair-D-build.json'));pt=[111.28,76.17]
for r in j['modified']:
 if r['net']=='+1V1':r['new_start_end'][0]=pt;idx[r['uuid']].SetStart(V(pt))
for r in j['added']:
 if r['net']=='+1V1' and r['start_mm']==[111.4,75.7]:r['end_mm']=pt;idx[r['uuid']].SetEnd(V(pt))
names=lambda:{uid(q):q.GetNetname() for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]};n=names();b.BuildConnectivity();assert n==names();p.ZONE_FILLER(b).Fill(b.Zones());assert n==names();p.SaveBoard(str(B),b);j['predecessor_sha256']=j['candidate_sha256'];j['candidate_sha256']=hashlib.sha256(B.read_bytes()).hexdigest();j['scope']='Final bounded shaped-rail variant: upper 0.60 mm jog (111.4,75.7) to (111.28,76.17); original endpoint vias/branches retained. Local COL5 adjustment and partial MCU_GPIO27 escape only. No full pair closed.';(R/'qa/repair-E-build.json').write_text(json.dumps(j,indent=2));print(j['candidate_sha256'])
