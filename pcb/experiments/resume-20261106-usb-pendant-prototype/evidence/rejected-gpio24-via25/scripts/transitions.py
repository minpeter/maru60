from screen import *
# Reload the actual saved candidate, not planning objects.
b=p.LoadBoard(str(ROOT/'candidate/pcb/maru60.kicad_pcb'));g=json.loads((ROOT/'qa/material-graph.json').read_text());plan=json.loads((ROOT/'qa/FROZEN_SCOPE.json').read_text());idx={U(q):q for q in b.GetTracks()};grounds=[]
for q in b.GetTracks():
 if not isinstance(q,p.PCB_VIA)or q.GetNetname()!='GND':continue
 roots=set(g['object_material_roots'][U(q)]);members=[u for u,z in g['pad_inventory'].items()if z['net']=='GND' and roots.intersection(g['object_material_roots'][u])];planes=[n for n,r in g['material_roots'].items()if r in roots and g['material_nodes'][n]['kind']=='zone'and g['material_nodes'][n]['layer']in ['In1.Cu','In2.Cu']];grounds.append((q,len(members),planes))
rows=[]
for a in [plan['via24_new']]+plan['gpio25_vias']:
 q=min([q for q in b.GetTracks()if isinstance(q,p.PCB_VIA)],key=lambda q:math.dist(a,(q.GetPosition().x/1e6,q.GetPosition().y/1e6)));near=sorted(grounds,key=lambda z:math.dist(a,(z[0].GetPosition().x/1e6,z[0].GetPosition().y/1e6)))[:3];rows.append(dict(signal_via=U(q),xy=a,net=q.GetNetname(),diameters_nm={b.GetLayerName(l):q.GetWidth(l)for l in L},drill_nm=q.GetDrillValue(),nearest_ground_vias=[dict(uuid=U(z),distance_mm=math.dist(a,(z.GetPosition().x/1e6,z.GetPosition().y/1e6)),xy=[z.GetPosition().x/1e6,z.GetPosition().y/1e6],rooted_ground_pads=n,plane_nodes=planes)for z,n,planes in near]))
for r in rows:assert r['drill_nm']==250000 and all(d==500000 for d in r['diameters_nm'].values())
(ROOT/'qa/transition-return-witnesses.json').write_text(json.dumps(dict(rows=rows,limits='Geometric distance and material-root witnesses only. Not SI, impedance, crosstalk, EMI or return-current qualification.'),indent=2));print(json.dumps(rows,indent=2))
