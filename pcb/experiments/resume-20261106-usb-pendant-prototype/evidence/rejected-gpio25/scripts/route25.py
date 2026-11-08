from screen import *
N='EXT_GPIO25';a=(93.5,39);z=(107.1,37.325)
j=search(N,p.B_Cu,a,box=(90,36,98,42),fanout=True,step=.025)
u=search(N,p.B_Cu,z,box=(103,34,113,40),fanout=True,step=.025)
f=search(N,p.F_Cu,j[-1],goal=u[-1],box=(86,29,118,49),step=.025)if j and u else None
plan={'J3':j,'U11':u,'F':f};(ROOT/'qa/route25-plan.json').write_text(json.dumps(plan,indent=2));print(plan)
