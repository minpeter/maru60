#!/usr/bin/env python3
"""Hash-guarded optional report synchronization API for the pinned QMK checkout; dry-run by default."""
from pathlib import Path
import argparse,hashlib,json,subprocess
a=argparse.ArgumentParser();a.add_argument('qmk_checkout');a.add_argument('--apply',action='store_true');args=a.parse_args()
root=Path(args.qmk_checkout).resolve();here=Path(__file__).resolve().parent
m=json.loads((here/'patches/report-state-sync-v1.json').read_text());patch=here/'patches/report-state-sync-v1.patch'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==m['qmk_commit'],'Unexpected QMK commit; review/rebase instead of guessing.'
states=[]
for c in m['changes']:
    actual=sha(root/c['path']);assert actual in [c['before_sha256'],c['after_sha256']],('Unexpected source bytes',c['path'],actual)
    states.append(actual==c['after_sha256'])
assert all(states) or not any(states),'Partially applied patch; inspect before continuing.'
assert sha(patch)==m['patch_sha256'],'Patch payload hash mismatch'
if all(states):print('Already applied and hash-verified.');raise SystemExit(0)
subprocess.run(['git','-C',str(root),'apply','--check',str(patch)],check=True)
if args.apply:
    subprocess.run(['git','-C',str(root),'apply',str(patch)],check=True)
    for c in m['changes']:assert sha(root/c['path'])==c['after_sha256']
print('APPLIED and hash-verified' if args.apply else 'DRY-RUN PASS; add --apply to modify exactly the four declared QMK files.')
