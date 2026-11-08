import native_ink as n
s=n.Scene('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-two-reference-legibility/candidate/pcb/maru60.kicad_pcb')
for r,f in s.fps.items():
 x,y=n.XY(f.GetPosition())
 if 172e6<x<185e6 and 77e6<y<90e6:
  print(r,n.XY(f.GetPosition()),n.typo(s.fields[r]))
