import pcbnew as p,json,hashlib,shutil
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu');S=R/'source/pcb';O=R/'repair-D/pcb';assert not O.exists();shutil.copytree(S,O)
B=O/'maru60.kicad_pcb';b=p.LoadBoard(str(B));uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in b.GetTracks()};V=lambda xy:p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6));j=json.load(open('/workspace/shared/maru60-resume/continuation-c782/mcu/qa/north-escape-c-build.json'))
for r in j['modified']:
 q=idx[r['uuid']];assert q.GetNetname()==r['net'];a,c=r['new_start_end'];
 if r['net']=='+1V1':a=[111.28,76.22];r['new_start_end'][0]=a
 if isinstance(q,p.PCB_VIA):q.SetPosition(V(a))
 else:q.SetStart(V(a));q.SetEnd(V(c))
for r in j['added']:
 if r['type']=='through_via' if 'type' in r else False:
  q=p.PCB_VIA(b);q.SetPosition(V(r['pos_mm']));q.SetWidth(p.F_Cu,round(r['diameter_mm']*1e6));q.SetDrill(round(r['drill_mm']*1e6));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu)
 else:
  if r['net']=='+1V1' and r['start_mm']==[111.4,75.7]:r['end_mm']=[111.28,76.22]
  q=p.PCB_TRACK(b);q.SetStart(V(r['start_mm']));q.SetEnd(V(r['end_mm']));q.SetLayer(b.GetLayerID(r['layer']));q.SetWidth(round(r['width_mm']*1e6))
 assert r['uuid'] not in idx;r['uuid']=uid(q);q.SetNet(b.FindNet(r['net']));b.Add(q)
names=lambda:{uid(q):q.GetNetname() for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]};before=names();b.BuildConnectivity();assert before==names();p.ZONE_FILLER(b).Fill(b.Zones());assert before==names();p.SaveBoard(str(B),b)
j.update(source_sha256=hashlib.sha256((S/'maru60.kicad_pcb').read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256(B.read_bytes()).hexdigest(),scope='Isolated partial MCU_GPIO27 launch, bounded COL5 adjustment, and shaped 0.60 mm +1V1 jog. Source 9d787421. Upper jog reaches x111.28 only at y76.22, preserving both original endpoints and all branches. No full MCU pair closed.')
(R/'qa/repair-D-build.json').write_text(json.dumps(j,indent=2));print(j['candidate_sha256'])
