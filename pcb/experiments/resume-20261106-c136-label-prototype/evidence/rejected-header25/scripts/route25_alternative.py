from route25_refactor import *
N='EXT_GPIO25'; j=search(N,p.B_Cu,(93.5,39),box=(91,35,97,39),fanout=True,step=.025);u=search(N,p.B_Cu,(107.1,37.325),box=(106,37,109.2,41.3),fanout=True,step=.025);f=search(N,p.F_Cu,j[-1],goal=u[-1],box=(90,33,112,39),step=.025)if u and j else None
plan={'U11':u,'J3':j,'F':f,'removed':removed,'detour':detour};(ROOT/'qa/route25-upper-plan.json').write_text(json.dumps(plan,indent=2));print(plan)
