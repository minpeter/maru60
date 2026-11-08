from pathlib import Path
import json,hashlib,shutil,re,pcbnew as p
R=Path('/workspace/shared/maru60-resume');S=R/'selected-repo/pcb/experiments/resume-20261106-3v3-branch-prototype';D=R/'continuation-fa96a7c/usb-stub';src=S/'pcb/maru60.kicad_pcb';h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();before=h(src);assert before=='88fbac1d15c3ad320bcdd8af3a6f7c8293da39342bb8869d71cfed406ce44d5e';proof=json.loads((D/'qa/full-graph-prune.json').read_text());ret=proof['proposed_retired'];assert len(ret)==1;assert proof['exact_retained_partition_unchanged'];assert len(proof['boundary_contacts'])==1
assert proof['finite_scope_authorized_for_candidate'];assert len(proof['retained_active_patches'])==2;assert not(D/'pcb').exists();shutil.copytree(S/'pcb',D/'pcb');text=src.read_text()
for u in ret:
 ms=[m for m in re.finditer(r'\n\t\((?:segment|via)\s.*?\n\t\)',text,re.S)if u in m.group()];assert len(ms)==1;m=ms[0];text=text[:m.start()]+text[m.end():]
cp=D/'pcb/maru60.kicad_pcb';cp.write_text(text);b=p.LoadBoard(str(cp));b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(cp),b);assert h(src)==before
(D/'qa/build.json').write_text(json.dumps(dict(source_sha256=before,candidate_sha256=h(cp),removed=ret),indent=2)+'\n')
