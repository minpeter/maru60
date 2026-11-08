from pathlib import Path
import json,pcbnew as p,hashlib
R=Path('/workspace/shared/maru60-resume');S=R/'continuation-c782/combined27fix2';D=R/'continuation-9d787/stub4v';x=json.loads((S/'qa/material-graph.json').read_text());b=p.LoadBoard(str(S/'pcb/maru60.kicad_pcb'));ix={q.m_Uuid.AsString():q for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]};u='83c3c335-9252-48a7-a6b9-33be2a34353e';ns=[n for n,v in x['material_nodes'].items()if v.get('uuid')==u];edges=[e for e in x['material_edges']if e[0]in ns or e[1]in ns];print(json.dumps(edges,indent=2));ids={x['material_nodes'][n].get('uuid')for e in edges for n in e[:2]};
for uid in ids:
 q=ix.get(uid)
 if q: print(uid,type(q).__name__,q.GetNetname(),b.GetLayerName(q.GetLayer()),'pos',q.GetPosition(),'start',q.GetStart()if hasattr(q,'GetStart')else'', 'end',q.GetEnd()if hasattr(q,'GetEnd')else'', 'pad',q.GetParentFootprint().GetReference()if isinstance(q,p.PAD)else'')
