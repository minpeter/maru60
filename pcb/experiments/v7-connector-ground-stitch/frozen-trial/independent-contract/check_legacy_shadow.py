#!/usr/bin/python3
import os,sys,json,hashlib
from pathlib import Path
if not __debug__ or sys.flags.optimize != 0 or os.environ.get('PYTHONOPTIMIZE','') not in ('','0'):raise SystemExit('Legacy checks require assertions; optimized Python is forbidden')
D=Path(__file__).resolve().parent;os.environ['XDG_CONFIG_HOME']=str(D/'xdg/legacy-config');os.environ['XDG_CACHE_HOME']=str(D/'xdg/legacy-cache')
import pcbnew as p
assert p.GetBuildVersion()=='9.0.2+dfsg-1'
B=D/'input-original-a9.kicad_pcb';sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();before=sha(B);assert before=='a9ff40100f8b34cd46b7706eb3264cbbc61508cc4c6895fdcefcb2cce35e7b67';b=p.LoadBoard(str(B));pt=p.VECTOR2I(17200000,9900000);hole=p.SHAPE_CIRCLE(pt,125000);checks=0;near=[];failed=[];retired=[]
for q in list(b.GetTracks())+[q for f in b.GetFootprints()for q in f.Pads()]:
 if q.GetNetname()=='GND':continue
 for l in [p.F_Cu,p.B_Cu]:
  if not q.IsOnLayer(l):continue
  checks+=1;s=q.GetEffectiveShape(l);distance=(s.Distance(pt)-125000)/1e6;row={'uuid':q.m_Uuid.AsString(),'net':q.GetNetname(),'layer':b.GetLayerName(l),'drill_to_legacy_nominal_shadow_mm':distance}
  if q.m_Uuid.AsString()=='2c517f5c-8f2d-4a2a-9fea-dc1b7376c3cd':retired.append(row)
  if s.Collide(hole,0):failed.append(row)
  if distance<2:near.append(row)
assert len(retired)==1;assert not failed;assert before==sha(B);near.sort(key=lambda x:x['drill_to_legacy_nominal_shadow_mm']);result={'native_version':p.GetBuildVersion(),'source_path':str(B),'source_sha256':before,'checked_original_non_GND_outer_shapes':checks,'no_intersections':True,'near_original_shadows':near,'explicit_retired_U10_Dminus_shadow':retired,'board_unchanged':True,'scope':'Nominal-copper shadows conservatively cover physical material; no hole or endpoint allowance.'};(D/'legacy_shadow_results.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
