from pathlib import Path
import hashlib, json, shutil
from sexpr_spans import children, head, field

R=Path('/tmp/v7-gnd-tail-cleanup-aead')
SOURCE=Path('/workspace/scratch/edd9a5be63e7/pcb-v7-recovery-20261104/pcb/experiments/v7-buck-feedback-cleanup/candidate/pcb')
SHA='aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f'
UIDS={'68f95f8e-16e1-430a-a0b2-1c1d51d16fde','577f36c1-4f15-4c40-b632-02db2931cfb0'}
H=lambda b:hashlib.sha256(b).hexdigest()
src=SOURCE/'maru60.kicad_pcb'; raw=src.read_bytes(); assert H(raw)==SHA
assert not (R/'source').exists() and not (R/'prefill').exists() and not (R/'filled').exists()
shutil.copytree(SOURCE,R/'source/pcb')
shutil.copytree(SOURCE,R/'prefill/pcb')
s=raw.decode(); matches=[(a,z,t)for a,z,t in children(s)if head(t) in ('segment','via') and any(field(t,'uuid')==f'(uuid "{u}")' for u in UIDS)];assert len(matches)==2,matches
records=[t for a,z,t in matches]
assert sum(head(t)=='segment' for t in records)==2 and sum(head(t)=='via' for t in records)==0
out=s
for a,z,t in sorted(matches,reverse=True):out=out[:a]+out[z:]
out=out.encode();assert not any(u.encode() in out for u in UIDS)
(R/'prefill/pcb/maru60.kicad_pcb').write_bytes(out)
shutil.copytree(R/'prefill/pcb',R/'filled/pcb')
contract={'status':'UNSELECTED two-track GND leaf retirement; validation pending','source_sha256':SHA,'prefill_sha256':H(out),'retired_uuids':sorted(UIDS),'retired_raw_records':records,'removed_net':'GND','removed_track_length_mm':1.9384776310850238,'retained_boundary_uuids':['277a8b55-ff78-53f6-840a-96fa0930cd16'],'removed_via':None,'added_objects':[],'scope':'Remove only two declared dead-end F.Cu GND tracks. All drills, components, schematics, nets, clearance and setup stay unchanged. Normal fill, retained material support, full corrected connectivity, native DRC and strict original plane-preservation gates required. No physical HF-ground or hardware qualification claimed.'}
(R/'BUILD_CONTRACT.json').write_text(json.dumps(contract,indent=2)+'\n')
source_files={str(p.relative_to(SOURCE)): {'sha256':H(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(SOURCE.rglob('*')) if p.is_file()}
(R/'SOURCE_TREE_MANIFEST.json').write_text(json.dumps(source_files,indent=2)+'\n')
for rel,d in source_files.items():
    assert H((R/'source/pcb'/rel).read_bytes())==d['sha256']
    if rel!='maru60.kicad_pcb':assert H((R/'prefill/pcb'/rel).read_bytes())==d['sha256']
assert src.read_bytes()==raw
print(json.dumps(contract,indent=2))
