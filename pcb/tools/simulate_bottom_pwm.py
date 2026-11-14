"""Exact piecewise capacitor/current-limit sensitivity screen for reverse LEDs.

Stops at the first violation of the selected part's 3.7 V supply minimum; it
never extrapolates a constant-current LED below its specified supply range.
Capacitance, ESR, phase and PWM frequency are explicit assumptions. Only 1 kHz
is a datasheet typical, with no guaranteed min/max. No physical qualification.
"""
import argparse,hashlib,itertools,json,math
from pathlib import Path
import numpy as np

def simulate(n,code,hz,cap,esr,ilim,phase,source=4.,rpath=.2844,idle=.0444,cycles=3):
 period=1/hz;duty=code/255;v=source-idle*rpath;t=0.;events={0.:0.,cycles*period:0.};peak=.0145*3
 for cycle in range(cycles):
  for i in range(n):
   start=(cycle+(i/n if phase=='distributed' else 0))*period;end=start+duty*period
   if start<cycles*period:events[start]=events.get(start,0)+peak
   if end<cycles*period:events[end]=events.get(end,0)-peak
 current=idle;points=[];vmin=source
 def terminal(v,load):
  supply=max(0.,min(ilim,(source-v+load*esr)/(rpath+esr)))
  return v+(supply-load)*esr
 def advance(v,load,dt):
  boundary=source+load*esr-ilim*(rpath+esr);equilibrium=source-load*rpath;tau=(rpath+esr)*cap
  if v<=boundary:
   slope=(ilim-load)/cap
   if slope<=0 or v+slope*dt<=boundary:return v+slope*dt
   dt-=(boundary-v)/slope;v=boundary
  if load>ilim and equilibrium<boundary:
   crossing=tau*math.log((v-equilibrium)/(boundary-equilibrium)) if v>boundary else 0.
   if crossing<dt:return boundary+(ilim-load)*(dt-crossing)/cap
  return equilibrium+(v-equilibrium)*math.exp(-dt/tau)
 for time,delta in sorted(events.items()):
  dt=time-t;new=advance(v,current,dt);end_voltage=terminal(new,current)
  if end_voltage<3.7:
   lo,hi=0.,dt
   for _ in range(45):
    mid=(lo+hi)/2
    if terminal(advance(v,current,mid),current)<3.7:hi=mid
    else:lo=mid
   points.append([(t+hi)*1e6,3.7]);return dict(stays_above_3p7=False,first_below_spec_us=(t+hi)*1e6,min_valid_voltage=3.7,points=points)
  v=new;t=time;vmin=min(vmin,end_voltage);points.append([t*1e6,end_voltage]);current+=delta;post=terminal(v,current);vmin=min(vmin,post);points.append([t*1e6,post])
  if post<3.7:return dict(stays_above_3p7=False,first_below_spec_us=t*1e6,min_valid_voltage=3.7,points=points)
 return dict(stays_above_3p7=True,first_below_spec_us=None,min_valid_voltage=vmin,points=points)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 rows=[];waves={}
 for n,hz,cu,esr,ilim,phase in itertools.product([1,8,16,32,64],[500,1000,2000],[8.9,12.5,47,100,220,470],[.005,.05,.1],[.174,.202,.234],['aligned','distributed']):
  code=min(255,1020//(3*n));r=simulate(n,code,hz,cu*1e-6,esr,ilim,phase);points=r.pop('points');row=dict(keys=n,RGB_code=code,PWM_sum=3*n*code,PWM_Hz_assumed=hz,effective_cap_uF=cu,ESR_ohm_assumed=esr,limit_A=ilim,phase=phase,**r);rows.append(row)
  if n==64 and hz==1000 and esr==.005 and ilim==.174 and cu in [8.9,12.5,220,470] and phase=='aligned':waves[str(cu)]=points
 nominal=[r for r in rows if r['effective_cap_uF']==8.9 and r['PWM_Hz_assumed']==1000 and r['ESR_ohm_assumed']==.005]
 report={'scope':__doc__,'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_V':4.,'minimum_LED_supply_V':3.7,'reverse_channel_peak_A':.0145,'combined_idle_A_typical':.0444,'source_path_R_ohm_assumed':.2844,'current_limit_response':'ideal instantaneous clamp; real response and source transients belong to the SPICE model/hardware','population':'64 reverse keys max; 12 underglow dark but their typical idle load included','capacitance_note':'8.9 uF is existing nominal derated assumption; 12.5 uF is nominal sum; larger values are hypothetical, not fitted','total_cases':len(rows),'existing_assumed_cap_at_typical_frequency':{'cases':len(nominal),'below_spec':sum(not r['stays_above_3p7'] for r in nominal)},'cases':rows}
 (a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');(a.output/'waveforms.json').write_text(json.dumps(waves,indent=2)+'\n');print(report['total_cases'],report['existing_assumed_cap_at_typical_frequency'])
if __name__=='__main__':main()
