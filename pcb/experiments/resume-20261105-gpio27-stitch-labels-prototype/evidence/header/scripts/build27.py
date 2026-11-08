from route27open import *
import hashlib,shutil
assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9'
plan=json.loads((ROOT/'qa/plan27open.json').read_text());F=plan['F'];assert F;viaxy=plan['via'];net='EXT_GPIO27';pre={U(q):q.GetNetname()for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]+list(b.Zones())};added=[U(q)for q in detour_added]
for a,z in zip(F,F[1:]):assert edge(net,p.F_Cu,a,z),(a,z)
assert edge(net,p.B_Cu,(96.5,39),viaxy)and viaok(net,viaxy)
for path,l in [([(96.5,39),viaxy],p.B_Cu),(F,p.F_Cu)]:
 for a,z in zip(path,path[1:]):
  q=p.PCB_TRACK(b);q.SetStart(V(*a));q.SetEnd(V(*z));q.SetWidth(W);q.SetLayer(l);q.SetNetCode(b.FindNet(net).GetNetCode());b.Add(q);added.append(U(q))
q=p.PCB_VIA(b);q.SetPosition(V(*viaxy));q.SetWidth(p.F_Cu,500000);q.SetDrill(250000);q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);q.SetNetCode(b.FindNet(net).GetNetCode());b.Add(q);added.append(U(q))
names=lambda:{U(q):q.GetNetname()for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]+list(b.Zones())}
b.BuildConnectivity();post=names();assert all(post[k]==v for k,v in pre.items());p.ZONE_FILLER(b).Fill(b.Zones());post=names();assert all(post[k]==v for k,v in pre.items());D=ROOT/'trial27/pcb';assert not D.exists();shutil.copytree(SRC.parent,D);p.SaveBoard(str(D/'maru60.kicad_pcb'),b)
plan.update({'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((D/'maru60.kicad_pcb').read_bytes()).hexdigest(),'added_uuids':added,'new_GPIO27_uuids':added[len(detour_added):],'new_EXT_GPIO10_uuids':[U(q)for q in detour_added],'modified_source_uuids':sorted({barrier_uuid,U(shifted_via)}|{x[0]for x in retargeted+raised_joint}),'native_names_stable':True});(ROOT/'qa/BUILD.json').write_text(json.dumps(plan,indent=2));print(json.dumps(plan,indent=2))
