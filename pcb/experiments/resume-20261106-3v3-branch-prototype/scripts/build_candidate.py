from pathlib import Path
import json,hashlib,shutil,re,pcbnew as p
R=Path('/workspace/shared/maru60-resume');S=R/'selected-repo/pcb/experiments/resume-20261106-c136-label-prototype';D=R/'continuation-97d9eb7/stub3v3';src=S/'pcb/maru60.kicad_pcb';h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before=h(src);assert before=='2e532c1a16e64a34eafafdfbd5b85c05d70bb12ad9e52924c5cbe024fdc9aa2c';proof=json.loads((D/'qa/full-graph-prune.json').read_text());ret=proof['proposed_retired'];assert len(ret)==10;assert proof['exact_retained_partition_unchanged'];assert len(proof['boundary_contacts'])==1
assert not(D/'pcb').exists();shutil.copytree(S/'pcb',D/'pcb');text=src.read_text()
for u in ret:
 ms=[m for m in re.finditer(r'\n\t\((?:segment|via)\s.*?\n\t\)',text,re.S)if u in m.group()];assert len(ms)==1;m=ms[0];text=text[:m.start()]+text[m.end():]
cp=D/'pcb/maru60.kicad_pcb';cp.write_text(text);b=p.LoadBoard(str(cp));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(cp),b);assert h(src)==before
(D/'qa/build.json').write_text(json.dumps(dict(source_sha256=before,candidate_sha256=h(cp),removed=ret),indent=2)+'\n')
