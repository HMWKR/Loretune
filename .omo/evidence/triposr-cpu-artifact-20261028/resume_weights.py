import pathlib,json,urllib.request,hashlib,shutil,time
out=pathlib.Path(__file__).resolve().parent;root=pathlib.Path(json.loads((out/"preflight.json").read_text())["temp_root"]);dest=root/"model";partial=dest/"model.ckpt.partial";offset=partial.stat().st_size;head=json.loads((out/"resume-head.json").read_text());etag=next(v for k,v in head["headers"].items() if k.lower()=="etag")
url="https://huggingface.co/stabilityai/TripoSR/resolve/5b521936b01fbe1890f6f9baed0254ab6351c04a/model.ckpt"
req=urllib.request.Request(url,headers={"Range":f"bytes={offset}-","If-Range":etag});started=time.monotonic()
with urllib.request.urlopen(req,timeout=60) as resp:
 record={"offset":offset,"status":resp.status,"content_range":resp.headers.get("Content-Range"),"etag":resp.headers.get("ETag")};(out/"resume-response.json").write_text(json.dumps(record,indent=2))
 assert resp.status==206 and resp.headers.get("Content-Range")==f"bytes {offset}-1677246741/1677246742",record
 assert resp.headers.get("ETag")==etag,record
 with partial.open("ab") as f:
  while True:
   chunk=resp.read(8*1024*1024)
   if not chunk:break
   f.write(chunk);print(f.tell(),flush=True)
   if f.tell()>1677246742 or time.monotonic()-started>300:raise RuntimeError("resume bound exceeded")
assert partial.stat().st_size==1677246742
sha=hashlib.file_digest(partial.open("rb"),"sha256").hexdigest();assert sha=="429e2c6b22a0923967459de24d67f05962b235f79cde6b032aa7ed2ffcd970ee"
partial.rename(dest/"model.ckpt");shutil.copyfile(out/"stabilityai-TripoSR-config.yaml",dest/"config.yaml");shutil.copyfile(out/"facebook-dino-vitb16-config.json",dest/"dino-config.json")
(out/"weight-provenance.json").write_text(json.dumps({"url":url,"sha256":sha,"bytes":1677246742,"resumed_from":offset,"resume_seconds":time.monotonic()-started,"auth":"none; public urllib GET with Range/If-Range","path":str(dest/"model.ckpt")},indent=2))
