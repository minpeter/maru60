#!/usr/bin/env python3
"""Read-only exact package and optional active-copy identity verifier."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
if not __debug__:raise SystemExit('Assertions required; do not use optimized Python')
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--active-root',type=Path);a=p.parse_args()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def files(r):return {str(f.relative_to(r)):sha(f) for f in sorted(r.rglob('*')) if f.is_file()}
m=json.loads((P/'PACKAGE-MANIFEST.json').read_text());actual=files(P);del actual['PACKAGE-MANIFEST.json'];assert actual==m['files'],'Package path/hash mismatch'
assert sha(P/'candidate/source-manifest.json')=='4ecbf22170617f42fccefb1ca5cbda496cb864d829965b0fcc80f241e72cefa0'
old=json.loads((P/'evidence/documentation-clarification/prior-source-manifest.json').read_text())['files']
current=json.loads((P/'candidate/source-manifest.json').read_text())['files']
assert set(old)==set(current)
assert [n for n in current if current[n]!=old[n]]==['README.md']
delta=json.loads((P/'evidence/documentation-clarification/delta.json').read_text())
prior=(P/'evidence/documentation-clarification/prior-README.md').read_text()
assert prior.count(delta['exact_old_sentence'])==1
assert prior.replace(delta['exact_old_sentence'],delta['exact_new_sentences'])==(P/'candidate/README.md').read_text()
subprocess.run([sys.executable,str(P/'candidate/verify_sources.py')],check=True)
if a.active_root:
 for part in ['firmware','engineering']:
  assert (a.active_root/part).is_dir()
  assert files(a.active_root/part)==files(P/'candidate'/part),f'Active {part} mismatch'
print(json.dumps({'pass':True,'package_files':len(actual)+1,'candidate_manifest_sha256':sha(P/'candidate/source-manifest.json'),'active_copy_checked':bool(a.active_root)},indent=2))
