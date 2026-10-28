"""Actual HTTP agent draft, frozen settings, explicit continuation and real render."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,subprocess,sys,tempfile,threading,uuid
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import app,backup,contracts,ledger
from tests.test_chat_runtime import response,use
OUT=Path(__file__).parent
previous=json.loads((OUT.parents[1]/'backend/http-media-verification.json').read_text())
folder=Path(tempfile.mkdtemp(prefix='loretune-agent-settings-'))
backup.restore(previous['backup_and_restore']['backup'],folder/'store')
http=app.server(folder/'store',0,general_chat_fixture=[])
thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
origin=f'http://127.0.0.1:{http.server_port}';trace=[];manifests=[]

def get(path):
    with urlopen(origin+path,timeout=45) as r:return r.read()

def state():return json.loads(get('/api/state'))
def project():return state()['projects']['actual overlay']

def action(action_name,**payload):
    current=state();payload.setdefault('song','actual overlay')
    body=dict(action=action_name,data=payload,revision=current['revision'],request_id=uuid.uuid4().hex)
    request=Request(origin+'/api/action',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':current['token']})
    try:
        with urlopen(request,timeout=45) as r:code=r.status;result=json.load(r)
    except HTTPError as error:
        with error:code=error.code;result=json.load(error)
    trace.append(dict(action=action_name,request_id=body['request_id'],revision=body['revision'],http_status=code,result=result))
    assert code==200,(action_name,code,result)
    return result

def tool(name,args,keep_follow=False):
    http.store.general_chat_runtime.transport.responses=[response([use('synthetic-call',name,args)],'tool_use')]
    preview=action('general_chat_preview',prompt='합성 계약 검증: '+name,maximum_micro=10000)['general_chat_preview']
    manifests.append(preview)
    action('general_chat_decide',preview_id=preview['id'],manifest_sha256=preview['manifest_sha256'],decision='approve',rights_confirmed=True)
    assert http.store.general_chat_runtime.process_next()
    p=project();turn=p['general_chat_turns'][-1];assert turn['status']=='awaiting_continuation_approval',turn
    follow=p['general_chat_previews'][-1]
    blocks=[b for m in follow['message_body']['messages'] if isinstance(m.get('content'),list)
            for b in m['content'] if b.get('type')=='tool_result']
    value=json.loads(blocks[-1]['content'])
    if keep_follow:return value,preview,follow
    action('general_chat_decide',preview_id=follow['id'],manifest_sha256=follow['manifest_sha256'],decision='reject',rights_confirmed=True)
    return value

try:
    action('model_settings',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
    pid=contracts.project_id(http.store.workspace_id,'actual overlay')
    with http.store.connect() as db:
        ledger.patch_budget(db,http.store.workspace_id,'rehearsal:project:'+pid,
                            dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
    saved=action('conversation_agent_settings',selection='anthropic-haiku-5-5',settings_revision=0,mode='full_access',effort='high')['agent_settings']
    assert saved['mode']=='full_access' and saved['effort']=='high'
    lookup=tool('search_project_context',dict(query='current overlay and approved immutable sources'))
    targets=lookup['execution_targets'];source=targets['motion_overlay_sources']['items'][0]
    assert 'motion_overlay' in targets['timeline']['clips'][0]
    assert 'scene' not in source and 'grant_id' not in source
    before=deepcopy(project()['timeline_versions'])
    (OUT/'before-settings-frame.png').write_bytes(get('/api/timeline-frame?'+urlencode(dict(song='actual overlay',timeline_revision=2,clip_index=0,frame=18))))
    command=dict(op='set_motion_overlay',clip_index=0,source_shot_id=source['source_shot_id'],
                 motion_revision=source['motion_revision'],start=.25,end=1.25,offset_x=640,offset_y=-120)
    proposed,preview,follow=tool('propose_timeline_changes',dict(description='합성 모델: FullAccess로 타이포 위치·시간과 자막을 미승인 초안에 반영',
        timeline_version=targets['timeline']['version'],commands=[command,dict(op='set_captions',cues=[dict(start=0,end=2.5,text='승인 전 AI 초안 · 내부 편집 검증')])]),keep_follow=True)
    assert proposed['status']=='applied_draft' and proposed['agent_draft_created']
    assert proposed['application_actor']=='agent-draft' and proposed['output_approved'] is False
    assert len(http.store.general_chat_runtime.transport.messages)==2
    turn=project()['general_chat_turns'][-1];assert turn['status']=='awaiting_continuation_approval' and turn['error'] is None
    assert not http.store.general_chat_runtime.process_next()
    action('conversation_agent_settings',selection='anthropic-haiku-5-5',settings_revision=1,mode='full_access',effort='medium')
    active=project()['agent_preferences'];assert active['active_response']['effort']=='high' and active['next_request']['effort']=='medium'
    http.store.general_chat_runtime.transport.responses=[response()]
    action('general_chat_decide',preview_id=follow['id'],manifest_sha256=follow['manifest_sha256'],decision='approve',rights_confirmed=True)
    assert http.store.general_chat_runtime.process_next()
    assert http.store.general_chat_runtime.transport.messages[-1]['output_config']['effort']=='high'
    assert project()['general_chat_turns'][-1]['status']=='completed'
    proposal=next(x for x in project()['timeline_edit_proposals'] if x['id']==proposed['proposal_id'])
    assert proposal['applied_by']=='agent-draft' and 'reviews' not in proposal
    reviewed=dict(human_edit_approval=False,agent_actor='agent-draft',human_final_output_approval='separate below')
    p=project();timeline=p['timeline_versions'][-1];assert timeline['id']==3 and 'approval' not in timeline
    raw=get('/api/timeline-frame?'+urlencode(dict(song='actual overlay',timeline_revision=3,clip_index=0,frame=18)))
    assert raw.startswith(b'\x89PNG');(OUT/'agent-draft-preview.png').write_bytes(raw)
    assert timeline['agent_draft']['actor']=='agent-draft'
    action('approve_timeline')
    refreshed=tool('search_project_context',dict(query='current exact approved timeline output grant'))
    current=refreshed['execution_targets']['timeline'];assert current['version']==3 and current['grant_id']
    queued=tool('request_render',dict(timeline_version=3,grant_id=current['grant_id']))
    assert queued['state']=='queued' and queued['finished_verified'] is False
    assert http.store.process_next()
    job=next(x for x in state()['jobs'] if x['id']==queued['job_id'])
    assert job['status']=='completed',job.get('error')
    raw=get(job['download']);assert hashlib.sha256(raw).hexdigest()==job['sha256'];(OUT/'agent-draft-output.mp4').write_bytes(raw)
    metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(OUT/'agent-draft-output.mp4')]))
    subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(OUT/'agent-draft-output.mp4'),'-f','null','-'],check=True)
    reopened=app.Store(folder/'store').state();assert reopened['projects']['actual overlay']['timeline_head']==3
    assert next(x for x in reopened['jobs'] if x['id']==job['id'])['sha256']==job['sha256']
    with http.store.connect() as db:
        reservations=[dict(state=row[0],actual_micro=row[1]) for row in db.execute('SELECT state,actual FROM reservations ORDER BY rowid')]
    report=dict(agent_settings=saved,active_and_next=active,proposal_record=proposal,reservations=reservations,recorded_at=datetime.now(timezone.utc).isoformat(),origin=origin,folder=str(folder),
                actual_provider_calls=0,real_model_quality='unverified',transport='explicit FixtureTransport, no provider credential supplier',
                selected_model=project()['model_settings']['selections']['chat'],request_models=[x['message_body']['model'] for x in manifests],
                manifest_sha256=[x['manifest_sha256'] for x in manifests],manifest_body_bytes=[len(json.dumps(x['message_body'],ensure_ascii=False).encode()) for x in manifests],
                token_count='synthetic100-token fixture; real token fit not verified',actual_provider_credentials=0,billing_confirmed=False,lookup=lookup,proposal=proposed,
                human_edit_review=reviewed,new_timeline=timeline,output_request=queued,completed_job=job,trace=trace,
                preview='agent-draft-preview.png',output='agent-draft-output.mp4',output_sha256=job['sha256'],
                decoded=True,streams=[x['codec_type'] for x in metadata['streams']],duration=metadata['format']['duration'],
                reopened_timeline=3,source_and_old_timeline_preserved=project()['timeline_versions'][:2]==before,
                notes=['Input fixtures and approved source are copied from prior actual-native/HTTP verification; no input/editor script substitutes for platform UI demo.',
                       'Provider tool responses explicitly synthetic. Actual local job processed by production Store.process_next.',
                       'Every request manifest approved separately. Auto draft result was held without another message, then explicit continuation consent sent it using frozen high effort despite desired medium.',
                       'Final output approval remains human and separate from agent-draft editing; no human edit-review receipt is forged.'])
    (OUT/'agent-settings-http-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',model_mapping=report['request_models'],trace_events=len(trace),job=job['id'],sha256=job['sha256'],streams=report['streams'],duration=report['duration']),ensure_ascii=False))
finally:
    http.shutdown();http.server_close();thread.join()
