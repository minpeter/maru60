import json
import math
import sys
import pcbnew as p

bp, routing = sys.argv[1:3]
b = p.LoadBoard(bp)
d = json.load(open(routing))
nets = b.GetNetsByName()
fps = {f.GetReference(): f for f in b.GetFootprints()}
assert set(d["positions"]) <= set(fps)
for ref, xy in d["positions"].items():
    assert math.dist(xy, [fps[ref].GetPosition().x / 1e6, fps[ref].GetPosition().y / 1e6]) < .0002, (ref, xy)

def point(x, y):
    return p.VECTOR2I(round(x * 1e6), round(y * 1e6))

def segment_key(t):
    a = (round(t["x1"], 5), round(t["y1"], 5))
    z = (round(t["x2"], 5), round(t["y2"], 5))
    return t["net"], t["layer"], min(a, z), max(a, z), round(t["w"], 5)

existing = set()
via_positions = set()
for t in b.GetTracks():
    if t.Type() == p.PCB_VIA_T:
        via_positions.add((t.GetNetname(), round(t.GetPosition().x / 1e6, 5), round(t.GetPosition().y / 1e6, 5)))
    else:
        existing.add((t.GetNetname(), t.GetLayerName(),
                      min((round(t.GetStart().x / 1e6, 5), round(t.GetStart().y / 1e6, 5)), (round(t.GetEnd().x / 1e6, 5), round(t.GetEnd().y / 1e6, 5))),
                      max((round(t.GetStart().x / 1e6, 5), round(t.GetStart().y / 1e6, 5)), (round(t.GetEnd().x / 1e6, 5), round(t.GetEnd().y / 1e6, 5))),
                      round(t.GetWidth() / 1e6, 5)))
added_tracks = added_vias = 0
for t in d["tracks"]:
    if segment_key(t) in existing:
        continue
    assert t["net"] in nets
    q = p.PCB_TRACK(b)
    q.SetStart(point(t["x1"], t["y1"]))
    q.SetEnd(point(t["x2"], t["y2"]))
    q.SetWidth(round(t["w"] * 1e6))
    q.SetLayer(b.GetLayerID(t["layer"]))
    q.SetNet(nets[t["net"]])
    b.Add(q)
    existing.add(segment_key(t))
    added_tracks += 1
for v in d["vias"]:
    key = (v["net"], round(v["x"], 5), round(v["y"], 5))
    if key in via_positions:
        continue
    assert v["net"] in nets
    q = p.PCB_VIA(b)
    q.SetViaType(p.VIATYPE_THROUGH)
    q.SetLayerPair(p.F_Cu, p.B_Cu)
    q.SetPosition(point(v["x"], v["y"]))
    q.SetWidth(p.F_Cu, round(v["d"] * 1e6))
    q.SetDrill(round(v["drill"] * 1e6))
    q.SetNet(nets[v["net"]])
    b.Add(q)
    via_positions.add(key)
    added_vias += 1
b.BuildConnectivity()
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(bp, b)
print("merged new SES routing", added_tracks, "tracks", added_vias, "vias; existing routing preserved")
