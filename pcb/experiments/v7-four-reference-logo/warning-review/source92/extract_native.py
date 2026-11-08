from pathlib import Path
import os,json,hashlib
root=Path(__file__).resolve().parent
for k in ['HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','XDG_RUNTIME_DIR']:
 d=root/'runtime'/k;d.mkdir(mode=0o700,parents=True,exist_ok=True);os.environ[k]=str(d)
import pcbnew as p
src=root.parent/'pcb-v7-recovery-20261104/pcb/experiments/v7-reference-legibility/candidate/pcb/maru60.kicad_pcb';h=hashlib.sha256(src.read_bytes()).hexdigest();assert h=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1';b=p.LoadBoard(str(src));b.BuildConnectivity();c=b.GetConnectivity();by={t.m_Uuid.AsString():t for t in b.GetTracks()};d=json.loads((src.parents[2]/'qa/recovery-native/drc.json').read_text())
def track(t):
 t=by.get(t.m_Uuid.AsString(),t)
 return {'uuid':t.m_Uuid.AsString(),'kind':'via'if isinstance(t,p.PCB_VIA)else 'track','net':t.GetNetname(),'layer':b.GetLayerName(t.GetLayer()),'a_mm':[t.GetStart().x/1e6,t.GetStart().y/1e6],'b_mm':[t.GetEnd().x/1e6,t.GetEnd().y/1e6],'width_mm':(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())/1e6,'length_mm':t.GetLength()/1e6,'drill_mm':t.GetDrillValue()/1e6 if isinstance(t,p.PCB_VIA)else None}
rows=[]
for v in d['violations']:
 if v['type']not in ['track_dangling','via_dangling']:continue
 t=by[v['items'][0]['uuid']];row=track(t);row.update(warning_type=v['type'],connected_tracks=[track(x)for x in c.GetConnectedTracks(t)],connected_pads=[{'uuid':x.m_Uuid.AsString(),'ref':x.GetParentFootprint().GetReference(),'pin':x.GetNumber(),'net':x.GetNetname()}for x in c.GetConnectedPads(t)]);rows.append(row)
assert len(rows)==7
out={'board_sha256':h,'native_version':p.Version(),'scope':'Read-only native immediate track/pad contacts. No refill, save, complete geometric graph or stability/return-current claim.','rows':rows,'source_unchanged':hashlib.sha256(src.read_bytes()).hexdigest()==h};(root/'native-dangling-contacts.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'rows':[{k:r[k]for k in ['uuid','net','warning_type','length_mm']}|{'connected_tracks':len(r['connected_tracks']),'connected_pads':len(r['connected_pads'])}for r in rows],'source_unchanged':out['source_unchanged']},indent=2))
