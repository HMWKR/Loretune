"""Read-only product audit; synthetic tool requests use a new isolated store."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,sys,tempfile,threading,time,uuid
from urllib.request import Request,urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import app,backup,chat_protocols,chat_general,contracts,ledger
OUT=Path(__file__).parent
previous=json.loads((OUT.parent/'backend/http-media-verification.json').read_text())
folder=Path(tempfile.mkdtemp(prefix='loretune-ai-overlay-contract-'))
backup.restore(previous['backup_and_restore']['backup'],folder/'store')
fixture=[dict(stop_reason='tool_use',content=[dict(type='tool_use',id='synthetic-search',name='search_project_context',input={'query':'현재 편집과 타이포 겹치기 원본'})],usage={'input_tokens':100,'output_tokens':30})]
http=app.server(folder/'store',0,general_chat_fixture=fixture)
thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
origin=f'http://127.0.0.1:{http.server_port}'
trace=[]

def state():
    with urlopen(origin+'/api/state') as r:return json.load(r)

def action(action_name,**payload):
    current=state();payload.setdefault('song','actual overlay')
    body=dict(action=action_name,data=payload,revision=current['revision'],request_id=uuid.uuid4().hex)
    request=Request(origin+'/api/action',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':current['token']})
    try:
        with urlopen(request) as response:code=response.status;result=json.load(response)
    except HTTPError as error:
        with error:code=error.code;result=json.load(error)
    trace.append(dict(action=action_name,request_id=body['request_id'],revision=body['revision'],http_status=code,result=result))
    assert code==200,(action_name,code,result)
    return result

def project():return state()['projects']['actual overlay']

def tool(run,name,args):
    call=dict(id=uuid.uuid4().hex,name=name,arguments=args,complete=True)
    return action('production_tool',run=run,call=call)['tool']

try:
    action('model_settings',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
    pid=contracts.project_id(http.store.workspace_id,'actual overlay')
    with http.store.connect() as c:
        ledger.patch_budget(c,http.store.workspace_id,'rehearsal:project:'+pid,
                            dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
    preview=action('general_chat_preview',prompt='합성 감사: 현재 타이포 겹치기 원본·위치·시간을 조회해 줘',maximum_micro=10000)['general_chat_preview']
    action('general_chat_decide',preview_id=preview['id'],manifest_sha256=preview['manifest_sha256'],decision='approve',rights_confirmed=True)
    assert http.store.general_chat_runtime.process_next()
    p=project();turn=p['general_chat_turns'][-1]
    assert turn['status']=='awaiting_continuation_approval',turn
    follow=p['general_chat_previews'][-1]
    result_blocks=[b for m in follow['message_body']['messages'] if m.get('role')=='user' and isinstance(m.get('content'),list)
                   for b in m['content'] if b.get('type')=='tool_result']
    assert len(result_blocks)==1
    lookup=json.loads(result_blocks[0]['content']);targets=lookup['execution_targets']
    raw_overlay=p['timeline_versions'][-1]['clips'][0]['motion_overlay']
    assert raw_overlay and all('motion_overlay' not in x for x in targets['timeline']['clips'])
    schema=next(x['input_schema'] for x in preview['message_body']['tools'] if x['name']=='propose_timeline_changes')
    operations=[x['properties']['op']['enum'][0] for x in schema['properties']['commands']['items']['anyOf']]
    assert 'set_motion_overlay' not in operations
    action('general_chat_decide',preview_id=follow['id'],manifest_sha256=follow['manifest_sha256'],decision='reject',rights_confirmed=True)
    run=action('production_run')['run']['id']
    args=dict(description='synthetic unsupported overlay edit',timeline_version=p['timeline_head'],commands=[dict(op='set_motion_overlay',clip_index=0,motion_overlay=raw_overlay)])
    first=tool(run,'propose_timeline_changes',args)
    assert first['status']=='invalid_arguments',first
    args['commands']=[dict(op='set_clip',clip_index=0,take=2,trim=0,duration=1.5,motion_overlay=raw_overlay)]
    second=tool(run,'propose_timeline_changes',args)
    assert second['status']=='invalid_arguments',second
    run=action('production_run')['run']['id']
    before=deepcopy(project()['timeline_versions'])
    supported=dict(description='synthetic existing trim change preserves overlay',timeline_version=p['timeline_head'],
                   commands=[dict(op='set_clip',clip_index=0,take=2,trim=.125,duration=1.5)])
    accepted=tool(run,'propose_timeline_changes',supported)
    assert accepted['status']=='proposed' and accepted['applied'] is False,accepted
    assert project()['timeline_versions']==before
    review=action('review_timeline_proposal',proposal_id=accepted['proposal_id'],timeline_version=p['timeline_head'],decision='approved')['timeline_proposal']
    after=project();assert review['applied'] and review['output_approved'] is False
    assert after['timeline_versions'][-1]['clips'][0]['motion_overlay']==raw_overlay
    assert 'approval' not in after['timeline_versions'][-1]
    run=action('production_run')['run']['id']
    shorter=dict(description='synthetic shorter clip conflicts with hidden overlay window',timeline_version=after['timeline_head'],
                 commands=[dict(op='set_clip',clip_index=0,take=2,trim=.125,duration=.75)])
    blocked=tool(run,'propose_timeline_changes',shorter)
    assert blocked['status']=='blocked',blocked
    runtime=http.store.general_chat_runtime.transport
    report=dict(recorded_at=datetime.now(timezone.utc).isoformat(),origin=origin,folder=str(folder),
                actual_provider_calls=0,actual_model_calls=0,actual_credential_reads=0,
                transport='explicit general_chat FixtureTransport; no external network provider',
                selected_model=project()['model_settings']['selections']['chat'],
                request_model=preview['message_body']['model'],manifest_sha256=preview['manifest_sha256'],
                manifest_bound_tools=[x['name'] for x in preview['message_body']['tools']],
                actual_fixture_message_count=len(runtime.messages),
                canonical_overlay=raw_overlay,lookup_targets=targets,wire_edit_schema=schema,wire_operations=operations,
                unsupported_set_overlay=first,unsupported_overlay_inside_set_clip=second,
                existing_trim_proposal=accepted,existing_trim_human_review=review,
                applied_overlay_preserved=after['timeline_versions'][-1]['clips'][0]['motion_overlay'],
                shorter_clip_blocked=blocked,trace=trace,
                synthetic_fixture_usage_not_real_billing=True,
                conclusion='Human UI overlay is implemented but AI lookup and edit command contracts do not disclose or edit it. Existing valid edits preserve the stored overlay; clipping its hidden window is blocked.',
                limits=['Not real selected-model understanding/quality/account/billing validation','No product/test/source changes','No root browser Space access'])
    (OUT/'probe-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='GAP_CONFIRMED',selected_model=report['selected_model'],request_model=report['request_model'],
                         lookup_omits_overlay=True,wire_operations=operations,unsupported=[first,second],supported_edit_preserves_overlay=True,
                         actual_provider_calls=0,events=len(trace)),ensure_ascii=False))
finally:
    http.shutdown();http.server_close();thread.join()
