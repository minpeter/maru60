from screen_rules import *
g=json.loads((SRC.parent.parent/'qa/material-graph.json').read_text());uid='79e90551-63f2-4d3a-82a7-9d5d6259c3d6';idx={U(q):q for q in list(b.GetTracks())+pads};edges=[]
for a,z,raw,guard in g['material_edges']:
 aa=g['material_nodes'][a].get('uuid');zz=g['material_nodes'][z].get('uuid')
 if uid not in [aa,zz] or aa==zz:continue
 other=zz if aa==uid else aa;q=idx.get(other);r=dict(a=a,z=z,raw_mm2=raw,guarded_mm2=guard)
 if q:
  r.update(other_uuid=other,type=q.GetClass(),net=q.GetNetname(),xy=[q.GetPosition().x/1e6,q.GetPosition().y/1e6])
  if isinstance(q,p.PCB_TRACK):r['end']=[q.GetEnd().x/1e6,q.GetEnd().y/1e6]
 edges.append(r)
roots=set(g['object_material_roots'][uid]);members=[dict(uuid=u,**d)for u,d in g['pad_inventory'].items()if roots.intersection(g['object_material_roots'][u])];out=dict(via=uid,pad_members=members,contacts=edges);(ROOT/'qa/via24-contacts.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
