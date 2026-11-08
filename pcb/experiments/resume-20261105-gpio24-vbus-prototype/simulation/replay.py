import pathlib,subprocess,hashlib,json,math
import numpy as np
D=pathlib.Path(__file__).resolve().parent; P=D/'inputs/v7-power-simulation'; results=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for f in sorted((P/'netlists').glob('*.cir')):
 name=f.stem
 signals=['v(out)','v(cnode)'] if name.startswith('capacitor') else ['v(fused)','v(out)','v(uv)','v(ov)'] if name=='efuse_hysteresis' else ['v(source)','v(capin)'] if name.startswith('input') else ['v(src)','v(out)']
 out=D/'runs'/name
 p=subprocess.run(['/usr/bin/python3',str(P/'ngrun.py'),str(f),str(out),*signals],cwd=P,capture_output=True,text=True,timeout=60)
 (out/'call.log').write_text(p.stdout+p.stderr)
 logs=(out/'ngspice.log').read_text(); a=np.loadtxt(out/'waveform.txt',skiprows=1)
 assert p.returncode==0 and a.ndim==2 and np.isfinite(a).all()
 assert not any(x in logs.lower() for x in ['simulation interrupted','simulation(s) aborted','timestep too small','circuit not parsed','mif-error','unknown model type'])
 expected=55e-6 if name.startswith('capacitor') else 2 if name=='efuse_hysteresis' else 30e-6 if name.startswith('input') else .005
 assert abs(a[-1,0]-expected)<1e-12
 prior=np.loadtxt(P/'runs'/name/'waveform.txt',skiprows=1)
 r={'name':name,'deck_sha256':sha(f),'rows':len(a),'end_time_s':float(a[-1,0]),'signals':signals,'min_V':a[:,1:].min(axis=0).tolist(),'max_V':a[:,1:].max(axis=0).tolist(),'final_V':a[-1,1:].tolist(),'saved_replay_same_shape':a.shape==prior.shape,'saved_replay_max_abs_difference':float(np.abs(a-prior).max()) if a.shape==prior.shape else None,'waveform_sha256':sha(out/'waveform.txt'),'warnings':[l for l in logs.splitlines() if any(w in l.lower() for w in ['warn','error','failed'])]}
 if name=='rc_control':
  r['analytic_max_abs_error_V']=float(np.max(np.abs(a[:,2]-(1-np.exp(-np.maximum(a[:,0]-.5e-9,0)/.001)))))
  assert r['analytic_max_abs_error_V']<1e-4
 elif name.startswith('capacitor'):
  c=float(name.split('_')[1][:-1])*1e-6; sign=-1 if name.endswith('unload') else 1
  ideal=4-sign*.2*(49.995e-6/c+.02)
  r['finite_ramp_analytic_endpoint_V']=ideal;r['analytic_endpoint_error_V']=float(abs(a[-1,1]-ideal));assert r['analytic_endpoint_error_V']<1e-5
 elif name=='efuse_hysteresis':
  on=a[:,2]>1; edges=np.where(on[1:]!=on[:-1])[0]+1
  r['transition_input_V']=a[edges,1].tolist(); expected_edges=np.array([1.2*(1+620/267),1.2*(1+590/156),1.09*(1+590/156),1.09*(1+620/267)])
  assert len(edges)==4 and np.max(abs(a[edges,1]-expected_edges))<.002
 results.append(r)
board=pathlib.Path('/workspace/shared/maru60-resume/header-routing/frozen26b/pcb/maru60.kicad_pcb')
report={'classification':'Fresh passive/behavioral frozen-deck replay only; not an active power or hardware qualification','selected_board_sha256':sha(board),'original_saved_deck_board_sha256':'3663aac96fb305eb4925fff938dd2db5862b880c6c262b2fa82707567a6e98f7','not_reextracted_from_selected_board':True,'libngspice_sha256':sha(pathlib.Path('/usr/lib/x86_64-linux-gnu/libngspice.so.0.0.12')),'runner_sha256':sha(P/'ngrun.py'),'runs':results}
(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
