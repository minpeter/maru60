"""Compare exported v7.15 solids with the original v7.13 joint geometry."""
import json
from pathlib import Path
import sys

import manifold3d as md
import trimesh

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
from maru60.mesh_io import to_manifold


def load(path):
    scene = trimesh.load_scene(path)
    parts = {}
    for node in scene.graph.nodes_geometry:
        transform, name = scene.graph[node]
        mesh = scene.geometry[name].copy()
        mesh.apply_transform(transform)
        parts[node] = to_manifold(mesh)
    return parts


def difference(a, b):
    return float((a - b).volume() + (b - a).volume())


old = load(ROOT.parent / 'v7_13_6095_stock_inserts/geometry/halves-world.3mf')
new = load(ROOT / 'geometry/halves-world.3mf')
joint_delta = {}
for y in (23.5, 50.0, 75.5):
    region = md.Manifold.cube([13.6, 14.4, 26]).translate([-3.9, y - 7.2, -0.5])
    for name in ('LeftHalf', 'RightHalf'):
        delta = difference(old[name] ^ region, new[name].translate([2.9, 0, 0]) ^ region)
        assert delta < 0.03, (name, y, delta)
        joint_delta[f'{name}-y{y}'] = delta

before = old['LeftHalf'] + old['RightHalf']
after = new['LeftHalf'] + new['RightHalf']
interfaces = md.Manifold.cube([310, 120, 30]).translate([-155, 84, -1])
skin = md.Manifold.cube([310, 80, 2.199]).translate([-155, 0, 0])
interface_delta = difference(before ^ interfaces, after ^ interfaces)
skin_delta = difference(before ^ skin, after ^ skin)
assert interface_delta < 0.05, interface_delta
assert skin_delta < 0.05, skin_delta
result = {
    'joint_translation_x_mm': -2.9,
    'joint_geometry_change_after_alignment_mm3': joint_delta,
    'keyboard_interface_change_mm3': interface_delta,
    'wrist_top_skin_change_mm3': skin_delta,
    'assembled_volume_change_from_v7_13_mm3': float(after.volume() - before.volume()),
    'rib_width_mm': 13.8,
    'middle_pad_width_mm': 16.0,
    'middle_pad_centre_x_mm': 0.0,
}
(ROOT / 'change-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
