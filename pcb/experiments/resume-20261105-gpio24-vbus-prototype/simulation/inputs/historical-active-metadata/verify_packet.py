#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent;m=json.loads((r/'MANIFEST.json').read_text());bad=[]
for f in m['files']:
 p=r/f['path']
 if not p.is_file() or p.stat().st_size!=f['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']:bad.append(f['path'])
print(json.dumps({'files_checked':len(m['files']),'mismatches':bad},indent=2));raise SystemExit(bool(bad))
