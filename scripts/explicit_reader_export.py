"""Local-only approved test export after the generated take has been visually reviewed."""
import base64,json,uuid,hashlib
from pathlib import Path
from app import Store
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/qa/live-kling-explicit-reader-20261025'
def main():
 s=Store(ROOT/'data');gate=json.loads((OUT/'approval.json').read_text());j=s.generation.get(json.loads((OUT/'job.json').read_text())['job'])
 if j['state']!='imported':raise ValueError('not imported')
 with (OUT/'export-once.json').open('x') as f:json.dump({'status':'started'},f)
 song=gate['song'];shot=gate['shot']
 def action(name,**data):return s.mutate(dict(action=name,data=dict(song=song,**data),revision=s.state()['revision'],request_id=uuid.uuid4().hex))
 audio=ROOT/'docs/qa/fixtures/kling-live-v1/local-audio.wav'
 if hashlib.sha256(audio.read_bytes()).hexdigest()!='9942854cede699fbb4bc8453ad553e3a267f62f40d954634e57ad675bf58155d':raise ValueError('audio hash')
 action('audio',filename='local-audio.wav',content=base64.b64encode(audio.read_bytes()).decode(),rights='직접 만든 비식별 합성 테스트 음원')
 p=s.state()['projects'][song];sh=p['shots'][shot]
 action('select',shot=shot,take=j['take'],shot_revision=sh['revision'])
 action('review_take',shot=shot,take=j['take'],decision='approved',reason='자동화 QA: 실영상 디코드·길이·기하학 프레임 검토. 사용자 납품 승인과 별개')
 action('timeline',timeline=dict(clips=[dict(shot=shot,take=j['take'],duration=10,trim=0)],audio=p['audio_versions'][-1]['id'],audio_offset=0,subtitles=[dict(start=0,end=10,text='로컬 검증 · 비식별 테스트')],profile='landscape'))
 action('approve_timeline');quote=action('estimate_render')['estimate'];rid=action('render_job',estimate=quote)['job']
 (OUT/'export-once.json').write_text(json.dumps({'job':rid,'status':'queued'}));s.process_next()
 job=next(x for x in s.state()['jobs'] if x['id']==rid)
 result={k:job.get(k) for k in ['id','status','error','sha256','verified','download']}
 result['path']=str(s.root/'exports'/(rid+'.mp4'));(OUT/'export-once.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
