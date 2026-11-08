from common import *
rows=[]
for q in obs:
 if q.IsOnLayer(p.B_Cu)and q.GetNetname()=='USB_UVLO'and q.GetBoundingBox().Intersects(p.BOX2I(vec([12.5,16.5]),vec([6,5.5]))):
  rows.append(dict(uuid=uid(q),type=q.GetClass(),start=[q.GetStart().x/1e6,q.GetStart().y/1e6],end=[q.GetEnd().x/1e6,q.GetEnd().y/1e6],width=(q.GetWidth(p.B_Cu) if isinstance(q,p.PCB_VIA) else q.GetWidth())/1e6))
(D/'uvlo-local-objects.json').write_text(json.dumps(dict(source_sha=sha(BP),status='inspection only; no retirement approved',rows=rows),indent=2));print(json.dumps(rows,indent=2))
