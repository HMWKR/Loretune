SCENE_JSON = '{"background":[0.1,0.3,0.8],"camera":{"lens_mm":50,"position":[5,-7,5],"target":[0,0,0]},"height":192,"lights":[{"color":[1,1,1],"energy_w":800,"id":"key","position":[3,-4,6],"size_m":3,"target":[0,0,0]}],"objects":[{"color":[0.05,0.25,0.8],"id":"subject","kind":"cube","position":[0,0,0],"rotation_degrees":[0,0,0],"scale":[1,1,1]}],"schema_version":1,"width":192}'
import bpy, json, math, time
from mathutils import Vector
scene_data = json.loads(SCENE_JSON)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 4
scene.cycles.seed = 0
scene.render.resolution_x = scene_data['width']
scene.render.resolution_y = scene_data['height']
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = '/output/frame.png'
scene.world.color = tuple(scene_data['background'])
for data in scene_data['objects']:
    if data['kind'] == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=2, location=data['position'])
    elif data['kind'] == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=data['position'])
    elif data['kind'] == 'plane':
        bpy.ops.mesh.primitive_plane_add(size=2, location=data['position'])
    obj = bpy.context.object
    obj.name = data['id']
    obj.rotation_euler = [math.radians(v) for v in data['rotation_degrees']]
    obj.scale = data['scale']
    material = bpy.data.materials.new('material-' + data['id'])
    material.use_nodes = True
    material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*data['color'], 1)
    obj.data.materials.append(material)
for data in scene_data['lights']:
    bpy.ops.object.light_add(type='AREA', location=data['position'])
    light = bpy.context.object
    light.name = data['id']
    light.data.energy = data['energy_w']
    light.data.size = data['size_m']
    light.data.color = data['color']
    light.rotation_euler = (Vector(data['target']) - light.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add(location=scene_data['camera']['position'])
camera = bpy.context.object
camera.rotation_euler = (Vector(scene_data['camera']['target']) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'PERSP'
camera.data.sensor_fit = 'HORIZONTAL'
camera.data.sensor_width = 36
camera.data.lens = scene_data['camera']['lens_mm']
scene.camera = camera
bpy.ops.render.render(write_still=True)
with open('/output/ready', 'x', encoding='ascii') as marker:
    marker.write('complete')
# The output tmpfs disappears when a container stops. Keep this trusted process
# alive while the host copies the verified-size result; the host then removes it.
while True:
    time.sleep(1)
