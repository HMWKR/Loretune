import bpy,json
w=bpy.context.scene.world
out=dict(blender=bpy.app.version_string,use_nodes=w.use_nodes,color=list(w.color),view_transform=bpy.context.scene.view_settings.view_transform,look=bpy.context.scene.view_settings.look,exposure=bpy.context.scene.view_settings.exposure,gamma=bpy.context.scene.view_settings.gamma,nodes=[dict(name=n.name,type=n.bl_idname,inputs={s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value')}) for n in w.node_tree.nodes],links=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in w.node_tree.links])
print('WORLD_PROBE_JSON='+json.dumps(out))
