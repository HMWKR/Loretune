import sys,time,json,pathlib,hashlib
import torch
from PIL import Image
from omegaconf import OmegaConf
from tsr.system import TSR
out=pathlib.Path(sys.argv[1]);modeldir=pathlib.Path(sys.argv[2]);inp=pathlib.Path(sys.argv[3]);res=int(sys.argv[4])
torch.set_num_threads(2);torch.set_num_interop_threads(2);torch.manual_seed(0)
t=time.monotonic();cfg=OmegaConf.load(modeldir/"config.yaml");cfg.image_tokenizer.pretrained_model_name_or_path=str(modeldir/"dino-config.json")
OmegaConf.resolve(cfg)
model=TSR(cfg);state=torch.load(modeldir/"model.ckpt",map_location="cpu",weights_only=True)
assert isinstance(state,dict) and all(isinstance(k,str) and isinstance(v,torch.Tensor) for k,v in state.items())
model.load_state_dict(state);del state;model.eval();model.renderer.set_chunk_size(4096)
print("MODEL_LOADED",time.monotonic()-t,flush=True)
image=Image.open(inp).convert("RGB")
with torch.inference_mode():
 codes=model([image],device="cpu");print("SCENE_CODE",time.monotonic()-t,flush=True)
 mesh=model.extract_mesh(codes,has_vertex_color=True,resolution=res)[0]
assert len(mesh.vertices)>0 and len(mesh.faces)>0
path=out/f"chair-preprocessed-resolution{res}-original.glb";mesh.export(path)
result={"resolution":res,"default_quality":res==256,"vertices":len(mesh.vertices),"faces":len(mesh.faces),"bounds":mesh.bounds.tolist(),"watertight":bool(mesh.is_watertight),"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"seconds":time.monotonic()-t,"input_sha256":hashlib.sha256(inp.read_bytes()).hexdigest(),"background_pixel":image.getpixel((0,0)),"crop":"official resize_foreground0.85 in derived input","background_removal":"exact known synthetic RGB58 mask; not rembg","torch":torch.__version__,"threads":torch.get_num_threads(),"interop_threads":torch.get_num_interop_threads(),"chunk_size":4096,"device":"cpu"}
(out/f"result-{res}.json").write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
