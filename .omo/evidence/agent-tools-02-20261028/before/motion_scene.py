"""Bounded, platform-neutral motion data and existing Store proposal/job records."""
from copy import deepcopy
import math,re,time,unicodedata,uuid,json
import guided,production_context
from loretune import Conflict

def obj(properties):return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)
KEY_SCHEMA=obj(dict(frame=dict(type='integer',minimum=0,maximum=95),x=dict(type='number',minimum=-1920,maximum=3840),y=dict(type='number',minimum=-1080,maximum=2160),opacity=dict(type='number',minimum=0,maximum=1),easing=dict(type='string',enum=['linear','easeInOutCubic'])))
LAYER_SCHEMA=obj(dict(id=dict(type='string'),kind=dict(type='string',enum=['text','rect','circle']),text=dict(type='string'),font=dict(type='string',enum=['system-ko-regular']),font_size=dict(type='number',minimum=24,maximum=160),width=dict(type='number',minimum=1,maximum=1920),height=dict(type='number',minimum=1,maximum=1080),color=dict(type='string'),in_frame=dict(type='integer',minimum=0,maximum=95),out_frame=dict(type='integer',minimum=1,maximum=96),keyframes=dict(type='array',minItems=1,maxItems=8,items=KEY_SCHEMA)))
SCHEMA=obj(dict(schema_version=dict(type='integer',enum=[1]),width=dict(type='integer',enum=[1920]),height=dict(type='integer',enum=[1080]),fps=dict(type='integer',enum=[24]),frame_count=dict(type='integer',minimum=72,maximum=96),background=dict(type='string'),layers=dict(type='array',minItems=1,maxItems=8,items=LAYER_SCHEMA)))

def exact(value,keys):
 if not isinstance(value,dict) or set(value)!=set(keys):raise ValueError('motion fields invalid')
def number(value,lo,hi):
 if type(value) not in (int,float) or not math.isfinite(value) or not lo<=value<=hi:raise ValueError('motion value outside bound')
def integer(value,lo,hi):
 if type(value) is not int or not lo<=value<=hi:raise ValueError('motion frame outside bound')
def color(value):
 if not isinstance(value,str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}',value):raise ValueError('motion requires opaque HEX color')
def validate(scene):
 exact(scene,SCHEMA['properties'])
 for k,v in dict(schema_version=1,width=1920,height=1080,fps=24).items():
  if type(scene[k]) is not int or scene[k]!=v:raise ValueError('unsupported motion profile')
 integer(scene['frame_count'],72,96);color(scene['background'])
 if not isinstance(scene['layers'],list) or not 1<=len(scene['layers'])<=8:raise ValueError('1–8 motion layers required')
 seen=set()
 for layer in scene['layers']:
  exact(layer,LAYER_SCHEMA['properties'])
  if not isinstance(layer['id'],str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]{0,31}',layer['id']) or layer['id'] in seen:raise ValueError('unique stable layer id required')
  seen.add(layer['id'])
  if layer['kind'] not in {'text','rect','circle'} or layer['font']!='system-ko-regular':raise ValueError('unsupported layer/font')
  text=layer['text']
  if not isinstance(text,str) or len(text)>80 or unicodedata.normalize('NFC',text)!=text or len(text.split('\n'))>2 or any(unicodedata.category(c).startswith('C') for c in text if c!='\n'):raise ValueError('motion text invalid')
  if layer['kind']=='text' and (not text.strip() or any(not x.strip() for x in text.split('\n'))):raise ValueError('text required')
  if layer['kind']!='text' and text!='':raise ValueError('shape text must be empty')
  number(layer['font_size'],24,160);number(layer['width'],1,1920);number(layer['height'],1,1080);color(layer['color'])
  if layer['kind']=='circle' and layer['width']!=layer['height']:raise ValueError('circle diameter mismatch')
  integer(layer['in_frame'],0,scene['frame_count']-1);integer(layer['out_frame'],layer['in_frame']+1,scene['frame_count'])
  keys=layer['keyframes']
  if not isinstance(keys,list) or not 1<=len(keys)<=8:raise ValueError('1–8 keyframes required')
  last=-1
  for key in keys:
   exact(key,KEY_SCHEMA['properties']);integer(key['frame'],last+1,scene['frame_count']-1);last=key['frame']
   number(key['x'],-1920,3840);number(key['y'],-1080,2160);number(key['opacity'],0,1)
   if key['easing'] not in {'linear','easeInOutCubic'}:raise ValueError('unsupported easing')
 return deepcopy(scene)

def frame_state(scene,frame,*,all_layers=False):
 validate(scene);integer(frame,0,scene['frame_count']-1);layers=[]
 for layer in scene['layers']:
  if not all_layers and not layer['in_frame']<=frame<layer['out_frame']:continue
  keys=layer['keyframes'];left=keys[0];right=keys[-1]
  for key in keys:
   if key['frame']<=frame:left=key
   if key['frame']>=frame:right=key;break
  if frame<=keys[0]['frame']:left=right=keys[0]
  if frame>=keys[-1]['frame']:left=right=keys[-1]
  t=0 if left['frame']==right['frame'] else (frame-left['frame'])/(right['frame']-left['frame'])
  if left['easing']=='easeInOutCubic':t=4*t*t*t if t<.5 else 1-((-2*t+2)**3)/2
  value={k:deepcopy(v) for k,v in layer.items() if k not in {'keyframes','in_frame','out_frame'}}
  value.update({k:left[k]+(right[k]-left[k])*t for k in ['x','y','opacity']});layers.append(value)
 return dict(width=scene['width'],height=scene['height'],background=scene['background'],layers=layers)

def context(p,shot):
 return guided.fingerprint(dict(shot_id=production_context.shot_id(p,shot),description=p['shots'][shot]['description'],canon=guided.context(p)))

def propose(p,args,source):
 shot=production_context.shot_key(p,args['shot_id']);s=p['shots'][shot];scene=validate(args['scene'])
 if type(args['base_motion_revision']) is not int or args['base_motion_revision']!=s.get('motion_head',0):raise Conflict('모션 기준 버전이 변경됐습니다.')
 item=dict(id=uuid.uuid4().hex,shot=shot,shot_id=production_context.shot_id(p,shot),base_revision=s.get('motion_head',0),base_context=context(p,shot),scene=scene,scene_hash=guided.fingerprint(scene),status='proposed',source=deepcopy(source),created=time.time())
 p.setdefault('motion_proposals',[]).append(item)
 return dict(status='proposed',proposal_id=item['id'],shot_id=item['shot_id'],base_revision=item['base_revision'],scene=deepcopy(scene),applied=False,rendered=False)

def review(store,p,data):
 exact(data,['song','proposal_id','decision'])
 item=next((x for x in p.get('motion_proposals',[]) if x['id']==data['proposal_id']),None)
 if not item or data['decision'] not in {'approved','held','rejected'}:raise ValueError('현재 작품의 모션 변경안을 선택하세요.')
 s=p['shots'][item['shot']]
 if item['status']=='applied':
  if data['decision']!='approved':raise ValueError('복원은 새 변경안으로 진행하세요.')
  return dict(applied=True,revision=item['applied_revision'])
 if data['decision']=='approved':
  if s.get('motion_head',0)!=item['base_revision'] or context(p,item['shot'])!=item['base_context']:raise Conflict('모션 기준이 바뀌었습니다. 새 변경안을 검토하세요.')
  from motion_renderer import font_manifest,validate_text
  validate(item['scene']);validate_text(item['scene'],store.root)
  version=dict(id=len(s.get('motion_versions',[]))+1,scene=deepcopy(item['scene']),scene_hash=item['scene_hash'],source=deepcopy(item['source']),context=item['base_context'],font=font_manifest(),created=time.time())
  version['approval']=dict(id=uuid.uuid4().hex,actor='local-owner',scope='local-motion-candidate',scene_hash=item['scene_hash'])
  s.setdefault('motion_versions',[]).append(version);s['motion_head']=version['id'];item.update(status='applied',applied_revision=version['id'])
 else:item['status']=data['decision']
 item.setdefault('reviews',[]).append(dict(actor='local-owner',decision=data['decision'],at=time.time()))
 return dict(applied=item['status']=='applied',revision=item.get('applied_revision'))

def request_render(store,c,p,name,args):
 exact(args,['shot_id','motion_revision','grant_id']);integer(args['motion_revision'],1,100000)
 if not isinstance(args['grant_id'],str) or not args['grant_id']:raise ValueError('saved motion grant required')
 shot=production_context.shot_key(p,args['shot_id']);s=p['shots'][shot]
 if args['motion_revision']!=s.get('motion_head',0):raise Conflict('모션 버전이 변경됐습니다.')
 v=next((x for x in s.get('motion_versions',[]) if x['id']==args['motion_revision']),None)
 if not v or v['approval']['id']!=args['grant_id'] or v['approval']['scope']!='local-motion-candidate' or context(p,shot)!=v['context']:raise ValueError('현재 모션의 사람 승인 필요')
 validate(v['scene'])
 if guided.fingerprint(v['scene'])!=v['scene_hash'] or v['approval']['scene_hash']!=v['scene_hash']:raise ValueError('모션 승인 내용이 변경됐습니다.')
 from motion_renderer import font_manifest
 if font_manifest()!=v['font']:raise ValueError('폰트·렌더러가 변경됐습니다. 새 버전을 검토하세요.')
 for row in c.execute('SELECT body FROM jobs'):
  j=json.loads(row[0])
  if j['song']==name and j.get('kind')=='local-motion' and j['motion']['approval']['id']==args['grant_id']:return receipt(j,True)
 identifier=uuid.uuid4().hex
 job=dict(id=identifier,revision=1,kind='local-motion',song=name,shot=shot,shot_id=production_context.shot_id(p,shot),status='queued',progress=0,created=time.time(),cancel_requested=False,motion=deepcopy(v),snapshot=dict(shots={}),download=None,error=None,cost=dict(provider_calls=0,provider_cost=0,local_compute='미계측',kind='local-motion-candidate'))
 c.execute('INSERT INTO jobs VALUES (?,?)',(identifier,json.dumps(job)));return receipt(job)

def receipt(job,existing=False):
 return dict(status='existing' if existing else 'accepted',job_id=job['id'],state=job['status'],mode='local-motion',finished_verified=job['status']=='completed' and bool(job.get('sha256')),take=job.get('take'),output_approved=False,external_calls=0)
