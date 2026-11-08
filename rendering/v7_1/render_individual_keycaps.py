import bpy,sys,os,math,json,importlib.util
from mathutils import Vector
BASE=os.path.dirname(os.path.abspath(__file__))
OUT=BASE+'/individual_keycaps'
os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
spec=importlib.util.spec_from_file_location('caps',BASE+'/create_keycaps_v7_1.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);objects=mod.build_keycaps()
layout=json.load(open(BASE+'/keycaps_v7_1/layout.json'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.cycles.adaptive_threshold=.03;scene.cycles.max_bounces=5
scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True;scene.render.threads_mode='FIXED';scene.render.threads=6
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.82,.84,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.25
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0

def aim(o,point=(0,0,.05)):o.rotation_euler=(Vector(point)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.32,-.45,.8));cam=bpy.context.object;cam.data.type='ORTHO';aim(cam);scene.camera=cam
for loc,power,size in [((-.6,-.5,1.2),35,.7),((.6,.3,.8),15,.6)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power*.8;o.data.size=size;aim(o)
for o in objects:o.hide_render=True
manifest=[]
for i,(o,k) in enumerate(zip(objects,layout)):
 filename=f"key_{i:02d}_{k['name']}.png"
 item={'index':i,'name':k['name'],'row':k['row'],'u_start':k['u_start'],'u_width':k['u_width'],'texture':k['texture'],'filename':filename};manifest.append(item)
 path=OUT+'/'+filename
 if os.path.exists(path): print('EXISTING diagnostic',i,flush=True);continue
 o.hide_render=False
 for mat in o.data.materials:
  node=mat.node_tree.nodes.get('Principled BSDF');node.inputs['Roughness'].default_value=.65
  if 'Specular IOR Level' in node.inputs:node.inputs['Specular IOR Level'].default_value=.12
 o.location=(0,0,0);o.rotation_euler=(0,math.pi,0);o.scale=(.01,.01,.01)
 cam.data.ortho_scale=max(.34,(k['u_width']*19.05-.95)*.01*1.30)
 scene.render.filepath=path;bpy.ops.render.render(write_still=True);o.hide_render=True
 print('DIAGNOSTIC SAVED',i,k['name'],flush=True)
 json.dump(manifest,open(OUT+'/key_manifest_partial.json','w'),indent=2)
json.dump(manifest,open(OUT+'/key_manifest.json','w'),indent=2)
print('ALL60 DIAGNOSTICS COMPLETE',flush=True)
