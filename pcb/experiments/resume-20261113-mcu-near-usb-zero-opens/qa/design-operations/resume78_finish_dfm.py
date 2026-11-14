import pcbnew as p,sys
bp=sys.argv[1];b=p.LoadBoard(bp)
n=0
for t in b.GetTracks():
 if t.Type()!=p.PCB_TRACE_T or t.GetNetname()!='+1V1' or t.GetLayerName()!='In2.Cu':continue
 a=(t.GetStart().x/1e6,t.GetStart().y/1e6);z=(t.GetEnd().x/1e6,t.GetEnd().y/1e6)
 if (a,z) in [((25.4,35.6),(25.4,37.8)),((25.4,33.2),(27.4,33.15))]:t.SetWidth(p.FromMM(.24));n+=1
assert n==2,n
f=b.FindFootprintByReference('D16');g=next(g for g in f.GraphicalItems() if g.m_Uuid.AsString()=='0c3099b2-54a8-44a7-862a-732a94021fcd');f.Remove(g)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(bp,b)
print('narrowed two 4.2-mm-total segments to 0.24 mm; kept D16 cathode bar and other silk edge')
