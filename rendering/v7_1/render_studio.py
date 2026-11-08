import bpy, math, os, sys, json, hashlib, time
from mathutils import Matrix, Vector
BASE=os.path.dirname(os.path.abspath(__file__))
OUT=os.environ.get('KEYBOARD_OUTDIR',BASE+'/output')
os.makedirs(OUT,exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
mode=args[0] if args else 'qa'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=48 if mode=='qa' else 256
scene.cycles.use_denoising=False
scene.cycles.adaptive_threshold=.025
scene.cycles.max_bounces=8
scene.cycles.transmission_bounces=5
scene.render.resolution_x=512 if mode=='qa' else 1024
scene.render.resolution_y=768 if mode=='qa' else 1536
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'; scene.render.image_settings.color_depth='8'
scene.render.film_transparent=True
scene.render.threads_mode='FIXED'; scene.render.threads=6
scene.world.color=(.15,.15,.15)
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.83,.88,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.16
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=0

def material(name,color,rough=.35,metallic=0,transmission=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metallic;p.inputs['Transmission Weight'].default_value=transmission
 return m
shellmat=material('Frosted natural PETG printed white',(.72,.735,.72),.38,0,.13)
p=shellmat.node_tree.nodes.get('Principled BSDF');p.inputs['IOR'].default_value=1.46;p.inputs['Subsurface Weight'].default_value=.045
nt=shellmat.node_tree; tex=nt.nodes.new('ShaderNodeTexCoord');wave=nt.nodes.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='Z';wave.inputs['Scale'].default_value=1.7
nt.links.new(tex.outputs['Object'],wave.inputs['Vector'])
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.035
nt.links.new(wave.outputs['Color'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.1;noise.inputs['Detail'].default_value=2
nt.links.new(tex.outputs['Object'],noise.inputs['Vector'])
ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.52,.54,.52,1);ramp.color_ramp.elements[1].color=(.83,.845,.82,1)
nt.links.new(noise.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],p.inputs['Base Color'])
bpy.ops.wm.stl_import(filepath=BASE+'/shell_assembled.stl');shell=bpy.context.object;shell.name='Exact v7.4 integrated top shell';shell.data.materials.append(shellmat)
# Preserve original tessellation and true holes. Angle-limited smoothing avoids melted corners.
for poly in shell.data.polygons: poly.use_smooth=False

bottommat=material('Inferred frosted translucent stock bottom',(.46,.49,.50),.42,0,.32)
metalmat=material('Inferred brushed champagne metal strip',(.60,.55,.43),.34,.78)
mn=metalmat.node_tree;mp=mn.nodes.get('Principled BSDF');mp.inputs['Anisotropic'].default_value=.65
mt=mn.nodes.new('ShaderNodeTexCoord');vm=mn.nodes.new('ShaderNodeVectorMath');vm.operation='MULTIPLY';vm.inputs[1].default_value=(.025,7,3)
mn.links.new(mt.outputs['Object'],vm.inputs[0]);nz=mn.nodes.new('ShaderNodeTexNoise');nz.inputs['Scale'].default_value=1;nz.inputs['Detail'].default_value=2;mn.links.new(vm.outputs[0],nz.inputs['Vector'])
br=mn.nodes.new('ShaderNodeValToRGB');br.color_ramp.elements[0].color=(.40,.36,.27,1);br.color_ramp.elements[1].color=(.67,.62,.49,1);mn.links.new(nz.outputs['Fac'],br.inputs[0]);mn.links.new(br.outputs[0],mp.inputs['Base Color'])
mb=mn.nodes.new('ShaderNodeBump');mb.inputs['Strength'].default_value=.18;mb.inputs['Distance'].default_value=.018;mn.links.new(nz.outputs['Fac'],mb.inputs['Height']);mn.links.new(mb.outputs[0],mp.inputs['Normal'])
feetmat=material('Cream silicone feet',(.76,.73,.62),.72)
platemat=material('Recessed dark switch plate',(.055,.05,.045),.6)

def cube(name,loc,size,mat,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:
  b=o.modifiers.new('Rounded manufacture edges','BEVEL');b.width=bevel;b.segments=3
  o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
 return o
# These non-CAD internals are reconstructed from the user's actual rear-view video, not claimed exact.
cube('Photo inferred bottom plate',(0,138.65,19.2),(289.8,108.4,2.4),bottommat,1.3)
cube('Recessed switch mounting plate',(0,138.7,3.7),(287.0,95.3,1.3),platemat,.5)
# Long metal accent with stepped center widening, aligned to rear long edge.
poly=[(-124,157),(-20,157),(-16,152),(16,152),(20,157),(124,157),(124,180),(-124,180)]
verts=[(x,y,z) for z in (20.45,21.05) for x,y in poly];n=len(poly)
faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
me=bpy.data.meshes.new('Metal strip mesh');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Photo inferred stepped brushed metal weight',me);bpy.context.collection.objects.link(ob);ob.data.materials.append(metalmat);b=ob.modifiers.new('Subtle machined bevel','BEVEL');b.width=.5;b.segments=2;ob.modifiers.new('Weight normals','WEIGHTED_NORMAL')
for x in(-132,132):
 for y in(94,183): cube('Photo inferred cream rubber foot',(x,y,21.15),(18,4.3,1.1) if y==94 else (4.3,18,1.1),feetmat,1.8)
# Black connector inset visible through exact shell notch.
cube('USB port dark inset',(123.6,192.8,15.7),(9.4,2.5,3.3),platemat,1)

# Keycap worker provides actual-photo legends and custom mesh reconstruction.
if os.path.exists(BASE+'/create_keycaps_v7_1.py'):
 import importlib.util
 spec=importlib.util.spec_from_file_location('keycaps',BASE+'/create_keycaps_v7_1.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 keycap_objects=mod.build_keycaps()
 for keycap_object in keycap_objects:
  for keycap_material in keycap_object.data.materials:
   keycap_node=keycap_material.node_tree.nodes.get('Principled BSDF');keycap_node.inputs['Roughness'].default_value=.65
   if 'Specular IOR Level' in keycap_node.inputs:keycap_node.inputs['Specular IOR Level'].default_value=.12
else: print('WARNING missing keycaps script')

objects=list(bpy.context.scene.objects)
root=bpy.data.objects.new('KEYBOARD_ROTATION_ROOT',None);bpy.context.collection.objects.link(root)
for ob in objects:ob.parent=root
# Source print coordinates: +X is Esc end, +Y away from palm edge, +Z underside.
# Screen front0: Esc end TOP; palmrest LEFT; all long-axis rotations use same transform.
M=Matrix(((0,1,0,0),(1,0,0,0),(0,0,-1,0),(0,0,0,1)))
center=Matrix.Translation((0,-98.685,-5))
def set_angle(angle):root.matrix_world=Matrix.Scale(.01,4)@Matrix.Rotation(math.radians(-15),4,'Z')@M@Matrix.Rotation(math.radians(angle),4,'X')@center
set_angle(0)

def aim(o,point=(0,0,0)):o.rotation_euler=(Vector(point)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,0,9));camera=bpy.context.object;camera.name='Fixed studio camera';camera.data.type='ORTHO';camera.data.ortho_scale=4.55;camera.data.lens=85;aim(camera);scene.camera=camera
for name,loc,power,size,color in [('Large key',(3.8,4.2,5),650,3.6,(1,.97,.92)),('Cool fill',(-4,1,3),150,3.2,(.92,.96,1)),('Top rim',(-1,-4,-2.0),500,3.0,(1,1,1)),('Back fill',(0,2,-4),330,3.0,(1,.98,.94))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power*.8;o.data.shape='DISK';o.data.size=size;o.data.color=color;aim(o)
scene.render.fps=24
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=BASE+'/keyboard_studio_v7_1.blend')
angles=[0,35,110,180] if mode=='qa' else list(range(0,360,5))
if len(args)>1:angles=[int(v) for v in args[1].split(',')]
layout=json.load(open(BASE+'/keycaps_v7_1/layout.json'))
asset_paths=[__file__,BASE+'/create_keycaps_v7_1.py',BASE+'/shell_assembled.stl',BASE+'/keycaps_v7_1/layout.json']+[BASE+'/keycaps_v7_1/'+k['texture'] for k in layout]
uv_config=BASE+'/keycaps_v7_1/uv_placements.json'
if os.path.exists(uv_config):asset_paths.append(uv_config)
asset_hashes={os.path.relpath(f,BASE):hashlib.sha256(open(f,'rb').read()).hexdigest() for f in sorted(set(asset_paths))}
digest=hashlib.sha256(json.dumps(asset_hashes,sort_keys=True).encode()).hexdigest()
statepath=OUT+'/render_checkpoint.json'
state=json.load(open(statepath)) if os.path.exists(statepath) else {'asset_digest':digest,'assets':asset_hashes,'completed':{}}
if state['asset_digest'] != digest: raise RuntimeError('Frozen assets differ from existing output checkpoint. Use a new output directory; do not mix frames.')
for a in angles:
 path=OUT+('/qa_%03d.png'%a if mode=='qa' else '/frame_%03d.png'%(a//5))
 key=str(a)
 old=state['completed'].get(key)
 if old and os.path.exists(path) and hashlib.sha256(open(path,'rb').read()).hexdigest()==old['sha256']:
  print('VALIDATED CHECKPOINT SKIP',a,flush=True);continue
 set_angle(a);scene.render.filepath=path;bpy.ops.render.render(write_still=True)
 state['completed'][key]={'angle_degrees':a,'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'size_bytes':os.path.getsize(path),'finished_unix':time.time()}
 with open(statepath+'.tmp','w') as f:json.dump(state,f,indent=2)
 os.replace(statepath+'.tmp',statepath)
 print('CHECKPOINT SAVED',a,len(state['completed']),flush=True)
print('RENDER COMPLETE',angles)
