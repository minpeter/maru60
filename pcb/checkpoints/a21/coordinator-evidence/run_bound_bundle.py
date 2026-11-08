"""Run read-only native/source gates into a NEW directory; bind each completed output to exact inputs.
Usage: python run_bound_bundle.py INPUT.kicad_pcb NEW_OUTPUT_DIR
No PCB edits/refill/save. A complete bundle is not automatically semantically passed.
"""
from pathlib import Path
import json,hashlib,subprocess,sys,os,datetime,collections
B=Path(sys.argv[1]).resolve();D=Path(sys.argv[2]).resolve();assert B.is_file();D.mkdir(exist_ok=False)
P=Path('/workspace/shared/maru60-kicad-linux/pcb/tools/studies');guard=Path('/workspace/shared/maru-native-net-assignment-guard-0215/net_assignment_guard.py');sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();stamp=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
inputs=[B,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_sch')]+sorted(B.parent.glob('maru60-*.kicad_sch'))
for n in ['Maru60.kicad_sym','fp-lib-table','sym-lib-table']:
 if (B.parent/n).is_file():inputs.append(B.parent/n)
inputs+=sorted((B.parent/'Maru60.pretty').glob('*.kicad_mod'))
inputs=list(dict.fromkeys(inputs));assert all(x.is_file()for x in inputs);baseline={str(f):sha(f)for f in inputs};env=os.environ.copy();env.update(KICAD_CONFIG_HOME='/tmp/maru-kicad-config',XDG_CONFIG_HOME='/tmp/maru-kicad-config',XDG_CACHE_HOME='/tmp/maru-kicad-cache',XDG_DATA_HOME='/tmp/maru-kicad-data',KICAD9_SYMBOL_DIR='/usr/share/kicad/symbols',KICAD9_FOOTPRINT_DIR='/usr/share/kicad/footprints')
steps=[('intended-net-identity',['/usr/bin/python3',str(guard),str(B),str(D/'intended-net-identity.json')],[guard]),('native-drc',['kicad-cli','pcb','drc','--format','json','--all-track-errors','--severity-all','--schematic-parity','-o',str(D/'native-drc.json'),str(B)],[]),('ground',['/usr/bin/python3',str(P/'experiment_a4l_ground_witness.py'),str(B),str(D/'ground.json')],[P/'experiment_a4l_ground_witness.py'])]
for name,net,ref,pin in [('3v3','+3V3','U2','5'),('1v1','+1V1','L1','1'),('5v','+5V','F1','2'),('LX','VREG_LX','U1','48'),('AVDD','VREG_AVDD','R104','2'),('LED5V','+5V_LED','U7','6'),('KEY-data','KEY_RGB_5V','R110','2'),('BOOT','BOOT_BUTTON','R106','2'),('SS','QSPI_SS','U3','1'),('UG-BUF','UNDERGLOW_5V_BUF','U6','4'),('UG-output','UNDERGLOW_5V','R111','2'),('KEY-BUF','KEY_RGB_5V_BUF','U5','4')]:
 steps.append((name,['/usr/bin/python3',str(P/'experiment_a_power_witness.py'),str(B),str(D/(name+'.json')),net,ref,pin],[P/'experiment_a_power_witness.py',P/'experiment_a4l_ground_witness.py']))
steps += [('critical-reference',['/usr/bin/python3',str(P/'experiment_a4l_reference.py'),str(B),str(D/'critical-reference.json')],[P/'experiment_a4l_reference.py']),('native-erc',['kicad-cli','sch','erc','--format','json','--severity-all','-o',str(D/'native-erc.json'),str(B.with_suffix('.kicad_sch'))],[])]
state={'status':'RUNNING_NOT_A_COMPLETED_GATE_BUNDLE','started_utc':stamp(),'input_board':str(B),'input_board_sha256':baseline[str(B)],'bound_inputs':baseline,'native_version':subprocess.check_output(['kicad-cli','version'],env=env,text=True).strip(),'steps':[],'complete':False};out=D/'BUNDLE.json'
def save():out.write_text(json.dumps(state,indent=2))
save()
try:
 for name,cmd,code in steps:
  before={str(f):sha(f)for f in inputs};assert before==baseline,'Input changed before '+name
  code_before={str(f):sha(f)for f in code};entry={'name':name,'started_utc':stamp(),'command':cmd,'input_board_sha256_before':sha(B),'code_hashes_before':code_before};state['steps'].append(entry);save()
  log=D/(name+'.log')
  with log.open('w')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
  after={str(f):sha(f)for f in inputs};code_after={str(f):sha(f)for f in code};report=D/(name+'.json');entry.update(completed_utc=stamp(),returncode=r.returncode,input_board_sha256_after=sha(B),all_bound_inputs_unchanged=after==baseline,code_unchanged=code_after==code_before,log_sha256=sha(log),report_exists=report.is_file())
  assert r.returncode==0 and after==baseline and code_after==code_before and report.is_file(),'Incomplete/changed-input gate '+name
  data=json.loads(report.read_text());entry['report_sha256']=sha(report);entry['json_parsed']=True
  if 'unreached_components'in data:entry['semantic_pass']=not data['unreached_components'];entry['unreached_components']=len(data['unreached_components'])
  elif name=='intended-net-identity':entry['semantic_pass']=data['pass']
  elif name=='native-erc':entry['semantic_pass']=not any(s['violations']for s in data['sheets'])
  elif name=='native-drc':entry['hard_errors']=sum(v['severity']=='error'for v in data['violations']);entry['warnings']=sum(v['severity']=='warning'for v in data['violations']);entry['opens']=len(data['unconnected_items']);entry['semantic_pass']=entry['hard_errors']==0 and not data['schematic_parity']
  else:entry['semantic_pass']=None;entry['meaning']='Data recorded; comparison/reference exception disposition required separately.'
  save()
 raw=json.loads((D/'intended-net-identity.json').read_text())['raw_expected_net_names'];drc=json.loads((D/'native-drc.json').read_text());openrows=[]
 allowed={f'ROW{i}'for i in range(5)}|{f'COL{i}'for i in range(3,15)}|{'KEY_RGB','UNDERGLOW','LED_ENABLE','LED_FAULT_N','RUN','SWCLK','SWDIO'}
 for item in drc['unconnected_items']:
  ids=[x['uuid']for x in item['items']];assert all(u in raw for u in ids);nets=sorted({raw[u]for u in ids});openrows.append({'nets':nets,'uuids':ids,'within_explicit_current_A25_incomplete_set':set(nets)<=allowed})
 state.update(completed_utc=stamp(),status='COMPLETED_EXACT_INPUT_BOUND_BUNDLE',complete=True,all_bound_inputs_unchanged={str(f):sha(f)for f in inputs}==baseline,all_boolean_semantic_gates_pass=all(x.get('semantic_pass')is not False for x in state['steps']),native_open_contract={'all_item_UUIDs_resolved':True,'unexpected_net_open_items':[x for x in openrows if not x['within_explicit_current_A25_incomplete_set']],'open_counts_by_net':dict(collections.Counter(n for x in openrows for n in x['nets']))},caveat='Complete means all listed processes terminated successfully and reports bind exact unchanged inputs; reference acceptance, cold refill, exact delta/functions, powered/physical qualification remain separate. Never report a RUNNING/FAILED bundle as complete. P3 reconstruction may intentionally fail source/open contract and is not A25-comparable.')
 assert state['all_bound_inputs_unchanged'];save();print(json.dumps({k:state[k]for k in ['status','input_board_sha256','complete','all_boolean_semantic_gates_pass','native_open_contract']}))
except Exception as e:
 state.update(status='FAILED_OR_INCOMPLETE_DO_NOT_CREDIT',failure=repr(e),failed_utc=stamp(),complete=False);save();raise
