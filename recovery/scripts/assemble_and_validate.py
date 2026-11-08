from pathlib import Path
import hashlib,shutil,json,os,subprocess,datetime
base=Path(__file__).resolve().parent.parent;out=base/'selected-recovered';pcb=out/'pcb';qa=out/'qa';qa.mkdir(parents=True,exist_ok=True)
src=base/'extracted/maru60-tscircuit-full/input/v7';assert not pcb.exists();shutil.copytree(src,pcb);(pcb/'maru60.kicad_pcb').write_bytes((base/'exact-reconstruction/typography-reconstructed.kicad_pcb').read_bytes());f=pcb/'maru60-expansion.kicad_sch';s=f.read_text();assert s.count('"+5V TEST"')==1 and s.count('"+5V_LED TEST"')==1;f.write_text(s.replace('"+5V TEST"','"+4V TEST"').replace('"+5V_LED TEST"','"+4V_LED TEST"'))
def files():return {str(f.relative_to(pcb)):{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f in sorted(pcb.rglob('*'))if f.is_file()}
before=files();(qa/'CAD_INPUTS.json').write_text(json.dumps(before,indent=2)+'\n')
cmds=[('drc',['kicad-cli','pcb','drc','--schematic-parity','--format','json','--severity-all','-o',str(qa/'drc.json'),str(pcb/'maru60.kicad_pcb')]),('erc',['kicad-cli','sch','erc','--format','json','--severity-all','-o',str(qa/'erc.json'),str(pcb/'maru60.kicad_sch')]),('netlist',['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(qa/'netlist.xml'),str(pcb/'maru60.kicad_sch')])]
for stage,cmd in cmds:
 env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';home=out/'runtime'/stage
 for k in ['HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','XDG_RUNTIME_DIR']:
  d=home/k;d.mkdir(parents=True,mode=0o700,exist_ok=True);env[k]=str(d)
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(qa/(stage+'.log')).write_text(r.stdout);(qa/(stage+'.execution.json')).write_text(json.dumps({'command':cmd,'exit_code':r.returncode,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n');print(stage,r.returncode,flush=True)
after=files();changes={k:{'before':before.get(k),'after':after.get(k)}for k in before.keys()|after.keys() if before.get(k)!=after.get(k)};(qa/'source-after.json').write_text(json.dumps({'unchanged':not changes,'changes':changes},indent=2)+'\n');assert not changes
