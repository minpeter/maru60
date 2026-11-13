"""Convert this variant's verified 3MF into Blender's portable mesh inputs.

From the repository root: uv run python rendering/v7_13_6095_stock_inserts/prepare.py
"""
import json
from pathlib import Path
import sys

import trimesh

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
import build_topcase_draft as top

report = json.loads((ROOT / 'geometry/draft-report.json').read_text())
verification = json.loads((ROOT / 'geometry/verification.json').read_text())
assert report['version'] == 'v7.13-seam-bumpon'
assert verification['status'] == 'ALL_PASSED'
assert verification['board'] == '6095-trimode'
assert verification['inserts'] and verification['catch_hardware'] == 'stock'

scene = trimesh.load_scene(ROOT / 'geometry/halves-world.3mf')
parts = []
for name in scene.graph.nodes_geometry:
    matrix, geometry = scene.graph[name]
    mesh = scene.geometry[geometry].copy()
    mesh.apply_transform(matrix)
    parts.append({'name': name, 'vertices': mesh.vertices.tolist(), 'faces': mesh.faces.tolist()})
(ROOT / 'shell-meshes.json').write_text(json.dumps(parts))

sites = []
for name, sx, sy in top.strike_centers_p():
    x, y = top.pw(sx, sy)
    for index, dx in enumerate((-6.5, 6.5), 1):
        recess = top.CANOT_INSERT['bl2_recess'] if name == 'BL' and index == 2 else 0
        sites.append({'name': f'U-{name}.{index}', 'x': x + dx, 'y': y,
                      'top': top.Z_STRIKE - recess, 'length': 3.0,
                      'outer_d': 3.5, 'inner_d': 2.0})
(ROOT / 'insert-sites.json').write_text(json.dumps(sites, indent=2))
print(f'Prepared {len(parts)} exact shell meshes and {len(sites)} insert visualization sites')
