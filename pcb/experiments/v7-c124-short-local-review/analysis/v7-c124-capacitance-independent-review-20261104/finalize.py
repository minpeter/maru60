#!/usr/bin/env python3
from pathlib import Path
from decimal import Decimal as D
import json,hashlib,shutil,subprocess
P=Path(__file__).resolve().parent;S=P.parent/'v7-c124-capacitance-options-20261104'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=lambda r:{str(p.relative_to(r)):H(p) for p in sorted(r.rglob('*')) if p.is_file()}
before=files(S);m=json.loads((S/'MANIFEST.json').read_text())['files'];assert all(H(S/k)==v for k,v in m.items())
for k in ('calculate.py','results.json','sensitivity.csv'):assert (S/k).read_bytes()==(P/'input-study'/k).read_bytes()
for k in ('README.md','REVIEW-CORRECTIONS.md'):assert (S/k).read_bytes()==(P/'input-study'/k).read_bytes()
new=P/'np0-reproduction';new.mkdir(exist_ok=False)
for k in ('np0_option.py','NP0-ALTERNATIVE.md','np0-option.json'):shutil.copyfile(S/k,new/k)
old=H(new/'np0-option.json')
x=subprocess.run(['python3','-B',str(new/'np0_option.py')],capture_output=True,text=True);assert x.returncode==0
(P/'np0-reproduction.stdout.log').write_text(x.stdout);(P/'np0-reproduction.stderr.log').write_text(x.stderr)
assert H(new/'np0-option.json')==old==H(S/'np0-option.json')
a=json.loads((P/'np0-alternative-review.json').read_text());b=json.loads((S/'np0-option.json').read_text());q=a['coefficient_only_assumed_envelope']
assert b['coefficient_only_symmetric_envelope_nF']==[float(x) for x in q['range_nF']]
assert b['coefficient_only_margin_to_10nF_nF']==float(q['upper_headroom_to10nF_nF'])
assert b['coefficient_only_design_5V_ramp_ms']==[float(x) for x in q['5V_design_ramp_ms_range']]
assert b['coefficient_only_cap_only_inrush_range_mA']==[float(x) for x in q['5p8uF_cap_only_inrush_range_mA']]
assert b['nominal_design_5V_ramp_ms']==20.5 and b['complete_all_stress_bound'] is False
assert a['land_comparison_mm']['existing_inner_gap']==b['actual_existing_0603_pad_mm']['inner_gap']
assert a['land_comparison_mm']['existing_each_axial_pad_length']==b['actual_existing_0603_pad_mm']['length']
assert a['land_comparison_mm']['existing_pad_width']==b['actual_existing_0603_pad_mm']['width']
a['coefficient_constant_over_full_catalog_range_is_a_screening_extrapolation']=True
(P/'np0-alternative-review.json').write_text(json.dumps(a,indent=2)+'\n')
assert files(S)==before
r={'decision':'approval_eligible_as_read_only_analytical_screen_only','CAD_BOM_selection_approved':False,'source_board_sha256':'7c23d6ea36b158fa706fa3e05f0e1f10fa4aa435deecb2d3bcd38c71cf9f8cb1','study_final_files':before,'original_1200_row_numerical_files_unchanged':True,'original_reproduction_byte_exact':True,'NP0_reproduction_byte_exact':True,'independent_decimal_and_SI_crosschecks_pass':True,'official_source_facts_verified':True,'documentation_corrections_verified':['TI current RevC section7.3.5.1/p30 citation','TDK0402 alternative Production(NRND) disclosure','Existing0603 versus initial0402 alternatives clearly distinguished'],'blocking_numerical_or_source_defects':[],'remaining_limits':['The 1200-row sweep is assumed constant-capacitance sensitivity, not active vendorSPICE, extracted circuit transient simulation or hardware measurement.','The 5.8uF nominal sum is directly connected capacitor values only; active U18 buck/downstream startup load and effective capacitance are omitted.','The supported NP0 option is current Production but not selected. A constant±30ppm/degree coefficient applied to the entire-55..150C catalog range is a screening extrapolation; detailed coefficient test points do not independently guarantee a pointwise fullrange bound.','The NP0 pad gap meets the manufacturer recommendation, but existing pad length/width exceed it. This requires assembly review, not an assumption of unsafe assembly or automatic drop-in.','TI100ohm advice for capacitance above10nF is a design recommendation, not an absolute-maximum rating or proof of failure.','No capacitor change fixes the existing UVLO/buck operating-headroom problem.'],'source_study_unchanged_during_final_review':True,'review_artifacts':{'arithmetic_source_review':H(P/'arithmetic-source-review.json'),'np0_alternative_review':H(P/'np0-alternative-review.json'),'official_original_facts':H(P/'official-facts/verification.md'),'official_NP0_facts':H(P/'official-facts/c0g-0603-extension.md')}}
(P/'FINAL_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n')
(P/'REVIEW.md').write_text('''# Independent C124 comparison review\n\n**Approval-eligible as a read-only analytical screen. No BOM/CAD selection or hardware qualification.**\n\nThe exact7c23 source board and recorded netlist bindings are correct. C124 has no recorded exact MPN or dielectric. USB_DVDT contains only C124.1 and U8.7; the directly connected1uF+0.1uF+4.7uF capacitors sum to5.8uF nominal. U18 VIN is on that rail with EN intentionally floating, so the simple capacitive-current calculation excludes active startup load.\n\nThe original1,200 unique factorial rows were independently recomputed in Decimal/SI units. The original calculation was also reproduced in an isolated copy, yielding byte-identical results.json and sensitivity.csv. The separate NP0 calculation likewise reproduces byte-identically and matches independent arithmetic. No original CAD/BOM/study file was edited by this review.\n\nThe simplified upper corners are10.373nF for8.2nF±10% with+15%,9.9015nF for8.2nF±5% with+15%, and8.602nF for6.8nF±10% with+15%. They are conditional tolerance/temperature screens, not guaranteed assembled-circuit limits.\n\nManufacturer facts and the corrected TI citation, TDK NRND status and0603/0402 distinction are verified. TDK C1608NP01H822J080AA is a supported Production0603/NP0 candidate. Its conditional coefficient-extrapolation upper case is8.6422875nF, with1.3577125nF to10nF. Detailed coefficient testing uses25/85C and lower-temperature checks; applying a constant worst coefficient across the full catalog range is explicitly an assumption, not a verified pointwise guarantee.\n\nExisting C124 lands have0.65mm gap,0.90mm axial length and0.95mm width. TDK recommends0.60–0.80mm for each. The gap matches; length and width exceed recommendations by0.10/0.15mm. This requires assembly review and is neither automatic drop-in approval nor proof of unsafe assembly.\n\nOfficial links and source-specific qualifications are in official-facts/. Full source hashes, numerical checks and limitations are in FINAL_REVIEW.json and the two detailed JSON reviews. No activeSPICE, hardware startup, parasitic extraction or production qualification was performed.\n''')
# Compact audit packet excludes duplicated full PCB/XML input copies and reproduced duplicate numerical files.
include=[p for p in P.rglob('*') if p.is_file() and not any(q in ('isolated','np0-reproduction') for q in p.relative_to(P).parts) and p.name!='MANIFEST.json']
manifest={str(p.relative_to(P)):H(p) for p in sorted(include)}
(P/'MANIFEST.json').write_text(json.dumps({'scope':'Independent read-only arithmetic, source and official-fact review; no CAD/BOM selection','files':manifest},indent=2)+'\n')
print(json.dumps({'decision':r['decision'],'final_review_sha256':H(P/'FINAL_REVIEW.json'),'manifest_sha256':H(P/'MANIFEST.json'),'packet_files':len(manifest)},indent=2))
