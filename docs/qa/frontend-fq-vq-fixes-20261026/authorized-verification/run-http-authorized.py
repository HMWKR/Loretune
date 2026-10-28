"""One authorized retry of the exact previously blocked tests; loopback only."""
import json,unittest,sys,socket,socketserver,time,os
from pathlib import Path
from unittest.mock import patch
out=Path(__file__).resolve().parent;root=out.parents[3];sys.path.insert(0,str(root))
ids=set(json.loads((out.parent/'blocked-http-tests.json').read_text()))
def flatten(suite):
 for case in suite:
  if isinstance(case,unittest.TestSuite):yield from flatten(case)
  else:yield case
suite=unittest.defaultTestLoader.discover(str(root/'tests'));cases=[c for c in flatten(suite) if c.id() in ids]
assert len(cases)==20
servers=[];connections=[];bind=socketserver.TCPServer.server_bind;connect=socket.socket.connect

def tracked_bind(server):
 assert server.server_address[0]=='127.0.0.1' and server.server_address[1]==0, 'only ephemeral IPv4 loopback listeners authorized'
 bind(server);servers.append((server,server.socket.getsockname()))
def local_connect(sock,address):
 if isinstance(address,tuple):
  assert address[0] in ('127.0.0.1','::1'), 'external socket denied by QA'
  connections.append({'host':address[0],'port':address[1]})
 return connect(sock,address)
start=time.time();result=None
try:
 with patch.object(socketserver.TCPServer,'server_bind',tracked_bind),patch.object(socket.socket,'connect',local_connect):
  result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(cases))
finally:
 before=[{'host':a[0],'port':a[1],'closed_by_test':s.socket.fileno()==-1}for s,a in servers]
 for s,a in servers:s.server_close()
 closed=all(s.socket.fileno()==-1 for s,a in servers)
 record={'pid':os.getpid(),'tests_requested':len(cases),'tests_run':result.testsRun if result else 0,'successful':result.wasSuccessful() if result else False,'failures':len(result.failures) if result else None,'errors':len(result.errors) if result else None,'seconds':time.time()-start,'listeners':before,'all_listener_sockets_closed':closed,'loopback_connections':len(connections),'external_connections':0,'synthetic_credentials_only':True}
 (out/'http-result.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
sys.exit(not(result and result.wasSuccessful() and closed))
