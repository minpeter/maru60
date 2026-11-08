from common import *
for q in b.Zones():
 if not q.IsOnLayer(p.B_Cu):continue
 bb=q.GetBoundingBox();print(uid(q),q.GetNetname(),[bb.GetX()/1e6,bb.GetY()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6])
