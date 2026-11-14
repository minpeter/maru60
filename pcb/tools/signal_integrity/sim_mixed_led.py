"""Mixed reverse/underglow LED SPICE sensitivity study on explicit routed inputs.

No vendor output or input models exist in this repository. Driver strength,
input capacitance and inner reference-plane geometry are assumed and swept.
Near/far uniform microstrip references are sensitivity cases, not bounds on a
3-D board with split planes. The legacy sim_led qualification guard stays intact.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,math,os,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import fieldsolve as fs
import spice
from geom import Board
from extract_geometry import led_chains
from sim_led import pwl

PROFILES={
 'SK6812MINI-E-012':dict(vih=.65,vil=.30,t0min=250,t0max=400,t1min=700,t1max=1000,t0low=800,t1low=200),
 'SK6805-EC15-001':dict(vih=.78,vil=.35,t0min=200,t0max=400,t1min=700,t1max=None,t0low=700,t1low=200)}
DRIVERS={'strong_assumed':(10.,1.,5.),'fast_assumed':(20.,2.,5.),'medium_assumed':(100.,10.,5.),'weak_assumed':(500.,30.,5.),'weak_capacitive_assumed':(1000.,30.,15.)}

def measure(t,v,profile,vdd=4.):
 lo,hi=profile['vil']*vdd,profile['vih']*vdd
 rows=[];budgets=[]
 for bit,start,on in [('0',2500.,300.),('1',3700.,900.)]:
  sel=(t>=start-50)&(t<=start+1140);x,y=t[sel],v[sel]
  uphi=spice.crossings(x,y,hi,True);uplo=spice.crossings(x,y,lo,True);dnhi=spice.crossings(x,y,hi,False);dnlo=spice.crossings(x,y,lo,False)
  if not all([uphi,uplo,dnhi,dnlo]):rows.append({'bit':bit,'error':'required threshold not crossed'});continue
  wmin=dnhi[-1]-uphi[0];wmax=dnlo[-1]-uplo[0]
  extra=sum(len(z)-1 for z in [uphi,uplo,dnhi,dnlo])
  # Stable middle of each plateau; threshold recrossings are counted separately.
  high=y[(x>=start+on*.4)&(x<=start+on*.85)];low=y[(x>=start+on+(1200-on)*.4)&(x<=start+1100)]
  vals={'bit':bit,'width_min_ns':float(wmin),'width_max_ns':float(wmax),'extra_threshold_crossings':extra,'high_margin_V':float(high.min()-hi) if len(high) else None,'low_margin_V':float(lo-low.max()) if len(low) else None}
  b={'high_above_min_ns':float(wmin-profile['t'+bit+'min']),'low_above_min_ns':float(1200-wmax-profile['t'+bit+'low'])}
  maximum=profile['t'+bit+'max']
  if maximum is not None:b['high_below_max_ns']=float(maximum-wmax)
  vals['timing_margins']=b;budgets+=list(b.values());rows.append(vals)
 passed=len(budgets)>0 and len(rows)==2 and all('error' not in r and r['extra_threshold_crossings']==0 and min(r['high_margin_V'],r['low_margin_V'])>=0 for r in rows) and min(budgets)>=0
 return dict(meets_assumed_corner=bool(passed),pulses=rows,minimum_timing_margin_ns=min(budgets) if budgets else None,unclamped_overshoot_V=float(v.max()-vdd),unclamped_undershoot_V=float(-v.min()))

def ladder(d,a,b,length,width,layer,tables):
 if length<=1e-9:d.add(f"R{d.uid('j')} {a} {b} 1m");return
 p=tables['inner' if layer.startswith('In') else 'outer'][round(width,6)]
 count=max(1,math.ceil(length/2));step=length/count;prev=a
 for k in range(count):
  mid=d.uid('m');nxt=b if k==count-1 else d.uid('n');tag=d.uid('')
  d.add(f'R{tag} {prev} {mid} {p["R"]*step:.8g}',f'L{tag} {mid} {nxt} {p["L_nH_per_mm"]*step:.8g}n',f'C{tag} {nxt} 0 {p["C_pF_per_mm"]*step:.8g}p');prev=nxt

def add_route(d,route,a,b,tables,base):
 stubs=sorted((s for s in route['stubs'] if s['length_mm']>.3),key=lambda s:s['from_src_mm']);node=a;pos=0.;si=0
 def stub(node,s):
  prev=node
  for layer,length in s['layers'].items():
   nxt=d.uid('stub');ladder(d,prev,nxt,length,.2,layer,tables);prev=nxt
  for _ in range(s['vias']):nxt=d.uid('sv');d.via(prev,nxt,base);prev=nxt
  d.add(f'C{d.uid("pad")} {prev} 0 0.15p')
 for i,e in enumerate(route['elements']):
  last=i==len(route['elements'])-1
  if e[0]=='via':nxt=b if last else d.uid('v');d.via(node,nxt,base);node=nxt;continue
  _,layer,w,length=e;end=pos+length
  while si<len(stubs) and stubs[si]['from_src_mm']<=end+1e-6:
   cut=min(length,max(0.,stubs[si]['from_src_mm']-pos))
   if cut>1e-9:
    nxt=d.uid('p');ladder(d,node,nxt,cut,w,layer,tables);node=nxt;pos+=cut;length-=cut
   stub(node,stubs[si]);si+=1
  nxt=b if last else d.uid('p');ladder(d,node,nxt,max(length,0.),w,layer,tables);node=nxt;pos=end
 if node!=b:d.add(f'R{d.uid("j")} {node} {b} 1m')
 for s in stubs[si:]:stub(b,s)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('geometry',type=Path);ap.add_argument('lines',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);spice.DECKS=out/'decks';spice.OUT=out/'raw';spice.DECKS.mkdir(exist_ok=True);b=Board(a.geometry);base=json.loads(a.lines.read_text());chain=led_chains(b)
 assert len(chain['key'])==64 and len(chain['underglow'])==12
 routes=[]
 for ch,hops in chain.items():
  for index,(net,src,dst,pre) in enumerate(hops):
   source=pre['from'] if pre else src
   sourcepads=[p for p in b.fps[source[0]]['pads'] if p['num']==source[1]];destpads=[p for p in b.fps[dst[0]]['pads'] if p['num']==dst[1]]
   for si,di in itertools.product(range(len(sourcepads)),range(len(destpads))):
    choices={source:sourcepads[si],dst:destpads[di]}
    def pick(p):
     q=choices.get((p['ref'],p['num']));return q is None or math.hypot(p['x']-q['x'],p['y']-q['y'])<1e-6
    route=b.route(net,src,dst,pick);assert route,(net,src,dst)
    prefix=(b.route(pre['net'],pre['from'],pre['to'],pick),pre['ohm']) if pre else None
    first=index==0
    if first:
     buf='U5' if ch=='key' else 'U6';bufnet='KEY_RGB_5V_BUF' if ch=='key' else 'UNDERGLOW_5V_BUF'
     prefix=(b.route(bufnet,(buf,'4'),(src[0],'1')),float(b.fps[src[0]]['value']))
    routes.append(dict(chain=ch,net=net,source=list(source),destination=list(dst),source_site=si,destination_site=di,route=route,pre=prefix,first_buffer_output=first,receiver_part=b.fps[dst[0]]['value']))
 widths={.2}|{round(e[2],6) for r in routes for q in [r['route'],r['pre'][0] if r['pre'] else None] if q for e in q['elements'] if e[0]=='track'}
 tables={}
 outer={w:fs.single(w) for w in widths}
 for w,p in outer.items():p['R']=1.72e-5/(w*.035)
 for name,h in [('near_reference_assumed',.2104),('far_reference_assumed',1.065)]:
  inner={w:fs.single(w,h=h,t=.0152,mask=0.) for w in widths}
  for w,p in inner.items():p['R']=1.72e-5/(w*.0152)
  tables[name]={'outer':outer,'inner':inner}
 (out/'line-models.json').write_text(json.dumps(tables,indent=2)+'\n')
 jobs=[(i,r,name,driver,params) for i,r in enumerate(routes) for name in tables for driver,params in DRIVERS.items()]
 def run(job):
  i,r,line,driver,params=job;resistance,edge,cin=params;name=f'led_{i:03d}_{line[:4]}_{driver}';d=spice.Deck(f'Mixed LED sensitivity: {r["receiver_part"]} {r["net"]} {line} {driver}')
  wave,tend=pwl('0101',4.,edge*1e-9);d.add(f'Vsrc src 0 PWL({wave})',f'Rdrv src dout {resistance}','Cdout dout 0 2p')
  start='dout'
  if r['pre']:
   add_route(d,r['pre'][0],start,'rs1',tables[line],base);d.add(f'Rseries rs1 rs2 {r["pre"][1]}');start='rs2'
  add_route(d,r['route'],start,'din',tables[line],base);d.add(f'Cin din 0 {cin}p')
  try:
   wave=d.run(name,['v(din)'],tran=f'0.2n {tend*1e9+100:.0f}n 0 0.2n');m=measure(wave['time']*1e9,wave['v(din)'],PROFILES[r['receiver_part']]);np.savez_compressed(spice.OUT/(name+'.npz'),**wave);(spice.OUT/(name+'.txt')).unlink()
   return {k:v for k,v in r.items() if k not in ['route','pre']}|dict(case=name,line_model=line,driver=driver,driver_assumptions={'R_ohm':resistance,'edge_ns':edge,'Cin_pF':cin},length_mm=r['route']['length_mm'],stub_mm=r['route']['stub_total_mm'],series_ohm=r['pre'][1] if r['pre'] else 0,measurement=m)
  except Exception as exc:return dict(case=name,net=r['net'],error=str(exc),simulation_complete=False)
 result=[]
 with ThreadPoolExecutor(max_workers=a.workers) as pool:
  for row in pool.map(run,jobs):
   result.append(row)
   if len(result)%20==0:print('mixed LED',len(result),'/',len(jobs),flush=True);(out/'progress.json').write_text(json.dumps({'completed':len(result),'total':len(jobs)}))
 report={'scope':__doc__,'geometry_sha256':hashlib.sha256(a.geometry.read_bytes()).hexdigest(),'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'profiles':PROFILES,'receiver_supply_V':4.,'threshold_note':'Reverse LED VIH/VIL ratios tested in supplier sheet at 5 V; applying those ratios at 4 V is an assumption.','first_hop_note':'First hops start at the buffer output with swept output impedance; MCU-to-buffer input is covered separately by geometry/misc and existing timing assumptions.','route_population_count':len(routes),'total_cases':len(result),'numerical_failures':sum('error' in r for r in result),'corners_not_meeting_assumptions':sum('error' not in r and not r['measurement']['meets_assumed_corner'] for r in result),'cases':result}
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print({k:report[k] for k in ['route_population_count','total_cases','numerical_failures','corners_not_meeting_assumptions']},flush=True)
if __name__=='__main__':main()
