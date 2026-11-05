from fractions import Fraction as F
import json
from pathlib import Path
O=Path('/workspace/shared/maru60-resume/header-exact-review')
A=(274426109,37930202);B=(274499669,37910492);C=(274540691,37899500);D=(274470567,37918289);L=274475000
line=lambda a,b,x:F(a[1])+F(b[1]-a[1],b[0]-a[0])*(x-a[0])
diff=lambda a,b,x:line(a,b,x)-line(D,C,x)
points=[(L,diff(A,B,L)),(B[0],diff(A,B,B[0])),(C[0],diff(B,C,C[0]))]
assert all(y>=0 for x,y in points)
loss=sum(F(v[0]-u[0],2)*(u[1]+v[1])for u,v in zip(points,points[1:]));assert loss==F(1189714324905,42986012)
r={'method':'Independent piecewise-linear integration of exact serialized edges, not clipping or polygon Boolean. Winding direction confirmed by reproduced full-outline classification.','loss_nm2':str(loss),'loss_mm2':float(loss)/1e12,'maximum_vertical_difference_nm':str(max(y for x,y in points)),'maximum_vertical_difference_nm_float':float(max(y for x,y in points)),'samples':[(x,str(y))for x,y in points]};(O/'analytic-target.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
