"""Export native component anchors and membership for each DRC open pair.

Native connectivity guides repair. Use export_material_graph.py for independent
material connectivity, especially for isolated zone islands and routed slots.
Run with the pinned KiCad Python environment.
"""
import json
import sys
import pcbnew as p

bp, drc_path, out_path = sys.argv[1:4]
b = p.LoadBoard(bp)
b.BuildConnectivity()
cn = b.GetConnectivity()
tracks = list(b.GetTracks())
pads = [q for f in b.GetFootprints() for q in f.Pads()]
zones = list(b.Zones())
items = tracks + pads + zones
uid = lambda q: q.m_Uuid.AsString()
idx = {uid(q):q for q in items}
adj = {u:set() for u in idx}
for t in tracks + pads:
    u = uid(t)
    for q in list(cn.GetConnectedTracks(t)) + list(cn.GetConnectedPads(t)):
        v = uid(q)
        if v in idx and q.GetNetCode() == t.GetNetCode():
            adj[u].add(v);adj[v].add(u)
for z in zones:
    u = uid(z)
    for q in list(cn.GetConnectedTracks(z)) + list(cn.GetConnectedPads(z)):
        v = uid(q)
        if v in idx and q.GetNetCode() == z.GetNetCode():
            adj[u].add(v);adj[v].add(u)

def points(t):
    pts = set()
    for layer,lid in [("F.Cu",p.F_Cu),("B.Cu",p.B_Cu)]:
        if not t.IsOnLayer(lid):
            continue
        if t.Type() == p.PCB_TRACE_T:
            qq = [t.GetStart(),t.GetEnd()]
        elif t.Type() == p.PCB_ZONE_T:
            qq = []
            fp = t.GetFilledPolysList(lid)
            for i in range(fp.OutlineCount()):
                o = fp.Outline(i)
                step = max(1,o.PointCount()//200)
                qq.extend(o.CPoint(j) for j in range(0,o.PointCount(),step))
        else:
            qq = [t.GetPosition()]
        for q in qq:
            pts.add((layer,round(q.x/1e6,6),round(q.y/1e6,6)))
    return sorted(pts)

d = json.load(open(drc_path))
out = []
for e in d["unconnected_items"]:
    groups = []
    members = []
    for it in e["items"]:
        u = it["uuid"]
        seen = set()
        todo = [u] if u in idx else []
        while todo:
            u = todo.pop()
            if u in seen:
                continue
            seen.add(u)
            todo.extend(adj[u]-seen)
        groups.append(sorted({q for u in seen for q in points(idx[u])}))
        members.append([{"uuid": u, "kind": "pad" if isinstance(idx[u], p.PAD) else "zone" if isinstance(idx[u], p.ZONE) else "via" if isinstance(idx[u], p.PCB_VIA) else "track",
                         "net": idx[u].GetNetname(),
                         **({"ref": idx[u].GetParentFootprint().GetReference(), "pad": idx[u].GetNumber()} if isinstance(idx[u], p.PAD) else {})}
                        for u in sorted(seen)])
    out.append({"items":e["items"],"groups":groups,"members":members})
json.dump(out,open(out_path,"w"),indent=2)
print("components exported",len(out))
