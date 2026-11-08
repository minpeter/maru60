#!/usr/bin/env python3
"""Check the NEW recovery packet; do not imply old Git or packet recovery."""
import hashlib,json
from pathlib import Path
if not __debug__:raise SystemExit('Assertions required; do not use optimized Python')
C=Path(__file__).resolve().parent;R=C.parent;Q=C/'firmware/qmk/keyboards/maru60/rp2350';B=R/'baseline-extracted/accepted-main/pcb/firmware/qmk/keyboards/maru60/rp2350'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def files(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
m=json.loads((C/'source-manifest.json').read_text());actual=files(C);del actual['source-manifest.json'];assert actual==m['files'],'Candidate exact file set/hash mismatch'
known=json.loads((R/'known-source-hashes.json').read_text());s=json.loads((C/'SOURCE-STATUS.json').read_text());assert files(B)==known['baseline'];assert files(Q)==s['source_hashes'];assert len(files(Q))==22
matches={n for n,h in files(Q).items() if h==known['active'][n]};assert len(matches)==19 and 'config.h' in matches
assert set(files(Q))-matches=={'maru_rgb.c','maru_rgb.h','maru_ws2812_transport.inc'}
assert '#    define MARU60_LED_POWER_QUALIFIED 0' in (Q/'config.h').read_text()
assert not s['full_arm_build'] and not s['hardware_qualification']
print(json.dumps({'pass':True,'candidate_files':len(actual)+1,'baseline_files_exact':22,'former_working_files_exact':19,'new_implementation_files':sorted(set(files(Q))-matches),'qualification_default':0,'original_complete_packet_recovered':False},indent=2))
