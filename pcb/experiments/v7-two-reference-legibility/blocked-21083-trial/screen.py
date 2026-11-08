import sys,os,json,hashlib,math
from pathlib import Path
W=Path(__file__).resolve().parent
sys.path.insert(0,str(W));sys.dont_write_bytecode=True
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 d=W/'runtime'/k.lower();d.mkdir(parents=True,exist_ok=True,mode=0o700);os.environ[k]=str(d)
os.environ['QT_QPA_PLATFORM']='offscreen'
from native_ink import *
source=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-c124-series-with-connector-ground/candidate/pcb/maru60.kicad_pcb')
assert SHA(source)=='7882c9d916b0b773bfc146d03b3f2bc66ba18494d87279c51c302d95b0baa401'
s=Scene(source);refs=['U18','R159','C139','R122','L2'];out={'source_sha256':s.before,'scope':'read-only simultaneous group placement screen; no CAD written','native_build':p.GetBuildVersion(),'refs':{},'method':'Native actual ink, full native mask inventory, silk, Fab/courtyard/edge. 0.8 mm height/width, 0.12 mm stroke. Candidate slots at 0.25 mm grid within 6 mm; 0/90 degrees. Existing target-group labels omitted for simultaneous proposal, all other objects retained. Conservative 0.15 mm spacing and 0.25 mm to outline. Screen does not establish label ownership.'}
exclude={UID(s.fields[r]) for r in refs}
for sl,bk in s.buckets.items():bk['silk']=[(i,g)for i,g in bk['silk']if i['uuid']not in exclude]
for ref in refs:
 fp=s.fps[ref];x=s.fields[ref];old=typo(x);center=XY(fp.GetPosition());x.SetTextSize(p.VECTOR2I(800000,800000));x.SetTextThickness(120000)
 bk=s.buckets[x.GetLayer()];obj=[(name,items,150000)for name,items in bk.items()]+[('edge',s.edges,250000)]
 slots=[];count=0
 for ang in [0,90]:
  x.SetTextAngle(p.EDA_ANGLE(ang,p.DEGREES_T))
  for ix in range(-24,25):
   for iy in range(-24,25):
    if ix*ix+iy*iy>24*24:continue
    xy=[center[0]+ix*250000,center[1]+iy*250000];x.SetPosition(p.VECTOR2I(*xy));sh=effective(x);count+=1
    if any(hits(sh,items,clear)for name,items,clear in obj):continue
    q=poly(sh);q.BooleanSubtract(s.outline)
    if q.Area()!=0:continue
    slots.append({'position_nm':xy,'angle_deg':ang,'owner_center_distance_mm':math.hypot(ix,iy)*.25})
 slots.sort(key=lambda z:(z['owner_center_distance_mm'],z['angle_deg'],z['position_nm']))
 out['refs'][ref]={'old':old,'owner_center_nm':center,'tested_slots':count,'passing_slots':len(slots),'closest_100':slots[:100]}
 print(ref,center,len(slots),slots[:3],flush=True)
assert SHA(source)==s.before
(W/'SCREEN.json').write_text(json.dumps(out,indent=2)+'\n')
