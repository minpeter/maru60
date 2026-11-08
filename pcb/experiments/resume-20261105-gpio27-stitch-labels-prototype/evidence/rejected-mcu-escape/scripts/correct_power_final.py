import pcbnew as p,json,shutil,hashlib
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-c782/mcu');A=R/'north-escape-b/pcb';O=R/'north-escape-c/pcb';shutil.copytree(A,O,dirs_exist_ok=True);B=O/'maru60.kicad_pcb';b=p.LoadBoard(str(B));uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in b.GetTracks()};V=lambda xy:p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6));j=json.load(open(R/'qa/north-escape-b-build.json'));mid='14d35ed0-d9e6-45a6-a698-4e8b482aba5f';a=[111.28,75.82];c=[111.28,79.2305];idx[mid].SetStart(V(a));idx[mid].SetEnd(V(c))
for r in j['modified']:
 if r['uuid']==mid:r['new_start_end']=[a,c]
for r in j['added']:
 if r['net']!='+1V1':continue
 if r['start_mm']==[111.4,75.7]:r['end_mm']=a
 else:r['start_mm']=c
 idx[r['uuid']].SetStart(V(r['start_mm']));idx[r['uuid']].SetEnd(V(r['end_mm']))
names={uid(q):q.GetNetname() for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]};b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());assert names=={uid(q):q.GetNetname() for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]};p.SaveBoard(str(B),b);j['predecessor_sha256']=j['candidate_sha256'];j['candidate_sha256']=hashlib.sha256(B.read_bytes()).hexdigest();j['scope']='Unselected partial MCU_GPIO27 escape. Final bounded correction shifts one +1V1 middle segment0.12mm left, retaining0.6mm width and both source endpoint vias, to clear the actually observed plane-neck boundary. No MCU open pair closed.';(R/'qa/north-escape-c-build.json').write_text(json.dumps(j,indent=2));print(json.dumps(j,indent=2))
