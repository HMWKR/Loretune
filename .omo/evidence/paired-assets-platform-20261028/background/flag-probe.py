import bpy,json
w=bpy.context.scene.world;before=w.use_nodes;w.use_nodes=False
print('FLAG_PROBE_JSON='+json.dumps(dict(before=before,after_setting_false=w.use_nodes,background_node=list(w.node_tree.nodes['Background'].inputs['Color'].default_value),blender=bpy.app.version_string)))
