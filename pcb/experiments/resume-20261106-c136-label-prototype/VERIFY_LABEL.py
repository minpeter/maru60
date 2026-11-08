from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
B=json.loads((P/'qa/build.json').read_text());a=(P/'evidence/source-ef45f84/pcb/maru60.kicad_pcb').read_text();b=(P/'pcb/maru60.kicad_pcb').read_text()
assert b.count(B['new_form'])==1 and b.replace(B['new_form'],B['old_form'],1)==a
H=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert H(P/'pcb/maru60.kicad_pcb')==B['candidate_sha256'] and H(P/'evidence/source-ef45f84/pcb/maru60.kicad_pcb')==B['source_sha256']
a={str(f.relative_to(P/'pcb')):H(f) for f in (P/'pcb').rglob('*') if f.is_file() and f.name!='maru60.kicad_pcb'};b={str(f.relative_to(P/'evidence/source-ef45f84/pcb')):H(f) for f in (P/'evidence/source-ef45f84/pcb').rglob('*') if f.is_file() and f.name!='maru60.kicad_pcb'}
assert a==b and len(a)==57
print('PASS: Only declared C136 Reference property differs; all copper, masks, fills, other labels, rules and57 companions exact.')
