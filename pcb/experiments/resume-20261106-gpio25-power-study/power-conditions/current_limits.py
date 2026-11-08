#!/usr/bin/env python3
"""Portable conditional arithmetic; no active circuit model or vendor files needed."""
import json,pathlib,math,hashlib
from fractions import Fraction as F
p=pathlib.Path(__file__).resolve().parent
x=json.loads((p/'EVIDENCE.json').read_text())
assert x['components']['R124']['value']=='6.65k 0.1%'
assert x['components']['R124']['native_pins']=={'1':'USB_ILM','2':'GND'}
assert x['components']['R112']['value']=='133k 1%'
assert x['components']['R112']['native_pins']=={'1':'LED_ILIM','2':'GND'}
r=F(6650);tol=F(1,1000)
u8={'R_ohm':[float(r*(1-tol)),float(r),float(r*(1+tol))], 'nominal_equation_mA':float(3334/r*1000),'table_mA':[425,500,575],'recommended_R_ohm':[549,6650],'high_R_corner_numerically_above_table_endpoint_not_violation':r*(1+tol)>6650,'nominal_equation_resistor_only_mA':[float(3334/(r*(1+tol))*1000),float(3334/(r*(1-tol))*1000)]}
r7=133.;u7={'R_kohm':[r7*.99,r7,r7*1.01],'equation_mA':[25230/(r7*1.01)**1.016,23950/r7**.977,22980/(r7*.99)**.94],'recommended_R_kohm':[15,232]}
assert all(15<=r<=232 for r in u7['R_kohm'])
# Independent logarithmic evaluation of power-law equations.
for expected,k,r,e in zip(u7['equation_mA'],[25230,23950,22980],[r7*1.01,r7,r7*.99],[1.016,.977,.94]):
 assert math.isclose(expected,math.exp(math.log(k)-e*math.log(r)),rel_tol=1e-14)
assert u8['table_mA'][0]<500<u8['table_mA'][2]
out={'evidence_sha256':hashlib.sha256((p/'EVIDENCE.json').read_bytes()).hexdigest(),'U8':u8,'U7':u7,'descriptor_mA':500,'sources':[{'url':'https://www.ti.com/lit/ug/slvuc01/slvuc01.pdf','revision':'SLVUC01 September 2020','printed_pages':[5,23],'evidence':'R7/R20: 6.65 kohm 1%, Yageo RC0603FR-076K65L; counters automatic violation inferred from tolerance above rounded table endpoint.'},{'url':'https://www.ti.com/lit/ds/symlink/tps25947.pdf','revision':'SLVSFC9C May 2026','printed_pages':[8,9,32,33],'conditions':'Electrical table: TJ -40..125 C, VIN 12 V, VEN/UVLO 2 V, VOVLO 0 V; row RILM 6.65 kohm. Equation 7 nominal; resistor corners exclude IC variation.'},{'url':'https://www.ti.com/lit/ds/symlink/tps2553-1.pdf','revision':'SLVS841G October 2026','printed_pages':[5,6,7,16,17,18],'conditions':'Electrical table: recommended operation, EN 0/VIN, RFAULT 10 kohm. Programming equations include process/temperature, exclude external resistor tolerance; incorporated +/-1% here.'}],'checks':'PASS native snapshot resistor identity/net assertions; rational U8 arithmetic; independent log-form U7 arithmetic','limits':['No actual USB input current, efficiency or LED load assumed.','U8 resistor-only equation range is not a total tolerance envelope.','U8 nominal 6.65 kohm is supported by TI EVM 1% BOM; rounded upper endpoint alone does not establish a violation. Exact actual-versus-nominal table interpretation is unstated.','No dynamic, thermal, hardware or USB-compliance qualification.','Official sources accessed by web, no local PDF byte hash claimed.']}
(p/'CURRENT_LIMITS.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'U8':u8,'U7':u7,'arithmetic':'PASS'}))
