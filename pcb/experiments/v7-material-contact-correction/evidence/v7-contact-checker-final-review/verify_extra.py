#!/usr/bin/python3
from pathlib import Path
import json,hashlib
P=Path('/tmp/v7-contact-checker-final-review/verify_completed.py')
text=P.read_text(); assert text.count('commands=json.loads')==1
ns={'__name__':'independent_extra_audit','__file__':str(P)}
exec(compile(text.split('commands=json.loads')[0],str(P)+'::definitions','exec'),ns,ns)
R=ns['R']; sha=ns['sha']; commands=json.loads((R/'extra-commands.json').read_text())
assert [c['label'] for c in commands]==['j3_b5c','c124_ec487']
report={'status':'PASS','scope':'Independent pure command/source/output/log/root/NPTH reconstruction for the two completed current-family corrected exports. No native rerun or selection.','runs':[ns['audit'](c)for c in commands],'source_bindings':{str(R/'extra-commands.json'):sha(R/'extra-commands.json'),str(P):sha(P)},'script_sha256':sha(__file__)}
Path('/tmp/v7-contact-checker-final-review/EXTRA_RUN_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
