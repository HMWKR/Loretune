import os,sys,json,time,pathlib,subprocess,signal
import psutil
out=pathlib.Path(sys.argv[1]).resolve();root=pathlib.Path(sys.argv[2]);inp=pathlib.Path(sys.argv[3]).resolve();res=int(sys.argv[4]);limit=8*1024**3
# Deliberate credential-free environment. Network is denied by OS profile, not just offline flags.
env={"PATH":str(root/"venv/bin")+":/usr/bin:/bin","TMPDIR":str(root),"PYTHONPATH":str(root/"TripoSR"),"HF_HOME":str(root/"hf-cache"),"HF_HUB_DISABLE_IMPLICIT_TOKEN":"1","HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1","OMP_NUM_THREADS":"2","MKL_NUM_THREADS":"2","TOKENIZERS_PARALLELISM":"false"}
cmd=["/usr/bin/sandbox-exec","-f",str(out/"network-deny.sb"),str(root/"venv/bin/python"),str(out/"infer.py"),str(out),str(root/"model"),str(inp),str(res)]
started=time.monotonic();peak=0;reason=None;count=0
with (out/f"inference-{res}.log").open("w") as log,(out/f"resources-{res}.jsonl").open("w") as samples:
 p=subprocess.Popen(cmd,env=env,stdout=log,stderr=log,start_new_session=True);print("PID",p.pid,flush=True)
 while p.poll() is None:
  try:proc=psutil.Process(p.pid);rss=sum(q.memory_info().rss for q in [proc]+proc.children(recursive=True) if q.is_running())
  except psutil.Error:rss=0
  peak=max(peak,rss);elapsed=time.monotonic()-started;available=psutil.virtual_memory().available
  sample={"seconds":elapsed,"rss_bytes":rss,"host_available_bytes":available};samples.write(json.dumps(sample)+"\n");samples.flush()
  if rss>limit:reason="RSS budget 8GiB exceeded"
  if available<2*1024**3:reason="host available memory below2GiB"
  if elapsed>1200:reason="inference20minute bound"
  if count%30==0:
   disk=sum(f.stat().st_size for f in root.rglob("*") if f.is_file() and not f.is_symlink())
   if disk>12*1024**3:reason="experiment disk12GiB bound"
  if reason:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=10);break
  count+=1;time.sleep(2)
 result={"invocation":cmd,"exit_code":p.wait(),"seconds":time.monotonic()-started,"peak_tree_rss_bytes":peak,"termination_reason":reason,"limits":{"rss_bytes":limit,"seconds":1200,"disk_bytes":12*1024**3},"network":"OS sandbox deny network; tested separately","environment_keys":sorted(env)}
(out/f"execution-{res}.json").write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
sys.exit(0 if result["exit_code"]==0 else 1)
