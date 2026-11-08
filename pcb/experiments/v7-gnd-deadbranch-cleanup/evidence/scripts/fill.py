from pathlib import Path
import hashlib,json,time,pcbnew as p
R=Path('/tmp/v7-gnd-tail-cleanup-aead'); f=R/'filled/pcb/maru60.kicad_pcb'
H=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
c=json.loads((R/'BUILD_CONTRACT.json').read_text());assert H(f)==c['prefill_sha256'];assert p.Version()=='9.0.2'
b=p.LoadBoard(str(f)); ts=list(b.GetTracks()); assert not any(t.m_Uuid.AsString() in c['retired_uuids'] for t in ts)
inv={'tracks':sum(t.GetClass()!='PCB_VIA' for t in ts),'vias':sum(t.GetClass()=='PCB_VIA' for t in ts),'footprints':len(list(b.GetFootprints())),'track_length_mm':sum(t.GetLength()/1e6 for t in ts if t.GetClass()!='PCB_VIA'),'native_version':p.Version()}
assert inv['tracks']==9750 and inv['vias']==918 and inv['footprints']==382
start=time.monotonic();b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(f),b)
r={'status':'UNSELECTED normal refill complete; validation pending','prefill_sha256':c['prefill_sha256'],'filled_sha256':H(f),'seconds':time.monotonic()-start,'zones':len(b.Zones()),'inventory':inv}
(R/'qa/native-fill.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
