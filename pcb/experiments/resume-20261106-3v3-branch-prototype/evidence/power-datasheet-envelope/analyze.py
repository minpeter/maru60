from pathlib import Path
from fractions import Fraction as F
import itertools,json,hashlib,xml.etree.ElementTree as E
D=Path(__file__).resolve().parent;B=D.parents[1]/'pcb/maru60.kicad_pcb';N=D/'netlist.xml';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert H(B)=='88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e'
# Source schematics are byte-identical to the source of this netlist; checked checkpoint companion hashes.
r=E.parse(N).getroot();values={q.attrib['ref']:q.findtext('value') for q in r.find('components')};nodes={q.attrib['name']: sorted((x.attrib['ref'],x.attrib['pin']) for x in q.findall('node')) for q in r.find('nets')}
import pcbnew as p
board=p.LoadBoard(str(B));parts={q.GetReference():q for q in board.GetFootprints()}
expected={'R120':'590k 0.1%','R121':'156k 0.1%','R122':'620k 0.1%','R123':'267k 0.1%','U8':'TPS259470LRPW'}
for ref,value in expected.items():
 assert values[ref]==parts[ref].GetValue()==value
 if ref.startswith('R'):
  np={(net,pin)for net,ns in nodes.items()for rr,pin in ns if rr==ref};bp={(pad.GetNetname(),pad.GetNumber())for pad in parts[ref].Pads()};assert np==bp
assert values['U8']=='TPS259470LRPW';assert {x[0]for x in nodes['USB_UVLO']}=={'R122','R123','U8'};assert {x[0]for x in nodes['USB_OVLO']}=={'R120','R121','U8'}
ranges={};allrows=[]
for key,top,bot,lo,hi in [('UV_enable',620000,267000,'1.183','1.223'),('UV_disable',620000,267000,'1.076','1.116'),('OV_disable',590000,156000,'1.183','1.223'),('OV_reenable',590000,156000,'1.076','1.116')]:
 rows=[]
 for st,sb,t,si in itertools.product([-1,1],[-1,1],[F(lo),F(hi)],[-1,1]):
  rt=F(top)*(1+F(st,1000));rb=F(bot)*(1+F(sb,1000));i=F(si,10000000);v=t*(1+rt/rb)+i*rt
  rows.append({'type':key,'Rtop_ohm':float(rt),'Rbottom_ohm':float(rb),'Vpin_V':float(t),'I_into_pin_A':float(i),'input_threshold_V':float(v),'exact_rational_V':str(v)})
 low=min(rows,key=lambda x:x['input_threshold_V']);high=max(rows,key=lambda x:x['input_threshold_V']);ranges[key]={'min_V':low['input_threshold_V'],'max_V':high['input_threshold_V'],'low_corner':low,'high_corner':high};allrows+=rows
# The explicit ratio and signed-leakage equation is independently checked using divider Thevenin form.
for row in allrows:
 rt=F(str(row['Rtop_ohm']));rb=F(str(row['Rbottom_ohm']));vp=F(str(row['Vpin_V']));i=F(str(row['I_into_pin_A']));v=(vp+i*(rt*rb/(rt+rb)))*((rt+rb)/rb);assert v==F(row['exact_rational_V'])
result={'source_pcb_sha256':H(B),'netlist_sha256':H(N),'U8_value':values['U8'],'UVLO_nodes':nodes['USB_UVLO'],'OVLO_nodes':nodes['USB_OVLO'],'equation':'Vbus = Vpin*(1+Rtop/Rbottom) + I_into_pin*Rtop','corners':allrows,'ranges':ranges,'source':'TI TPS25947 SLVSFC9C revised May2026, electrical characteristics pp8-9; https://www.ti.com/lit/ds/symlink/tps25947.pdf','table_test_conditions':'TJ -40 to125 C; VIN12V and remaining default test conditions unless noted. Do not claim these calculations independently qualify every input/temperature/load condition.','assumptions':['Independent resistor deviations limited to nominal0.1%; specific populated MPN/TCR/aging not established.','Only specified U8 pin leakage +/-0.1uA; excludes board leakage, contamination and other parasitics.','Static divider equation; excludes delays, dVdt, current limiting, capacitance, control loops, supply loss and dynamics.'],'method':'64 exact-rational static corners and independent Thevenin equation crosscheck; no active SPICE solve.'};(D/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:{q:v[q]for q in ['min_V','max_V']}for k,v in ranges.items()},indent=2))
