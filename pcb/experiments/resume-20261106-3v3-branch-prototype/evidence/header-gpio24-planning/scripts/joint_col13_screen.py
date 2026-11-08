from optimistic_screen import *
# Only a planning relaxation. Remove second COL13 segment from shape index;
# native source remains untouched and no PCB is saved.
uid='393cd1e2-4007-43d0-803e-78162f1899a5'
for l in L:
 if (uid,l)in shapes:
  shapes[(uid,l)]=('COL13',shapes[(uid,l)][1])
# Existing same-net tracks are ignored by COL13 routing naturally.
virtual=[]
for a in [(88.85,42),(92.5,39.5)]:
 q=p.PCB_VIA(b);q.SetPosition(V(*a));q.SetWidth(p.F_Cu,500000);q.SetWidth(p.In1_Cu,500000);q.SetWidth(p.In2_Cu,500000);q.SetWidth(p.B_Cu,500000);q.SetDrill(250000);q.SetNetCode(b.GetNetcodeFromNetname('EXT_GPIO24'));q.SetLayerPair(p.F_Cu,p.B_Cu);virtual.append(q);addobs(q)
assert all(q.GetWidth(l)==500000 and q.GetDrillValue()==250000 for q in virtual for l in L)
print('ASSERTED: both virtual vias are 0.50/0.25 mm on all four copper layers',flush=True)
path=search('COL13',p.F_Cu,(87.65,43.5),goal=(93.5,39.05),box=(86.8,38.5,94,44),step=.05)
out={'COL13_joint_path':path,'hypothetical_vias':[[88.85,42],[92.5,39.5]],'box':[86.8,38.5,94,44],'step_mm':.05,'saved_candidate':False}
(ROOT/'qa/joint-col13-screen.json').write_text(json.dumps(out,indent=2));print(out)
