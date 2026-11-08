#!/usr/bin/env python3
"""Analyze stored outputs without trusting process exit status or waveform existence."""
from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parent
BAD=('simulation(s) aborted','Simulation interrupted','circuit not parsed','Timestep too small','unknown model type','MIF-ERROR')
def status(p):
 log=(p/'ngspice.log').read_text() if (p/'ngspice.log').exists() else ''
 result={'error_lines':[line for line in log.splitlines() if any(x.lower() in line.lower() for x in BAD)],'warning_lines':[line for line in log.splitlines() if 'warning' in line.lower()]}
 if (p/'waveform.txt').exists():
  a=np.atleast_2d(np.loadtxt(p/'waveform.txt',skiprows=1));result.update(rows=len(a),last=a[-1].tolist(),minimum=a.min(axis=0).tolist(),maximum=a.max(axis=0).tolist())
 else:result['rows']=0
 result['numerical_run_without_detected_fatal_error']=bool(result['rows']) and not result['error_lines']
 return result
out={'scope':'Runtime capability and semantic eligibility, not board or hardware validation','runs':{p.name:status(p) for p in sorted((ROOT/'runs').iterdir()) if p.is_dir()}}
for name in ['u7-original-xnor','u7-original-xnor-psa','u7-original-xnor-ltpsa']:
 r=out['runs'][name];r['input_order']=['00','01','10','11'];r['expected']=[1,0,0,1];r['actual']=r['last'][1:];r['semantic_pass']=bool(np.allclose(r['expected'],r['actual'],atol=1e-9,rtol=0));assert not r['semantic_pass']
expected=json.loads((ROOT/'netlists/buck-original-static-logic-expected.json').read_text())
for mode in ['ps','psa']:
 r=out['runs'][f'buck-original-static-logic-{mode}'];r['static_output_count']=len(expected);r['maximum_absolute_error']=float(np.max(abs(np.array(r['last'][1:])-np.array(list(expected.values())))));assert r['maximum_absolute_error']<1e-9
p=ROOT/'runs/reversed-limit-control-psa/waveform.txt';a=np.loadtxt(p,skiprows=1);out['runs']['reversed-limit-control-psa']['maximum_clamp_error']=float(max(abs(a[:,2]-np.clip(a[:,1],0,5)).max(),abs(a[:,3]-np.clip(a[:,1],0,5)).max()));assert out['runs']['reversed-limit-control-psa']['maximum_clamp_error']<1e-9
out['runs']['buck-diagnostic-24v']['requested_stop_seconds']=.006
out['runs']['buck-diagnostic-24v']['reached_requested_stop']=out['runs']['buck-diagnostic-24v']['last'][0]>=.006*(1-1e-10)
assert not out['runs']['buck-diagnostic-24v']['reached_requested_stop'];assert out['runs']['buck-diagnostic-24v']['error_lines']
(ROOT/'RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
print('Classification passed: U7 semantic rejection, buck24V incomplete/aborted, buck40 static cases pass.')
