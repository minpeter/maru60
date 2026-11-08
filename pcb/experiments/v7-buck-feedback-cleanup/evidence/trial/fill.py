import os,pathlib,hashlib,time,json
D=pathlib.Path(__file__).parent
for k in ['CONFIG','CACHE','DATA']:os.environ['XDG_'+k+'_HOME']=str(D/k.lower())
import pcbnew as p
B=D/'filled/pcb/maru60.kicad_pcb';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before=sha(B);b=p.LoadBoard(str(B));start=time.monotonic();b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(B),b);r=dict(status='UNSELECTED normal native refill; no rule changes',prefill_sha256=before,filled_sha256=sha(B),seconds=time.monotonic()-start);(D/'qa/fill.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
