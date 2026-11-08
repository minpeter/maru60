from pathlib import Path
import hashlib,json,csv,itertools,os,xml.etree.ElementTree as ET
_private=Path(__file__).resolve().parent/'runtime'
for _k in ['HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','MPLCONFIGDIR']:
 _p=_private/_k;_p.mkdir(parents=True,exist_ok=True,mode=0o700);os.environ[_k]=str(_p)
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parent;w=r.parent;board=w/'pcb-v7-recovery-20261104/pcb/experiments/v7-reference-legibility/candidate/pcb/maru60.kicad_pcb';plan=Path('/tmp/v7-c124-rebound-short/PLAN_MANIFEST.json');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(board)=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'
netlist=w/'pcb-v7-recovery-20261104/pcb/experiments/v7-reference-legibility/qa/recovery-native/netlist.xml'
x=ET.parse(netlist).getroot();values={v.get('ref'):v.findtext('value')for v in x.find('components')};nets={n.get('name'):{(t.get('ref'),t.get('pin'))for t in n.findall('node')}for n in x.find('nets')}
assert values['C124']=='10nF 10% 50V' and nets['USB_DVDT']=={('C124','1'),('U8','7')}
assert {k:values[k]for k in ['R120','R121','R122','R123']}=={'R120':'590k 0.1%','R121':'156k 0.1%','R122':'620k 0.1%','R123':'267k 0.1%'}
assert nets['USB_OVLO']=={('R120','2'),('R121','1'),('U8','2')} and nets['USB_UVLO']=={('R122','2'),('R123','1'),('U8','1')}
f=np.logspace(2,8,601);s=2j*np.pi*f
# All parasitics below are hypothetical matched scenarios, never extraction from route length.
scenarios=[('low',1e-12,.1,.5e-9,.05,.3e-9,.01e-12),('central',2e-12,.3,2e-9,.15,.8e-9,.1e-12),('high',5e-12,1.,10e-9,.5,2e-9,1e-12)]
options=[('10n_direct',10e-9,0),('10n_100R',10e-9,100),('8p2n_NP0_direct',8.2e-9,0)]
rows=[];curves={};checks=[]
for name,cp,rt,lt,esr,esl,cc in scenarios:
 for opt,c,rs in options:
  zlink=rt+rs+s*lt;zc=esr+s*esl+1/(s*c);yp=s*cp;yl=1/zlink;yc=1/zc
  for inject in ['pin','cap']:
   a=yp+yl+(s*cc if inject=='pin'else 0);d=yc+yl+(s*cc if inject=='cap'else 0);b=-yl
   rhs0=s*cc if inject=='pin'else np.zeros_like(s);rhs1=s*cc if inject=='cap'else np.zeros_like(s)
   v0=(rhs0*d-b*rhs1)/(a*d-b*b);v1=(a*rhs1-b*rhs0)/(a*d-b*b)
   # Independently solve nodal equations with LAPACK at every frequency.
   matrices=np.array([[a,b],[b,d]]).transpose(2,0,1);rhs=np.array([rhs0,rhs1]).T;sol=np.linalg.solve(matrices,rhs[...,None])[...,0]
   err=np.max(np.abs(sol[:,0]-v0));scale=max(float(np.max(np.abs(v0))),1e-30);assert err/scale<1e-9,(name,opt,inject,err/scale)
   kcl0=a*v0+b*v1-rhs0;kcl1=b*v0+d*v1-rhs1;res=max(np.max(np.abs(kcl0)),np.max(np.abs(kcl1)))/max(float(np.max(np.abs(rhs))),1e-30);assert res<1e-8
   curves[name,opt,inject]=v0;checks.append({'scenario':name,'option':opt,'inject':inject,'relative_crosscheck_max':float(err/scale),'normalized_KCL_residual':float(res)})
   for freq,h in zip(f,v0):rows.append({'scenario':name,'option':opt,'pickup_location':inject,'frequency_Hz':float(freq),'Vpin_per_1V_aggressor_real':float(h.real),'Vpin_per_1V_aggressor_imag':float(h.imag),'magnitude_V_per_V':float(abs(h))})
# UVLO/OVLO divider: exact resistor values, hypothetical C to ground/coupled aggressor.
dividers={'UVLO':(620e3,267e3),'OVLO':(590e3,156e3)};div=[]
for node,(top,bottom)in dividers.items():
 rth=1/(1/top+1/bottom)
 for cg,cc in itertools.product([1e-12,5e-12,20e-12],[.01e-12,.1e-12,1e-12]):
  h=s*cc/(1/rth+s*(cg+cc));alt=(s*cc*rth)/(1+s*rth*(cg+cc));assert np.max(np.abs(h-alt))<1e-14
  div.append({'node':node,'Rtop_ohm':top,'Rbottom_ohm':bottom,'Rthevenin_ohm':rth,'assumed_Cground_pF':cg*1e12,'assumed_Ccoupling_pF':cc*1e12,'high_frequency_ratio_Cc_over_Ctotal':cc/(cg+cc),'decay_tau_us':rth*(cg+cc)*1e6,'at_1MHz_magnitude_V_per_V':float(abs(2j*np.pi*1e6*cc/(1/rth+2j*np.pi*1e6*(cg+cc))))})
central={}
for inject in ['pin','cap']:
 central[inject]={opt:{str(int(q)):float(abs(curves['central',opt,inject][np.argmin(abs(f-q))])) for q in [1e3,1e6,1e7,1e8]}for opt,_,_ in options}
fig,axs=plt.subplots(1,3,figsize=(14,4.4),layout='constrained')
for ax,inject in zip(axs[:2],['pin','cap']):
 for opt,_,_ in options:ax.loglog(f,np.abs(curves['central',opt,inject])*1000,label={'10n_direct':'10 nF direct','10n_100R':'10 nF + 100 Ω','8p2n_NP0_direct':'8.2 nF direct (C only)'}[opt])
 ax.set(xlabel='Frequency (Hz)',ylabel='Pin response (mV / 1 V aggressor)',title=f'Hypothetical pickup at {inject} node');ax.grid(True,which='both',alpha=.2);ax.legend(fontsize=8)
for name,(top,bottom)in dividers.items():
 rt=1/(1/top+1/bottom);cg=5e-12;cc=.1e-12;h=s*cc/(1/rt+s*(cg+cc));axs[2].loglog(f,abs(h)*1000,label=name)
axs[2].set(xlabel='Frequency (Hz)',ylabel='Sense response (mV / 1 V aggressor)',title='Divider pickup: assumed 5 pF + 0.1 pF');axs[2].grid(True,which='both',alpha=.2);axs[2].legend();fig.suptitle('Passive sensitivity only: no controller, extracted parasitics or board prediction',fontsize=12);fig.savefig(r/'passive-comparison.png',dpi=180);fig.savefig(r/'passive-comparison.svg')
report={'status':'UNREVIEWED_PASSIVE_SENSITIVITY_NOT_ADOPTED','board_sha256':sha(board),'netlist_sha256':sha(netlist),'source_nodes_and_values_asserted':True,'plan_manifest_sha256':sha(plan),'constructed_candidate':False,'parasitics_derived_from_geometry':False,'active_controller_model':False,'frequency_range_Hz':[100,1e8],'scenario_fields':['name','Cpin_F','trace_R_ohm','trace_L_H','capacitor_ESR_ohm','capacitor_ESL_H','coupling_F'],'scenarios':scenarios,'options':options,'AC_points':len(rows),'independent_matrix_crosschecks':checks,'central_response_V_per_1V':central,'divider_scenarios':div,'notes':['Selected board is unchanged. V4 plan is analytical and unconstructed.','The 100 ohm resistor satisfies a separate manufacturer recommendation; this passive model cannot establish its active-controller purpose.','Pin-side series resistance can increase this hypothetical pickup while cap-side pickup behaves differently. It is not a predicted old/new board noise ratio.','8.2nF option is nominal-C-only substitution with matched assumed ESR/ESL; no NP0 dielectric/bias/temperature/aging model.','Divider supply and return are ideal AC grounds; supply noise, source impedance and common return are omitted.','UVLO/OVLO resistor topology is unchanged; changed routing does not determine Cground or Ccoupling.','No pin input clamps/filter, active eFuse, load/buck, return-plane extraction, transient/ESD, assembly or hardware qualification.']};(r/'results.json').write_text(json.dumps(report,indent=2)+'\n')
with (r/'ac-sweep.csv').open('w',newline='')as h:wcsv=csv.DictWriter(h,fieldnames=rows[0]);wcsv.writeheader();wcsv.writerows(rows)
print(json.dumps({'AC_points':len(rows),'matrix_cases':len(checks),'divider_cases':len(div),'central':central},indent=2))
