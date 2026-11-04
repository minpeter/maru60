from pathlib import Path
import hashlib,json,time,pcbnew as p
R=Path('/tmp/v7-connector-gnd-stitch-c770');f=R/'filled/pcb/maru60.kicad_pcb';H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
c=json.loads((R/'BUILD_CONTRACT.json').read_text());assert H(f)==c['prefill_sha256'];b=p.LoadBoard(str(f));ts=list(b.GetTracks());v=next(t for t in ts if t.m_Uuid.AsString()==c['new_via']['uuid'])
assert v.GetClass()=='PCB_VIA' and v.GetNetname()=='GND' and v.GetDrill()==250000 and v.GetViaType()==p.VIATYPE_THROUGH
assert all(v.GetWidth(layer)==500000 for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]);assert [v.GetPosition().x,v.GetPosition().y]==[17200000,9900000]
inv={'tracks':sum(t.GetClass()!='PCB_VIA' for t in ts),'vias':sum(t.GetClass()=='PCB_VIA' for t in ts),'footprints':len(list(b.GetFootprints())),'track_length_mm':sum(t.GetLength()/1e6 for t in ts if t.GetClass()!='PCB_VIA'),'native_version':p.Version()}
assert inv['tracks']==9750 and inv['vias']==919 and inv['footprints']==382
start=time.monotonic();b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(f),b)
r={'status':'UNSELECTED native normal fill complete; full validation pending','prefill_sha256':c['prefill_sha256'],'filled_sha256':H(f),'seconds':time.monotonic()-start,'inventory':inv,'new_via_all_four_native_widths_verified_mm':.5,'construction_API_warning':'SetWidth without layer emitted a diagnostic; actual saved through-via width is independently checked on all four copper layers. The serialized record has ordinary size0.5/drill0.25.'}
(R/'qa/native-fill.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
