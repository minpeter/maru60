from optimistic_screen import *
# Target existing same-net via, rather than asking J3 for a redundant transition.
u=search('EXT_GPIO24',p.B_Cu,(89.45,42),box=(87.8,41.2,90,42.8),fanout=True,step=.025)
f=search('EXT_GPIO24',p.F_Cu,u[-1],goal=(92.35,37.75),box=(87,36.8,106,45),step=.05)if u else None
(ROOT/'qa/complete-screen.json').write_text(json.dumps({'U13':u,'F':f,'optimistic_COL13_removed_only_in_memory':True},indent=2))
