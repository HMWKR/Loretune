import bpy,json,math,time,hashlib,struct,resource
from pathlib import Path
import numpy as np
from mathutils import Vector
out=Path('/output');cfg=json.loads(Path('/input/scene.json').read_text());started=time.monotonic()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4;scene.cycles.seed=0
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=cfg['width'];scene.render.resolution_y=cfg['height'];scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(*cfg['background'],1)
raw=Path('/input/chair.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:];primitive=doc['meshes'][0]['primitives'][0]
def decode(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dims={'VEC3':3,'VEC4':4}[a['type']];dt={5121:'u1',5126:'<f4'}[a['componentType']];assert 'byteStride' not in v
 return np.frombuffer(binary,dtype=dt,count=a['count']*dims,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,dims)
positions=decode(primitive['attributes']['POSITION']);colors=decode(primitive['attributes']['COLOR_0']).astype(np.float64)/255
expected={}
for pos,color in zip(positions,colors):
 key=tuple(round(float(x),6) for x in (pos[0],-pos[2],pos[1]))
 if key in expected:assert np.array_equal(expected[key],color),'color collision at mapped position'
 expected[key]=color
bpy.ops.import_scene.gltf(filepath='/input/chair.glb');imported=list(bpy.context.scene.objects);meshes=[o for o in imported if o.type=='MESH'];assert len(meshes)==1
obj=meshes[0];mesh=obj.data
asset_root=bpy.data.objects.new('diagnostic-root',None);scene.collection.objects.link(asset_root)
for item in imported:
 if item.parent not in imported:
  world=item.matrix_world.copy();item.parent=asset_root;item.matrix_world=world
spec=cfg['objects'][0];asset_root.location=spec['position'];asset_root.rotation_euler=[math.radians(x) for x in spec['rotation_degrees']];asset_root.scale=spec['scale']
original_attr=mesh.color_attributes[0];original_attr_name=original_attr.name
float_colors=np.array([expected[tuple(round(float(x),6) for x in v.co)] for v in mesh.vertices],dtype=np.float64)
attr=mesh.color_attributes.new('DiagnosticExact',type='FLOAT_COLOR',domain='POINT')
mat=mesh.materials[0];tree=mat.node_tree;vnode=next(n for n in tree.nodes if n.bl_idname=='ShaderNodeVertexColor');bsdf=next(n for n in tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');output=next(n for n in tree.nodes if n.bl_idname=='ShaderNodeOutputMaterial')
emission=tree.nodes.new('ShaderNodeEmission');emission.inputs['Strength'].default_value=1;tree.links.new(vnode.outputs['Color'],emission.inputs['Color'])
for data in cfg['lights']:
 bpy.ops.object.light_add(type='AREA',location=data['position']);light=bpy.context.object;light.data.energy=data['energy_w'];light.data.size=data['size_m'];light.data.color=data['color'];light.rotation_euler=(Vector(data['target'])-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=cfg['camera']['position']);camera=bpy.context.object;camera.rotation_euler=(Vector(cfg['camera']['target'])-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='PERSP';camera.data.sensor_fit='HORIZONTAL';camera.data.sensor_width=36;camera.data.lens=cfg['camera']['lens_mm'];scene.camera=camera
# Object-index mask is identical across cases and separates the subject from background.
obj.pass_index=1;scene.view_layers[0].use_pass_object_index=True

def geometry_digest():
 return hashlib.sha256(json.dumps({'vertices':[list(v.co) for v in mesh.vertices],'faces':[list(p.vertices) for p in mesh.polygons]},separators=(',',':')).encode()).hexdigest()
geometry_sha=geometry_digest();records=[]
for name,interpretation,shader in [('native-byte-pbr','imported-byte','pbr'),('raw-float-pbr','raw','pbr'),('inverse-srgb-float-pbr','inverse-srgb','pbr'),('raw-float-emission','raw','emission')]:
 t=time.monotonic();vnode.layer_name=original_attr_name if interpretation=='imported-byte' else attr.name
 values=float_colors.copy()
 if interpretation=='inverse-srgb':values[:,:3]=np.where(values[:,:3]<=0.04045,values[:,:3]/12.92,((values[:,:3]+0.055)/1.055)**2.4)
 attr.data.foreach_set('color',values.astype(np.float32).reshape(-1));actual=np.empty((len(attr.data),4),dtype=np.float32);attr.data.foreach_get('color',actual.reshape(-1))
 for link in list(output.inputs['Surface'].links):tree.links.remove(link)
 tree.links.new(emission.outputs[0] if shader=='emission' else bsdf.outputs[0],output.inputs['Surface'])
 assert geometry_digest()==geometry_sha
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='8';scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_depth='32';scene.render.image_settings.exr_codec='ZIP'
 exr=out/(name+'.exr');bpy.data.images['Render Result'].save_render(str(exr),scene=scene)
 loaded=bpy.data.images.load(str(exr),check_existing=False);rgba=np.empty((cfg['height'],cfg['width'],4),dtype=np.float32);loaded.pixels.foreach_get(rgba.reshape(-1));np.save(out/(name+'-linear.npy'),rgba);space=loaded.colorspace_settings.name;bpy.data.images.remove(loaded)
 record={'case':name,'interpretation':interpretation,'shader':shader,'seconds':time.monotonic()-t,'geometry_sha256':geometry_sha,'vertices':len(mesh.vertices),'triangles':len(mesh.polygons),'float_attr_max_storage_error':float(np.max(np.abs(actual-values))),'vertex_color_layer':vnode.layer_name,'surface_link':[l.from_node.bl_idname for l in output.inputs['Surface'].links],'linear_buffer_colorspace':space,'linear_min':rgba[:,:,:3].min((0,1)).tolist(),'linear_max':rgba[:,:,:3].max((0,1)).tolist(),'linear_center':rgba[cfg['height']//2,cfg['width']//2].tolist(),'png_sha256':hashlib.sha256((out/(name+'.png')).read_bytes()).hexdigest(),'exr_sha256':hashlib.sha256(exr.read_bytes()).hexdigest()}
 records.append(record);(out/'case-receipts.json').write_text(json.dumps(records,indent=2));print('CASE_DONE '+json.dumps(record),flush=True)
settings={'blender':bpy.app.version_string,'original_glb_sha256':hashlib.sha256(raw).hexdigest(),'scene':cfg,'engine':scene.render.engine,'device':scene.cycles.device,'samples':scene.cycles.samples,'seed':scene.cycles.seed,'threads':scene.render.threads,'view_transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma,'world_strength':scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value,'bsdf_defaults':{k:bsdf.inputs[k].default_value for k in ['Metallic','Roughness','IOR','Specular IOR Level']},'geometry_sha256':geometry_sha,'float_color_domain':attr.domain,'float_color_type':attr.data_type,'time_total_seconds':time.monotonic()-started,'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'differences_from_product':['independent script; direct read-only input mount and owned output bind','explicit fixed2 Blender threads and AgX/None/exposure0/gamma1','diagnostic FLOAT_COLOR and shader variants; no production adapter','extra EXR/float-buffer output and object-index pass; no new provider inference']}
(out/'settings.json').write_text(json.dumps(settings,indent=2));print('EXPERIMENT_COMPLETE',flush=True)
