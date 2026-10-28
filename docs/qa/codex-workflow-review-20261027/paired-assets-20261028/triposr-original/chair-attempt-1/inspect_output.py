import sys,pathlib,json,hashlib,struct
import trimesh
from scene_assets import validate_glb
out=pathlib.Path(sys.argv[1]);src=out/"chair-resolution256-original.glb";raw=src.read_bytes();mesh=trimesh.load(src,force="mesh")
result={"original":{"path":str(src),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"vertices":len(mesh.vertices),"faces":len(mesh.faces),"visual_kind":mesh.visual.kind,"watertight":bool(mesh.is_watertight),"euler_number":int(mesh.euler_number),"component_count":len(mesh.split(only_watertight=False))}}
try:result["original"]["platform_validation"]=validate_glb(raw)
except ValueError as e:result["original"]["platform_validation_error"]=str(e)
(out/"platform-profile-inspection.json").write_text(json.dumps(result,indent=2));print(json.dumps(result))
