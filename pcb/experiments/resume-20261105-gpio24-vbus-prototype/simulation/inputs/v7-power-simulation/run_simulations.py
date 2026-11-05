#!/usr/bin/python3
"""Datasheet-bounded and deliberately limited power simulations, no CAD edits."""
from pathlib import Path
import os,sys,json,subprocess,hashlib,csv,itertools,math,argparse
D=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(D/'mplconfig')
os.environ['XDG_CACHE_HOME']=str(D/'cache')
(D/'cache').mkdir(exist_ok=True)
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=D/'plots';P.mkdir(exist_ok=True)
N=D/'netlists';N.mkdir(exist_ok=True)
O=D/'runs';O.mkdir(exist_ok=True)
R=D.parent.parent/'pcb-pr-publish/v7-protection-layout/pcb/integration/v7-label-candidate/pcb/maru60.kicad_pcb'
H='3663aac96fb305eb4925fff938dd2db5862b880c6c262b2fa82707567a6e98f7'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--board',type=Path,default=R,help='Exact accepted candidate PCB; checked read-only')
parser.add_argument('--frozen-inputs',action='store_true',help='Use frozen source-bound values without rereading CAD')
args=parser.parse_args()
R=args.board.resolve()
source_checked=not args.frozen_inputs
if source_checked:
 assert R.exists(), 'Provide --board /path/to/candidate or explicitly use --frozen-inputs'
 assert hashlib.sha256(R.read_bytes()).hexdigest()==H, 'Candidate hash mismatch: re-audit changed CAD first'
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2,'figure.facecolor':'#f8fafc','axes.facecolor':'white'})
summary={'board_sha256':H,'source_hash_checked_this_run':source_checked,'ngspice_version':'44.2 shared','classification':{'spice':'Passive networks and explicitly behavioral eFuse hysteresis only','numerical':'Datasheet timing/DC/headroom/uncertainty sweeps','not_executed':'TI TPS62932 and TPS2553-1 vendor models parse failed; TPS25947 vendor model is encrypted; no full switching-controller closed-loop/thermal/USB eye/ESD waveform simulation'},'spice_runs':[]}
def save(fig,name):
 fig.savefig(P/(name+'.png'),dpi=170,bbox_inches='tight');fig.savefig(P/(name+'.svg'),bbox_inches='tight');plt.close(fig)
def circuit(name,body,signals):
 f=N/(name+'.cir');f.write_text(body)
 out=O/name
 x=subprocess.run([sys.executable,str(D/'ngrun.py'),str(f),str(out),*signals],capture_output=True,text=True,timeout=60,cwd=D)
 if x.returncode:raise RuntimeError(name+' '+x.stdout+x.stderr)
 a=np.loadtxt(out/'waveform.txt',skiprows=1)
 assert len(a)>20 and np.all(np.isfinite(a))
 summary['spice_runs'].append({'name':name,'netlist':str(f.relative_to(D)),'points':len(a),'max_time_s':a[-1,0],'waveform':str((out/'waveform.txt').relative_to(D))})
 return a
# Shared-library positive control, analytic RC transient.
a=circuit('rc_control','''RC control 1k and1uF
V1 src 0 PULSE(0 1 0 1n 1n 10m 20m)
R1 src out 1k
C1 out 0 1u
.tran 10u 5m
.end
''',['v(src)','v(out)'])
err=float(np.max(np.abs(a[:,2]-(1-np.exp(-np.maximum(a[:,0]-.5e-9,0)/.001)))))
assert err<1e-4
summary['RC_control_max_absolute_error_V']=err
# Native SPICE switches emulate static comparator hysteresis only.
a=circuit('efuse_hysteresis','''Behavioral U8 hysteresis: not a TI macro-model; excludes dVdt,currentlimit,delay
Vstim fused 0 PWL(0 0 1 6.5 2 0)
R122 fused uv 620k
R123 uv 0 267k
R120 fused ov 590k
R121 ov 0 156k
BOV ovinv 0 V=-V(ov)
SUV fused mid uv 0 UVSW
SOV mid out ovinv 0 OVSW
.model UVSW SW(Ron=0.01415 Roff=1e9 Vt=1.145 Vh=0.055)
.model OVSW SW(Ron=0.01415 Roff=1e9 Vt=-1.145 Vh=0.055)
Rload out 0 33
.tran .1m 2 0 .1m
.end
''',['v(fused)','v(out)','v(uv)','v(ov)'])
on=a[:,2]>1;edges=np.where(on[1:]!=on[:-1])[0]+1
summary['efuse_behavioral_transitions']=[{'time_s':float(a[i,0]),'input_V':float(a[i,1]),'on':bool(on[i])}for i in edges]
expected=np.array([1.2*(1+620/267),1.2*(1+590/156),1.09*(1+590/156),1.09*(1+620/267)])
assert len(edges)==4 and np.max(abs(a[edges,1]-expected))<.002
fig,ax=plt.subplots(figsize=(10,4.8));ax.plot(a[:,0],a[:,1],label='VBUS_FUSED stimulus',color='#64748b');ax.plot(a[:,0],a[:,2],label='Behavioral protected output',color='#2563eb');ax.axhline(3.8,color='#dc2626',ls='--',label='Buck specified VIN minimum 3.8 V');ax.axhline(4/.98,color='#d97706',ls=':',label='4 V / 98% ideal-duty reference')
for i in edges:ax.annotate(f'{a[i,1]:.3f} V',(a[i,0],a[i,1]),xytext=(8,12),textcoords='offset points',fontsize=9)
ax.set(xlabel='Time (s)',ylabel='Voltage (V)',title='Protection hysteresis leaves a brownout gap');ax.legend(loc='upper left',fontsize=9);fig.text(.1,-.03,'Behavioral SPICE: actual divider values; nominal thresholds. No slew/current limit/delay model.',fontsize=9,color='#475569');save(fig,'01_protection_hysteresis')
# Passive charge-deficit tests, not closed-loop regulator response.
caprows=[];fig,axs=plt.subplots(1,2,figsize=(12,4.6),sharey=True)
for sign,ax in [(1,axs[0]),(-1,axs[1])]:
 for cap in [8,24,44]:
  base=.3 if sign<0 else .1;after=base+sign*.2
  name=f'capacitor_{cap}u_'+('load'if sign>0 else'unload')
  body=f'''Charge-deficit envelope: regulator current held fixed for50us
Ireg 0 out {base}
Iload out 0 PWL(0 {base} 5u {base} 5.01u {after})
RESR out cnode 0.02
Cout cnode 0 {cap}u IC=4
.tran .05u 55u 0 .05u UIC
.end
'''
  z=circuit(name,body,['v(out)','v(cnode)']);ax.plot((z[:,0]-5e-6)*1e6,z[:,1],label=f'{cap} uF')
  delta=float(z[-1,1]-4);analytic=-sign*.2*(50e-6/(cap*1e-6)+.02)
  assert abs(delta-analytic)<.001
  caprows.append({'cap_uF':cap,'load_change_A':sign*.2,'regulator_response_assumption':'No current response for50us','endpoint_delta_V':delta,'analytic_delta_V':analytic})
 ax.axhline(3.7,color='#dc2626',ls='--',lw=1);ax.set(xlim=(0,50),xlabel='Time after current step (us)',title='+200 mA load step'if sign>0 else'−200 mA load step');ax.legend()
axs[0].set_ylabel('Output voltage (V)');fig.suptitle('Capacitance sensitivity before the control loop responds',y=1.03);fig.text(.1,-.05,'SPICE charge-deficit envelope, not the actual buck transient: ESR assumed 20 mΩ; red line: 3.7 V LED minimum. 8 uF stress, 24 uF target, 44 uF nominal.',fontsize=9,color='#475569');save(fig,'02_capacitor_transient_envelope');summary['capacitor_scenarios']=caprows
# Input line L-C under abrupt recovery, unknown L swept rather than extracted.
fig,axs=plt.subplots(1,2,figsize=(12,4.6),sharey=True);hot=[]
for cap,ax in zip([2,4.7],axs):
 for lind in [.1,.5,1.0]:
  name=f'input_recovery_C{cap}u_L{lind}u'.replace('.','p')
  z=circuit(name,f'''Abrupt protected-feed recovery sensitivity; no eFuse slew model
Vin source 0 PWL(0 0 100n 5)
Rseries source n1 0.3582870323
Lfeed n1 capin {lind}u
RESR capin cnode 0.02
Cin cnode 0 {cap}u
Rload capin 0 33
.tran 2n 30u 0 2n
.end
''',['v(source)','v(capin)'])
  ax.plot(z[:,0]*1e6,z[:,2],label=f'L = {lind} uH');peak=float(z[:,2].max());hot.append({'Cin_effective_uF':cap,'assumed_line_L_uH':lind,'peak_V':peak})
 ax.axhline(5,color='#64748b',ls='--',lw=1);ax.set(xlabel='Time (us)',title=f'Effective input capacitance {cap} uF',xlim=(0,20));ax.legend()
axs[0].set_ylabel('Buck input voltage (V)');fig.suptitle('Abrupt input recovery: unknown inductance matters',y=1.03);fig.text(.1,-.05,'Passive SPICE sensitivity only. 5 V / 100 ns edge; R = 0.3583 Ω; L and ESR assumed. Not normal slew-limited startup or ESD.',fontsize=9,color='#475569');save(fig,'03_input_recovery_sensitivity');summary['input_recovery_scenarios']=hot
# Idealized timing envelopes: equations directly from component datasheets.
t=np.linspace(0,.05,5001);c_dv=10e-9;sr=2000/(c_dv*1e12)*1000 #V/s
prot=np.minimum(5,t*sr);buck_start=3.6/sr;tss=100e-9*.8/5.5e-6
v4=np.minimum(4,np.maximum(0,(t-buck_start)*4/tss));v4=np.minimum(v4,.98*prot)
v33=np.minimum(3.3,np.maximum(v4-.1,0));fig,ax=plt.subplots(figsize=(10,4.8));ax.plot(t*1e3,prot,label='eFuse slew envelope (0.2 V/ms)');ax.plot(t*1e3,v4,label='4 V buck ideal SS envelope');ax.plot(t*1e3,v33,label='3.3 V ceiling with assumed 100 mV headroom');ax.axvline((buck_start+tss)*1000,color='#64748b',ls=':',lw=1);ax.set(xlabel='Time after input becomes valid (ms)',ylabel='Voltage (V)',title='Startup timing envelope, not a coupled transient prediction');ax.legend(fontsize=9);fig.text(.1,-.04,'Uses typical slew/SS equations. Omits turn-on delays, current limit, capacitor charging, loop dynamics and boot load.',fontsize=9,color='#475569');save(fig,'04_startup_timing_envelope')
np.savetxt(D/'startup_envelope.csv',np.c_[t,prot,v4,v33],delimiter=',',header='time_s,efuse_slew_V,buck_ideal_SS_V,LDO_headroom_ceiling_V',comments='')
summary['startup_envelope']={'efuse_typ_slew_V_per_ms':sr/1000,'efuse_5V_rise_time_ms':5/sr*1000,'buck_typ_internal_UVLO_rising_V':3.6,'buck_typ_soft_start_ms':tss*1000,'ideal_buck_full_output_time_ms':(buck_start+tss)*1000,'not_actual_startup_prediction':True}
# Input power/DC headroom solution, retained feed plus explicit source resistance assumptions.
fig,axs=plt.subplots(1,3,figsize=(14,4.5),sharey=True);sweep=[]
for cable,ax in zip([0,.5,1.0],axs):
 vx=np.linspace(4.0,5.5,151);iy=np.linspace(.05,.6,111);V,I=np.meshgrid(vx,iy);rtotal=cable+.132+.0283+.197987032329;eta=.9
 p=4*I;disc=V*V-4*rtotal*p/eta
 iin=(V-np.sqrt(np.maximum(disc,0)))/(2*rtotal);vlocal=V-iin*rtotal
 head=.98*vlocal-I*(.076+.0441)-4
 # Positive margin is headroom only, not qualified operation/current budget.
 im=ax.pcolormesh(V,I*1000,head,cmap='RdYlGn',vmin=-.8,vmax=.8,shading='auto',rasterized=True)
 ax.contour(V,I*1000,head,levels=[0],colors='black',linewidths=1.3)
 for lim,color in[(.425,'#7c3aed'),(.575,'#dc2626')]:ax.contour(V,I*1000,iin,levels=[lim],colors=color,linestyles='--',linewidths=1)
 ax.set(title=f'Assumed cable/source R = {cable:g} Ω',xlabel='Upstream supply (V)')
 for vin in [4.4,4.75,5.0]:
  for load in [.15,.3,.5]:
   d=vin*vin-4*rtotal*4*load/eta;ii=(vin-math.sqrt(d))/(2*rtotal);vl=vin-ii*rtotal
   sweep.append({'source_R_ohm':cable,'upstream_supply_V':vin,'4V_output_total_A':load,'efficiency_assumed':eta,'input_A':ii,'buck_VIN_V':vl,'modeled_regulation_headroom_V':.98*vl-load*(.076+.0441)-4,'below_min_efuse_current_limit':ii<.425})
axs[0].set_ylabel('Total current on 4 V domain (mA)');fig.colorbar(im,ax=axs,label='Modeled dropout headroom (V)',fraction=.02,pad=.02);fig.suptitle('DC headroom and input-current sensitivity, with explicit assumptions',y=1.04);fig.text(.08,-.06,'Black: zero headroom. Purple/red dashes: 0.425/0.575 A eFuse thresholds. η = 90%, 98% duty, RHS = 76 mΩ typical; no guarantee.',fontsize=9,color='#475569');save(fig,'05_dc_headroom_map');summary['DC_scenarios']=sweep
with (D/'dc_sweep.csv').open('w')as f:
 w=csv.DictWriter(f,fieldnames=sweep[0].keys());w.writeheader();w.writerows(sweep)
# Buck ripple/LC small-signal natural-frequency sensitivity (not loop stability).
rip=[]
for vin,l,fs,c in itertools.product([4.4,5,5.5],[3.76e-6,4.7e-6,5.64e-6],[450e3,500e3,550e3],[24e-6,44e-6]):
 di=(vin-4)*4/(vin*l*fs);vr=di/(8*fs*c);rip.append({'VIN_V':vin,'L_uH':l*1e6,'fs_kHz':fs/1000,'C_uF':c*1e6,'CCM_inductor_ripple_A_pp':di,'ideal_capacitive_ripple_V_pp':vr,'natural_LC_Hz':1/(2*np.pi*np.sqrt(l*c))})
summary['ripple_analysis']={'scope':'CCM ideal approximation only; light-load PFM,spread-spectrum,ESR,layout and closed-loop dynamics excluded','corners':len(rip),'current_ripple_A_pp_range':[min(x['CCM_inductor_ripple_A_pp']for x in rip),max(x['CCM_inductor_ripple_A_pp']for x in rip)],'capacitive_voltage_ripple_V_pp_range':[min(x['ideal_capacitive_ripple_V_pp']for x in rip),max(x['ideal_capacitive_ripple_V_pp']for x in rip)],'natural_LC_Hz_range':[min(x['natural_LC_Hz']for x in rip),max(x['natural_LC_Hz']for x in rip)]}
with(D/'ripple_corners.csv').open('w')as f:w=csv.DictWriter(f,fieldnames=rip[0].keys());w.writeheader();w.writerows(rip)
summary['source_unchanged']=(hashlib.sha256(R.read_bytes()).hexdigest()==H) if source_checked else None
if source_checked: assert summary['source_unchanged']
(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'SPICE_runs':len(summary['spice_runs']),'plots':len(list(P.glob('*.png'))),'RC_error_V':err,'startup':summary['startup_envelope'],'input_recovery':hot,'source_unchanged':summary['source_unchanged'],'source_hash_checked_this_run':source_checked},indent=2))
