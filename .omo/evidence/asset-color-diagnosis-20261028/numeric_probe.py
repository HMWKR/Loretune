import pathlib,json,hashlib,struct,numpy as np
from PIL import Image
from trimesh.visual.color import to_rgba
out=pathlib.Path(__file__).resolve().parent;ev=out.parent
files=[ev/"triposr-cpu-artifact-20261028/chair-attempt-1/chair-resolution256-original.glb",ev/"triposr-cpu-artifact-20261028/cube-resolution256-original.glb"]
records=[]
for p in files:
 raw=p.read_bytes();n=struct.unpack_from("<I",raw,12)[0];d=json.loads(raw[20:20+n]);offset=28+n;binary=raw[offset:];a=d["accessors"][d["meshes"][0]["primitives"][0]["attributes"]["COLOR_0"]];v=d["bufferViews"][a["bufferView"]];assert a["componentType"]==5121 and a["type"]=="VEC4" and a["normalized"] is True
 start=v.get("byteOffset",0)+a.get("byteOffset",0);colors=np.frombuffer(binary,dtype=np.uint8,count=a["count"]*4,offset=start).reshape(-1,4);norm=colors/255.
 records.append({"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"accessor":a,"color_sha256":hashlib.sha256(colors.tobytes()).hexdigest(),"rgba_min":colors.min(0).tolist(),"rgba_max":colors.max(0).tolist(),"rgba_mean":colors.mean(0).tolist(),"rgba_quantiles":np.quantile(colors,[.1,.5,.9],axis=0).tolist(),"normalized_rgb_mean":norm[:,:3].mean(0).tolist(),"materials_present":"materials" in d,"primitive_material":d["meshes"][0]["primitives"][0].get("material"),"note":"vertex-weighted distribution, not pixel/area weighted and no image correspondence"})
images=[]
for rel in ["paired-3d-benchmark-inputs-20261028/case-2-chair.png","paired-assets-platform-20261028/ui/default-chair.png","paired-assets-platform-20261028/ui/edited-chair.png"]:
 p=ev/rel;im=Image.open(p);arr=np.array(im.convert("RGB"));images.append({"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"size":list(im.size),"metadata_keys":list(im.info),"all_pixel_mean":arr.mean((0,1)).tolist(),"center_pixel":arr[arr.shape[0]//2,arr.shape[1]//2].tolist(),"note":"descriptive only; different framing/lighting, includes background; no perceptual quality score"})
probe=np.array([[0.1,0.5,0.9]],dtype=np.float32);answer=to_rgba(probe.copy());assert answer.tolist()==[[26,128,230,255]]
report={"glbs":records,"pngs":images,"export_numeric_probe":{"input_float32":probe.tolist(),"to_rgba_uint8":answer.tolist(),"observed":"multiply255/round/uint8/opaque alpha; no transfer function in conversion"},"inference":False,"render":False,"source_modifications":False};(out/"numeric-results.json").write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
