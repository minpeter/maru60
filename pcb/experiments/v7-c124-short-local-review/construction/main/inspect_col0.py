from common import *
for x in ['5cd30845-f09e-4ecf-9e5d-f0638932fe94','4aeca723-e904-4998-98f6-e5f1d0ed1c68']:
 q=idx[x];print(x,q.GetClass(),q.GetNetname(),q.GetLayerName(),dump(copper(q,p.B_Cu)));print('ref',q.GetParent().GetReference()if isinstance(q,p.PAD)else'',q.GetWidth()if isinstance(q,p.PCB_TRACK)else'')
