#!/usr/bin/python3
import os,sys,json,hashlib,shutil,time
from pathlib import Path
if not __debug__ or sys.flags.optimize!=0 or os.environ.get('PYTHONOPTIMIZE','')not in('','0'):raise SystemExit('Cold refill requires assertions')
D=Path(__file__).resolve().parent;SRC=Path('/tmp/v7-connector-gnd-stitch-c770/filled/pcb');OUT=D/'cold/pcb';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='aaafc033c6e9809afcb189290c3740157b7ab5596aaa0867e581f08d89807eca'
assert H(SRC/'maru60.kicad_pcb')==expected;assert not OUT.exists();assert not any(p.is_symlink()for p in SRC.rglob('*'));before={str(p.relative_to(SRC)):H(p)for p in SRC.rglob('*')if p.is_file()};shutil.copytree(SRC,OUT)
os.environ['XDG_CONFIG_HOME']=str(D/'cold-xdg/config');os.environ['XDG_CACHE_HOME']=str(D/'cold-xdg/cache');os.environ['XDG_DATA_HOME']=str(D/'cold-xdg/data')
import pcbnew as p
assert p.GetBuildVersion()=='9.0.2+dfsg-1';f=OUT/'maru60.kicad_pcb';assert H(f)==expected;b=p.LoadBoard(str(f));start=time.monotonic();b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(f),b);after=H(f);assert after==expected;assert before=={str(p.relative_to(SRC)):H(p)for p in SRC.rglob('*')if p.is_file()}
r={'source_board_sha256':expected,'cold_refilled_board_sha256':after,'byte_identical':True,'seconds':time.monotonic()-start,'native_version':p.GetBuildVersion(),'source_tree_unchanged':True,'source_file_count':len(before),'independent_copy':str(OUT),'private_XDG':True,'source_file_hashes':before};(D/'cold_refill_results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
