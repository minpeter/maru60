import pcbnew as p,json,hashlib,shutil
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu-led-repair');S=Path('/workspace/shared/maru60-resume/continuation-9d787/mcu/source/pcb');shutil.copytree(S,R/'source/pcb');O=R/'candidate-F/pcb';shutil.copytree(S,O);B=O/'maru60.kicad_pcb';b=p.LoadBoard(str(B));uid=lambda q:q.m_Uuid.AsString();idx={uid(q):q for q in b.GetTracks()};V=lambda a:p.VECTOR2I(round(a[0]*1e6),round(a[1]*1e6));j=json.load(open('/workspace/shared/maru60-resume/continuation-9d787/mcu/qa/repair-E-build.json'));assessment=json.load(open(R/'qa/read-only-assessment.json'));assert assessment['screen_pass']
for a in assessment['proposal']:
 old=a['source'];j['modified'].append({'uuid':old['uuid'],'net':old['net'],'layer':'F.Cu','old_start_end':[old['start_mm'],old['end_mm']],'new_start_end':[a['proposed_start_mm'],a['proposed_end_mm']],'retained_width_mm':.15})
for r in j['modified']:
 q=idx[r['uuid']];assert q.GetNetname()==r['net'];a,c=r['new_start_end']
 if isinstance(q,p.PCB_VIA):q.SetPosition(V(a))
 else:q.SetStart(V(a));q.SetEnd(V(c))
for r in j['added']:
 if r.get('type')=='through_via':
  q=p.PCB_VIA(b);q.SetPosition(V(r['pos_mm']));q.SetWidth(p.F_Cu,round(r['diameter_mm']*1e6));q.SetDrill(round(r['drill_mm']*1e6));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu)
 else:
  q=p.PCB_TRACK(b);q.SetStart(V(r['start_mm']));q.SetEnd(V(r['end_mm']));q.SetWidth(round(r['width_mm']*1e6));q.SetLayer(b.GetLayerID(r['layer']))
 r['uuid']=uid(q);q.SetNet(b.FindNet(r['net']));b.Add(q)
names=lambda:{uid(q):q.GetNetname() for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]};n=names();b.BuildConnectivity();assert names()==n;p.ZONE_FILLER(b).Fill(b.Zones());assert names()==n;p.SaveBoard(str(B),b);j.update(source_sha256=hashlib.sha256((S/'maru60.kicad_pcb').read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256(B.read_bytes()).hexdigest(),scope='One isolated candidate: four LED_FAULT_N F.Cu tracks retargeted around vertices shifted left0.10mm; 0.15mm widths retained; E-shaped0.60mm rail, original endpoint vias and all pad branches retained. Reconstructed from immutable9d787421 plus declared changes, no PCB copied from rejected C/D/E. Partial MCU_GPIO27 launch only, unselected.');(R/'qa/candidate-F-build.json').write_text(json.dumps(j,indent=2));print(j['candidate_sha256'])
