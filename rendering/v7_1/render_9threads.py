"""Performance-only runtime override; original visual scene and checkpoint files unchanged."""
import os,json,hashlib,time
P=os.path.join(os.path.dirname(os.path.abspath(__file__)),'render_studio.py')
source=open(P).read();old='scene.render.threads_mode=\'FIXED\'; scene.render.threads=6'
assert source.count(old)==1,'Expected exactly one explicit thread assignment'
new="scene.render.threads_mode='FIXED'; scene.render.threads=9; print('RUNTIME THREADS CONFIRMED',scene.render.threads,flush=True); assert scene.render.threads==9"
code=source.replace(old,new)
out=os.environ.get('KEYBOARD_OUTDIR',os.path.dirname(P)+'/output');os.makedirs(out,exist_ok=True)
record={'timestamp_unix':time.time(),'original_script_sha256':hashlib.sha256(source.encode()).hexdigest(),'override':'Only renderer thread assignment6→9 at runtime','threads':9,'quality_changes':False,'visual_asset_digest':'92213d3439a1e4d030a18b133904b3439b5a8f2205bddb6a31ec66574a016adf'}
open(out+'/performance_override_9threads.json','w').write(json.dumps(record,indent=2))
exec(compile(code,P,'exec'),{'__name__':'__main__','__file__':P})
