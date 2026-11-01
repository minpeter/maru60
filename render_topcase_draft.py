"""Render the Maru60 HHKB top case + honeycomb wrist rest (SolidCraft draft) with Blender Cycles."""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector

ONLY_UNDERSIDE = "--only-underside" in sys.argv
ROOT = Path(__file__).resolve().parent / "topcase-draft"
bpy.ops.object.delete(use_global=False)

parts = []
for i, data in enumerate(json.loads((ROOT / "render-meshes.json").read_text())):
    mesh = bpy.data.meshes.new(data.get("name", f"part-{i}"))
    mesh.from_pydata(data["vertices"], [], data["faces"])
    mesh.update()
    obj = bpy.data.objects.new(data.get("name", f"part-{i}"), mesh)
    bpy.context.collection.objects.link(obj)
    parts.append(obj)


def material(name: str, color: tuple[float, float, float], rough: float = 0.48):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return m


mat_left = material("LeftHalfMat", (0.20, 0.23, 0.27), 0.45)
mat_right = material("RightHalfMat", (0.22, 0.40, 0.52), 0.45)
for i, o in enumerate(parts):
    o.data.materials.clear()
    o.data.materials.append(mat_left if i == 0 else mat_right)

bpy.context.view_layer.update()
all_pts = [o.matrix_world @ Vector(c) for o in parts for c in o.bound_box]
bmin = [min(p[k] for p in all_pts) for k in range(3)]
bmax = [max(p[k] for p in all_pts) for k in range(3)]
center = Vector(((bmin[0] + bmax[0]) / 2, (bmin[1] + bmax[1]) / 2, (bmin[2] + bmax[2]) / 2))
print("BOUNDS", bmin, bmax)

ground = material("StudioGround", (0.78, 0.76, 0.72), 0.75)
bpy.ops.mesh.primitive_plane_add(size=2400, location=(center.x, center.y, -0.5))
ground_obj = bpy.context.object
ground_obj.data.materials.append(ground)

bpy.ops.object.camera_add(location=(center.x + 310, center.y - 430, 360))
cam = bpy.context.object
cam.rotation_euler = (Vector((center.x, center.y, 12)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.type = "ORTHO"
cam.data.ortho_scale = 380
bpy.context.scene.camera = cam

for loc, power, size in [
    ((center.x - 90, center.y - 200, 420), 2800000, 300),
    ((center.x + 260, center.y + 240, 320), 1900000, 260),
]:
    bpy.ops.object.light_add(type="AREA", location=loc)
    lt = bpy.context.object
    lt.data.energy, lt.data.shape, lt.data.size = power, "DISK", size
    lt.rotation_euler = (Vector((center.x, center.y, 8)) - lt.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 36
scene.world.color = (0.32, 0.32, 0.33)
scene.render.resolution_x, scene.render.resolution_y = 1500, 1000
scene.render.resolution_percentage = 100

if not ONLY_UNDERSIDE:
    # 1. Assembled hero view (desk pose)
    scene.render.filepath = str(ROOT / "render-assembled.png")
    bpy.ops.render.render(write_still=True)

    # 2. Exploded dovetail assembly view (RightHalf lifted along insertion axis)
    parts[1].location.z += 22
    parts[1].location.x += 6
    scene.render.filepath = str(ROOT / "render-exploded.png")
    bpy.ops.render.render(write_still=True)
    parts[1].location.z = 0
    parts[1].location.x = 0

    # 3. Direct top view
    cam.location = (center.x, center.y, 500)
    cam.rotation_euler = (0, 0, 0)
    cam.data.ortho_scale = 330
    scene.render.filepath = str(ROOT / "render-top.png")
    bpy.ops.render.render(write_still=True)

# 4. Underside internal structure view — matched warm studio backdrop & unclipped framing
ground_obj.hide_render = True
bpy.ops.mesh.primitive_plane_add(size=2800, location=(center.x, center.y, 120.0))
backdrop_u = bpy.context.object
backdrop_u.data.materials.append(ground)

bpy.ops.object.light_add(type="AREA", location=(center.x - 80, center.y - 160, -360))
lt_u = bpy.context.object
lt_u.data.energy, lt_u.data.shape, lt_u.data.size = 3100000, "DISK", 320
lt_u.rotation_euler = (Vector((center.x, center.y, 10)) - lt_u.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.light_add(type="AREA", location=(center.x + 220, center.y + 180, -280))
lt_u2 = bpy.context.object
lt_u2.data.energy, lt_u2.data.shape, lt_u2.data.size = 1900000, "DISK", 260
lt_u2.rotation_euler = (Vector((center.x, center.y, 10)) - lt_u2.location).to_track_quat("-Z", "Y").to_euler()

cam.location = (center.x + 175, center.y - 270, -340)
cam.rotation_euler = (Vector((center.x - 2, center.y, 10)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.ortho_scale = 455
scene.render.filepath = str(ROOT / "render-underside.png")
bpy.ops.render.render(write_still=True)
