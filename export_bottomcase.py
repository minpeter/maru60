"""Publish the HHKB bottom-case draft print files and evidence from `bottomcase-draft/` (default board only)."""
from pathlib import Path
import json
import shutil

import rule60_spec as spec

ROOT = Path(__file__).resolve().parent
source = ROOT / 'bottomcase-draft'

verification = json.loads((source / 'verification.json').read_text())
assert verification['status'] == 'ALL_PASSED', verification['status']
assert verification['board'] == spec.default_board(), 'publish the default-board build only'
for name in ('left', 'right', 'fit-coupon', 'joint-test'):
    shutil.copyfile(source / f'rule60-hhkb-bottomcase-{name}.3mf', ROOT / 'models' / f'rule60-hhkb-bottomcase-{name}.3mf')
for src, dst in [('draft-report.json', 'bottomcase-report.json'), ('verification.json', 'bottomcase-verification.json')]:
    shutil.copyfile(source / src, ROOT / 'evidence' / dst)
print('Exported bottom-case downloads and evidence.')
