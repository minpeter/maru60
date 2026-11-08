from pathlib import Path
import hashlib,json,shutil,zipfile
R=Path('/tmp/v7-connector-gnd-stitch-c770');P=Path('/workspace/scratch/edd9a5be63e7/v7-connector-gnd-aaaf-preserved'); assert not P.exists();P.mkdir()
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='aaafc033c6e9809afcb189290c3740157b7ab5596aaa0867e581f08d89807eca'
assert H(R/'filled/pcb/maru60.kicad_pcb')==expected
for name in ['source','prefill','filled','scripts','qa']:shutil.copytree(R/name,P/name)
for name in ['BUILD_CONTRACT.json','SOURCE_TREE_MANIFEST.json','maru60-v7-connector-gnd-unselected-aaaf.png']:shutil.copy2(R/name,P/name)
C=Path('/workspace/scratch/edd9a5be63e7/v7-connector-ground-contract-c770');A=Path('/workspace/scratch/edd9a5be63e7/v7-connector-ground-actual-aaaf')
shutil.copytree(C,P/'independent-contract',ignore=shutil.ignore_patterns('xdg','__pycache__'))
(P/'independent-actual').mkdir()
for f in A.iterdir():
 if f.is_file():shutil.copy2(f,P/'independent-actual'/f.name)
assert H(A/'FINAL_ELIGIBILITY.json')=='27c41ca26cfa052bbb2f7c983152d285c584299d8dff5f40d4a3fced05d58d69'
shutil.copy2('/tmp/v7-gnd-tail-cleanup-aead/qa/material-graph.json',P/'qa/source-material-graph-R2.json')
text='''# Connector GND stitch: verified, unselected trial

Open `filled/pcb/maru60.kicad_pro` for the actual candidate. The selected recovery repository is unchanged at commit 094851aa91eb49e40182c9a88657a8ed6e6dcba8; this archive is not a selected-board or manufacturing release.

Source: c77020ca2e05de0684d6a6c724bf568937bd7e7cbce4ce0c395924d0c97a8e4a.
Candidate: aaafc033c6e9809afcb189290c3740157b7ab5596aaa0867e581f08d89807eca.

Exactly one ordinary GND through-via is added at (17.20, 9.90) mm, diameter 0.50 mm, drill 0.25 mm. The original connector stub, signal traces, all existing holes, components, schematics and settings are unchanged. All 12 serialized zone records are byte-identical. Actual physical ground loses only the exact new drill polygon, 0.049087681002 mm² per inner plane; outer zone material is unchanged. All 13,129 current and 11,905 historical non-GND shadows are protected, including the retired U10 D− segment.

Fresh corrected all-drill material graph and independent review preserve all 245 pad-net partitions, 247 original GND pad roots, every old material component and retained contact witness. The new plated barrel has one intact annulus on each copper layer and two positive guarded inner-plane contacts. Independent normal cold refill reproduces the candidate byte-for-byte. Native DRC: 66 unchanged warnings, 12 unchanged expansion opens, zero other hard errors, zero schematic parity issues. ERC: zero. Inventory: 9,750 tracks, 919 vias, 382 footprints, 13,176.816253756544 mm summed track length.

This passes the frozen bounded one-via geometry/nominal-connectivity contract. It does not restore the missing USB between-via ground neck. The left D+ via's nearest rooted GND via distance changes from 2.351197 to 1.597655 mm, which is geometry only. Added grounded copper can alter actual local fields and coupling. No parasitic extraction, post-change waveform, SI/ESD/EMC, physical stability, assembly or hardware qualification is claimed.

The full source, prefill and candidate project trees are separate. Their schematics are supplied so the actual project can be opened. QA serialization-only/intermediate boards are not the candidate. Existing firmware and prior recovery history are not changed or duplicated here; the selected full-repository backup remains separate. The original lost pre-recovery Git history/full historical QA are still missing.

## Evidence and execution history

The independent contract and actual review are preserved under `independent-contract` and `independent-actual`. The actual graph is `qa/material-graph.json`; its source is `qa/source-material-graph-R2.json`. `qa/comparison.json` and the independent result preserve exact source bindings. Historical run paths inside frozen reports/scripts are provenance, not a claim that every original script is a one-command relocated replay. `verify.py` checks the portable archive contents only.

The initial constructor attempted an unsupported UUID setter and stopped before saving a modified board. Its script/log are retained. The successful constructor emitted a SetWidth-without-layer API diagnostic; the serialized 0.50/0.25 geometry was independently reloaded and verified on all four layers. An initial edge-list comparison was order-sensitive; the corrected comparison uses complete-record multisets, preserving duplicates, and finds zero changed/lost old edges. The original diagnostic is retained. These corrections do not change geometric acceptance tolerances.

The independent review retains its interrupted slow-audit script/log. Its first cold-refill SyntaxError exists in the tool transcript and README summary, but that local error log was overwritten by the successful run; do not interpret its README phrase “Both diagnostics are retained” as preserving that original local log. The successful cold-refill receipt and frozen result hashes are intact.
'''
(P/'README.md').write_text(text)
(P/'verify.py').write_text('''from pathlib import Path\nimport json,hashlib\nr=Path(__file__).resolve().parent;m=json.loads((r/'MANIFEST.json').read_text());actual={str(p.relative_to(r)) for p in r.rglob('*') if p.is_file() and p.name!='MANIFEST.json'};assert actual==set(m['files'])\nfor n,v in m['files'].items():\n b=(r/n).read_bytes();assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],n\nassert hashlib.sha256((r/'filled/pcb/maru60.kicad_pcb').read_bytes()).hexdigest()==m['candidate_sha256'];print('PASS: all archived files and exact candidate identity match. This is not a fresh native or hardware qualification.')\n''')
files={str(f.relative_to(P)):{'bytes':f.stat().st_size,'sha256':H(f)} for f in sorted(P.rglob('*')) if f.is_file()};manifest={'status':'verified bounded trial; UNSELECTED','candidate_sha256':expected,'files':files};(P/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
Z=Path('/workspace/scratch/edd9a5be63e7/v7-release-files/v7-connector-gnd-aaaf-unselected-20261104.zip');assert not Z.exists()
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(P.rglob('*')):
  if f.is_file():z.write(f,str(f.relative_to(P)))
with zipfile.ZipFile(Z) as z:
 for rel,v in files.items():assert H(P/rel)==hashlib.sha256(z.read(rel)).hexdigest()==v['sha256']
 assert set(z.namelist())==set(files)|{'MANIFEST.json'}
receipt={'archive':str(Z),'bytes':Z.stat().st_size,'sha256':H(Z),'members':len(files)+1,'manifest_sha256':H(P/'MANIFEST.json'),'candidate_sha256':expected,'all_members_reloaded_verified':True};(R/'ARCHIVE.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
