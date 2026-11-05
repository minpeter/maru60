from screen import *
g=json.loads((SRC.parent.parent/'qa/material-graph.json').read_text());idx={U(q):q for q in list(b.GetTracks())+pads};out=[]
for uid in ['cff436d2-a051-486a-8eda-ad80c8687157','bee40e5c-5047-43dd-8262-df42b4062ba6','a18e6e59-fb74-4513-a5f4-6a34d9223429']:
 roots=g['object_material_roots'][uid];rows=[]
 for node,root in g['material_roots'].items():
  if root not in roots:continue
  meta=g['material_nodes'][node];q=idx.get(meta.get('uuid'));r=dict(meta)
  if q:
   r['xy']=[q.GetPosition().x/1e6,q.GetPosition().y/1e6]
   if isinstance(q,p.PCB_TRACK):r['end']=[q.GetEnd().x/1e6,q.GetEnd().y/1e6]
  rows.append(r)
 out.append(dict(pad=uid,roots=roots,nodes=rows))
(ROOT/'qa/target-components.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
