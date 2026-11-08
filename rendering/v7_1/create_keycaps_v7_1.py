"""Photo-derived approximate Cherry-profile keycaps in v7.4 PRINT coordinates (mm).
Call build_keycaps() inside Blender. Shell is top-down: typing face z=0, keys extend -Z.
Geometry dimensions/profile inferred from user photos and verified shell layout.
Legends combine verified-source reconstruction, official marks, and QA-accepted
imagegen restorations; exact provenance and uncertain microtext remain documented.
"""
import bpy, math, json, os
from mathutils import Vector
ROOT=os.path.dirname(os.path.abspath(__file__))
ASSETS=os.path.join(ROOT,'keycaps_v7_1')
def srgb(c): return ((c+.055)/1.055)**2.4 if c>.04045 else c/12.92

def rounded_ring(w,h,r,steps=8):
    pts=[]
    for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(steps):
            a=math.radians(start+j*90/steps)
            pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts

def configure_region_ink(nodes,links,texture,color,k):
    configpath=os.path.join(ASSETS,'uv_placements.json')
    cfg=json.load(open(configpath)).get(k['name'],{}) if os.path.exists(configpath) else {}
    uv=nodes.new('ShaderNodeTexCoord').outputs['UV']
    def mathnode(op,a,b=None):
        n=nodes.new('ShaderNodeMath');n.operation=op
        if isinstance(a,(int,float)):n.inputs[0].default_value=a
        else:links.new(a,n.inputs[0])
        if b is not None:
            if isinstance(b,(int,float)):n.inputs[1].default_value=b
            else:links.new(b,n.inputs[1])
        return n.outputs[0]
    def transform(scale,anchor,offset=(0,0)):
        a=nodes.new('ShaderNodeVectorMath');a.operation='SUBTRACT';links.new(uv,a.inputs[0]);a.inputs[1].default_value=(anchor[0]+offset[0],anchor[1]+offset[1],0)
        b=nodes.new('ShaderNodeVectorMath');b.operation='SCALE';links.new(a.outputs[0],b.inputs[0]);b.inputs[3].default_value=1/scale
        c=nodes.new('ShaderNodeVectorMath');c.operation='ADD';links.new(b.outputs[0],c.inputs[0]);c.inputs[1].default_value=(*anchor,0)
        return c.outputs[0]
    def mask(coords,bounds):
        x0,y0,x1,y1=bounds;n=nodes.new('ShaderNodeSeparateXYZ');links.new(coords,n.inputs[0])
        return mathnode('MULTIPLY',mathnode('MULTIPLY',mathnode('GREATER_THAN',n.outputs[0],x0),mathnode('LESS_THAN',n.outputs[0],x1)),mathnode('MULTIPLY',mathnode('GREATER_THAN',n.outputs[1],y0),mathnode('LESS_THAN',n.outputs[1],y1)))
    regions=cfg.get('regions',[])
    if cfg.get('whole_scale'):
        links.new(transform(cfg['whole_scale'],cfg.get('whole_anchor',(.5,.5))),texture.inputs['Vector'])
    alpha=texture.outputs['Alpha']
    for r in regions:alpha=mathnode('MULTIPLY',alpha,mathnode('SUBTRACT',1,mask(uv,r['bounds'])))
    mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=color;links.new(alpha,mix.inputs[0]);links.new(texture.outputs['Color'],mix.inputs[2]);result=mix.outputs[0]
    for r in regions:
        coords=transform(r['scale'],r['anchor'],r.get('offset',(0,0)));t=nodes.new('ShaderNodeTexImage');t.image=texture.image;t.extension='CLIP';t.interpolation='Linear';links.new(coords,t.inputs['Vector'])
        a=mathnode('MULTIPLY',t.outputs['Alpha'],mask(coords,r['bounds']))
        m=nodes.new('ShaderNodeMixRGB');links.new(a,m.inputs[0]);links.new(result,m.inputs[1]);links.new(t.outputs['Color'],m.inputs[2]);result=m.outputs[0]
    return result

def make_material(k):
    m=bpy.data.materials.new('Keycap_'+k['name']); m.use_nodes=True
    nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes.get('Principled BSDF')
    color=tuple(srgb(c) for c in k['color'][:3])+(1,)
    p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.37
    if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.28
    texture=nodes.new('ShaderNodeTexImage'); texture.image=bpy.data.images.load(os.path.join(ASSETS,k['texture']),check_existing=True)
    texture.extension='CLIP';texture.interpolation='Linear'
    links.new(configure_region_ink(nodes,links,texture,color,k),p.inputs['Base Color'])
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=110
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.06;bump.inputs['Distance'].default_value=.015
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],p.inputs['Normal'])
    body=bpy.data.materials.new('KeycapSides_'+k['name']);body.use_nodes=True
    q=body.node_tree.nodes.get('Principled BSDF');q.inputs['Base Color'].default_value=color;q.inputs['Roughness'].default_value=.4
    return m,body

def stepped_capslock_geometry(w,h,height):
    """v7: dense rounded S-fillet top and contoured side loft avoids nonplanar flat-quad triangle seams."""
    tw=w-4.6;th=12.6;cut=tw/2-17.5;start=cut-2.4
    xs=sorted(set([-tw/2+i*tw/72 for i in range(73)]+[start,cut]))
    ny=33;verts=[];faces=[];mids=[]
    for j in range(ny):
        v=-1+2*j/(ny-1)
        for x in xs:
            radius=1.15;dx=max(0,abs(x)-(tw/2-radius));ym=th/2-radius+math.sqrt(max(0,radius*radius-dx*dx))
            y=v*ym;t=max(0,min(1,(x-start)/(cut-start)))
            drop=3.2*(.5+.5*math.cos(math.pi*t))
            dish=(.10+.45*t)*(1-(y/(th/2))**2)
            verts.append((x,y,-height+drop+dish))
    nx=len(xs)
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i;faces.append((a,a+nx,a+nx+1,a+1));mids.append(0 if xs[i]>=cut-1e-6 else 1)
    edge=list(range(nx))+[j*nx+nx-1 for j in range(1,ny)]+[(ny-1)*nx+i for i in range(nx-2,-1,-1)]+[j*nx for j in range(ny-2,0,-1)]
    top=[verts[i]for i in edge];prior=edge
    # Closely-spaced side loft quads + smooth normals, ratherthan large twisted panels.
    for ringstep in range(1,9):
        q=ringstep/8;ring=[]
        for x,y,z in top:
            ring.append(len(verts));verts.append((x*(1+q*((w-.2)/tw-1)),y*(1+q*((h-.2)/th-1)),z+q*((-height+5)-z)))
        for i in range(len(edge)):
            ni=(i+1)%len(edge);faces.append((prior[i],prior[ni],ring[ni],ring[i]));mids.append(1)
        prior=ring
    ring=[]
    for x,y,z in top:ring.append(len(verts));verts.append((x*w/tw,y*h/th,2))
    for i in range(len(edge)):
        ni=(i+1)%len(edge);faces.append((prior[i],prior[ni],ring[ni],ring[i]));mids.append(1)
    faces.append(tuple(reversed(ring)));mids.append(1)
    return verts,faces,mids

def build_keycaps():
    layout=json.load(open(os.path.join(ASSETS,'layout.json')))
    collection=bpy.data.collections.new('PhotoReferencedKeycaps');bpy.context.scene.collection.children.link(collection)
    objects=[]
    for k in layout:
        row=k['row'];u=k['u_width'];w=u*19.05-.95;h=18.1;tw=w-4.6;th=12.6
        height=[11.3,9.9,8.8,10.3,10.2][row]
        if k['name']=='space': th=14.0;height=10.1
        n=32; verts=[];faces=[];mids=[];uv=[]
        bottom=rounded_ring(w,h,.7); shoulder=rounded_ring(w-.2,h-.2,.8);top=rounded_ring(tw,th,1.0)
        # Body bottom and shoulder then lip; negativeZ is outwards.
        for ring,z in [(bottom,2.0),(shoulder,-height+5.0),(top,-height)]:
            verts.extend([(x,y,z) for x,y in ring])
        for ring in range(2):
            for i in range(n):
                faces.append((ring*n+(i+1)%n,ring*n+i,(ring+1)*n+i,(ring+1)*n+(i+1)%n));mids.append(1)
        # Sculpted top: concentric rounded rectangles with shallow cylindrical dish.
        last=2*n
        for ri,scale in enumerate([.8,.6,.4,.2]):
            offset=len(verts)
            for x,y in top:
                xx=x*scale;yy=y*scale
                dish=.85*(1-(yy/(th/2))**2)
                if k['name']=='space':dish=-.3*(1-(yy/(th/2))**2)
                verts.append((xx,yy,-height+dish))
            for i in range(n):faces.append((last+(i+1)%n,last+i,offset+i,offset+(i+1)%n));mids.append(0)
            last=offset
        center=len(verts);verts.append((0,0,-height+(-.3 if k['name']=='space' else .85)))
        for i in range(n):faces.append((last+(i+1)%n,last+i,center));mids.append(0)
        faces.append(tuple(range(n)));mids.append(1)
        if k['name']=='CapsLock': verts,faces,mids=stepped_capslock_geometry(w,h,height)
        if k['name'] in ['F','J']:
            # Photo-confirmed homing bars, estimated dimensions in mm.
            by=-4.7; dish=.85*(1-(by/(th/2))**2); zbase=-height+dish+.10; ztop=zbase-.40
            start=len(verts)
            verts.extend([(x,y,z) for z in [ztop,zbase] for x,y in [(-1.75,by-.275),(1.75,by-.275),(1.75,by+.275),(-1.75,by+.275)]])
            for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
                faces.append(tuple(start+i for i in face));mids.append(1)
        mesh=bpy.data.meshes.new(k['name']+'_mesh');mesh.from_pydata(verts,[],faces);mesh.update()
        obj=bpy.data.objects.new('Keycap_'+k['name'],mesh);collection.objects.link(obj)
        obj.location=(142.95-(k['u_start']+u/2)*19.05,84.82+91.944-row*19.05,0)
        m,b=make_material(k);mesh.materials.append(m);mesh.materials.append(b)
        layer=mesh.uv_layers.new(name='PhotoLegendUV')
        for poly,mid in zip(mesh.polygons,mids):
            poly.material_index=mid;poly.use_smooth=(mid==0 or k['name']=='CapsLock')
            for li in poly.loop_indices:
                v=mesh.vertices[mesh.loops[li].vertex_index].co
                # PlateX reversed in PRINT coords, therefore textU must reverse.
                layer.data[li].uv=(( (tw/2-v.x)/17.5 if k['name']=='CapsLock' else .5-v.x/tw),.5+v.y/th)
        bevel=obj.modifiers.new('Soft physical edges','BEVEL');bevel.width=.22;bevel.segments=2
        if k['name']=='CapsLock':
            bevel.width=.18;bevel.segments=3;bevel.harden_normals=True
            wn=obj.modifiers.new('Stable step normals','WEIGHTED_NORMAL');wn.keep_sharp=True;wn.weight=30
        objects.append(obj)
    return objects

if __name__=='__main__':
    build_keycaps()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'keycaps_v7_1.blend'))
