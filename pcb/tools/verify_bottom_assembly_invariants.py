#!/usr/bin/env python3
"""Check preserved layout choices and critical copper against the pinned baseline.

Compare two dump_board_geometry.py exports. Placement invariants do not replace
DRC, material connectivity, power analysis, or physical assembly qualification.
"""
import argparse,hashlib,json
from pathlib import Path
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('baseline',type=Path);ap.add_argument('candidate',type=Path);ap.add_argument('plan',type=Path);ap.add_argument('output',type=Path)
a=ap.parse_args();old=json.loads(a.baseline.read_text());new=json.loads(a.candidate.read_text());plan=json.loads(a.plan.read_text())
changed=set(plan['relocate_top']+plan['relocate_bottom'])|{s['ref'] for s in plan['sites']}
cosmetic={'LOGO1'}
# Normalize nm-level floating point representation, but do not relax CAD units.
def norm(x):
 if isinstance(x,float):return round(x,6)
 if isinstance(x,list):return [norm(v) for v in x]
 if isinstance(x,dict):return {k:norm(v) for k,v in x.items()}
 return x
oldfp={f['ref']:norm(f) for f in old['fps']};newfp={f['ref']:norm(f) for f in new['fps']}
missing=sorted(set(oldfp)^set(newfp));fixed=sorted(set(oldfp)-changed-cosmetic)
geometry_changes=[ref for ref in fixed if oldfp[ref]!=newfp.get(ref)]
mechanical=sorted(ref for ref,f in oldfp.items() if ref.startswith(('SW','STAB','H')) or any(p['drill'][0] for p in f['pads']))
mechanical_changes=[ref for ref in mechanical if oldfp[ref]!=newfp.get(ref)]
critical=lambda n:n.startswith(('USB_DP','USB_DM','QSPI_','VREG_')) or n in ('XIN','XOUT','XTAL_OUT','+1V1')
def copper(g):
 result=[]
 for t in g['tracks']:
  if critical(t['net']):
   ends=sorted([(round(t['x1'],6),round(t['y1'],6)),(round(t['x2'],6),round(t['y2'],6))]);result.append(('track',t['net'],t['layer'],round(t['w'],6),tuple(ends)))
 for v in g['vias']:
  if critical(v['net']):result.append(('via',v['net'],round(v['x'],6),round(v['y'],6),round(v['d'],6),round(v['drill'],6)))
 return sorted(result)
top_smt=sorted(f['ref'] for f in new['fps'] if f['layer']=='F.Cu' and f['attr']&2)
reverse=[f for f in new['fps'] if 'LED_SK6812MINI_E_012_Reverse' in f['fpid']]
windows=sum(len(poly)-1 for poly in new['board_material'])
result={'scope':'geometry and critical-copper invariants; not fabrication qualification','candidate_geometry_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
 'fixed_footprints_compared':len(fixed),'fixed_geometry_changes':geometry_changes,'missing_or_added_references':missing,'cosmetic_placement_exception':sorted(cosmetic),
 'mechanical_footprints_compared':len(mechanical),'mechanical_changes':mechanical_changes,'usb_data_qspi_crystal_vreg_copper_identical':copper(old)==copper(new),
 'top_smt':top_smt,'reverse_led_references':len(reverse),'internal_windows':windows,
 'exclusive_backspace_sites':{f['ref']:len(f['pads'])//4 for f in reverse if f['ref'] in ('LED14','LED15')}}
result['pass']=not(missing or geometry_changes or mechanical_changes or top_smt) and result['usb_data_qspi_crystal_vreg_copper_identical'] and len(reverse)==64 and windows==66 and result['exclusive_backspace_sites']=={'LED14':2,'LED15':2}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['pass'] else 1)
