"""Authorized single count diagnostic; cannot send Messages or retry."""
import sys,json,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import chat_runtime,anthropic_ontology as a
from scripts.anthropic_smoke import credential
OUT=Path(__file__).resolve().parent
p=ROOT/'docs/qa/native-motion-20261026/live/case-1'
files=list(p.glob('request-*.json'));assert len(files)==1
saved=json.loads(files[0].read_text());body=saved['public_request']
digest=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest();assert digest==saved['input_hash']
assert body['model']=='claude-haiku-5-5'
with (OUT/'attempt.json').open('x') as f:json.dump(dict(at=time.time(),input_sha256=digest,count_only=True,messages=0,retries=0),f)
adapter=chat_runtime.AnthropicChatAdapter(lambda name:credential(ROOT/'.env') if name=='Anthropic_KEY' else None,enabled=True)
result=dict(input_sha256=digest,messages=0,count_invocations=0,retries=0)
try:
 adapter.preflight(body);result['count_invocations']=1
 count=adapter.count(body);result.update(status='count_succeeded',input_tokens=count)
except a.ProposalError as e:result.update(status='count_failed',failure=dict(stage='count',**a.safe_failure(**e.failure)))
except Exception:result.update(status='local_preparation_failed',failure={'stage':'preflight','category':'unavailable'})
(OUT/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
