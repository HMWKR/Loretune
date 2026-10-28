"""A2b offline byte measurement: scene schema options and worst-case scene-status continuation. No network/keys."""
import json,sys
root=sys.argv[1];sys.path.insert(0,root)
import chat_general,chat_protocols,chat_models,scene_spec
from copy import deepcopy
spec=chat_models.contract('anthropic-haiku-5-5')
def wire(x):return len(json.dumps(x,ensure_ascii=False,allow_nan=False).encode('utf-8'))
defs={d['name']:d for d in chat_protocols.tool_definitions('anthropic')}
full=defs['propose_scene_3d']
# Smaller per-target alternative (C1 measurement shape): 3 branches, value anyOf; field<->value binding left to the validator.
value=dict(anyOf=[dict(type='number'),dict(type='array',minItems=3,maxItems=3,items=dict(type='number')),scene_spec._value_schema('asset')])
alt=deepcopy(full);alt['input_schema']['properties']['operations']['items']=dict(anyOf=[dict(type='object',properties=dict(target=dict(type='string',enum=[k]),id=dict(type='string',enum=['camera']) if k=='camera' else dict(type='string',minLength=1,maxLength=32),field=dict(type='string',enum=list(f)),value=value),required=['target','id','field','value'],additionalProperties=False) for k,f in scene_spec.CHANGE_FIELDS.items()])
def body(names,history,override=None):
    ds=[deepcopy(override) if override and d['name']==override['name'] else deepcopy(d) for d in chat_protocols.tool_definitions('anthropic') if d['name'] in names]
    for d in ds:d['strict']=True
    return chat_models.body(spec,history,ds,chat_general.MAX_OUTPUT,effort='low')
prompt='음원에 맞는 장면을 제안해 줘'
names=list(chat_general.ALLOWED_TOOLS)
first=body(names,[dict(role='user',content=prompt)]);first_alt=body(names,[dict(role='user',content=prompt)],alt)
out=dict(propose_scene_3d_full_bytes=wire(full),propose_scene_3d_per_target_bytes=wire(alt),propose_preference_rule_bytes=wire(defs['propose_preference_rule']),
         review_first_body_bytes_full=wire(first),review_first_body_bytes_per_target=wire(first_alt),tools_bytes_full=wire(first['tools']))
if len(sys.argv)>2:
    status=json.load(open(sys.argv[2]))  # measured worst-case scene-status (32 scenes x 10 pending) is not stored; rebuild size-equivalent payload
size=None
for label,override in (('full',None),('per_target',alt)):
    # Worst-case scene-status continuation: replace a 39515-byte result (measured) with an equal-size string payload.
    result=json.dumps(dict(scene_status=dict(pad='x'*(39515-27))),ensure_ascii=False)
    response=dict(content=[dict(type='tool_use',id='toolu_fixture',name='search_project_context',input={'query':'scene-status'})])
    tool=dict(role='user',content=[dict(type='tool_result',tool_use_id='toolu_fixture',content=result)])
    history=chat_models.continuation(spec,[dict(role='user',content=prompt)],response,[tool])
    b=body(names,history,override)
    out['worst_scene_status_continuation_body_bytes_'+label]=wire(b)
    out['worst_scene_status_tool_result_bytes']=len(result.encode())
out['transport_max_request_bytes']=65536;out['max_input_tokens']=chat_general.MAX_INPUT
print(json.dumps(out,ensure_ascii=False,indent=1))
