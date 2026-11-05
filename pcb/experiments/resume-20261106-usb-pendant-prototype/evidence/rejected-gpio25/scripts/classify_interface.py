from screen_rules import *
idx={U(q):q for q in list(b.GetTracks())+pads};j=json.loads((ROOT/'qa/bridge-frontier.json').read_text());ids={h['uuid']for r in j['rows']for h in r['hits']if h['net']in ['EXT_GPIO24','EXT_GPIO26']};rows=[]
for uid in sorted(ids):
 q=idx[uid];r=dict(uuid=uid,net=q.GetNetname(),type=q.GetClass(),xy=[q.GetPosition().x/1e6,q.GetPosition().y/1e6])
 if isinstance(q,p.PAD):r.update(ref=q.GetParentFootprint().GetReference(),pad=q.GetNumber(),fixed=True)
 elif isinstance(q,p.PCB_TRACK):r.update(end=[q.GetEnd().x/1e6,q.GetEnd().y/1e6],fixed=False)
 rows.append(r)
(ROOT/'qa/interface-objects.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
removed={r['uuid']for r in rows if not r['fixed']};print('NONPAD REMOVED',removed,flush=True)
for l in bins:
 for k in bins[l]:bins[l][k]=[key for key in bins[l][k]if key[0]not in removed]
path=search('EXT_GPIO25',p.B_Cu,(98.15,40.6),goal=(107.1,37.325),box=(95.5,29,115,46),step=.0125)
reach=json.loads((ROOT/'qa/reach-last.json').read_text())if path is None else None
out=dict(removed_nonpad_uuids=sorted(removed),never_removed_pads=True,diagnostic_only=True,path=path,reachable_count=len(reach)if reach else None)
(ROOT/'qa/interface-traces-omitted.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
