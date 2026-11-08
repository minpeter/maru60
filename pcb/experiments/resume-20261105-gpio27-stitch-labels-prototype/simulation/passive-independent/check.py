from pathlib import Path
import json,hashlib,subprocess
import numpy as np
import pcbnew
root=Path('/workspace/shared/maru60-resume')
p=root/'continuation-c782/power-envelope'
o=root/'continuation-c782/power-envelope-independent'
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
r=json.loads((p/'RESULTS.json').read_text())
board=root/'continuation-c782/combined27fix2/pcb/maru60.kicad_pcb'
assert h(board)=='9d787421bddf23dd06eb8ec51a984ab6cbcc7a36b92a8700a041cb41fc1f18ed'
b=pcbnew.LoadBoard(str(board))
inv=[]
for expected in r['verified_components']:
 f=next(f for f in b.GetFootprints() if f.GetReference()==expected['reference'])
 row=dict(reference=f.GetReference(),value=f.GetValue(),pads={pad.GetNumber():pad.GetNetname() for pad in f.Pads()})
 assert row['value']==expected['value'] and row['pads']==expected['pads']
 inv.append(row)
checks=[]
for rr in r['runs']:
 name=rr['case'];deck=p/'cases'/f'{name}.cir';wave=p/'runs'/name/'waveform.txt'
 assert h(deck)==rr['deck_sha256'] and h(wave)==rr['waveform_sha256']
 a=np.loadtxt(wave,skiprows=1);t,v,vc=a.T
 assert np.isfinite(a).all() and len(a)==rr['rows'] and np.all(np.diff(t)>0)
 C=float(rr['capacitance_uF_assumption'])*1e-6;T=rr['fixed_regulator_time_us_assumption']*1e-6
 s=1 if rr['direction']=='load' else -1
 dt=np.maximum(t-5e-6,0);ramp=1e-8
 q=.2*np.where(dt<ramp,dt**2/(2*ramp),dt-ramp/2)
 current=.2*np.minimum(dt/ramp,1)
 predicted_c=4-s*q/C;predicted=predicted_c-s*current*.02
 assert abs(t[-1]-(5e-6+T))<1e-12
 err=float(np.max(abs(v-predicted)));cerr=float(np.max(abs(vc-predicted_c)))
 assert err<1e-5 and cerr<1e-5
 assert np.max(abs((v-vc)+s*current*.02))<1e-9
 assert abs(v[-1]-rr['final_output_V'])<1e-12
 assert abs(v.min()-rr['minimum_output_V'])<1e-12 and abs(v.max()-rr['maximum_output_V'])<1e-12
 dest=o/'replays'/name
 ret=subprocess.run(['/usr/bin/python3',str(root/'power-replay-20261105/inputs/v7-power-simulation/ngrun.py'),str(deck),str(dest),'v(out)','v(cnode)'],capture_output=True,text=True)
 assert ret.returncode==0,ret.stderr
 replay=np.loadtxt(dest/'waveform.txt',skiprows=1)
 assert np.array_equal(a,replay)
 checks.append(dict(case=name,rows=len(t),max_all_sample_error_V=err,max_capacitor_error_V=cerr,endpoint_error_V=float(abs(v[-1]-predicted[-1])),replay_identical=True))
report=dict(result='PASS synthetic passive numerical checks; provenance qualification required',source_board_sha256=r['board_sha256'],final_board_sha256=h(board),final_board_capacitor_inventory_matches=True,final_board_inventory=inv,checks=checks,max_all_sample_error_V=max(x['max_all_sample_error_V'] for x in checks))
(o/'CHECKS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
