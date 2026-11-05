from pathlib import Path
from fractions import Fraction as F
from itertools import product
import json,hashlib,xml.etree.ElementTree as E
import pcbnew
O=Path(__file__).resolve().parent
S=Path('/workspace/shared/maru60-resume/selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype/pcb')
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert H(S/'maru60.kicad_pcb')=='88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e'
b=pcbnew.LoadBoard(str(S/'maru60.kicad_pcb'))
refs=['U18','L2','R159','R160','C100','C120','C126','C136','C137','C138','C139','C140','C141']
a={f.GetReference():{'value':f.GetValue(),'footprint':str(f.GetFPID().GetLibItemName()),'fields':{x.GetName():x.GetText() for x in f.GetFields()},'pads':{x.GetNumber():x.GetNetname() for x in f.Pads()}} for f in b.GetFootprints() if f.GetReference() in refs}
t=E.parse(O/'netlist.xml'); c={x.attrib['ref']:x for x in t.findall('./components/comp')}; nets={}
for n in t.findall('./nets/net'):
 for p in n.findall('node'): nets[(p.attrib['ref'],p.attrib['pin'])]=n.attrib['name']
for ref,d in a.items():
 x=c[ref];d['schematic_fields']={v.attrib['name']:v.text for v in x.findall('./fields/field')};d['schematic_value']=x.findtext('value');d['net_parity']={k:nets.get((ref,k))==v for k,v in d['pads'].items()};assert d['schematic_value']==d['value']; assert all(d['net_parity'].values()),(ref,d)
(O/'components-audit.json').write_text(json.dumps(a,indent=2))
enc=lambda x:{'exact':str(x),'decimal':float(x)}
results={}
for name,lo,hi in [('25C','0.792','0.808'),('0_to_85C','0.788','0.812'),('minus40_to_150C','0.784','0.816')]:
 rows=[]
 for vr,rt,rb,ileak in product([F(lo),F(hi)],[F(40000)*F('0.999'),F(40000)*F('1.001')],[F(10000)*F('0.999'),F(10000)*F('1.001')],[F('-0.00000015'),F('0.00000015')]):
  v=vr*(1+rt/rb)+ileak*rt
  rows.append({'vref':enc(vr),'rt':enc(rt),'rb':enc(rb),'assumed_signed_leak_A':enc(ileak),'vout':enc(v)})
 results[name]={'assumption':'Conservative signed magnitude |IFB| <= 0.15uA, although table prints a positive MAX, not a signed min/max pair. Resistor initial tolerance only. Regulated operation.','min':min(r['vout']['decimal'] for r in rows),'max':max(r['vout']['decimal'] for r in rows),'corners':rows,'without_leak_min':enc(F(lo)*(1+F(40000)*F('.999')/(F(10000)*F('1.001')))),'without_leak_max':enc(F(hi)*(1+F(40000)*F('1.001')/(F(10000)*F('.999'))))}
results['soft_start']={'nominal_s':enc(F('100e-9')*F('.8')/F('5.5e-6')),'conditional_min_s':enc(F('90e-9')*F('.784')/F('6.5e-6')),'conditional_max_s':enc(F('110e-9')*F('.816')/F('4.5e-6')),'assumption':'C139 nameplate +/-10% only; no DC bias, temperature or aging loss. Time is SS-reference ramp, not observed board startup.'}
V=F(4);Vi=F(5);L=F('4.7e-6');f=F(500000);di=V*(Vi-V)/(Vi*L*f)
results['nominal_design_screen']={'assumption':'5V at U18 VIN; 4V regulated output; nominal 4.7uH, 500kHz, CCM. This is a design calculation, not a verified USB input range or load. 2A is IC rating only. No losses, saturation, frequency spread, PFM or transient effects.','delta_i_A':enc(di),'K_at_IC_2A_rating':enc(di/2),'peak_at_IC_rating_A':enc(2+di/2),'Cout_nominal_only_uF':49.7,'capacitive_ripple_nominal_only_V':enc(di/(8*f*F('49.7e-6'))),'L_at_K_0p4_at_IC_rating_H':enc(V*(Vi-V)/(Vi*f*F('.4')*2)),'minimum_Vin_no_foldback_ideal_V':enc(V/(1-f*F('140e-9'))),'minimum_Vin_98percent_ideal_V':enc(V/F('.98'))}
(O/'calculations.json').write_text(json.dumps(results,indent=2))
files=list(S.glob('*.kicad_sch'))+[S/'maru60.kicad_pcb',S/'Study.kicad_sym',O/'tps62932.pdf',O/'xal4000.pdf']
(O/'source-hashes.json').write_text(json.dumps({'pcbnew':pcbnew.Version(),'base_commit':'fa96a7c8b334f0f496ab7cdb4de9b18cf9276966','files':{str(p):H(p) for p in files}},indent=2))
print(json.dumps({k:{x:y for x,y in v.items() if x!='corners'} for k,v in results.items()},indent=2))
