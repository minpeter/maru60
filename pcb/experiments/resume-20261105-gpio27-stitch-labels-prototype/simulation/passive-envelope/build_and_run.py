from pathlib import Path
from decimal import Decimal
import pcbnew as p,numpy as np,sys,re,json,hashlib,subprocess,math
R=Path('/workspace/shared/maru60-resume');D=R/'continuation-c782/power-envelope';BOARD=R/'combined-trial/pcb/maru60.kicad_pcb';H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert H(BOARD)=='56d66f65bb1f30d6ec7860f398cfd4f2399f3a9d305ef80d4bebab721d2571d9';b=p.LoadBoard(str(BOARD));refs=['C100','C120','C140','C141'];inventory=[];total=Decimal(0)
for ref in refs:
 f=next(q for q in b.GetFootprints()if q.GetReference()==ref);pads={q.GetNumber():q.GetNetname()for q in f.Pads()};assert pads=={'1':'+4V_REG','2':'GND'};value=f.GetValue();m=re.match(r'([0-9.]+)\s*u',value);assert m,value;nominal=Decimal(m.group(1));total+=nominal;inventory.append({'reference':ref,'value':value,'nominal_uF':str(nominal),'pads':pads})
assert total==Decimal('49.7');runner=R/'power-replay-20261105/inputs/v7-power-simulation/ngrun.py';results=[]
for frac in [Decimal('1'),Decimal('0.5'),Decimal('0.2')]:
 for hold_us in [10,50,100]:
  for direction in ['load','unload']:
   capacitance=total*frac;name=f'fraction_{str(frac).replace(".","p")}_{hold_us}us_{direction}';deck=D/'cases'/(name+'.cir');out=D/'runs'/name;assert not out.exists();ireg,ilast=(Decimal('.1'),Decimal('.3'))if direction=='load'else(Decimal('.3'),Decimal('.1'));stop=Decimal(5)+Decimal(hold_us);sign=1 if direction=='load'else-1
   deck.write_text(f'''Synthetic charge-balance sensitivity; NOT active/current-board stability
* Source PCB SHA256 {H(BOARD)}
* Verified directly connected nominal capacitance: C100+C120+C140+C141 = {total}uF
* ASSUMED effective fraction {frac}; neither measured value nor confidence bound
* ASSUMED initial capacitor voltage4V, aggregate ESR0.02ohm, fixed regulator current
* ASSUMED load delta0.2A,10ns ramp, no regulator response for{hold_us}us
Ireg 0 out {ireg}
Iload out 0 PWL(0 {ireg} 5u {ireg} 5.01u {ilast})
RESR out cnode 0.02
Cout cnode 0 {capacitance}u IC=4
.tran .05u {stop}u 0 .05u UIC
.end
''')
   run=subprocess.run(['/usr/bin/python3',str(runner),str(deck),str(out),'v(out)','v(cnode)'],capture_output=True,text=True,timeout=45);(out/'call.log').write_text(run.stdout+run.stderr);assert run.returncode==0,(name,run.stderr);a=np.loadtxt(out/'waveform.txt',skiprows=1);assert a.ndim==2 and np.isfinite(a).all();end=float(stop)*1e-6;assert abs(a[-1,0]-end)<1e-12;bad=['simulation interrupted','simulation(s) aborted','timestep too small','circuit not parsed','mif-error','unknown model type'];log=(out/'ngspice.log').read_text().lower();assert not any(x in log for x in bad)
   expected=4-sign*.2*((hold_us-.005)*1e-6/(float(capacitance)*1e-6)+.02);err=abs(a[-1,1]-expected);assert err<1e-5,(name,err)
   result={'case':name,'effective_fraction_assumption':str(frac),'capacitance_uF_assumption':str(capacitance),'fixed_regulator_time_us_assumption':hold_us,'direction':direction,'rows':len(a),'end_time_s':float(a[-1,0]),'minimum_output_V':float(a[:,1].min()),'maximum_output_V':float(a[:,1].max()),'final_output_V':float(a[-1,1]),'analytic_finite_ramp_endpoint_V':expected,'analytic_error_V':err,'deck_sha256':H(deck),'waveform_sha256':H(out/'waveform.txt')};results.append(result);print(name,result['final_output_V'],flush=True)
report={'classification':'Current-nameplate-informed synthetic charge-balance sensitivity only; not current-board or active stability simulation','board_sha256':H(BOARD),'verified_components':inventory,'verified_nominal_sum_uF':str(total),'assumptions':{'initial_voltage_V':4,'step_delta_A':.2,'aggregate_ESR_ohm':.02,'ramp_ns':10,'effective_fractions':['1','0.5','0.2'],'fixed_current_holds_us':[10,50,100]},'unknown_or_excluded':['True per-part effective capacitance, bias, tolerance, aging and temperature','Per-part ESR/ESL and distributed trace/plane parasitics','Buck feedback/current limit/control loop','eFuse, LED load behavior and rail state','Any real edge rate, transient workload, startup/fault/brownout behavior','Pass/fail operating thresholds'], 'all18_runs_and_analytic_checks_pass':True,'runs':results,'scope':'This bench addresses omission of directly connected nominal capacitors from historical selected-capacitor examples; it does not fill the active-model coverage gap.'};(D/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');assert H(BOARD)==report['board_sha256']
