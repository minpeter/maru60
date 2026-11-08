from pathlib import Path
import hashlib,json,zipfile
D=Path('/tmp/v7-buck-deadarm-evidence-20261104');Z=Path('/tmp/v7-buck-deadarm-evidence-20261104.zip')
h=lambda b:hashlib.sha256(b).hexdigest()
assert h((D/'trial/source/pcb/maru60.kicad_pcb').read_bytes())=='2c7e100a450ead86bdd1b790876a8890ec5befea25ea04ae2aeb5a62c08e2373'
assert h((D/'trial/filled/pcb/maru60.kicad_pcb').read_bytes())=='aead2fb0c61ee3cb565f03e3a271f213911767c37f47e86d0adae87735428b3f'
files=[p for p in D.rglob('*') if p.is_file() and p!=D/'MANIFEST.json']
m={'status':'UNSELECTED; strict global no-plane-loss FAIL; coordinate analysis is not adoption','files':[{'path':str(p.relative_to(D)),'bytes':p.stat().st_size,'sha256':h(p.read_bytes())} for p in sorted(files)]}
(D/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(D.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(D)))
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 for q in m['files']:assert h(z.read(q['path']))==q['sha256']
 assert z.read('MANIFEST.json')==(D/'MANIFEST.json').read_bytes()
r={'zip':str(Z),'sha256':h(Z.read_bytes()),'bytes':Z.stat().st_size,'manifest_sha256':h((D/'MANIFEST.json').read_bytes()),'manifested_files':len(files),'all_archive_entries_verified':True}
Path('/tmp/v7-buck-deadarm-evidence-20261104-receipt.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
