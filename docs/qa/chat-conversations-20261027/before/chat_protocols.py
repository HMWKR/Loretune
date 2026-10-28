"""Offline protocol codecs only. No clients, keys, HTTP, or automatic tool execution."""
import json,uuid
from copy import deepcopy
import production_tools
import model_selection
PROVIDERS={'anthropic','openai','xai'}


def object_pairs(pairs):
 result={}
 for k,v in pairs:
  if k in result:raise ValueError('중복 JSON 키')
  result[k]=v
 return result


def normalize(provider,response,run_id):
 if provider not in PROVIDERS or not isinstance(response,dict):raise ValueError('지원하지 않는 protocol')
 if len(json.dumps(response))>100_000:raise ValueError('응답 크기 초과')
 if provider=='anthropic':
  if response.get('stop_reason') not in {'tool_use','end_turn'}:raise ValueError('미완료 또는 거부 응답')
  blocks=response.get('content',[]);kind='tool_use'
 else:
  if response.get('status')!='completed':raise ValueError('미완료 또는 거부 응답')
  blocks=response.get('output',[]);kind='function_call'
 if not isinstance(blocks,list) or len(blocks)>32 or any(not isinstance(b,dict) for b in blocks):raise ValueError('응답 블록 오류')
 if any('content' in b and not isinstance(b['content'],list) for b in blocks):raise ValueError('응답 content 형식 오류')
 if any(b.get('type')=='refusal' or any(x.get('type')=='refusal' for x in b.get('content',[]) if isinstance(x,dict)) for b in blocks):raise ValueError('거부 응답')
 calls=[];bindings={}
 for b in blocks:
  if b.get('type')!=kind:
   if b.get('type') not in {'text','message','thinking','redacted_thinking','reasoning'}:raise ValueError('지원하지 않는 내장 도구/멀티모달 출력')
   continue
  external=b.get('id') if provider=='anthropic' else b.get('call_id')
  if not isinstance(external,str) or not 1<=len(external)<=256 or external in bindings:raise ValueError('도구 호출 ID 오류')
  args=b.get('input') if provider=='anthropic' else json.loads(b['arguments'],object_pairs_hook=object_pairs)
  production_tools.validate(b.get('name'),args)
  identifier=uuid.uuid5(uuid.NAMESPACE_URL,provider+':'+run_id+':'+external).hex
  calls.append(dict(id=identifier,name=b['name'],arguments=deepcopy(args),complete=True))
  bindings[external]=dict(internal=identifier,provider=provider,run=run_id)
 if provider=='anthropic' and bool(calls)!=(response['stop_reason']=='tool_use'):raise ValueError('도구 종료 상태 불일치')
 return dict(calls=calls,bindings=bindings,provider=provider,run=run_id)


def result_message(normalized,call_id,result,*,provider,run_id):
 if normalized['provider']!=provider or normalized['run']!=run_id:raise ValueError('다른 제공자/실행에 도구 결과를 인계할 수 없습니다.')
 binding=next((k for k,v in normalized['bindings'].items() if v['internal']==call_id),None)
 if binding is None:raise ValueError('원본 도구 호출이 없습니다.')
 text=json.dumps(result,ensure_ascii=False)
 if len(text)>100_000:raise ValueError('도구 결과 크기 초과')
 if provider=='anthropic':return dict(role='user',content=[dict(type='tool_result',tool_use_id=binding,content=text)])
 return dict(type='function_call_output',call_id=binding,output=text)


def handoff(project,project_name,jobs,execution_targets=None):
 """Fresh provider conversation, never provider pending IDs/reasoning blobs."""
 messages=[dict(role=m['role'],text=m['text']) for m in project.get('conversation',[]) if m.get('role') in {'user','assistant','system'} and isinstance(m.get('text'),str)]
 states=[dict(id=j['id'],state=j['state'],mode=j.get('mode','provider-unverified')) for j in jobs if j.get('context',{}).get('song')==project_name]
 return dict(context=model_selection.snapshot(project),messages=deepcopy(messages),jobs=states,execution_targets=deepcopy(execution_targets),
             instructions='서버 상태만 작업 결과로 설명하세요. 미수집 결과를 완료로 설명하지 마세요.',embedding_policy='unchanged')


def tool_definitions(provider):
 if provider not in PROVIDERS:raise ValueError('지원하지 않는 protocol')
 definitions=[]
 for name,fields in production_tools.TOOLS.items():
  schema=dict(type='object',properties={key:dict(type='integer' if value is int else 'string') for key,value in fields.items()},required=list(fields),additionalProperties=False)
  if name=='propose_timeline_edit':
   import local_creation_tools
   schema['properties']['changes']=deepcopy(local_creation_tools.CHANGE_SCHEMA)
  if name=='propose_motion_scene':schema['properties']['scene']=deepcopy(__import__('motion_scene').SCHEMA)
  if name=='propose_timeline_changes':schema['properties']['commands']=deepcopy(__import__('local_creation_tools').COMMAND_SCHEMA)
  if provider=='anthropic':definitions.append(dict(name=name,description='Loretune server-controlled '+name,input_schema=schema))
  else:definitions.append(dict(type='function',name=name,description='Loretune server-controlled '+name,parameters=schema,strict=True))
 return definitions
