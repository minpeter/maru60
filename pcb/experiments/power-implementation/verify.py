from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as E,math,builtins
P=Path(__file__).parent;S=P.parent/'correction-study-20261102';O=P/'native-max38902a'
sys.path.insert(0,'/workspace/shared/maru60-kicad-linux/pcb/tools')
from sexp import parse,get,all
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(path):
 r=E.parse(path).getroot();p={}
 for n in r.findall('./nets/net'):
  for x in n.findall('node'):p[(x.attrib['ref'],x.attrib['pin'])]=None if n.attrib['name'].startswith('unconnected-') else n.attrib['name']
 return p
base=S/'native-max38902a/v6-protection.xml'
assert sha(base)=='5d62cba98c3fd64e222d965e49bac21d20c4cafc1494dea342e10c9ac7b58f0d'
assert pins(base)==pins(O/'v6-protection.xml')
for name in ['input-protection','v6-regulated-domain','v6-rgb-translation','gpio-isolation']:
 assert sha(S/'native-max38902a'/f'{name}.kicad_sch')==sha(O/f'{name}.kicad_sch')
r=E.parse(O/'v6-protection.xml').getroot()
br=E.parse(base).getroot()
oldc={c.attrib['ref']:(c.findtext('value'),c.findtext('footprint')) for c in br.findall('./components/comp')}
newc={c.attrib['ref']:(c.findtext('value'),c.findtext('footprint')) for c in r.findall('./components/comp')}
assert set(oldc)==set(newc)
changed=[ref for ref in oldc if oldc[ref]!=newc[ref]]
assert set(changed)=={'U2','R163','C100','C101','C142'}
for b in json.loads((P/'bom.json').read_text()):
 c=r.find(f'./components/comp[@ref="{b["reference"]}"]');assert c is not None
 assert c.findtext('footprint')==b['footprint']
 assert c.find('fields/field[@name="MPN"]').text==b['mpn']
f=parse(next((O/'MaruStudy.pretty').glob('MAX*.kicad_mod')).read_text())
pads={p[1]:p for p in all(f,'pad') if p[1]}
assert set(pads)==set(map(str,range(1,10)))
for i in range(1,9):
 p=pads[str(i)];x,y=get(p,'at')[1:3]
 assert math.isclose(float(x),-.99 if i<5 else .99)
 assert math.isclose(float(y),-.75+.5*(i-1) if i<5 else .75-.5*(i-5))
 assert list(map(float,get(p,'size')[1:3]))==[.7,.3]
assert list(map(float,get(pads['9'],'size')[1:3]))==[.8,1.38]
board=parse((O/'ldo-placement-only.kicad_pcb').read_text())
refpads={}
for f in all(board,'footprint'):
 ref=next(x[2] for x in all(f,'property') if x[1]=='Reference')
 for p in all(f,'pad'):
  if not p[1]:continue
  n=get(p,'net');refpads[ref,str(p[1])]=n[2] if n else None
np=pins(O/'v6-protection.xml')
for key,n in refpads.items():assert np[key]==n,(key,n,np[key])
assert len(refpads)==17
assert not all(board,'segment') and not all(board,'via') and not all(board,'zone')
dr=json.loads((O/'placement-drc.json').read_text());assert not dr['violations'];assert len(dr['unconnected_items'])==12
erc=json.loads((O/'erc.json').read_text());assert builtins.all(not x.get('violations') for x in erc['sheets'])
main=Path('/workspace/shared/maru60-kicad-linux/pcb/maru60.kicad_pcb')
assert sha(main)=='80681cd392d1ca83bd37e58faef07a0def301f2d93763102982eaf1c0148f831'
# Conservative arithmetic allocation, not a combined environmental qualification guarantee.
R=31600.; terms_pct={'initial':.1,'TCR_105K_10ppm':.105,'225kh_70C_drift':.3+.05/R*100,'solder':.02+.01/R*100,'humidity':.1+.01/R*100,'thermal_cycles':.1+.01/R*100,'cold':.05+.01/R*100,'board_bend':.05+.01/R*100}
total=sum(terms_pct.values());assert total<1
calc={'resistor_error_allocation_percent':terms_pct,'sum_percent':total,'unused_to_1pct_percent':1-total,'I_at3p2_Rmax_uA':3.2/(R*(1+total/100))*1e6,'I_min_static_uA':3.267/(R*(1+total/100))*1e6,'I_max_static_uA':3.333/(R*(1-total/100))*1e6,
'C101_no_bias_no_aging_uF':4.7*.9*.85,'C101_min_combined_remaining_factor_for2uF':2/(4.7*.9*.85),
'C101_conditional_screen_uF':4.7*.9*.85*.9*.7,'C101_DF_test_ESR_upper_ohm_NOT_30mOhm_proof':.025/(2*math.pi*1000*4.7e-6*.9),
'BYP_68nF_alternate_initial_screen_nF':[68*.95*(1-.003),68*1.05*(1+.0058)],
'BYP_68nF_alternate_room_IR_Gohm_using_Cmax':500/(68e-9*1.05*1.0058)/1e9,
'BYP_68nF_alternate_room_IR_inferred_leak_nA_at3p4':3.4/(500/(68e-9*1.05*1.0058))*1e9,
'BYP_68nF_alternate_after_damp_IR_inferred_leak_nA_at3p4':3.4/(25/(68e-9*1.05*1.0058))*1e9,
'nominal_startup_ms':3.3/(5*.01/.010),'nominal_short_recovery_ms':3.3/(5*.01/.010)*500,
'nominal_10p7uF_startup_charge_mA':10.7e-6*(5*.01/.010)*1e6,
'BYP_10nF_room_leak_inference_nA_at3p4':3.4/10e9*1e9,'BYP_10nF_post_damp_leak_inference_nA_at3p4':3.4/500e6*1e9,
'BYP_comparison':[{'C_nF':c,'nominal_start_ms':3.3/(50/c),'nominal_recovery_ms':3.3/(50/c)*500,'nominal_10p7uF_charging_mA':10.7e-6*(50/c)*1e6} for c in [1.5,10,22,47,68]],
'LDO_normal_300mA_screen_W':(4.0865345345-3.267)*(.3+106.54e-6)+4.0865345345*.0006,
'EP_paste_coverage_fraction':2*.6*.55/(.8*1.38),'WARNINGS':['Error allocation sums independent test limits, not a manufacturer simultaneous lifetime guarantee.','No DC bias/aging/ESR all-corner guarantee is inferred from nominal/X7R/DF or typical curves.','BYP IR is measured at rated voltage and room temperature; inferred lower-voltage leakage is not guaranteed hot-PCB leakage.','No whole USB or fault current pass.']}
(P/'implementation-calculations.json').write_text(json.dumps(calc,indent=2)+'\n')
proof={'all_pin_net_endpoints_identical_to_reviewed_correction':True,'only_value_footprint_deltas':sorted(changed),'unchanged_other_child_sheets':4,'ERC_all_severity_violations':0,'MPN_properties_checked':5,'U2_land_pattern':'90-0065 Rev E copied dimensions verified','placement_pad_net_mappings_checked':17,'placement_unrouted_connections':12,'placement_other_DRC_violations':0,'placement_no_tracks_vias_planes':True,'accepted_main_sha256':sha(main),'reviewed_correction_manifest_sha256':sha(S/'manifest.json'),'candidate_xml_sha256':sha(O/'v6-protection.xml')}
assert proof['reviewed_correction_manifest_sha256']=='5021d103e7a0cff7a40223e8f14e1991e3427be898be3267497bd4a77fcc4737'
(P/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2));print(json.dumps(calc,indent=2))
