"""Bounded arithmetic only; no active-model run, CAD edit, or qualified input contract."""
from pathlib import Path
import json,itertools,hashlib
p=Path(__file__).parent;rt=590e3;rb=156e3;t=.001
# Normal input examples only; same values/tolerance in selected and D.
rows=[]
for vin in [5,5.25,5.5]:
 currents=[vin/(a+b) for a,b in itertools.product([rt*(1-t),rt*(1+t)],[rb*(1-t),rb*(1+t)])]
 rows.append({'Vin_example_V':vin,'nominal_OVLO_divider_uA':vin/(rt+rb)*1e6,'tolerance_only_uA':[min(currents)*1e6,max(currents)*1e6],'nominal_delta_selected_to_D_uA':0})
nom=lambda v:v*(1+rt/rb)
threshold={}
for name,vt in [('rising',1.2),('falling',1.09)]:
 vals=[vt*(1+a/b) for a,b in itertools.product([rt*(1-t),rt*(1+t)],[rb*(1-t),rb*(1+t)])]
 threshold[name]={'nominal_V':nom(vt),'tolerance_only_V':[min(vals),max(vals)],'nominal_delta_selected_to_D_V':0}
# Published test limits at different conditions, not a predicted drift comparison or baseline bound.
drift=[]
for name,d in [('KOA_RN73R_standard_1000h_85C',.001+.05/rb),('UNSELECTED_TNPW_general_1000h_70C',.0005+.01/rb)]:
 changes=[1.2*(1+rt/(rb*(1+s*d)))-nom(1.2) for s in [-1,1]]
 drift.append({'published_test_case':name,'bottom_fractional_test_limit':d,'R121_only_threshold_movement_V':changes,'excludes_R120_and_other_errors':True,'not_selected_baseline_or_actual_drift_prediction':True})
out={'scope':'Selected and D share nominal values and initial tolerances; not a full environmental or active threshold bound','example_currents':rows,'thresholds':threshold,'resistor_only_divider_Rthevenin_ohm':rt*rb/(rt+rb),'initial_tolerance_percent_each':.1,'nominal_C124_nF':10,'tolerance_only_C124_nF':[9,11],'TI_recommendation_trigger_nF':'>10','series_R125_ohm_tolerance_only':[99,101],'passive_RC_product_us':[99*9e-9*1e6,101*11e-9*1e6],'RC_product_is_not_startup_time':True,'published_R121_drift_limit_sensitivity':drift,'selected_baseline_R121_MPN_and_drift':'unknown; cannot assign TNPW or RN73R specs','undefined_inputs':['accepted VBUS_FUSED operating/fault/transient maximum','R120 MPN/TCR/tracking','complete drift budget','effective C124 over bias/temperature/aging','active dVdt discharge pulse and repetition']}
(p/'nominal-and-drift-deltas.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
