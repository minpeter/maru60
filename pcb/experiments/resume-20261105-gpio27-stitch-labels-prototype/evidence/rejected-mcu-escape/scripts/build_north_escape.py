import pcbnew as p,json,hashlib,shutil,math
from pathlib import Path
R=Path('/workspace/shared/maru60-resume/continuation-c782/mcu');S=R/'source/pcb/maru60.kicad_pcb';O=R/'north-escape/pcb';shutil.copytree(S.parent,O,dirs_exist_ok=True);B=O/'maru60.kicad_pcb';b=p.LoadBoard(str(S));uid=lambda q:q.m_Uuid.AsString();h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();by={uid(q):q for q in b.GetTracks()};V=lambda x,y:p.VECTOR2I(round(x*1e6),round(y*1e6));changes=[]
def mod(u,a,c):
 q=by[u];assert q.GetNetname()=='COL5';old=[[q.GetStart().x/1e6,q.GetStart().y/1e6],[q.GetEnd().x/1e6,q.GetEnd().y/1e6]]
 if isinstance(q,p.PCB_VIA):q.SetPosition(V(*a))
 else:q.SetStart(V(*a));q.SetEnd(V(*c))
 changes.append({'uuid':u,'net':'COL5','layer':b.GetLayerName(q.GetLayer()),'old_start_end':old,'new_start_end':[a,c]})
mod('f44d59d3-0c42-48c1-b89c-540ea6a07763',[112.175,76.3],[112.175,76.3])
mod('224e7239-5039-4cc7-b38b-ca258f485b01',[112.6,77.5],[112.695,77.405])
mod('65c0b9cf-87fb-4ae5-a2e0-e11b853cd699',[112.695,77.405],[112.695,76.7])
mod('d94e477a-28ae-41a9-bdea-441b16be174c',[112.35,76.3],[112.35,73.65])
added=[]
def track(n,l,a,c):
 q=p.PCB_TRACK(b);q.SetStart(V(*a));q.SetEnd(V(*c));q.SetLayer(l);q.SetWidth(150000);q.SetNet(b.FindNet(n));b.Add(q);added.append({'uuid':uid(q),'net':n,'layer':b.GetLayerName(l),'start_mm':a,'end_mm':c,'width_mm':.15});return q
track('COL5',p.B_Cu,[112.695,76.7],[112.175,76.3]);track('COL5',p.In1_Cu,[112.175,76.3],[112.35,76.3]);track('MCU_GPIO27',p.B_Cu,[112.2,78.05],[112.16,77.0]);q=p.PCB_VIA(b);q.SetPosition(V(112.16,77.0));q.SetWidth(p.F_Cu,500000);q.SetDrill(250000);q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);q.SetNet(b.FindNet('MCU_GPIO27'));b.Add(q);added.append({'uuid':uid(q),'net':'MCU_GPIO27','type':'through_via','pos_mm':[112.16,77.0],'diameter_mm':.5,'drill_mm':.25})
names={uid(q):q.GetNetname() for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]};b.BuildConnectivity();assert names=={uid(q):q.GetNetname() for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]};p.ZONE_FILLER(b).Fill(b.Zones());assert names=={uid(q):q.GetNetname() for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]};p.SaveBoard(str(B),b)
r={'source_sha256':h(S),'candidate_sha256':h(B),'modified':changes,'added':added,'scope':'Unselected local COL5 refactor and partial MCU_GPIO27 escape. Full expansion connection remains open; no broad route, component move or rule change.'};(R/'qa/north-escape-build.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
