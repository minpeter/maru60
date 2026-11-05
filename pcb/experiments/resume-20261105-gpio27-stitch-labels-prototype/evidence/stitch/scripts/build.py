from pathlib import Path
import sys,shutil,hashlib,json
import pcbnew as p
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-c782/stitch';S=R/'combined-trial/pcb';C=D/'pcb';H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert H(S/'maru60.kicad_pcb')=='56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9'
assert not C.exists();shutil.copytree(S,C);f=C/'maru60.kicad_pcb';b=p.LoadBoard(str(f));v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(105650000,36050000));v.SetWidth(500000);v.SetDrill(250000);v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v);p.SaveBoard(str(D/'prefill.kicad_pcb'),b)
names=lambda:{x.m_Uuid.AsString():x.GetNetname()for x in list(b.GetTracks())+[q for fp in b.GetFootprints()for q in fp.Pads()]};ns=names();b.BuildConnectivity();assert names()==ns;p.ZONE_FILLER(b).Fill(b.Zones());assert names()==ns;p.SaveBoard(str(f),b)
r=dict(source_sha256=H(S/'maru60.kicad_pcb'),candidate_sha256=H(f),via_uuid=v.m_Uuid.AsString(),position_mm=[105.65,36.05],diameter_mm=.5,drill_mm=.25,net='GND',names_stable=True);(D/'qa/build.json').write_text(json.dumps(r,indent=2));print(r)
