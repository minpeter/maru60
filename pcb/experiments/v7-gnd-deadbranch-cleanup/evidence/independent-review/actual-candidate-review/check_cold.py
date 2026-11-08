from pathlib import Path
import os,tempfile,shutil,hashlib,json,time
R=Path(__file__).resolve().parent;S=Path('/tmp/v7-gnd-tail-cleanup-aead/filled/pcb');H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a';assert H(S/'maru60.kicad_pcb')==expected
T=Path(tempfile.mkdtemp(prefix='cold-fixed-point-',dir=R));P=T/'pcb';shutil.copytree(S,P)
for k in ['CONFIG','CACHE','DATA','STATE','RUNTIME']:
 d=T/k.lower();d.mkdir(mode=0o700);os.environ['XDG_'+k+('_DIR'if k=='RUNTIME'else'_HOME')]=str(d)
os.environ['QT_QPA_PLATFORM']='offscreen'
import pcbnew as p
assert p.Version()=='9.0.2'and p.GetBuildVersion()=='9.0.2+dfsg-1'
f=P/'maru60.kicad_pcb';before=H(f);companions={str(q.relative_to(P)):H(q)for q in P.rglob('*')if q.is_file()and q!=f};b=p.LoadBoard(str(f));t=time.monotonic();b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(f),b);after=H(f)
r=dict(candidate_sha256=expected,cold_output_sha256=after,normal_refill_fixed_point=(before==after),candidate_input_unchanged=H(S/'maru60.kicad_pcb')==expected,companion_files_unchanged=all(H(P/k)==v for k,v in companions.items()),seconds=time.monotonic()-t,native_version=p.GetBuildVersion(),cold_copy_directory=str(T),scope='Isolated copied PCB/project tree, fresh XDG directories; normal LoadBoard/BuildConnectivity/ZONE_FILLER/SaveBoard. No AppConsole, thread-count override, fill transplant or candidate mutation.')
(R/'COLD_FIXED_POINT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['candidate_input_unchanged']and r['companion_files_unchanged']
