from pathlib import Path
import json,heapq,collections,pcbnew as p
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-fa96a7c/usb-stub';S=R/'selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype';layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
def capture(folder):
 b=p.LoadBoard(str(folder/'pcb/maru60.kicad_pcb'));out={}
 for net,pairs in {'USB_DM_CONN':[(('J1','A7'),('R103','1')),(('J1','B7'),('R103','1'))], 'USB_DP_CONN':[(('J1','A6'),('R102','1')),(('J1','B6'),('R102','1'))], 'USB_DM':[(('R103','2'),('U1','51'))], 'USB_DP':[(('R102','2'),('U1','52'))]}.items():
  adj=collections.defaultdict(list);tracks=[q for q in b.GetTracks()if q.GetNetname()==net]
  def node(v,l):return(v.x,v.y,l)
  def edge(a,c,w,u):adj[a].append((c,w,u));adj[c].append((a,w,u))
  for q in tracks:
   if isinstance(q,p.PCB_VIA):
    ns=[node(q.GetPosition(),l)for l in layers if q.IsOnLayer(l)]
    for a,c in zip(ns,ns[1:]):edge(a,c,0,q.m_Uuid.AsString())
   else:edge(node(q.GetStart(),q.GetLayer()),node(q.GetEnd(),q.GetLayer()),q.GetLength()/1e6,q.m_Uuid.AsString())
  pads={(f.GetReference(),q.GetNumber()):q for f in b.GetFootprints()for q in f.Pads()if q.GetNetname()==net}
  for start,end in pairs:
   starts=[node(pads[start].GetPosition(),l)for l in layers if pads[start].IsOnLayer(l) and node(pads[start].GetPosition(),l)in adj];ends={node(pads[end].GetPosition(),l)for l in layers if pads[end].IsOnLayer(l) and node(pads[end].GetPosition(),l)in adj}
   assert starts and ends,(net,start,end,starts,ends)
   todo=[(0,n,[])for n in starts];heapq.heapify(todo);seen=set();found=None
   while todo:
    dist,n,path=heapq.heappop(todo)
    if n in seen:continue
    seen.add(n)
    if n in ends:found=(dist,path);break
    for other,w,u in adj[n]:
     if other not in seen:heapq.heappush(todo,(dist+w,other,path+[u]))
   assert found,(net,start,end)
   uu=list(dict.fromkeys(found[1]));ii={q.m_Uuid.AsString():q for q in tracks};out[net+':'+'.'.join(start)+'-'+'.'.join(end)]={'length_mm':found[0],'trace_uuids':[u for u in uu if not isinstance(ii[u],p.PCB_VIA)],'via_uuids':[u for u in uu if isinstance(ii[u],p.PCB_VIA)],'widths_mm':sorted({ii[u].GetWidth()/1e6 for u in uu if not isinstance(ii[u],p.PCB_VIA)})}
 return out
a=capture(S);b=capture(D);assert a==b;assert all('b04e3a6d-1e98-43d1-9b10-58c23321ca28'not in v['trace_uuids']for v in a.values());res={'before':a,'after':b,'exact_equal':True,'method':'Shortest centerline graph with exact integer coincident endpoints; pads at exact graph endpoints; via transitions have zero lateral length. Not electromagnetic delay or actual 3D trace length. Material graph separately proves contacts.'};(D/'qa/active-paths.json').write_text(json.dumps(res,indent=2));print({k:v['length_mm']for k,v in a.items()})
