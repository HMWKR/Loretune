import json,torch,socket
from torchmcubes import marching_cubes
torch.set_num_threads(2)
x=torch.linspace(-1,1,32);g=torch.meshgrid(x,x,x,indexing="ij");field=sum(v*v for v in g)
v,f=marching_cubes(field.contiguous(),0.5)
assert v.numel()>0 and f.numel()>0 and torch.isfinite(v).all()
try:
 socket.create_connection(("1.1.1.1",443),timeout=2)
 raise AssertionError("Network unexpectedly allowed")
except PermissionError as e:
 denied=str(e)
print(json.dumps({"torch":torch.__version__,"vertices":len(v),"faces":len(f),"device":str(v.device),"network_denied":denied}))
