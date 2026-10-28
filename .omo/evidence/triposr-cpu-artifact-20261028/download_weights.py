import pathlib,sys,urllib.request,hashlib,json,time,shutil
out=pathlib.Path(sys.argv[1]);root=pathlib.Path(sys.argv[2]);dest=root/"model";dest.mkdir(exist_ok=True)
url="https://huggingface.co/stabilityai/TripoSR/resolve/5b521936b01fbe1890f6f9baed0254ab6351c04a/model.ckpt"
started=time.monotonic();h=hashlib.sha256();total=0
with urllib.request.urlopen(url,timeout=60) as response,(dest/"model.ckpt.partial").open("wb") as f:
 while True:
  chunk=response.read(8*1024*1024)
  if not chunk:break
  f.write(chunk);h.update(chunk);total+=len(chunk)
  print(total,flush=True)
  if total>1_800_000_000 or time.monotonic()-started>600:raise RuntimeError("download budget exceeded")
assert total==1677246742,total
(dest/"model.ckpt.partial").rename(dest/"model.ckpt")
shutil.copyfile(out/"stabilityai-TripoSR-config.yaml",dest/"config.yaml")
shutil.copyfile(out/"facebook-dino-vitb16-config.json",dest/"dino-config.json")
(out/"weight-provenance.json").write_text(json.dumps({"url":url,"sha256":h.hexdigest(),"bytes":total,"seconds":time.monotonic()-started,"path":str(dest/"model.ckpt"),"auth":"none; urllib public GET"},indent=2))
