from pathlib import Path
import itertools,json,hashlib,re
from fractions import Fraction as F
import pcbnew as p
D=Path(__file__).resolve().parent;B=D.parents[1]/'pcb/maru60.kicad_pcb';deck=D/'efuse_hysteresis.cir'
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert H(B)=='2e532c1a16e64a34eafafdfbd5b85c05d70bb12ad9e52924c5cbe024fdc9aa2c';b=p.LoadBoard(str(B));fp={x.GetReference():x for x in b.GetFootprints()};res={'R122':620000,'R123':267000,'R120':590000,'R121':156000};nets={'R122':{'VBUS_FUSED','USB_UVLO'},'R123':{'USB_UVLO','GND'},'R120':{'VBUS_FUSED','USB_OVLO'},'R121':{'USB_OVLO','GND'}};parts={}
for ref,v in res.items():
 q=fp[ref];assert q.GetValue()==str(v//1000)+'k 0.1%';pn={x.GetNumber():x.GetNetname()for x in q.Pads()};assert set(pn.values())==nets[ref];parts[ref]={'value':q.GetValue(),'pin_nets':pn,'nominal_ohm':v}
s=deck.read_text();assert 'Vt=1.145 Vh=0.055' in s and 'Vt=-1.145 Vh=0.055' in s
upper=F('1.145')+F('0.055');lower=F('1.145')-F('0.055')
def evaluate(r):
 uv=1+r['R122']/r['R123'];ov=1+r['R120']/r['R121'];return {'UV_enable_V':upper*uv,'UV_disable_V':lower*uv,'OV_disable_V':upper*ov,'OV_reenable_V':lower*ov}
nom=evaluate({k:F(v)for k,v in res.items()});corners=[]
for signs in itertools.product([-1,1],repeat=4):
 r={k:F(v)*(1+F(sign,1000))for(k,v),sign in zip(res.items(),signs)};out=evaluate(r);corners.append({'resistor_errors_percent':{k:s/10 for k,s in zip(res,signs)},'thresholds_V':{k:float(v)for k,v in out.items()}})
ranges={k:{'nominal_V':float(v),'min_V':min(x['thresholds_V'][k]for x in corners),'max_V':max(x['thresholds_V'][k]for x in corners)}for k,v in nom.items()}
# Independent closed-form extrema for each positive divider. No Monte Carlo claim.
for key,top,bot,threshold in [('UV_enable_V','R122','R123',upper),('UV_disable_V','R122','R123',lower),('OV_disable_V','R120','R121',upper),('OV_reenable_V','R120','R121',lower)]:
 lo=float(threshold*(1+F(res[top]*999,res[bot]*1001)));hi=float(threshold*(1+F(res[top]*1001,res[bot]*999)));assert ranges[key]['min_V']==lo and ranges[key]['max_V']==hi
out={'source_board_sha256':H(B),'behavioral_deck_sha256':H(deck),'components':parts,'assumed_comparator_thresholds_V':{'upper':float(upper),'lower':float(lower)},'corner_count':16,'method':'Exact rational resistor ratios; independent monotonic closed-form extrema; no SPICE run needed or claimed. Positive Vtop*(1+Rtop/Rbottom) is increasing in top resistance and decreasing in bottom resistance.','ranges':ranges,'corners':corners,'all_UV_enable_corners_below_synthetic_4V_target':all(x['thresholds_V']['UV_enable_V']<4 for x in corners),'scope':'Current-CAD resistor nominal and 0.1% nameplate tolerance sensitivity only, conditional on frozen synthetic comparator thresholds. NOT real U8 guaranteed threshold bounds, buck startup/fault validation or a current-board active model.','omitted':['Actual U8 threshold/hysteresis tolerances, temperature, leakage, delay, dVdt, current limiting, reverse flow and fault dynamics.','Resistor MPN/TCR/aging, parasitic loading, effective capacitors, source/load/temperature and regulator dynamics.']};(D/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(ranges,indent=2))
