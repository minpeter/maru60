import os,sys,json,subprocess,hashlib,time
from pathlib import Path
W=Path(__file__).resolve().parent;name=sys.argv[1];cmd=sys.argv[2:];env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';homes={}
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 p=W/'qa/runtime'/name/k.lower();p.mkdir(parents=True,mode=0o700);env[k]=str(p);homes[k]=str(p)
log=W/'qa'/(name+'.log');start=time.monotonic()
with log.open('x')as f:r=subprocess.run(cmd,cwd=W,env=env,stdout=f,stderr=subprocess.STDOUT)
(W/'qa'/(name+'.execution.json')).write_text(json.dumps({'command':cmd,'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-start,'private_xdg':homes,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()},indent=2)+'\n');sys.exit(r.returncode)
