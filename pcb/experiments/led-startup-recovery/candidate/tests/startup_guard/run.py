#!/usr/bin/env python3
"""NEW source-bound recovery tests. No QMK build, flash, or hardware claim."""
import argparse, hashlib, json, os, re, shutil, subprocess, resource
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
from pathlib import Path
if not __debug__:
    raise SystemExit('Assertions required; do not use optimized Python')
H=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
S=a.source.resolve();B=a.baseline.resolve();O=a.output.resolve();assert not O.is_relative_to(S) and not O.is_relative_to(B) and not O.is_relative_to(H.parents[1]);assert not O.exists();O.mkdir(parents=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
before=hashes(S);baseline_before=hashes(B);tests_before=hashes(H);cc=os.environ.get('CC','cc');rows=[]
def run(name,cmd,success=True):
 r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,input='',cwd=O)
 (O/(name+'.log')).write_text('$ '+' '.join(map(str,cmd))+'\n'+r.stdout+r.stderr)
 assert (r.returncode==0 if success else r.returncode!=0),(name,r.returncode,r.stdout,r.stderr)
 rows.append({'name':name,'expected_success':success,'exit_code':r.returncode,'stdout':r.stdout.strip()})
 return r
base=[cc,'-std=c11','-Wall','-Wextra','-Werror','-Wno-pointer-to-int-cast']
def enabled(ms=7,report='RECOVERY-HOST-ONLY-NOT-RAIL-QUALIFICATION'):
 return ['-DMARU60_LED_POWER_QUALIFIED=1',f'-DMARU60_LED_POWER_SETTLE_MS={ms}',f'-DMARU60_LED_POWER_SETTLE_REPORT="{report}"']
def body(source):
 m=re.search(r'^void ws2812_flush\(void\) \{.*?^\}',(source/'maru_ws2812_transport.inc').read_text(),re.M|re.S);assert m
 return m.group(0)+'\n'
def compile_test(source,dest,defs,opt,name,success=True,body_override=None):
 d=O/(name+'-build');d.mkdir();(d/'transport_flush.inc').write_text(body(source) if body_override is None else body_override)
 return run(name,[*base,opt,*defs,'-I'+str(d),'-I'+str(H/'mock'),'-I'+str(source),H/'guard_test.c',source/'maru_rgb.c','-o',dest],success)
scenarios=[['normal'],['wrap'],['resource']]+[['restart',v] for v in ['usb','policy','manual']]+[['wrap_restart','manual']]+[['latch',v] for v in ['fault','transport']]
for cause in ['fault','usb','transport','enable','off','policy']:
 scenarios.append(['cancel','settle',cause,'0','0'])
 for chain in ['0','1']:scenarios.append(['cancel','resume',cause,chain,'0'])
 scenarios.append(['cancel','render',cause,'0','1'])
 for chain in ['0','1']:scenarios.append(['cancel','color',cause,chain,'1'])
transport=[]
for stage in ['entry','sync','pack','source','counter','mode']:
 for cause in ['fault','usb','transport','enable','off','policy']:
  for chain in ['0','1']:
   for phase in ['0','1']:transport.append(['cancel',stage,cause,chain,phase])
for opt in ['-O0','-O2']:
 exe=O/('candidate'+opt);compile_test(S,exe,enabled(),opt,'compile-candidate'+opt)
 for case in scenarios+transport:run('-'.join(case)+opt,[exe,*case])
 run('expected-nonatomic-submit'+opt,[exe,'cancel','submit','fault','0','0'],False)
exe=O/'default-off';compile_test(S,exe,[],'-O2','compile-default-off');off=run('default-off',[exe,'default_off']).stdout.strip()
invalid=[('missing-contract',['-DMARU60_LED_POWER_QUALIFIED=1']),('missing-report',['-DMARU60_LED_POWER_QUALIFIED=1','-DMARU60_LED_POWER_SETTLE_MS=7']),('missing-interval',['-DMARU60_LED_POWER_QUALIFIED=1','-DMARU60_LED_POWER_SETTLE_REPORT="TEST"']),('zero',enabled(0)),('negative',enabled(-1)),('oversized',enabled('0x80000000U')),('empty-report',enabled(7,''))]
for name,defs in invalid:compile_test(S,O/('invalid-'+name),defs,'-O0','reject-'+name,False)
# Same recovered baseline source and NEW fixture: fresh observation, not a
# restoration of the lost historical baseline report or its old counts.
baseline=[]
for opt in ['-O0','-O2']:
 exe=O/('baseline'+opt);compile_test(B,exe,enabled(),opt,'compile-baseline'+opt)
 for cause in ['fault','usb']:
  r=run('baseline-'+cause+opt,[exe,'observe',cause]);baseline.append({'cause':cause,'optimization':opt,'stdout':r.stdout.strip()})
exe=O/'baseline-off';compile_test(B,exe,[],'-O2','compile-baseline-off');baseline_off=run('baseline-off',[exe,'default_off']).stdout.strip()
# Sensitivity controls modify only disposable source copies. Match exactly one
# replacement, then require the selected safety test to fail.
mutations=[('skip-settling','    if (timer_elapsed32(settle_started) < MARU_LED_SETTLE_MS) return;','    (void)timer_elapsed32(settle_started);',['normal']),('retain-state','    power_state = MARU_LED_OFF;','    /* deliberate stale-state mutant */',['restart','manual']),('forget-fault','    if (!gpio_read_pin(MARU_LED_FAULT_N)) fault_latched = true;','    fault_latched = !gpio_read_pin(MARU_LED_FAULT_N);',['latch','fault']),('between-chains','    maru_key_flush();\n    if (!maru_rgb_can_flush()) return;','    maru_key_flush();',['cancel','entry','fault','0','0']),('black-first','        maru_key_set_color_all(0,0,0); maru_ug_set_color_all(0,0,0);','        /* deliberate missing black preparation */',['restart','manual'])]
killed=[]
for name,old,new,case in mutations:
 d=O/('mutant-'+name);shutil.copytree(S,d);f=d/'maru_rgb.c';s=f.read_text();assert s.count(old)==1;f.write_text(s.replace(old,new));exe=d/'test';compile_test(d,exe,enabled(),'-O2','compile-mutant-'+name);run('kill-'+name,[exe,*case],False);killed.append(name)
for name,old,new,case in [('post-sync','    if (!maru_rgb_can_flush() || transfer_failed) return;','    if (transfer_failed) return;',['cancel','sync','usb','0','0']),('final-dma','    if (!maru_rgb_can_flush()) return;\n    dmaChannelEnableX(dma_channel);','    dmaChannelEnableX(dma_channel);',['cancel','mode','fault','0','0'])]:
 src=body(S);assert src.count(old)==1;exe=O/('mutant-'+name);compile_test(S,exe,enabled(),'-O2','compile-mutant-'+name,body_override=src.replace(old,new));run('kill-'+name,[exe,*case],False);killed.append(name)
assert hashes(S)==before and hashes(B)==baseline_before and hashes(H)==tests_before
report={'pass':True,'status':'NEW_RECOVERY_CANDIDATE_WITH_FRESH_TESTS_NOT_HISTORICAL_PACKET','source_directory':str(S),'source_hashes':before,'baseline_directory':str(B),'baseline_hashes':baseline_before,'test_source_hashes':tests_before,'source_and_baseline_unchanged':True,'compiler':run('compiler',[cc,'--version']).stdout.splitlines()[0],'startup_scenarios':len(scenarios),'startup_executions':len(scenarios)*2,'transport_scenarios':len(transport),'transport_executions':len(transport)*2,'default_off':off,'baseline_default_off':baseline_off,'baseline_fresh_observations':baseline,'rejected_contracts':len(invalid),'killed_mutations':killed,'expected_nonatomic_limit_controls':2,'actual_transport_body_sha256':hashlib.sha256(body(S).encode()).hexdigest(),'limits':['Actual maru_rgb.c plus source-extracted ws2812_flush; not full transport translation units or QMK/ARM','All GPIO, scheduling, time, packing, transport lifecycle, register access and DMA are mocks','Submit-time fault controls expose non-atomic polling; no physical cancellation-latency or signal-edge guarantee','7 ms is synthetic host-only contract; production default stays 0 with no interval/report','Baseline observations use a new common fixture, not recovered historical tests or logs'],'tests':rows}
(O/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['tests','source_hashes','baseline_hashes','test_source_hashes']},indent=2))
