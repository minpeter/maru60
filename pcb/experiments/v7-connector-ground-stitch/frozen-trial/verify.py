from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parent;m=json.loads((r/'MANIFEST.json').read_text());actual={str(p.relative_to(r)) for p in r.rglob('*') if p.is_file() and p.name!='MANIFEST.json'};assert actual==set(m['files'])
for n,v in m['files'].items():
 b=(r/n).read_bytes();assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],n
assert hashlib.sha256((r/'filled/pcb/maru60.kicad_pcb').read_bytes()).hexdigest()==m['candidate_sha256'];print('PASS: all archived files and exact candidate identity match. This is not a fresh native or hardware qualification.')
