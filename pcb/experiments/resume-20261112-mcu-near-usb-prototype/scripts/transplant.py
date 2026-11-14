import pcbnew,json
from pathlib import Path
root=Path('build/mcu-near-usb');b=pcbnew.LoadBoard(str(root/'trial/pcb/maru60.kicad_pcb'));ops=json.load(open(root/'placement-ops.json'))['ops'];fps={f.GetReference():f for f in b.GetFootprints()};mm=pcbnew.FromMM
P=lambda x,y:pcbnew.VECTOR2I(round(x*1e6),round(y*1e6))
core=set(o['ref'] for o in ops)-{'U3','C118','R105','C105'}
nets={p.GetNetname() for r in core for p in fps[r].Pads()}
# Transfer the existing escape and local core interconnect; terminal trunks outside
# this rectangle remain in place and will be reconnected explicitly.
def inside(p):return 96.0<=p.x/1e6<=120.0 and 73.0<=p.y/1e6<=89.0
def tx(p):return P(137-p.x/1e6,116.5-p.y/1e6)
n=0
for t in list(b.GetTracks()):
 if t.GetNetname() not in nets:continue
 if inside(t.GetStart()) and inside(t.GetEnd()):
  if t.Type()==pcbnew.PCB_VIA_T:t.SetPosition(tx(t.GetPosition()))
  else:
   a,z=tx(t.GetStart()),tx(t.GetEnd());t.SetStart(a);t.SetEnd(z)
  n+=1
for o in ops:
 f=fps[o['ref']];f.SetPosition(P(o['x'],o['y']));f.SetOrientationDegrees(o['rot'])
pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(root/'trial/pcb/maru60.kicad_pcb'),b)
print('transferred tracks/vias',n)
