#!/usr/bin/env python3
"""Read-only original study review; isolated numerical reproduction, no native CAD APIs."""
from pathlib import Path
from decimal import Decimal as D
import json,csv,hashlib,shutil,subprocess,itertools,xml.etree.ElementTree as E,re
OUT=Path(__file__).resolve().parent
STUDY=OUT.parent/'v7-c124-capacitance-options-20261104'
ROOT=OUT.parent/'pcb-v7-recovery-20261104'
REL=Path('pcb/experiments/v7-reference-legibility')
PCB=ROOT/REL/'candidate/pcb/maru60.kicad_pcb';XML=ROOT/REL/'qa/recovery-native/netlist.xml'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def fmap(root):return {str(p.relative_to(root)):H(p) for p in sorted(root.rglob('*')) if p.is_file()}
before=fmap(STUDY);source_before={str(p):H(p) for p in (PCB,XML)}
assert H(PCB)=='7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1'
manifest=json.loads((STUDY/'MANIFEST.json').read_text());print('Study manifest',manifest)
m=manifest.get('files',manifest)
assert all(H(STUDY/k)==(v['sha256'] if isinstance(v,dict) else v) for k,v in m.items())
snapshot=OUT/'input-study';snapshot.mkdir(exist_ok=False)
for p in STUDY.iterdir():
 if p.is_file():shutil.copyfile(p,snapshot/p.name)
replay=OUT/'isolated/reproduction';replay.mkdir(parents=True)
shutil.copyfile(snapshot/'calculate.py',replay/'calculate.py')
for rel in ('candidate/pcb/maru60.kicad_pcb','qa/recovery-native/netlist.xml'):
 dst=OUT/'isolated/pcb-v7-recovery-20261104'/REL/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/REL/rel,dst)
run=subprocess.run(['python3','-B',str(replay/'calculate.py')],capture_output=True,text=True,check=False)
(OUT/'reproduction.stdout.log').write_text(run.stdout);(OUT/'reproduction.stderr.log').write_text(run.stderr)
assert run.returncode==0
for f in ('results.json','sensitivity.csv'):assert (replay/f).read_bytes()==(snapshot/f).read_bytes(),f
j=json.loads((snapshot/'results.json').read_text());rows=list(csv.DictReader((snapshot/'sensitivity.csv').open()))
assert len(rows)==1200
opts={'baseline_10n_10pct_direct':(D('10'),D('.10')),'same_10n_plus_100ohm':(D('10'),D('.10')),'counterexample_8p2n_10pct':(D('8.2'),D('.10')),'YAGEO_CC0402JRX7R9BB822':(D('8.2'),D('.05')),'TDK_C1005X7R1H682K050BA':(D('6.8'),D('.10'))}
expected=set(itertools.product(opts,('-1','1'),('-1','1'),('1','.90','.75','.50'),('1','5.8','10','50','100'),('4.4','5','5.25')))
seen=set();max_errors={k:0 for k in ('C_eff_nF','SR_design_V_per_ms','ramp_design_ms','cap_only_inrush_mA')}
for row in rows:
 key=tuple(row[k] for k in ('option','initial_sign','temperature_sign','hypothetical_remaining_C_factor','Cload_uF','input_V'))
 assert key in expected and key not in seen;seen.add(key)
 name,sig,tig,factor,load,vin=key;c,tol=opts[name]
 # Independent dimensioned SI computation: inverse capacitance proportionality.
 cf=c*D('1e-9')*(1+D(sig)*tol)*(1+D(tig)*D('.15'))*D(factor)
 volts_per_second=D('2e-6')/cf
 calc={'C_eff_nF':cf/D('1e-9'),'SR_design_V_per_ms':volts_per_second/D('1000'),'ramp_design_ms':D(vin)/volts_per_second*1000,'cap_only_inrush_mA':D(load)*D('1e-6')*volts_per_second*1000}
 for k,v in calc.items():
  error=abs(D(row[k])-v);assert error<D('1e-12'),(key,k,error);max_errors[k]=max(max_errors[k],float(error))
assert seen==expected
for row in j['options']:
 c,tol=opts[row['option']];lo=c*(1-tol)*D('.85');hi=c*(1+tol)*D('1.15')
 assert row['initial_plus_assumed_X7R_range_nF']==[float(lo),float(hi)]
 assert abs(D(str(row['nominal_5V_design_ramp_ms']))-D('5')*c/D('2'))<D('1e-12')
 assert abs(D(str(row['nominal_5p8uF_capacitive_inrush_mA']))-D('5.8')*D('2')/c)<D('1e-12')
 assert row['upper_initial_plus_temp_headroom_to_10nF_pF']==float((10-hi)*1000)
 assert row['initial_plus_temp_exceeds_10nF']==(hi>10)
 assert abs(D(str(row['ideal_pin_C_over_I_ms_per_volt_range'][0]))-lo/D('3.82'))<D('1e-12')
 assert abs(D(str(row['ideal_pin_C_over_I_ms_per_volt_range'][1]))-hi/D('.81'))<D('1e-12')
R=j['options'][1];assert R['R_plus1pct_C_upper_RC_us']==float(D('101')*D('12.65')/1000) and R['R_plus1pct_Idvdt_max_drop_mV']==float(D('101')*D('3.82')/1000)
x=E.parse(XML).getroot();cs={c.attrib['ref']:c for c in x.find('components')};nets={n.attrib['name']:{(q.attrib['ref'],q.attrib['pin']) for q in n.findall('node')} for n in x.find('nets')}
assert nets['USB_DVDT']=={('C124','1'),('U8','7')}
assert {n for n in nets['VBUS_PROTECTED_RAW'] if n[0].startswith('C')}=={('C126','1'),('C136','1'),('C137','1')}
assert ('U18','3') in nets['VBUS_PROTECTED_RAW']
assert cs['C124'].findtext('value')=='10nF 10% 50V' and cs['C124'].findtext('footprint')=='Capacitor_SMD:C_0603_1608Metric'
assert not any('MPN' in q.attrib.get('name','').upper() or 'DIELECTRIC' in q.attrib.get('name','').upper() for q in cs['C124'].iter())
u18_en_nets={k:list(v) for k,v in nets.items() if ('U18','2') in v}
# XML omits explicitly no-connect pins; the PCB still carries the named unconnected net.
board=PCB.read_text();footprints=re.findall(r'\n\t\(footprint\s.*?\n\t\)',board,re.S)
physical={}
for ref in ('C124','C126','C136','C137','U8','U18'):
 f=next(q for q in footprints if f'(property "Reference" "{ref}"' in q)
 pads=re.findall(r'\(pad "([^"]+)".*?\(net \d+ "([^"]+)"',f,re.S)
 physical[ref]={'value':re.search(r'\(property "Value" "([^"]+)"',f).group(1),'pads':pads}
assert ('1','USB_DVDT') in physical['C124']['pads'] and ('2','GND') in physical['C124']['pads']
assert ('7','USB_DVDT') in physical['U8']['pads']
assert all(('1','VBUS_PROTECTED_RAW') in physical[c]['pads'] and ('2','GND') in physical[c]['pads'] for c in ('C126','C136','C137'))
assert ('2','unconnected-(U18-EN_FLOAT_ENABLE-Pad2)') in physical['U18']['pads'] and ('3','VBUS_PROTECTED_RAW') in physical['U18']['pads']
assert D('1')+D('.1')+D('4.7')==D('5.8')
assert before==fmap(STUDY) and source_before=={str(p):H(p) for p in (PCB,XML)}
report={'arithmetic_pass':True,'scope':'Analytical sensitivity audit only; no CAD/BOM edits, active SPICE, native CAD load/fill/save or hardware qualification.','original_study_files':before,'source_file_hashes':source_before,'isolated_reproduction_exit_code':run.returncode,'both_results_byte_equal':True,'unique_complete_sweep_rows':len(rows),'independent_SI_max_absolute_errors':max_errors,'exact_corner_caps_nF':{'8.2nF_10pct_plus15pct':10.373,'8.2nF_5pct_plus15pct':9.9015,'6.8nF_10pct_plus15pct':8.602},'source_pin_inventory':physical,'XML_U18_EN_nets':u18_en_nets,'U18_EN_intentionally_floating_in_netlist_status':cs['U18'].find('fields/field[@name="Status"]').text,'baseline_C124_footprint':'0603 metric1608','proposed_both_package':'0402 metric1005; not assumed drop-in','source_study_unchanged':True,'limitations':['The 1200 rows are a complete factorial of assumed constant-capacitance cases, not vendor active-controller simulations.','Manufacturer capacitance tolerance and X7R temperature factors alone do not prove combined all-condition effective capacitance.','The 5.8uF nominal sum excludes active buck/downstream load, capacitor bias/aging, source impedance, current limits and thermal dynamics.','No source/physical net completeness beyond the stated source bindings and checked relevant pin sets is newly claimed.']}
(OUT/'arithmetic-source-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'arithmetic_pass':True,'source_study_unchanged':True,'sweep_rows':len(rows),'max_errors':max_errors},indent=2))
