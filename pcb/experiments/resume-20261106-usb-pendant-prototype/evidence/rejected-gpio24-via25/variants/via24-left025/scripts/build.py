from screen import *
import shutil,hashlib
plan=json.loads((ROOT/'qa/FROZEN_SCOPE.json').read_text());ds=b.GetDesignSettings();assert ds.m_MaxError==5000,ds.m_MaxError
assert all(z.GetLocalClearance()==200000 for z in b.Zones()if z.GetNetname()=='GND'and z.GetLayer()in[p.In1_Cu,p.In2_Cu])
folder=ROOT/'candidate/pcb';assert not folder.exists();shutil.copytree(SRC.parent,folder);idx={U(q):q for q in b.GetTracks()};added=[]
v=idx[plan['via_uuid']];v.SetPosition(V(*plan['via24_new']));assert v.GetDrillValue()==250000 and all(v.GetWidth(l)==500000 for l in L)
for t in plan['modified_tracks']:
 old=idx[t['uuid']];old.SetEnd(V(*t['retain_to']));q=p.PCB_TRACK(b);q.SetStart(V(*t['retain_to']));q.SetEnd(V(*t['new_end']));q.SetWidth(old.GetWidth());q.SetLayer(old.GetLayer());q.SetNetCode(old.GetNetCode());b.Add(q);added.append(U(q))
code=b.FindNet('EXT_GPIO25').GetNetCode()
for a in plan['gpio25_vias']:
 q=p.PCB_VIA(b);q.SetPosition(V(*a));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu)
 for l in L:q.SetWidth(l,500000)
 q.SetDrill(250000);q.SetNetCode(code);b.Add(q);added.append(U(q));assert all(q.GetWidth(l)==500000 for l in L)and q.GetDrillValue()==250000
for key,l in [('J3',p.B_Cu),('F',p.F_Cu),('B',p.B_Cu)]:
 for a,z in zip(plan[key],plan[key][1:]):
  q=p.PCB_TRACK(b);q.SetStart(V(*a));q.SetEnd(V(*z));q.SetLayer(l);q.SetWidth(150000);q.SetNetCode(code);b.Add(q);added.append(U(q))
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(folder/'maru60.kicad_pcb'),b)
h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();out=dict(source_sha256=h(SRC),candidate_sha256=h(folder/'maru60.kicad_pcb'),modified=[plan['via_uuid']]+plan['retarget_tracks'],added=added);(ROOT/'qa/BUILD.json').write_text(json.dumps(out,indent=2));print(out)
