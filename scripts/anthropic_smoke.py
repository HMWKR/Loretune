"""Approved synthetic-only single attempt; secrets remain in process memory."""
import sys,json,sqlite3,hashlib,os,stat,re,time
from pathlib import Path
from decimal import Decimal,ROUND_CEILING
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import anthropic_ontology as a

ROOT=Path(__file__).resolve().parents[1]
SOURCES={'brief-1':'Mira and Theo perform on a rooftop. Mira wears a blue coat.',
         'brief-2':'Mira wears a red coat in the studio. It is unknown whether this replaces the rooftop costume.'}

def credential(path):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 with os.fdopen(fd,'rb') as stream:
  info=os.fstat(stream.fileno())
  if not stat.S_ISREG(info.st_mode) or info.st_size>65536:raise ValueError('credential file format')
  raw=stream.read(65537)
 if len(raw)>65536:raise ValueError('credential file size')
 values=[]
 for line in raw.decode('utf-8').splitlines():
  line=line.strip()
  if line.startswith('export '):line=line[7:].strip()
  if '=' not in line:continue
  name,value=line.split('=',1)
  if name.strip()!='Anthropic_KEY':continue
  value=value.strip()
  if len(value)>1 and value[0]==value[-1] and value[0] in '\"\'':value=value[1:-1]
  if not re.fullmatch(r'[A-Za-z0-9_:.-]{8,512}',value):raise ValueError('credential literal format')
  values.append(value)
 if len(values)!=1:raise ValueError('credential entry unavailable')
 return values[0]

def reserve(db,identifier,digest,held=1434):
 db.execute('BEGIN IMMEDIATE')
 db.execute('CREATE TABLE IF NOT EXISTS trials (id TEXT PRIMARY KEY, input_hash TEXT, state TEXT, held_micro INTEGER, actual_micro INTEGER, metadata TEXT)')
 if db.execute('SELECT 1 FROM trials WHERE id=?',(identifier,)).fetchone():raise ValueError('attempt already recorded; no retry')
 total=db.execute('SELECT COALESCE(SUM(COALESCE(actual_micro,held_micro)),0) FROM trials').fetchone()[0]
 if total+held>50000000:raise ValueError('cumulative budget exhausted')
 if identifier.startswith('ontology-eval-'):
  stage=db.execute("SELECT count(*),COALESCE(SUM(held_micro),0) FROM trials WHERE id LIKE 'ontology-eval-%'").fetchone()
  if stage[0]>=3 or stage[1]+held>50000:raise ValueError('small evaluation stage limit')
 if identifier.startswith('claude-tools-'):
  stage=db.execute("SELECT count(*),COALESCE(SUM(held_micro),0) FROM trials WHERE id LIKE 'claude-tools-%'").fetchone()
  if stage[0]>=5 or stage[1]+held>50000:raise ValueError('tool evaluation stage limit')
 if identifier.startswith('claude-answer-v1-'):
  stage=db.execute("SELECT count(*),COALESCE(SUM(held_micro),0) FROM trials WHERE id LIKE 'claude-answer-v1-%'").fetchone()
  if stage[0]>=1 or stage[1]+held>2458:raise ValueError('answer completion stage limit')
 db.execute('INSERT INTO trials VALUES (?,?,?,?,?,?)',(identifier,digest,'reserved',held,None,'{}'));db.commit()

def run(folder,env_path,*,count_transport=None,message_transport=None,key_supplier=None,evaluation=None):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 if evaluation not in (None,'001','002','003'):raise ValueError('evaluation case unavailable')
 identifier='ontology-smoke-001' if evaluation is None else 'ontology-eval-'+evaluation
 body=a.request_body(SOURCES)
 if evaluation:body['max_tokens']=8192
 held=1434 if evaluation is None else 4506
 digest=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
 db=sqlite3.connect(folder/'usage.sqlite3')
 try:reserve(db,identifier,digest,held)
 except Exception:
  db.close();raise
 output=folder if evaluation is None else folder/identifier;output.mkdir(exist_ok=True)
 report=dict(model=a.MODEL,input_sha256=digest,maximum_input_tokens=4096,maximum_output_tokens=body['max_tokens'],
             reserved_usd=str(Decimal(held)/1000000),budget_usd='50',automatic_retries=0,billing_confirmed=False,state='reserved')
 def save(state):
  report['state']=state
  db.execute('UPDATE trials SET state=?,metadata=? WHERE id=?',(state,json.dumps(report),identifier));db.commit()
  (output/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 try:
  key=(key_supplier or credential)(env_path)
  headers={'x-api-key':key,'anthropic-version':'2023-06-01','content-type':'application/json'}
  save('count_started')
  counted=(count_transport or a.BoundedCountTransport())(a.BoundedCountTransport.endpoint,headers,{k:v for k,v in body.items() if k!='max_tokens'})
  tokens=counted.get('input_tokens')
  if type(tokens) is not int or not 0<=tokens<=4096:raise ValueError('input token limit')
  report['counted_input_tokens']=tokens
  (output/'request.json').write_text(json.dumps(body,ensure_ascii=False,indent=2))
  save('message_started')
  response=(message_transport or a.BoundedMessagesTransport(timeout=60))(a.ENDPOINT,headers,body)
  report.update(request_id=response.get('_request_id'),message_id=response.get('id'),stop_reason=response.get('stop_reason'))
  usage=response.get('usage',{})
  if any(type(usage.get(k)) is not int or usage[k]<0 for k in ['input_tokens','output_tokens']):raise ValueError('usage unavailable')
  report['usage']={k:usage[k] for k in ['input_tokens','output_tokens']}
  cost=Decimal(usage['input_tokens'])*Decimal('.1')/1000000+Decimal(usage['output_tokens'])*Decimal('.5')/1000000
  report['usage_cost_usd']=str(cost)
  db.execute('UPDATE trials SET actual_micro=? WHERE id=?',(int((cost*1000000).to_integral_value(rounding=ROUND_CEILING)),identifier));db.commit()
  text=''.join(x.get('text','') for x in response.get('content',[]) if x.get('type')=='text')
  report['output_sha256']=hashlib.sha256(text.encode()).hexdigest()
  if len(text.encode())<=100000 and key not in text:
   try:candidate=json.loads(text)
   except (ValueError,TypeError):candidate=None
   if isinstance(candidate,dict):(output/'unapproved-candidate.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2))
  save('response_received')
  graph=a.parse_response(response,SOURCES)
  if key in json.dumps(graph):raise ValueError('unexpected sensitive output')
  (output/'proposal.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2))
  report.update(schema_and_exact_spans_valid=True,approval_required=True,applied=False,entity_count=len(graph['entities']),relation_count=len(graph['relations']))
  save('validated')
 except Exception as exc:
  report['error_class']=type(exc).__name__
  if isinstance(exc,a.ProposalError):
   match=re.fullmatch(r'provider HTTP (\d{3}); no automatic retry',str(exc))
   if match:report['http_status']=int(match[1])
   if str(exc).startswith('ontology contract: ') or str(exc) in {'incomplete or refused proposal','unverified source span','conflicting claims require explicit uncertainty','invalid structured proposal'}:report['validation_error']=str(exc)
  # Never persist exception bodies, credentials, thinking blocks or opaque response.
  save('response_validation_failed' if report.get('state')=='response_received' else 'blocked_or_unknown')
 finally:
  key=None;headers=None;db.close()
 return report

if __name__=='__main__':
 if sys.argv[1:] not in [['--execute-approved'],['--execute-approved','--evaluation-001'],['--execute-approved','--evaluation-002']]:raise SystemExit('explicit approved execution flag required')
 print(json.dumps(run(ROOT/'docs/qa/anthropic-smoke-20261025',ROOT/'.env',evaluation=sys.argv[2][-3:] if len(sys.argv)>2 else None),ensure_ascii=False))
