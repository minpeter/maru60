from pathlib import Path
import collections,datetime,hashlib,json,shutil,subprocess,zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path.cwd();raw=root/'build/bottom-sim-20261114';candidate=root/'pcb/experiments/resume-20261113-bottom-assembly-prototype';out=candidate/'evidence/simulation-suite-20261114';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
board=candidate/'pcb/maru60.kicad_pcb';geometry=candidate/'evidence/final-geometry.json';baseline=root/'pcb/experiments/resume-20261113-mcu-near-usb-zero-opens/pcb/maru60.kicad_pcb'
assert sha(board)=='875ee106148f266e6fc24f938eddfaef901e4a263cc295df41cfb3e270a8301d'
assert sha(geometry)==sha(raw/'geometry.json')=='9359f5505ebaee21363d35e8ebf7cbcf4857b7103d6ddb86cdc66652954e21d7'
assert sha(baseline)=='2cc544c8e6eb00bd3f53fa480a0167dcb8e14dac687f7eb2af0c85946bda5584'
led=read(raw/'mixed-led/results.json');sup=read(raw/'supplement/results.json');pwm=read(raw/'pwm/results.json');thermal=read(raw/'thermal-final/results.json');usb=read(raw/'si-final/out/usb.json');matrix=read(raw/'si-final/out/matrix.json');xtal=read(raw/'si-final/out/xtal.json');power=read(raw/'power-corrected-labels.json')['results'];fw=read(raw/'current-firmware-netlist.json');calls=read(raw/'power2/calls.json')
assert len(calls)==30 and all(x.get('complete') for x in calls)
assert led['numerical_failures']==0 and led['total_cases']==810 and len(thermal['steady_cases'])==360 and pwm['total_cases']==1620
failed=[r for r in led['cases'] if not r['measurement']['meets_assumed_corner']];refined_bad=[r for r in sup['numerical_sensitivity'] if not r['refined']['meets_assumed_corner']];first_bad=[r for r in sup['first_hop'] if not r['measurement']['meets_assumed_corner']];xtalk_bad=[r for r in sup['crosstalk'] if not r['meets_assumed_corner']]
# Read each test result; do not infer success from the last shell command.
tests={}
for name in ['signal','spice','bottom','reverse']:
 text=(raw/f'tests-{name}.log').read_text();assert '\nOK\n' in text and 'FAILED' not in text
 import re
 tests[name]=int(re.search(r'Ran (\d+) tests',text).group(1))
rows=thermal['steady_cases'];coarse={(str(x['population']),x['case'],x['sheet_W_per_K'],x['face_heat_transfer_W_m2K']):x for x in rows if x['grid_mm']==1.};fine=[x for x in rows if x['grid_mm']==.5]
deltas=[]
for x in fine:
 y=coarse[(str(x['population']),x['case'],x['sheet_W_per_K'],x['face_heat_transfer_W_m2K'])];d=abs(x['maximum_rise_C']-y['maximum_rise_C']);deltas.append((d,100*d/x['maximum_rise_C']))
thermal_summary={}
for n in dict.fromkeys(x['case'] for x in rows):
 vals=[x['maximum_rise_C'] for x in fine if x['case']==n];nom=[x['maximum_rise_C'] for x in fine if x['case']==n and x['sheet_W_per_K']==.01 and x['face_heat_transfer_W_m2K']==5.]
 thermal_summary[n]={'rise_range_C':[min(vals),max(vals)],'nominal_assumption_rise_range_C':[min(nom),max(nom)]}
pwm_selected=[r for r in pwm['cases'] if r['keys']==64 and r['PWM_Hz_assumed']==1000 and r['ESR_ohm_assumed']==.005 and r['limit_A']==.174 and r['phase']=='aligned']
first_refinement=read(raw/'first-refinement/results.json')
summary={'status':'Simulation campaign complete; electrical LED issues remain; NOT FOR FABRICATION','board_sha256':sha(board),'geometry_sha256':sha(geometry),'fresh_netlist_sha256':sha(raw/'netlist.xml'),'counts':{'power_SPICE':30,'LED_route_population_driver_line_SPICE':810,'buffer_to_first_LED_SPICE':len(sup['first_hop']),'first_hop_timestep_sensitivity_SPICE':len(first_refinement['cases']),'crosstalk_SPICE':len(sup['crosstalk']),'LED_timestep_sensitivity_SPICE':len(sup['numerical_sensitivity']),'USB_transient_including_delay':10,'USB_dielectric_delay':5,'matrix_analog_SPICE':len(matrix['cases']),'crystal_AC_negative_resistance':len(xtal['negative_resistance']),'crystal_drive_level':len(xtal['drive_level_bound']),'PWM_charge_cases':1620,'thermal_steady_grid_material_population_load_cases':360,'thermal_ambient_offsets_per_case':4,'thermal_transient_runs':1,'regression_tests':sum(tests.values()),'ideal_matrix_pressed_subsets':sum(sum(r['exhaustive_pressed_subsets'].values()) for r in fw['matrix_results'])},'LED':{'route_population_count':led['route_population_count'],'initial_failed_corners':len(failed),'failures_by_driver':dict(collections.Counter(r['driver'] for r in failed)),'time_refined_flagged_remaining':len(refined_bad),'time_refined_decision_changes':sum(not r['same_decision'] for r in sup['numerical_sensitivity']),'first_hop_failed_assumed_corners':len(first_bad),'first_hop_refined_flagged_remaining':sum(not x['measurement']['meets_assumed_corner'] for x in first_refinement['cases']),'crosstalk_failed_assumed_corners':len(xtalk_bad),'crosstalk_minimum_margin_V':min(r['threshold_margin_V'] for r in sup['crosstalk'])},'PWM':{'all_cases_below_spec':sum(not r['stays_above_3p7'] for r in pwm['cases']),'selected':pwm_selected,'instantaneous_key_peak_A':2.784,'aligned_on_time_us':1000*5/255},'USB_delay_ns':usb['delay']['simulated']['J1_to_RP2350_pins_ns'],'matrix':{'select_worst_ns':max(r['t_col_below_VIL_ns'] for r in matrix['cases'].values()),'release_worst_us':max(r['t_col_above_VIH_after_release_us'] for r in matrix['cases'].values())},'thermal':thermal_summary,'thermal_grid_max_difference_C':max(x[0] for x in deltas),'thermal_grid_max_difference_percent':max(x[1] for x in deltas),'thermal_max_energy_error_W':max(x['numerical_energy_balance_error_W'] for x in rows),'firmware_current_netlist_pass':fw['pass'],'firmware_RGB_qualification':0,'test_counts':tests,'hardware_measured':False}
write(out/'summary.json',summary)
# Compact accepted outputs, retaining the original raw power labels with a correction.
files={'first-refinement/results.json':'led/first-refinement.json','refine_first_hop.py':'source/refine_first_hop.py','mixed-led/results.json':'led/results.json','mixed-led/line-models.json':'led/line-models.json','supplement/results.json':'led/supplement.json','pwm/results.json':'pwm/results.json','pwm/waveforms.json':'pwm/waveforms.json','thermal-final/results.json':'thermal/results.json','power2/results.json':'power/raw-results.json','power-corrected-labels.json':'power/corrected-results.json','power2/provenance.json':'power/provenance.json','power2/calls.json':'power/calls.json','current-firmware-netlist.json':'firmware/current-netlist.json','firmware/results.json':'firmware/portable.json','usb-dielectric-final.json':'signal/usb-dielectric.json','field-selftest.log':'signal/field-selftest.log','netlist.xml':'inputs/netlist.xml'}
for n in ['usb','matrix','xtal','misc','lines','geometry']:files[f'si-final/out/{n}.json']=f'signal/{n}.json'
for p in (raw/'si-final').glob('*-provenance.json'):files[str(p.relative_to(raw))]='signal/'+p.name
for p in (raw/'si-final/plots').glob('*.png'):files[str(p.relative_to(raw))]='plots/'+p.name
for p in raw.glob('tests-*.log'):files[p.name]='tests/'+p.name
for src,dst in files.items():dest=out/dst;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(raw/src,dest)
for directory,target in [(root/'pcb/tools/signal_integrity',out/'source/signal_integrity'),(raw/'power2/model',out/'source/power-model-executed')]:
 target.mkdir(parents=True,exist_ok=True)
 for p in directory.iterdir():
  if p.is_file() and p.suffix in ['.py','.lib','.inc','.cir']:shutil.copyfile(p,target/p.name)
for p in [root/'pcb/tools'/n for n in ['run_bottom_power_suite.py','simulate_bottom_pwm.py','simulate_bottom_thermal.py']]+[root/'tests'/n for n in ['test_signal_geometry.py','test_spice_runner.py','test_bottom_simulation.py','test_reverse_led_analysis.py']]:
 dest=out/'source'/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
shutil.copyfile(Path(__file__),out/'assemble_report.py')
# Standalone exportable figure: board temperature rise in the declared nominal model.
z=np.load(raw/'thermal-final/temperature-maps.npz');xy=z['xy_mm'];v=z['typical_idle_plus_PWM_average_LED14-0_LED15-0']
fig,ax=plt.subplots(figsize=(10,4));sc=ax.scatter(xy[:,0],-xy[:,1],c=v,s=1,cmap='inferno',rasterized=True);ax.set_aspect('equal');ax.set_title('Board temperature rise: assumed average LED load, primary population');ax.set_xlabel('x (mm)');ax.set_ylabel('-y (mm)');fig.colorbar(sc,ax=ax,label='Rise above ambient (°C)');fig.tight_layout();fig.savefig(out/'plots/thermal-rise.png',dpi=160);plt.close(fig)
# Decks provide a small portable reproduction artifact; large raw arrays stay in build/.
accepted=['first-refinement','mixed-led','supplement','si-final','dielectric-final','power2','thermal-final','pwm','firmware']
with zipfile.ZipFile(out/'spice-decks.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ['first-refinement','mixed-led','supplement','si-final','dielectric-final','power2']:
  for p in sorted((raw/name).rglob('*')):
   if p.is_file() and p.suffix in ['.cir','.inc','.lib']:z.write(p,str(p.relative_to(raw)))
raw_index=[]
for name in accepted:
 for p in sorted((raw/name).rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:raw_index.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)})
write(out/'raw-artifacts.json',raw_index)
print(json.dumps(summary,ensure_ascii=False,indent=2))
