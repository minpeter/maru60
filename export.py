"""Publish current model-only downloads, including float32-safe binary STLs."""
from pathlib import Path
import io
import shutil
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
source = ROOT / 'rib-2.4-male-expanded-0.20-compression-0.10'
models = ROOT / 'models' / 'rule60-v3-wrist-rest'

for name, count in [('left', 1), ('right', 1), ('rule60-one-plate', 2)]:
    original = trimesh.load_mesh(source / (name + '.stl'))
    # Binary STL uses float32. Round before removing collapsed triangles, so
    # MakerWorld's conversion cannot leave zero-area faces in the download.
    mesh = trimesh.load(io.BytesIO(original.export(file_type='stl')), file_type='stl')
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-8))
    mesh.remove_unreferenced_vertices()
    data = mesh.export(file_type='stl')
    check = trimesh.load(io.BytesIO(data), file_type='stl')
    assert check.is_watertight and check.is_winding_consistent
    assert len(check.split(only_watertight=False)) == count
    assert np.allclose(check.bounds, original.bounds, atol=1e-5, rtol=0)
    assert abs(check.volume - original.volume) < .02
    (models / (name + '.stl')).write_bytes(data)

for src, dst in [
    ('rule60-one-plate', 'rule60-v9-honeycomb-body'),
    ('test-joint-plate', 'rule60-v9-joint-test'),
    ('replacement-left', 'rule60-tight-fit-left'),
    ('replacement-test-left', 'rule60-tight-fit-test-left'),
]:
    shutil.copyfile(source / (src + '.3mf'), models / (dst + '.3mf'))
for name in ('dimensions.json', 'verification.json'):
    shutil.copyfile(source / name, ROOT / 'evidence' / name)
print('Exported tight-fit downloads; binary STL round-trip checks passed.')
