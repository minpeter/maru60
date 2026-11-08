from screen import *
N='EXT_GPIO25';removed=[]
for q in list(b.GetTracks()):
 if isinstance(q,p.PCB_VIA)or q.GetNetname()!='GPIO_ISOLATE'or q.GetLayer()!=p.B_Cu:continue
 a,z=q.GetStart(),q.GetEnd()
 if min(a.y,z.y)>=35050000 and max(a.y,z.y)<=41500000 and min(a.x,z.x)>=108100000 and max(a.x,z.x)<=109300000:removed.append(q)
ids={U(q)for q in removed};g=json.loads((SRC.parent.parent/'qa/material-graph.json').read_text());contacts=[]
for a,z,raw,guard in g['material_edges']:
 aa=g['material_nodes'][a].get('uuid');zz=g['material_nodes'][z].get('uuid')
 if (aa in ids)!=(zz in ids):contacts.append(dict(a=a,z=z,raw=raw,guard=guard))
out={'scope':[{'uuid':U(q),'start':[q.GetStart().x/1e6,q.GetStart().y/1e6],'end':[q.GetEnd().x/1e6,q.GetEnd().y/1e6]}for q in removed],'contacts':contacts}
(ROOT/'qa/joint-scope.json').write_text(json.dumps(out,indent=2))
# Optimistic reachability is diagnostic only; never save or call it a complete candidate.
for l in bins:
 for k in bins[l]:bins[l][k]=[key for key in bins[l][k]if key[0]not in ids]
path=search(N,p.B_Cu,(98.15,40.6),goal=(107.1,37.325),box=(95.5,34,110,44),step=.025)
out['GPIO25_B_diagnostic']=path
if path:
 added=[]
 for a,z in zip(path,path[1:]):
  q=p.PCB_TRACK(b);q.SetStart(V(*a));q.SetEnd(V(*z));q.SetWidth(150000);q.SetLayer(p.B_Cu);q.SetNetCode(b.FindNet(N).GetNetCode());added.append(q);addobs(q)
 # Bounded to original side, x <=109.3; retained COL5/GPIO3 copper is still an obstacle.
 iso=search('GPIO_ISOLATE',p.B_Cu,(108.1,35.05),goal=(109.3,41.5),box=(101,33,109.3,43),step=.025)
 out['restored_GPIO_ISOLATE']=iso
 if iso:
  for a,z in zip(iso,iso[1:]):assert edge('GPIO_ISOLATE',p.B_Cu,a,z)
else:out['restored_GPIO_ISOLATE']=None
(ROOT/'qa/joint-plan.json').write_text(json.dumps(out,indent=2));print('SCOPE',len(ids),'CONTACTS',contacts,'PLAN',path,'RESTORED',out['restored_GPIO_ISOLATE'],flush=True)
