"""Recolour the saved v7.15 scene's actual halves and render with HIP.

blender-gfx803 -b maru60-v7.15-6095-stock-inserts.blend \
    --python-exit-code 1 --python render_two_tone.py
"""
import hashlib
import json
from pathlib import Path
import time

import bpy

ROOT = Path(__file__).resolve().parent
source = Path(bpy.data.filepath)
assert source.name == 'maru60-v7.15-6095-stock-inserts.blend', source
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
scene = bpy.context.scene
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'HIP'
prefs.refresh_devices()
for device in prefs.devices:
    device.use = device.type == 'HIP'
assert any(device.use and device.type == 'HIP' for device in prefs.devices)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'

colors = {'LeftHalf': (0.045, 0.25, 0.55), 'RightHalf': (0.64, 0.20, 0.055)}
for name, color in colors.items():
    obj = bpy.data.objects[name]
    assert obj.type == 'MESH'
    mat = obj.data.materials[0].copy()
    mat.name = 'Blue left half' if name == 'LeftHalf' else 'Orange right half'
    mat.diffuse_color = (*color, 1)
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*color, 1)
    obj.data.materials.clear()
    obj.data.materials.append(mat)

scene.render.filepath = str(ROOT / 'maru60-v7.15-two-tone.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'maru60-v7.15-two-tone.blend'))
start = time.time()
bpy.ops.render.render(write_still=True)
receipt = {
    'version': 'v7.15-centred-joint-axis',
    'change': 'Materials only; saved geometry, camera, lights and inserts retained',
    'colors_linear_rgb': colors,
    'device': scene.cycles.device,
    'backend': prefs.compute_device_type,
    'devices': [{'name': d.name, 'type': d.type, 'enabled': d.use} for d in prefs.devices],
    'blender': bpy.app.version_string,
    'samples': scene.cycles.samples,
    'resolution': [scene.render.resolution_x, scene.render.resolution_y],
    'elapsed_seconds': round(time.time() - start, 2),
    'source_scene_sha256': source_hash,
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'image_sha256': hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest(),
}
(ROOT / 'two-tone-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('RENDER_COMPLETE', json.dumps(receipt), flush=True)
