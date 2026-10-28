import sys,socket,json,hashlib,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent/'snapshot'))
from tests.test_local_creation_tools import LocalToolsTest
from tests.test_fal_multimodel import FalMultiTest
from tests.test_chat_runtime import Fake,response
import chat_runtime,model_selection,contracts
E={}
def block(*a,**kw):raise AssertionError('network/listener prohibited')
def runtime(st,name,prompt):
 def call(a,**d):return st.mutate(dict(action=a,data=d,revision=st.state()['revision'],request_id=__import__('uuid').uuid4().hex))
 p=st.state()['projects'][name];call('model_settings',song=name,selections={'chat':'anthropic-haiku-5-5'},model_revision=p['model_settings']['revision'])
 p=st.state()['projects'][name];ad=Fake([response()]);ap=dict(model='claude-haiku-5-5',workspace_id=st.workspace_id,project_id=contracts.project_id(st.workspace_id,name),synthetic_only=True,expires=time.time()+300,context_hash=model_selection.snapshot(p)['sha256'],prompt_hashes=[hashlib.sha256(prompt.encode()).hexdigest()],price_revision='haiku-5-5-20261025',max_rounds=2)
 rt=chat_runtime.ChatRuntime(st,ad,ap,st.root/'audit-usage.sqlite3');st.chat_runtime=rt
 call('chat_turn',song=name,prompt=prompt)
 with st.connect() as c:turn=json.loads(c.execute('SELECT body FROM chat_turns ORDER BY rowid DESC').fetchone()[0])
 run=turn['run'];lookup=call('production_tool',song=name,run=run,call=dict(id='lookup',name='search_project_context',arguments={'query':'current approved timeline, shots, takes and actions'},complete=True))['tool']
 return turn,lookup
with patch.object(socket.socket,'bind',block),patch.object(socket.socket,'connect',block):
 f=LocalToolsTest();f.setUp()
 try:
  grant=f.grant();turn,lookup=runtime(f.st,'song','Render the current approved timeline.')
  model_data=json.dumps(dict(handoff=turn['handoff'],lookup=lookup))
  E['render_context']={'required_timeline_version':f.project()['timeline_head'],'required_grant_id':grant,'grant_present':grant in model_data,'timeline_state_present':'timeline_version' in model_data or 'timeline_head' in model_data,'model_visible':json.loads(model_data)}
  bad,_=f.tool('request_render',dict(timeline_version=1,grant_id='current-approved'))
  E['render_context']['without_hidden_grant_result']=bad
 finally:f.doCleanups()
 FalMultiTest.setUpClass();f=FalMultiTest();f.setUp()
 try:
  f.setup_model('fal-flux-schnell');turn,lookup=runtime(f.st,'synthetic','Generate the already approved image action.')
  model_data=json.dumps(dict(handoff=turn['handoff'],lookup=lookup))
  E['media_context']={'action_present':f.action['id'] in model_data,'grant_present':f.grant['id'] in model_data,'plan_present':f.plan in model_data,'shot_name_present':'장면 1' in model_data or '\\uc7a5\\uba74 1' in model_data,'approved_shots':turn['handoff']['context']['value']['approved_shots'],'actual_shot_names':list(f.project()['shots']),'model_visible':json.loads(model_data)}
  visible_id=turn['handoff']['context']['value']['approved_shots'][0]['id']
  E['media_context']['using_only_visible_shot_id']=f.call('production_tool',song='synthetic',run=turn['run'],call=dict(id='prepare-visible',name='prepare_image_action',arguments=dict(shot_id=visible_id,model_id='fal-flux-schnell',prompt='blue geometry',ratio='16:9',shot_revision=f.shot()['revision']),complete=True))['tool']
 finally:f.doCleanups()
print(json.dumps(E,ensure_ascii=False,indent=2))
