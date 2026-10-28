import pathlib,json,sys,hashlib,subprocess
out=pathlib.Path(__file__).resolve().parent;root=pathlib.Path(json.loads((out/"preflight.json").read_text())["temp_root"])
weight=root/"model/model.ckpt";sha=hashlib.file_digest(weight.open("rb"),"sha256").hexdigest();expected=next(i["lfs"]["oid"] for i in json.loads((out/"hf-tree.json").read_text()) if i.get("path")=="model.ckpt")
assert sha==expected,(sha,expected)
(out/"weight-integrity.json").write_text(json.dumps({"actual":sha,"expected":expected,"matched":True},indent=2))
env={"PATH":str(root/"venv/bin")+":/usr/bin:/bin","TMPDIR":str(root)}
cmd=[str(root/"venv/bin/python"),str(out/"watchdog.py"),str(out),str(root),str(out.parent/"paired-3d-benchmark-inputs-20261028/case-1-cube.png"),"256"]
print("LAUNCH",cmd,flush=True)
sys.exit(subprocess.call(cmd,env=env))
