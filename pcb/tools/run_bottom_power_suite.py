"""Run candidate-bound behavioral SPICE power scenarios, preserving every deck/log.

Uses the existing AP2112/TPS259470A/TPS62932/TPS2553 models, not vendor macros.
Parasitic resistance comes from the candidate DC solve; inductance and effective
capacitance remain explicit assumptions. Does not enable hardware LED power.
"""
import argparse,hashlib,importlib.util,json,os,re,shutil,subprocess,sys
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('geometry',type=Path);ap.add_argument('netlist',type=Path);ap.add_argument('pdn',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
 import xml.etree.ElementTree as ET
 values={c.get('ref'):c.findtext('value') for c in ET.parse(a.netlist).getroot().find('components')}
 for ref,expected in {'U2':'AP2112K-3.3TRG1','U7':'TPS2553DBVR','U8':'TPS259470ARPWR','U18':'TPS62932DRLR','R159':'40.0k 0.1%','R160':'10.0k 0.1%','C143':'22pF','C124':'10nF 10% 50V','C139':'100nF 10% 16V - soft start'}.items():
  if values.get(ref)!=expected:raise ValueError(f'{ref}: model no longer matches {values.get(ref)}')
 g=json.loads(a.geometry.read_text());pdn=json.loads(a.pdn.read_text());assert pdn['provenance']['geometry_sha256']==sha(a.geometry)
 led_counts={part:sum(f['value']==part for f in g['fps']) for part in ['SK6812MINI-E-012','SK6805-EC15-001']};assert led_counts=={'SK6812MINI-E-012':64,'SK6805-EC15-001':12}
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);source=Path(__file__).resolve().parent/'power_sim';pkg=out/'model';pkg.mkdir(exist_ok=True)
 for p in source.iterdir():
  if p.suffix in ('.inc','.lib','.cir'):shutil.copyfile(p,pkg/p.name)
 params=(pkg/'params.inc').read_text();changes={'iled':'0.058','rtrin':str(pdn['paths']['VBUS_PROTECTED_RAW U8 -> U18 @20C']['resistance_mohm']/1000)}
 for k,v in changes.items():params,n=re.subn(rf'(?m)^\.param {k}=\S+',f'.param {k}={v}',params);assert n==1
 (pkg/'params.inc').write_text(params)
 text=(pkg/'board.inc').read_text().replace('Bledq vled 0 I = 0.038','Bledq vled 0 I = 0.0444')
 def r(key):return pdn['paths'][key+' @20C']['resistance_mohm']/1000
 text=re.sub(r'(?m)^Rconn .*$',f'Rconn vbus vbf {r("VBUS J1 -> F1")}',text)
 text=text.replace('Rf1   vbf  vfused {rfuse}',f'Rf1 vbf vflead {{rfuse}}\nRfeed vflead vfused {r("VBUS_FUSED F1 -> U8")}')
 text=re.sub(r'(?m)^Rtr2 .*$',f'Rtr2 v4 v4x {r("+4V_REG L2 -> U2")}',text)
 text=re.sub(r'(?m)^Rtr3 .*$',f'Rtr3 v4 v4y {r("+4V_REG L2 -> U7")}',text)
 text=re.sub(r'(?m)^Rtr4 .*$',f'Rtr4 v33 v33x {r("+3V3 U2 -> U1 pin 49 (VREG_VIN)")}',text)
 text='* Candidate-bound resistor network; radial equivalent branches, shared-path coupling approximated.\n'+text
 (pkg/'board.inc').write_text(text)
 # AC deck has its own copies of the branch resistors.
 loop=(pkg/'loop_ac.cir').read_text();loop=re.sub(r'(?m)^Rtr2 .*$',f'Rtr2 v4 v4x {r("+4V_REG L2 -> U2")}',loop);loop=re.sub(r'(?m)^Rtr3 .*$',f'Rtr3 v4 v4y {r("+4V_REG L2 -> U7")}',loop);(pkg/'loop_ac.cir').write_text(loop)
 runner=(source/'run_power_sim.py').read_text().replace('0.025','0.058').replace('0.196','0.1896').replace('38 mA static + 25 mA','44.4 mA static + 58 mA').replace('38 mA','44.4 mA')
 # These labels describe drive current, excluding the 44.4 mA idle load.
 runner=runner.replace('150mA','58mA_drive').replace('0->150 mA','0->58 mA drive').replace('LEDs 150 mA','LEDs 44.4 mA idle + 58 mA drive')
 (pkg/'runner.py').write_text(runner)
 spec=importlib.util.spec_from_file_location('bound_power',pkg/'runner.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.HERE=pkg;calls=[]
 def run(case,deck,params=None,deck_params=None,drop=()):
  d=out/'cases'/f'{len(calls):02d}_{case}';d.mkdir(parents=True,exist_ok=False)
  row={'case':case,'deck':deck,'params':params or {},'deck_params':deck_params or {},'path':str(d)};calls.append(row)
  for p in pkg.iterdir():
   if p.suffix in ('.inc','.lib'):shutil.copyfile(p,d/p.name)
  txt=(pkg/(deck+'.cir')).read_text()
  for k,v in (deck_params or {}).items():txt,n=re.subn(rf'(?m)^\.param {k}=\S+',f'.param {k}={v}',txt);assert n==1
  for vec in drop:txt=txt.replace(' '+vec,'')
  (d/(deck+'.cir')).write_text(txt)
  txt=(d/'params.inc').read_text()
  for k,v in (params or {}).items():txt,n=re.subn(rf'(?m)^\.param {k}=\S+',f'.param {k}={v}',txt);assert n==1
  (d/'params.inc').write_text(txt)
  cmd=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}','-v',f'{d}:/work','-w','/work','maru60-ngspice:bookworm','-b',deck+'.cir']
  # The pinned image uses ngspice as its ENTRYPOINT.
  result=subprocess.run(cmd,capture_output=True,text=True,timeout=900);log=result.stdout+result.stderr;(d/'run.log').write_text(log)
  row['returncode']=result.returncode
  if result.returncode or re.search(r'(?i)(timestep too small|simulation.*aborted|doanalyses:|fatal error|Error:)',log):
   row['error']='SPICE failure';(out/'calls.json').write_text(json.dumps(calls,indent=2));raise RuntimeError(f'{case}: failed, see {d}')
  raw=d/'out.txt';names=raw.open().readline().lower().split();data=np.loadtxt(raw,skiprows=1);assert data.ndim==2 and len(data)>1 and np.isfinite(data).all()
  row['samples']=len(data);row['complete']=True;(out/'calls.json').write_text(json.dumps(calls,indent=2)+'\n');print('power case',len(calls),case,'complete',flush=True)
  return {n:data[:,i] for i,n in enumerate(names)}
 m.run=run;sys.argv=['bound_power',str(out)];m.main()
 (out/'provenance.json').write_text(json.dumps({'inputs':{str(p):sha(p) for p in [a.geometry,a.netlist,a.pdn,Path(__file__)]},'models':{p.name:sha(p) for p in pkg.iterdir() if p.is_file()},'LED_counts':led_counts,'LED_idle_mA_typical':44.4,'PWM_average_drive_mA':58,'limitations':['Behavioral models, not vendor macros or measured dynamics','DC radial branch equivalents; shared copper and physical parasitic inductance approximated','Nominal effective capacitors and omitted LDO/buck thermal retry/PFM effects remain stated assumptions','This tree model uses average LED load; separate synchronized-PWM transient screen is required']},indent=2)+'\n')
if __name__=='__main__':main()
