from screen import *
plan=json.loads((ROOT/'qa/PLAN.json').read_text());idx={U(q):q for q in b.GetTracks()};v=idx[plan['via_uuid']];print('RULES',b.GetDesignSettings().m_MinClearance,b.GetDesignSettings().m_TrackMinWidth,flush=True)
for z in b.Zones():
 if z.GetNetname()=='GND':print('ZONE',z.GetLayer(),z.GetLocalClearance(),z.GetMinThickness(),flush=True)
ids=[plan['via_uuid']]+plan['retarget_tracks'];joints=[(105.51,37.6),(105.99,37.26)]
for l in bins:
 for k in bins[l]:bins[l][k]=[key for key in bins[l][k]if key[0]not in ids]
keep=[];tracks=[]
for t,joint in zip(plan['retarget_tracks'],joints):
 old=idx[t];a=(old.GetStart().x/1e6,old.GetStart().y/1e6);z=(old.GetEnd().x/1e6,old.GetEnd().y/1e6);assert abs((joint[0]-a[0])*(z[1]-a[1])-(joint[1]-a[1])*(z[0]-a[0]))<1e-10
 for aa,zz in [(a,joint),(joint,plan['via24_new'])]:
  assert edge('EXT_GPIO24',old.GetLayer(),aa,zz,old.GetWidth())
  q=p.PCB_TRACK(b);q.SetStart(V(*aa));q.SetEnd(V(*zz));q.SetWidth(old.GetWidth());q.SetLayer(old.GetLayer());q.SetNetCode(old.GetNetCode());keep.append(q);addobs(q)
 tracks.append(dict(uuid=t,start=a,old_end=z,retain_to=joint,new_end=plan['via24_new'],width_nm=old.GetWidth(),layer=b.GetLayerName(old.GetLayer())))
q=v.Duplicate();q.SetPosition(V(*plan['via24_new']));keep.append(q);addobs(q)
for name,l in [('J3',p.B_Cu),('F',p.F_Cu),('B',p.B_Cu)]:
 for a,z in zip(plan[name],plan[name][1:]):assert edge('EXT_GPIO25',l,a,z),(name,a,z)
plan['modified_tracks']=tracks;plan['transition_radius_nm']=455000;plan['transition_derivation']='Native via radius250000 + plane clearance200000 + native polygon max error5000 nm (must assert source settings). Envelope is the union of old/new transition disks only; GPIO25 own disks separate.'
(ROOT/'qa/FROZEN_SCOPE.json').write_text(json.dumps(plan,indent=2));print('FROZEN',tracks)
