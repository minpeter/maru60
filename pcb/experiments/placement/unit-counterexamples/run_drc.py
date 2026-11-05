from pathlib import Path
import os,json,subprocess,concurrent.futures,collections,time
r=Path(__file__).parent
names=['via_touching','via_touching_attach_on','plane_center','plane_pad_offcenter','plane_via_offcenter']
exe='/workspace/shared/maru60-local-router/freerouting-2.5.0-linux-x64/bin/freerouting';sandbox='/workspace/shared/maru60-local-router/no_network.py'
def run(name):
 d=r/name;config=d/'config';config.mkdir(exist_ok=True);env=dict(os.environ,JAVA_TOOL_OPTIONS='-Xms64m -Xmx384m');t=time.monotonic()
 cmd=['/usr/bin/python3',sandbox,exe,'-de',str(d/'input.dsn'),'-drc',str(d/'router-drc.json'),'--router.automatic_neckdown=false','-da','--gui.enabled=false','--profile.allow_telemetry=false','--profile.allow_contact=false','--user_data_path='+str(config)]
 with open(d/'router.log','w')as f:
  try:ret=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=90).returncode
  except subprocess.TimeoutExpired:ret='timeout'
 out={'name':name,'exit':ret,'elapsed_sec':round(time.monotonic()-t,2)}
 if(d/'router-drc.json').exists():
  j=json.loads((d/'router-drc.json').read_text());out['router_unconnected']=dict(collections.Counter(v['type']for v in j['unconnectedItems']));out['router_violations']=dict(collections.Counter(v['type']for v in j['violations']));out['clearance_examples']=[v['description']for v in j['violations']if v['type']in['clearance','holeClearance']][:4]
 native=d/'native-summary.json'
 if native.exists():out['native']=json.loads(native.read_text())
 (d/'comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True);return out
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:results=list(pool.map(run,names))
(r/'results.json').write_text(json.dumps(results,indent=2))
