"""Publish the Maru60 HHKB bottom-case draft print files and evidence from `bottomcase-draft/`.

A build for the default board publishes everything; `--no-battery-bay` adds a `-no-battery-bay` suffix. A build for
another `--board` changes only the USB-C slot in the left half, so it publishes just that half as
`models/maru60-hhkb-bottomcase-left[-no-battery-bay]-usb-<board>.3mf` with its verification.
"""
from pathlib import Path
import json
import shutil

import rule60_spec as spec
from maru60.paths import topcase_dir, bottomcase_dir
from maru60.provenance import require_verified

ROOT = Path(__file__).resolve().parent
source = bottomcase_dir()

require_verified(source, (topcase_dir(),))
verification = json.loads((source / 'verification.json').read_text())
assert verification['status'] == 'ALL_PASSED', verification['status']
board = verification['board']
report = json.loads((source / 'draft-report.json').read_text())
assert verification['board'] == report['board'] and verification['battery_bay'] == report['battery_bay'], 'verify the current board/battery-bay variant before export'
luban = report.get('catch_hardware', 'stock') == 'luban32'
assert verification.get('catch_hardware', 'stock') == report.get('catch_hardware', 'stock'), 'verify the current catch variant before export'
suffix = ('-luban32' if luban else '') + ('' if verification['battery_bay'] else '-no-battery-bay')
if luban and board != spec.default_board():
    suffix += f'-usb-{board}'

if board != spec.default_board() and not luban:
    shutil.copyfile(source / 'maru60-hhkb-bottomcase-left.3mf',
                    ROOT / 'models' / f'maru60-hhkb-bottomcase-left{suffix}-usb-{board}.3mf')
    shutil.copyfile(source / 'verification.json', ROOT / 'evidence' / f'bottomcase-verification{suffix}-usb-{board}.json')
    print(f'Exported the left half for board {board!r} and its verification.')
    raise SystemExit

for name in ('left', 'right', 'fit-coupon', 'joint-test'):
    shutil.copyfile(source / f'maru60-hhkb-bottomcase-{name}.3mf',
                    ROOT / 'models' / f'maru60-hhkb-bottomcase-{name}{suffix}.3mf')
for src, dst in [('draft-report.json', 'bottomcase-report.json'), ('verification.json', 'bottomcase-verification.json')]:
    shutil.copyfile(source / src, ROOT / 'evidence' / f'{Path(dst).stem}{suffix}.json')
print('Exported bottom-case downloads and evidence.')
