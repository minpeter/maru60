"""Publish the Maru60 HHKB top case + wrist rest print files, evidence and renders from `topcase-draft/`.

A build for the default board publishes everything. A build for another `--board` changes only the USB-C notch in the
right half, so it publishes just that half as `models/maru60-hhkb-topcase-right-usb-<board>.3mf` with its verification.
The upper-only CANOT insert variant exports both halves with a separate `-canot-inserts` suffix.
"""
from pathlib import Path
import json
import shutil
import zipfile

import rule60_spec as spec
from maru60.paths import topcase_dir
from maru60.provenance import require_verified

ROOT = Path(__file__).resolve().parent
source = topcase_dir()

require_verified(source)
verification = json.loads((source / 'verification.json').read_text())
assert verification['status'] == 'ALL_PASSED', verification['status']
report = json.loads((source / 'draft-report.json').read_text())
board = report['geometry_mm']['usb_notch']['board']
inserts = report['strike_inserts']
assert verification['board'] == board and verification['strike_inserts'] == inserts, 'Verify the current board/insert variant before export'
suffix = '-canot-inserts' if inserts else ''
if inserts and board != spec.default_board():
    suffix += f'-usb-{board}'


def publish_3mf(src: str, dst: str) -> None:
    # Each print 3MF carries the 0.10 mm layer range over the pocket floors.
    with zipfile.ZipFile(source / src) as z:
        assert 'Metadata/layer_config_ranges.xml' in z.namelist(), src
    shutil.copyfile(source / src, ROOT / 'models' / dst)


if board != spec.default_board() and not inserts:
    publish_3mf('maru60-hhkb-right-plate.3mf', f'maru60-hhkb-topcase-right-usb-{board}.3mf')
    shutil.copyfile(source / 'verification.json', ROOT / 'evidence' / f'topcase-verification-usb-{board}.json')
    print(f'Exported the right half for board {board!r} and its verification.')
    raise SystemExit

for src, dst in [
    ('maru60-hhkb-left-plate.3mf', 'maru60-hhkb-topcase-left.3mf'),
    ('maru60-hhkb-right-plate.3mf', 'maru60-hhkb-topcase-right.3mf'),
    ('maru60-fit-test-coupons.3mf', 'maru60-hhkb-topcase-fit-coupons.3mf'),
]:
    publish_3mf(src, f'{Path(dst).stem}{suffix}.3mf')
for src, dst in [('draft-report.json', 'topcase-report.json'), ('verification.json', 'topcase-verification.json')]:
    shutil.copyfile(source / src, ROOT / 'evidence' / f'{Path(dst).stem}{suffix}.json')
# Renders come from the optional Blender step; publish them only when all four exist and postdate the build.
renders = [source / f'render-{view}.png' for view in ('assembled', 'top', 'exploded', 'underside')]
built_at = (source / 'render-meshes.json').stat().st_mtime
if all(p.exists() and p.stat().st_mtime >= built_at for p in renders):
    for p in renders:
        shutil.copyfile(p, ROOT / 'images' / f'{p.stem.replace("render-", "topcase-")}{suffix}.png')
    print('Exported top-case downloads, evidence and renders.')
else:
    print('Exported top-case downloads and evidence; renders missing or older than the build, images/ unchanged.')
