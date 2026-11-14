"""Candidate-specific buffer, matrix crosstalk and LED numerical sensitivity.

All output stages and uniform return planes are assumptions. No IBIS, clamp,
3-D return-path, EMC certification or physical LED qualification is implied.
"""
import argparse,hashlib,json,re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import spice,fieldsolve as fs
from geom import Board
from extract_geometry import led_chains
from sim_led import pwl,sim_crosstalk
from sim_mixed_led import add_route,measure,PROFILES

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for name in ['geometry','extracted','lines','mixed','output']:ap.add_argument(name,type=Path)
 a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);spice.DECKS=out/'decks';spice.OUT=out/'raw';spice.DECKS.mkdir(exist_ok=True);spice.OUT.mkdir(exist_ok=True)
 b=Board(a.geometry);geo=json.loads(a.extracted.read_text());base=json.loads(a.lines.read_text());chain=led_chains(b)
 tables=json.loads((a.mixed/'line-models.json').read_text());tables={k:{layer:{float(w):v for w,v in tab.items()} for layer,tab in val.items()} for k,val in tables.items()}
 report={'scope':__doc__,'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.geometry,a.extracted,a.lines,Path(__file__)]},'first_hop':[],'crosstalk':[],'numerical_sensitivity':[]}
 def save(name,w):
  np.savez_compressed(spice.OUT/(name+'.npz'),**w);(spice.OUT/(name+'.txt')).unlink()
 cases={'typical_assumed':dict(rgpio=40,cbuf=2,vth=1.3,tpd=3.5,edge=1.5,rbuf=25,cin=5),'slow_assumed':dict(rgpio=125,cbuf=10,vth=1.75,tpd=6.5,edge=3.,rbuf=100,cin=15),'fast_low_threshold_assumed':dict(rgpio=40,cbuf=2,vth=.8,tpd=2.5,edge=1.,rbuf=15,cin=5)}
 for ch in chain:
  buf,pin,net=('U5','32','KEY_RGB') if ch=='key' else ('U6','33','UNDERGLOW')
  n,src,dst,pre=chain[ch][0];routes=[b.route(net,('U1',pin),(buf,'2')),b.route(n+'_BUF',(buf,'4'),(src[0],'1')),b.route(n,src,dst)];assert all(routes)
  for line,tab in tables.items():
   for cn,c in cases.items():
    name=f'first_{ch}_{line[:4]}_{cn}';d=spice.Deck(name);wave,tend=pwl('0101',3.3,1.5e-9)
    d.add(f'Vsrc src 0 PWL({wave})',f'Rgpio src gpio {c["rgpio"]}','Cgpio gpio 0 3p')
    add_route(d,routes[0],'gpio','bufin',tab,base)
    d.add(f'Cbufin bufin 0 {c["cbuf"]}p',f'Bthr thr 0 V=4/(1+exp(-(v(bufin)-{c["vth"]})/0.03))','Rthr thr dly_in 50',f'Tdly dly_in 0 dly_out 0 Z0=50 TD={c["tpd"]}n','Rdly dly_out 0 50','Eshp shp 0 dly_out 0 2','Rshp shp shpc 1k',f'Cshp shpc 0 {c["edge"]/2.2}p','Ebuf bufi 0 shpc 0 1',f'Rbuf bufi bufout {c["rbuf"]}','Cbufout bufout 0 2.5p')
    add_route(d,routes[1],'bufout','rin',tab,base);d.add('Rseries rin rout 330','Crpad rout 0 .1p');add_route(d,routes[2],'rout','din',tab,base);d.add(f'Cin din 0 {c["cin"]}p')
    cached=spice.OUT/(name+'.npz');deck=spice.DECKS/(name+'.cir')
    if cached.exists() and deck.exists() and deck.read_text().startswith('\n'.join(d.lines)+'\n'):
     with np.load(cached) as z:w={k:z[k] for k in z.files}
    else:
     w=d.run(name,['v(bufin)','v(din)'],tran='0.1n 5000n 0 0.1n');save(name,w)
    report['first_hop'].append(dict(case=name,chain=ch,line_assumption=line,driver_assumptions=c,receiver=dst,route_lengths_mm=[r['length_mm'] for r in routes],measurement=measure(w['time']*1e9,w['v(din)'],PROFILES[b.fps[dst[0]]['value']])))
 print('first hops',len(report['first_hop']),flush=True)
 # Pick two strongest local same-layer matrix-neighbour envelopes per chain.
 # Existing extraction lists the six largest neighbours, not an exhaustive EM model.
 selected=[]
 for ch in chain:
  rows=geo['led'][ch];opts=[]
  for row in rows:
   for other,nb in row.get('neighbours',{}).items():
    if re.fullmatch(r'(ROW|COL)\d+',other):opts.append(dict(chain=ch,victim=row['net'],aggressor=other,route_length_mm=row['length_mm'],**nb))
  opts.sort(key=lambda x:x['len_le_0p6']/max(.15,x['min_gap']),reverse=True)
  selected+=opts[:2]
 for idx,row in enumerate(selected):
  part=b.fps[next(dst[0] for net,src,dst,pre in chain[row['chain']] if net==row['victim'])]['value'];profile=PROFILES[part]
  width=max(t['w'] for t in b.by_net[row['victim']]);awidth=max(t['w'] for t in b.by_net[row['aggressor']]);clen=min(row['route_length_mm'],row['len_le_0p6']);gap=max(.15,row['min_gap'])
  for resistance in [20.,500.,1000.]:
   for level in [0.,4.]:
    name=f'xtalk_{idx}_{int(resistance)}_{int(level)}';m,w=sim_crosstalk(name,base,row['route_length_mm'],clen,gap,width,awidth,resistance,level);save(name,w)
    margin=profile['vil']*4-m['peak_pos_V'] if level==0 else 4-profile['vih']*4+m['peak_neg_V']
    report['crosstalk'].append(dict(case=name,geometry=row,assumed_uniform_coupled_mm=clen,assumed_uniform_gap_mm=gap,victim_width_mm=width,aggressor_width_mm=awidth,driver_ohm=resistance,quiet_V=level,threshold_margin_V=margin,meets_assumed_corner=margin>=0,**m))
 print('crosstalk cases',len(report['crosstalk']),flush=True)
 original=json.loads((a.mixed/'results.json').read_text())['cases'];bad=[r for r in original if not r['measurement']['meets_assumed_corner']];controls=[r for r in original if r['driver']=='fast_assumed'][:4];chosen=bad+controls
 # Time-step + tolerance sensitivity, fixed spatial discretisation. This is
 # not spatial convergence of the distributed-line approximation.
 def refine(row):
  name=row['case']+'_dt025';d=spice.Deck(name);text=(a.mixed/'decks'/(row['case']+'.cir')).read_text();d.lines=text.split('.tran')[0].splitlines();d.add('.options reltol=1e-4 abstol=1e-12 vntol=1e-7')
  w=d.run(name,['v(din)'],tran='0.025n 5000n 0 0.025n');save(name,w);m=measure(w['time']*1e9,w['v(din)'],PROFILES[row['receiver_part']])
  return dict(case=name,original_case=row['case'],net=row['net'],original=row['measurement'],refined=m,same_decision=m['meets_assumed_corner']==row['measurement']['meets_assumed_corner'])
 with ThreadPoolExecutor(max_workers=4) as pool:
  for r in pool.map(refine,chosen):report['numerical_sensitivity'].append(r)
 report['crosstalk_scope']='Four extracted neighbour envelopes, uniform outer-microstrip approximation, all coupled length placed at minimum gap; one matrix aggressor at a time. Width=max actual net width. Not a strict bound or exhaustive 3D coupling analysis.'
 report['numerical_scope']='All 37 flagged LED cases plus four fast-driver controls: 0.025 ns vs 0.2 ns max step, reltol 1e-4. Spatial ladder unchanged.'
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('supplement complete',flush=True)
if __name__=='__main__':main()
