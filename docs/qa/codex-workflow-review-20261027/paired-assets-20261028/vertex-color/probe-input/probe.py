import bpy,json,struct,hashlib
from pathlib import Path
out=[]
for path in sorted(Path('/input').glob('*.glb')):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);b=raw[28+n:]
 def decode(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dim={'VEC3':3,'VEC4':4}[a['type']];code,size={5121:('B',1),5123:('H',2),5126:('f',4)}[a['componentType']]
  return [struct.unpack_from('<'+code*dim,b,v.get('byteOffset',0)+a.get('byteOffset',0)+j*v.get('byteStride',dim*size)) for j in range(a['count'])]
 primitive=d['meshes'][0]['primitives'][0];colors=decode(primitive['attributes']['COLOR_0']);positions=decode(primitive['attributes']['POSITION']);a=d['accessors'][primitive['attributes']['COLOR_0']];maximum={5121:255,5123:65535,5126:1}[a['componentType']]
 expected={tuple(round(x,6) for x in (p[0],-p[2],p[1])):tuple(x/maximum for x in c) for p,c in zip(positions,colors)}
 bpy.ops.import_scene.gltf(filepath=str(path));meshes=[o.data for o in bpy.context.scene.objects if o.type=='MESH'];errors=[];records=[]
 for m in meshes:
  attr=m.color_attributes[0];missing=0
  for i,item in enumerate(attr.data):
   v=m.vertices[i if attr.domain=='POINT' else m.loops[i].vertex_index];key=tuple(round(x,6) for x in v.co);target=expected.get(key)
   if target is None:missing+=1;continue
   errors.extend(abs(item.color[j]-target[j]) for j in range(len(target)))
  records.append(dict(vertices=len(m.vertices),triangles=len(m.polygons),attribute_type=attr.data_type,domain=attr.domain,missing_positions=missing,shader_links=[(l.from_node.bl_idname,l.from_socket.name,l.to_node.bl_idname,l.to_socket.name) for mat in m.materials if mat and mat.node_tree for l in mat.node_tree.links]))
 assert errors and all(r['missing_positions']==0 for r in records)
 ia=d['accessors'][primitive['indices']];iv=d['bufferViews'][ia['bufferView']];code={5121:'B',5123:'H',5125:'I'}[ia['componentType']];indices=struct.unpack_from('<'+code*ia['count'],b,iv.get('byteOffset',0)+ia.get('byteOffset',0))
 def point(p):return tuple(round(x,6) for x in (p[0],-p[2],p[1]))
 expected_faces=sorted(tuple(sorted(point(positions[i]) for i in indices[j:j+3])) for j in range(0,len(indices),3) if len(set(indices[j:j+3]))==3)
 actual_faces=sorted(tuple(sorted(tuple(round(x,6) for x in m.vertices[i].co) for i in poly.vertices)) for m in meshes for poly in m.polygons)
 assert expected_faces==actual_faces, path.name+' changed nondegenerate geometry'
 out.append(dict(file=path.name,sha256=hashlib.sha256(raw).hexdigest(),max_linear_error=max(errors),mean_linear_error=sum(errors)/len(errors),nondegenerate_geometry_exact=True,nondegenerate_geometry_sha256=hashlib.sha256(json.dumps(expected_faces).encode()).hexdigest(),meshes=records))
print('COLOR_PROBE_JSON='+json.dumps(out))
