"""Offline byte measurement of general-chat preview bodies. No network, no Store, no keys."""
import json,sys
root=sys.argv[1];sys.path.insert(0,root)
import chat_general,chat_protocols,chat_models,agent_preferences
spec=chat_models.contract('anthropic-haiku-5-5')
def wire(x):return len(json.dumps(x,ensure_ascii=False,allow_nan=False).encode('utf-8'))
def body(names,history):
    defs=[d for d in chat_protocols.tool_definitions('anthropic') if d['name'] in names]
    for d in defs:d['strict']=True
    return chat_models.body(spec,history,defs,chat_general.MAX_OUTPUT,effort='low')
prompt='음원에 맞는 장면을 제안해 줘'
out={'module_root':root,'allowed_tools':list(chat_general.ALLOWED_TOOLS),'read_tools':sorted(agent_preferences.READ_TOOLS),'modes':{}}
for mode in ('review','full_access','read_only'):
    names=[n for n in chat_general.ALLOWED_TOOLS if mode!='read_only' or n in agent_preferences.READ_TOOLS]
    b=body(names,[dict(role='user',content=prompt)])
    out['modes'][mode]=dict(tool_names=[t['name'] for t in b['tools']],tools_bytes=wire(b['tools']),
        message_body_bytes=wire(b),count_body_bytes=wire({k:v for k,v in b.items() if k!='max_tokens'}),
        per_tool_bytes={t['name']:wire(t) for t in b['tools']},description_bytes=sum(len(t['description'].encode()) for t in b['tools']))
if len(sys.argv)>2:
    # Representative continuation: one get_generation_job round with a receipt shaped like tests/test_general_chat_job_query.py.
    job=dict(status='succeeded',job=dict(id='0'*32,state='imported',failure_code=None,mode='contract-fake',action_id='1'*32,plan_id='2'*32,plan_revision=1,release_id='fal-ai/flux/schnell',external_calls=1,result=dict(sha256='c'*64,output_slot='video'),result_approved=False,provider_completed=True,cost=dict(reservation_state='unknown',estimate={'amount':'0.01','currency':'USD'},actual=None,billing_confirmed=False,evidence=None),registered_takes=[]))
    est=dict(status='estimated',actions=[dict(action_id=str(i)*32,model='fal-ai/flux/schnell',role='image',money={'amount':'0.01','currency':'USD'},price_kind='fixture',expired=False) for i in range(3)],total={'amount':'0.03','currency':'USD'},billing_confirmed=False,approval=False,label='이 대화에서 준비된 작업(보류·거절 제외)의 견적 합계입니다. 계획 전체 견적이나 청구 금액이 아닙니다.')
    names=list(chat_general.ALLOWED_TOOLS)
    for label,name,result in (('get_generation_job',('get_generation_job',{'job_id':'0'*32}),job),('estimate_media_plan',('estimate_media_plan',{'plan_id':'2'*32}),est)):
        response=dict(content=[dict(type='tool_use',id='toolu_fixture',name=name[0],input=name[1])])
        tool=dict(role='user',content=[dict(type='tool_result',tool_use_id='toolu_fixture',content=json.dumps(result,ensure_ascii=False))])
        history=chat_models.continuation(spec,[dict(role='user',content=prompt)],response,[tool])
        b=body(names,history)
        out.setdefault('continuation',{})[label]=dict(tool_result_bytes=len(tool['content'][0]['content'].encode()),message_body_bytes=wire(b))
print(json.dumps(out,ensure_ascii=False))
