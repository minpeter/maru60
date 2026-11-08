from common import *
print([(uid(q),q.GetNetname(),[b.GetLayerName(l)for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]if q.IsOnLayer(l)],q.GetFilledArea()/1e12)for q in b.Zones()]);print('tracksvias',len(list(b.GetTracks())),'footprints',len(fs))
