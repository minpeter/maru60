from pathlib import Path
import os,hashlib,json,shutil,time
W=Path(__file__).resolve().parent;S=Path('/tmp/v7-serial-legs-plus-two-labels/filled/pcb');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='4765dfd82f70cfcfc00c06b4d9abfb614c7d657ec086fcf57c28d49bc3236136';assert H(S/'maru60.kicad_pcb')==expected
for k in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME','XDG_RUNTIME_DIR']:
 p=W/'runtime'/k.lower();p.mkdir(parents=True,mode=0o700);os.environ[k]=str(p)
import pcbnew as p
D=W/'cold/pcb';assert not D.exists();shutil.copytree(S,D);b=p.LoadBoard(str(D/'maru60.kicad_pcb'));start=time.monotonic();f=p.ZONE_FILLER(b);assert f.Fill(b.Zones());p.SaveBoard(str(D/'maru60.kicad_pcb'),b);sec=time.monotonic()-start;assert H(D/'maru60.kicad_pcb')==H(S/'maru60.kicad_pcb')==expected
out={'source_sha256':expected,'result_sha256':expected,'independent_normal_cold_refill':True,'seconds':sec,'native':p.GetBuildVersion()};(W/'COLD_REFILL.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
