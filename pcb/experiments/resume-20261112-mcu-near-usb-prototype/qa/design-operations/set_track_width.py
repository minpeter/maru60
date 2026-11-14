import sys
import pcbnew as p

bp, uid, width = sys.argv[1], sys.argv[2], float(sys.argv[3])
b = p.LoadBoard(bp)
hits = [t for t in b.GetTracks() if t.m_Uuid.AsString() == uid]
assert len(hits) == 1, (uid, len(hits))
hits[0].SetWidth(round(width * 1e6))
b.BuildConnectivity()
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(bp, b)
print("set track width", uid, width)
