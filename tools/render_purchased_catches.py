"""Blender: render the real exported trial meshes; no smoothing modifiers or invented hardware detail.

blender -b --python tools/render_purchased_catches.py -- OUTPUT_DIRECTORY
"""
from pathlib import Path
import sys
import bpy
from mathutils import Matrix, Vector

root=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=20
scene.render.resolution_x=1400
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.world.color=(.35,.35,.35)
scene.view_settings.view_transform='AgX'


def material(name,color):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.48
    return m


blue=material('UPPER / BLUE',(.025,.19,.65))
orange=material('LOWER / ORANGE',(.93,.22,.025))


def load(name,mat,transform=Matrix.Identity(4)):
    bpy.ops.wm.stl_import(filepath=str(root/f'{name}-world.stl'))
    o=bpy.context.object
    o.data.materials.append(mat)
    o.matrix_world=transform
    return o


bpy.ops.object.camera_add()
cam=bpy.context.object
cam.data.type='ORTHO'
scene.camera=cam
for loc,power,size in [((0,-100,450),3300000,280),((220,320,300),2300000,220)]:
    bpy.ops.object.light_add(type='AREA',location=loc)
    o=bpy.context.object
    o.data.energy=power;o.data.shape='DISK';o.data.size=size
    o.rotation_euler=(Vector((0,135,10))-o.location).to_track_quat('-Z','Y').to_euler()


def render(name,focus,offset,scale):
    cam.location=Vector(focus)+Vector(offset)
    cam.rotation_euler=(Vector(focus)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=scale
    scene.render.filepath=str(root/f'{name}.png')
    bpy.ops.render.render(write_still=True)


for version in ['before','purchased']:
    for part in ['upper','lower']:
        # Present the two mating surfaces toward the same camera hemisphere.
        xf=Matrix.Identity(4) if part=='upper' else Matrix.Translation((0,280,30))@Matrix.Rotation(3.141592653589793,4,'X')
        prefix=version if part=='upper' else f'no-bay-{version}'
        objs=[load(f'{prefix}-{part}-{side}',blue if part=='upper' else orange,xf) for side in ['left','right']]
        render(f'{version}-{part}-whole',(0,98.5 if part=='upper' else 140,10),(70,-180,330),450)
        # Back-left (BL) seam/insert area, identical cameras before/after for each case.
        focus=xf@Vector((53.1,191.37,7 if part=='upper' else 15.7))
        render(f'{version}-{part}-detail',focus,(12,-18,70),57)
        for o in objs: bpy.data.objects.remove(o,do_unlink=True)

xf=Matrix.Translation((0,280,30))@Matrix.Rotation(3.141592653589793,4,'X')
objs=[load(f'with-bay-purchased-lower-{side}',orange,xf) for side in ['left','right']]
render('purchased-lower-with-bay',(0,140,10),(70,-180,330),450)
for o in objs: bpy.data.objects.remove(o,do_unlink=True)
