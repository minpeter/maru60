#!/usr/bin/env python3
"""Plan exact duplicate, floating component, and native dangling-via removal.

Run with KiCad Python. This does not modify CAD. A new DRC/connectivity check is
required after applying; source reports must describe the input board.
"""
import argparse,json
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('board',type=Path);ap.add_argument('drc',type=Path);ap.add_argument('components',type=Path);ap.add_argument('output',type=Path)
a=ap.parse_args();b=p.LoadBoard(str(a.board));d=json.loads(a.drc.read_text());components=json.loads(a.components.read_text())
critical=lambda n:n.startswith(('USB_DP','USB_DM','QSPI_','VREG_')) or n in ('XIN','XOUT','XTAL_OUT','+1V1')
items=list(b.GetTracks());index={q.m_Uuid.AsString():q for q in items};remove=set();reasons={};seen={}
def mark(uid,why):
 if uid not in index:raise ValueError('stale report UUID '+uid)
 if critical(index[uid].GetNetname()):raise ValueError('refusing to remove critical copper '+uid)
 remove.add(uid);reasons.setdefault(uid,[]).append(why)
for entry in components:
 for group in entry['members']:
  if group and not any(item['kind'] in ('pad','zone') for item in group):
   for item in group:mark(item['uuid'],'native component has no pad or zone')
for q in items:
 if q.Type()!=p.PCB_TRACE_T or critical(q.GetNetname()):continue
 endpoints=tuple(sorted([(q.GetStart().x,q.GetStart().y),(q.GetEnd().x,q.GetEnd().y)]))
 key=(q.GetNetname(),q.GetLayer(),q.GetWidth(),endpoints)
 uid=q.m_Uuid.AsString()
 if key in seen:mark(uid,'exact duplicate track')
 else:seen[key]=uid
for v in d['violations']:
 if v['type']=='via_dangling':mark(v['items'][0]['uuid'],'native dangling via')
# Strip whole pendant chains in one plan. Stop at every pad, retained via,
# zone contact or branch junction. This preserves connected circuitry and
# avoids dozens of refill/DRC rounds for a long chain of obsolete segments.
b.BuildConnectivity();cn=b.GetConnectivity()
trace_ids={uid for uid,q in index.items() if q.Type()==p.PCB_TRACE_T}
adj={uid:set() for uid in trace_ids};anchors=set();queue=[]
for uid in trace_ids:
 q=index[uid]
 for neighbor in cn.GetConnectedTracks(q):
  other=neighbor.m_Uuid.AsString()
  if other==uid:continue
  if other in trace_ids:adj[uid].add(other)
  elif other not in remove:anchors.add(uid)
  elif other in remove:queue.append(uid)
 if list(cn.GetConnectedPads(q)):anchors.add(uid)
for z in b.Zones():
 anchors.update(q.m_Uuid.AsString() for q in cn.GetConnectedTracks(z) if q.m_Uuid.AsString() in trace_ids)
queue.extend(v['items'][0]['uuid'] for v in d['violations'] if v['type']=='track_dangling')
queue.extend(other for uid in remove if uid in adj for other in adj[uid])
while queue:
 uid=queue.pop()
 if uid in remove or uid in anchors or uid not in adj or critical(index[uid].GetNetname()):continue
 neighbors=adj[uid]-remove
 if len(neighbors)>1:continue
 mark(uid,'pendant trace chain without a pad/via/zone anchor')
 queue.extend(neighbors)
tracks=[];vias=[]
for uid in sorted(remove):
 q=index[uid]
 if q.Type()==p.PCB_TRACE_T:tracks.append(uid)
 elif q.Type()==p.PCB_VIA_T:vias.append(dict(x=p.ToMM(q.GetPosition().x),y=p.ToMM(q.GetPosition().y),net=q.GetNetname()))
 else:raise ValueError('unsupported cleanup item')
out={'status':'removal plan; native validation required','ops':[{'op':'remove_track_uuids','uuids':tracks},{'op':'remove_vias','vias':vias}],'reasons':reasons}
a.output.write_text(json.dumps(out,indent=2)+'\n');print('planned removal',len(tracks),'tracks and',len(vias),'vias')
