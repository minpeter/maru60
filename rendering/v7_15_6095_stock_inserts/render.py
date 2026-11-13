"""Render the exported v7.15 shell on llm-labs with Cycles HIP.

Shell vertices are unchanged from geometry/halves-world.3mf. Brass inserts
are nominal OD3.5 x L3 visualization sleeves; threads/knurling are omitted.
Run with Blender --background --python render.py -- --quality final.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--quality', choices=('preview', 'final'), default='final')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
preview = args.quality == 'preview'

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'HIP'
prefs.refresh_devices()
for device in prefs.devices:
    device.use = device.type == 'HIP'
devices = [{'name': d.name, 'type': d.type, 'enabled': d.use} for d in prefs.devices]
if not any(d['enabled'] and d['type'] == 'HIP' for d in devices):
    raise RuntimeError('HIP GPU required; refusing CPU fallback')
print('RENDER_DEVICES', json.dumps(devices), flush=True)
scene.cycles.device = 'GPU'
scene.cycles.samples = 40 if preview else 256
scene.cycles.adaptive_threshold = 0.025 if preview else 0.008
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 4
scene.cycles.glossy_bounces = 4
scene.render.resolution_x = 1000 if preview else 2800
scene.render.resolution_y = 750 if preview else 2100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.world.use_nodes = True
background = scene.world.node_tree.nodes['Background']
background.inputs['Color'].default_value = (0.78, 0.84, 0.90, 1)
background.inputs['Strength'].default_value = 0.28


def material(name, color, roughness, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return mat


shell_mat = material('Satin blue grey polymer', (0.28, 0.40, 0.46), 0.39)
brass_mat = material('Nominal CANOT brass inserts', (0.60, 0.36, 0.095), 0.27, 0.82)
floor_mat = material('Warm neutral studio', (0.69, 0.68, 0.65), 0.82)


def mesh_object(name, vertices, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.scale = (0.001, 0.001, 0.001)
    obj.data.materials.append(mat)
    return obj


for part in json.loads((ROOT / 'shell-meshes.json').read_text()):
    mesh_object(part['name'], part['vertices'], part['faces'], shell_mat)

# Closed annular sleeves, recessed at the exact eight specified mounting axes.
# The shell itself retains the designed pre-installation bore diameter.
for site in json.loads((ROOT / 'insert-sites.json').read_text()):
    count = 96
    vertices = []
    for z, radius in ((site['top'] - site['length'], site['outer_d'] / 2),
                      (site['top'], site['outer_d'] / 2),
                      (site['top'], site['inner_d'] / 2),
                      (site['top'] - site['length'], site['inner_d'] / 2)):
        for i in range(count):
            angle = 2 * math.pi * i / count
            vertices.append((site['x'] + radius * math.cos(angle),
                             site['y'] + radius * math.sin(angle), z))
    faces = []
    for band in range(4):
        nxt = (band + 1) % 4
        for i in range(count):
            j = (i + 1) % count
            faces.append((band * count + i, band * count + j,
                          nxt * count + j, nxt * count + i))
    mesh_object(site['name'], vertices, faces, brass_mat)

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0.1, -0.001))
bpy.context.object.name = 'Studio ground'
bpy.context.object.data.materials.append(floor_mat)

focus = Vector((0, 0.100, 0.008))


def aim(obj):
    obj.rotation_euler = (focus - obj.location).to_track_quat('-Z', 'Y').to_euler()


bpy.ops.object.camera_add(location=(0.105, -0.120, 0.950))
camera = bpy.context.object
camera.name = 'Underside overview — inserts and stock strike pockets'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 0.448
camera.data.clip_start = 0.001
aim(camera)
scene.camera = camera

for name, location, power, size, color in (
    ('Large warm key', (-0.22, -0.14, 0.45), 1.875, 0.34, (1.0, 0.94, 0.85)),
    ('Cool fill', (0.30, 0.20, 0.28), 1.0, 0.28, (0.85, 0.93, 1.0)),
    ('Rear rim', (-0.10, 0.42, 0.32), 1.4375, 0.24, (1.0, 0.98, 0.92)),
):
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = power
    light.data.shape = 'DISK'
    light.data.size = size
    light.data.color = color
    aim(light)

scene.render.filepath = str(ROOT / ('preview.png' if preview else 'maru60-v7.15-6095-stock-inserts.png'))
if not preview:
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'maru60-v7.15-6095-stock-inserts.blend'))
start = time.time()
bpy.ops.render.render(write_still=True)
receipt = {
    'version': 'v7.15-centred-joint-axis',
    'board': '6095-trimode',
    'catches': 'stock',
    'inserts': 'CANOT M2 OD3.5 x L3; eight nominal sleeves',
    'geometry': 'Unmodified exported upper shell; no lower case, PCB or catch hardware shown',
    'device': scene.cycles.device,
    'backend': prefs.compute_device_type,
    'devices': devices,
    'blender': bpy.app.version_string,
    'samples': scene.cycles.samples,
    'resolution': [scene.render.resolution_x, scene.render.resolution_y],
    'elapsed_seconds': round(time.time() - start, 2),
    'image': Path(scene.render.filepath).name,
    'sha256': hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest(),
    'input_hashes': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                     for name in ('render.py', 'shell-meshes.json', 'insert-sites.json')},
}
(ROOT / ('preview-receipt.json' if preview else 'render-receipt.json')).write_text(json.dumps(receipt, indent=2))
print('RENDER_COMPLETE', json.dumps(receipt), flush=True)
