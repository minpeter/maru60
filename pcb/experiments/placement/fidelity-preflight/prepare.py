import os,sys,shutil,subprocess
from pathlib import Path
os.environ['KICAD_CONFIG_HOME']='/tmp/maru-placement-config';os.environ['XDG_CONFIG_HOME']='/tmp/maru-placement-config'
import pcbnew as p
r=Path('/workspace/shared/maru60-placement-lab');d=r/'fidelity-preflight';b=p.LoadBoard(str(r/'frozen.kicad_pcb'))
for t in b.GetTracks():t.SetLocked(True)
p.SaveBoard(str(d/'input.kicad_pcb'),b);shutil.copyfile(r/'frozen.kicad_pro',d/'input.kicad_pro');shutil.copyfile(r/'fp-lib-table',d/'fp-lib-table');assert p.ExportSpecctraDSN(b,str(d/'input.dsn'));subprocess.run([sys.executable,str(r/'router_contract.py'),str(d/'input.kicad_pcb')],check=True)
