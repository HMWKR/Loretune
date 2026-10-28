import base64
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid
from app import Store, Conflict
from editing import current, render_project, save_timeline, srt, preflight

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Media tools required')
class EditingTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.store=Store(self.temp.name)
        self.img=Path(self.temp.name)/'image.png';self.wav=Path(self.temp.name)/'song.wav'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=64x64','-frames:v','1',str(self.img)],check=True)
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=5',str(self.wav)],check=True)
        self.call('project',name='song',era='default',story=0)
        for name in ['a','b']:
            self.call('shot',shot=name,description=name)
            self.call('take',shot=name,shot_revision=0,filename='image.png',content=base64.b64encode(self.img.read_bytes()).decode(),reason='initial',rights='직접 제작')
            self.call('select',shot=name,take=1,shot_revision=1)
    def call(self,action,**data):
        data.setdefault('song','song')
        return self.store.mutate(dict(action=action,data=data,request_id=uuid.uuid4().hex,revision=self.store.state()['revision']))
    def p(self):return self.store.state()['projects']['song']
    def timeline(self):
        value=current(self.p())
        if not self.p()['timeline_head']:value['profile']='preview'
        return value
    def save_approve(self,timeline):
        self.call('timeline',timeline=timeline)
        for clip in timeline['clips']:self.call('review_take',shot=clip['shot'],take=clip['take'],decision='approved',reason='검토 완료')
        self.call('approve_timeline')
    def test_generation_preparation_requires_approved_frame_and_never_dispatches(self):
        from unittest.mock import patch
        with self.assertRaises(ValueError):self.call('prepare_generation',shot='a',shot_revision=2,prompt='clouds')
        self.call('assign_reference',shot='a',shot_revision=2,role='start_frame',source_song='song',source_shot='a',source_take=1,reason='QA')
        with self.assertRaises(ValueError):self.call('prepare_generation',shot='a',shot_revision=3,prompt='clouds')
        self.call('review_reference',shot='a',shot_revision=3,version=1,decision='approved',reason='QA')
        before=self.p()['shots']['a']
        request=dict(action='prepare_generation',data=dict(song='song',shot='a',shot_revision=4,prompt='clouds'),request_id=uuid.uuid4().hex,revision=self.store.state()['revision'])
        with patch('fal_provider.os.environ.get',side_effect=AssertionError('secret read')),patch('fal_provider.FalKling.submit',side_effect=AssertionError('external call')):
            first=self.store.mutate(request);self.assertEqual(first,self.store.mutate(request))
        after=self.p()['shots']['a'];self.assertEqual(before['takes'],after['takes']);self.assertEqual(after['selected'],1)
        self.assertEqual(len(after['generation_preparations']),1)
        prep=after['generation_preparations'][0];self.assertFalse(prep['external_transmission']);self.assertIsNone(prep['provider_request_id'])
        self.assertEqual(prep['estimate']['money']['amount'],'0.70')
        self.assertEqual(Store(self.temp.name).state()['projects']['song']['shots']['a']['generation_preparations'],after['generation_preparations'])
        with self.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)

    def test_generation_runtime_fake_end_to_end_and_live_gate(self):
        import time,ledger
        self.call('assign_reference',shot='a',shot_revision=2,role='start_frame',source_song='song',source_shot='a',source_take=1,reason='QA')
        self.call('review_reference',shot='a',shot_revision=3,version=1,decision='approved',reason='QA')
        prep=self.call('prepare_generation',shot='a',shot_revision=4,prompt='blue landscape')['preparation']
        with self.assertRaises(ValueError):self.call('start_generation',shot='a',preparation=prep)
        self.assertEqual(self.store.state()['generation_jobs'],[])
        calls=[];video=Path(self.temp.name)/'provider-fixture.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=64x64:d=10','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
        class FakeAdapter:
            def submit(_,data):calls.append(data);return {'request_id':'fake-fixture'}
            def status(_,receipt):return {'state':'COMPLETED','result_ready':True}
            def result(_,receipt):return {'url':'https://fal.media/fixture.mp4'}
            def download(_,url):return video.read_bytes()
        self.store.provider_adapter=FakeAdapter()
        prepared=self.p()['shots']['a']['generation_preparations'][0]
        import hashlib
        self.store.generation_approval=dict(expires=time.time()+60,maximum_calls=1,maximum_units=1_000_000,model=prepared['estimate']['model'],workspace_id=self.store.workspace_id,song='song',shot='a',image_sha256=prepared['source']['sha256'],prompt_sha256=hashlib.sha256(prepared['prompt'].encode()).hexdigest(),privacy='private',retention_seconds=3600,duration=10,generate_audio=False,price_money=prepared['estimate']['money'],price_checked_at=time.time())
        scope='project:'+self.store.state()['project_ids']['song']
        with self.store.connect() as c:ledger.patch_budget(c,self.store.workspace_id,scope,dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
        before=self.p()['shots']['a']['takes']
        job=self.call('start_generation',shot='a',preparation=prep)['job']
        self.assertEqual(job,self.call('start_generation',shot='a',preparation=prep)['job'])
        self.assertTrue(self.store.process_generation());self.assertEqual(len(calls),1)
        with self.store.connect() as c:
            j=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(job,)).fetchone()[0]);j['updated']=0
            c.execute('UPDATE generation_jobs SET body=? WHERE id=?',(json.dumps(j),job))
        self.assertTrue(self.store.process_generation());self.assertTrue(self.store.process_generation())
        result=self.store.generation.get(job);self.assertEqual(result['state'],'imported')
        self.assertEqual(self.p()['shots']['a']['selected'],1);self.assertEqual(self.p()['shots']['a']['takes'][0],before[0])
        self.assertFalse(result['cost_confirmed']);self.assertEqual(len(calls),1)
        with self.store.connect() as c:self.assertEqual(ledger.budget(c,self.store.workspace_id,scope)['data']['reserved']['amount'],'0.7')

    def test_audio_captions_and_actual_render(self):
        self.call('audio',filename='song.wav',content=base64.b64encode(self.wav.read_bytes()).decode(),rights='직접 제작')
        timeline=self.timeline();timeline.update(audio=1,audio_offset=1,subtitles=[dict(start=0,end=1,text='달빛 moon 月')]);timeline['clips'][0]['duration']=1;timeline['clips'][1]['duration']=1.5
        self.save_approve(timeline);job=self.call('render_job')['job'];self.assertTrue(self.store.process_next())
        result=self.store.state()['jobs'][0];self.assertEqual(result['status'],'completed',result['error'])
        output=self.store.root/'exports'/(job+'.mp4')
        data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]))
        self.assertCountEqual([s['codec_type'] for s in data['streams']],['video','audio','subtitle'])
        self.assertAlmostEqual(float(data['format']['duration']),2.5,places=1)
        self.assertNotIn('delivery_reviews',result)
        review=self.call('delivery_review',job=job,decision='approved',reason='출력 재생과 음원·자막 검토')['delivery_review']
        self.assertEqual(review['sha256'],result['sha256'])
        self.assertIn('달빛 moon 月',(self.store.root/'exports'/(job+'.srt')).read_text())
        record=json.loads((self.store.root/'exports'/(job+'.json')).read_text())
        self.assertEqual(record['verified']['streams'],['video','audio','subtitle'])
        self.assertEqual(len(record['selected_takes']),2)
        self.assertFalse((self.store.root/'exports'/('parts-'+job)/'final.mp4').exists())
        from renderer import verify_output
        wrong=deepcopy(result['snapshot']);wrong['profile']='portrait'
        with self.assertRaises(ValueError):verify_output(output,wrong)
        old=deepcopy(self.p()['timeline_versions'][0]);self.call('audio',filename='new.wav',content=base64.b64encode(self.wav.read_bytes()).decode(),rights='직접 제작')
        self.assertEqual(old,self.p()['timeline_versions'][0]);self.assertEqual(self.p()['timeline_versions'][0]['audio'],1)
    def test_music_range_and_audio_version_remain_a_pair(self):
        first=base64.b64encode(self.wav.read_bytes()).decode()
        short=Path(self.temp.name)/'short.wav'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=660:duration=1',str(short)],check=True)
        self.call('audio',filename='first.wav',content=first,rights='직접 제작')
        self.call('audio',filename='short.wav',content=base64.b64encode(short.read_bytes()).decode(),rights='직접 제작')
        self.call('music_structure',audio=1,start=3,end=4,sections=[])
        p=Store(self.temp.name).state()['projects']['song']; draft=current(p)
        self.assertEqual((p['audio_selected'],draft['audio'],draft['audio_offset']),(1,1,3))
        save_timeline(p,deepcopy(draft))
        before=deepcopy(p['timeline_versions'])
        self.call('timeline',timeline=draft)
        self.call('audio',filename='short-again.wav',content=base64.b64encode(short.read_bytes()).decode(),rights='직접 제작')
        stored=self.p()
        self.assertEqual(stored['timeline_versions'],before)
        self.assertEqual((current(stored)['audio'],current(stored)['audio_offset']),(1,3))
        stored['timeline_head']=None
        self.assertEqual((current(stored)['audio'],current(stored)['audio_offset']),(3,0))
    def test_caption_rejects_characters_that_cannot_be_exported(self):
        for text in ['앞\x00뒤','앞\ud800뒤']:
            timeline=self.timeline();timeline['subtitles']=[dict(start=0,end=1,text=text)]
            with self.assertRaisesRegex(ValueError,'자막에 지원하지 않는 문자'):
                self.call('timeline',timeline=timeline)
            self.assertFalse(self.p()['timeline_versions'])
    def test_versions_restore_and_approval_invalidation(self):
        t=self.timeline();self.save_approve(t);old=deepcopy(self.p()['timeline_versions'][0]);t['clips'].reverse();self.call('timeline',timeline=t)
        self.assertEqual(old,self.p()['timeline_versions'][0]);self.assertNotIn('approval',current(self.p()))
        with self.assertRaises(ValueError):self.call('render_job')
        self.call('restore_timeline',version=1);self.assertEqual(current(self.p())['clips'],old['clips']);self.assertNotIn('approval',current(self.p()))
    def test_supported_output_profiles_are_measured(self):
        from editing import PROFILES
        self.assertEqual(self.p()['profile'],'landscape')
        unsupported=self.timeline();unsupported['profile']='4k'
        with self.assertRaises(ValueError):self.call('timeline',timeline=unsupported)
        self.call('audio',filename='song.wav',content=base64.b64encode(self.wav.read_bytes()).decode(),rights='직접 제작')
        for profile,dimensions in PROFILES.items():
            with self.subTest(profile=profile):
                t=self.timeline();t['profile']=profile
                t.update(audio=1,audio_offset=0,subtitles=[dict(start=0,end=.5,text='승인 사양 QA')])
                for clip in t['clips']:clip['duration']=.5
                self.save_approve(t)
                identifier=self.call('render_job')['job'];self.store.process_next()
                job=next(j for j in self.store.state()['jobs'] if j['id']==identifier)
                self.assertEqual(job['status'],'completed',job['error'])
                self.assertEqual((job['verified']['width'],job['verified']['height']),dimensions)
                self.assertEqual(job['verified']['frame_rate'],'24/1')
                self.assertEqual(job['verified']['streams'],['video','audio','subtitle'])
                self.assertEqual(job['verified']['audio_sample_rate'],'48000')
    def test_reference_api_validates_rights_and_preserves_output_inputs(self):
        before=deepcopy(self.p()['shots']['a']['takes'])
        sh=self.p()['shots']['a']
        self.call('assign_reference',shot='a',shot_revision=sh['revision'],source_song='song',source_shot='a',source_take=1,role='start_frame',reason='첫 프레임 계획')
        sh=self.p()['shots']['a']
        self.assertEqual(sh['takes'],before)
        self.call('asset_rights',sha256=before[0]['sha256'],blocked=True,reason='사용 중지')
        with self.assertRaises(ValueError):
            self.call('review_reference',shot='a',shot_revision=sh['revision'],version=1,decision='approved',reason='검토')
        self.assertEqual(self.p()['shots']['a']['reference_versions'][0]['status'],'unreviewed')
    def test_music_32_to_47_second_offset(self):
        from array import array
        # Silence before second 32, then a tone: wrong source offset cannot pass.
        subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',
                        'aevalsrc=if(gte(t\\,32)\\,0.2*sin(2*PI*440*t)\\,0):s=48000:d=50',
                        str(self.wav)],check=True)
        self.call('audio',filename='offset.wav',content=base64.b64encode(self.wav.read_bytes()).decode(),rights='test waveform')
        timeline=self.timeline();timeline.update(audio=1,audio_offset=32)
        for clip in timeline['clips']:clip['duration']=7.5
        self.save_approve(timeline)
        identifier=self.call('render_job')['job'];self.store.process_next()
        job=next(j for j in self.store.state()['jobs'] if j['id']==identifier)
        self.assertEqual(job['status'],'completed',job['error'])
        output=self.store.root/'exports'/(identifier+'.mp4')
        info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(output)]))
        self.assertAlmostEqual(float(info['format']['duration']),15,places=1)
        pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(output),'-map','0:a:0','-t','0.5','-f','s16le','-ac','1','-ar','48000','pipe:1'])
        samples=array('h');samples.frombytes(pcm)
        rms=(sum(x*x for x in samples)/len(samples))**.5
        self.assertGreater(rms,3000)
    def test_bad_captions_and_trim(self):
        for lines in [[dict(start=1,end=7,text='past end')],[dict(start=0,end=2,text='one'),dict(start=1,end=3,text='overlap')]]:
            t=self.timeline();t['subtitles']=lines
            with self.assertRaises(ValueError):self.call('timeline',timeline=t)
        t=self.timeline();t['clips'][0]['trim']=-1
        with self.assertRaises(ValueError):self.call('timeline',timeline=t)
    def test_comments_block_approval(self):
        self.call('timeline',timeline=self.timeline());self.call('comment',at=1,text='fix')
        with self.assertRaises(ValueError):self.call('approve_timeline')
        self.call('resolve_comment',id=1);self.save_approve(self.timeline())
    def test_preflight_readiness_and_short_audio_warning(self):
        self.assertFalse(preflight(self.p())['ready'])
        self.call('audio',filename='song.wav',content=base64.b64encode(self.wav.read_bytes()).decode(),rights='self')
        timeline=self.timeline();timeline.update(audio=1,audio_offset=0)
        self.save_approve(timeline)
        result=preflight(self.p())
        self.assertTrue(result['ready'])
        self.assertIn('무음',result['warnings'][0])
        self.call('comment',at=1,text='검토 필요')
        self.assertFalse(preflight(self.p())['ready'])
    def test_asset_stop_propagates_to_queue_and_reuse(self):
        self.save_approve(self.timeline())
        identifier=self.call('render_job')['job']
        sha=self.p()['shots']['a']['takes'][0]['sha256']
        result=self.call('asset_rights',sha256=sha,blocked=True,reason='권리 확인 대기')
        self.assertIn(identifier,result['affected_jobs'])
        self.assertFalse(self.store.process_next())
        with self.assertRaises(ValueError):self.call('render_job')
        with self.assertRaises(ValueError):
            self.call('reuse_take',shot='b',shot_revision=self.p()['shots']['b']['revision'],source_song='song',source_shot='a',source_take=1,reason='reused')
        self.call('asset_rights',sha256=sha,blocked=False,reason='새 사용 허가 확인')
        self.call('render_job')
    def test_cancel_queued_and_recover_running(self):
        self.save_approve(self.timeline());job=self.call('render_job')['job'];self.call('cancel_job',job=job)
        self.assertFalse(self.store.process_next());self.assertEqual(self.store.state()['jobs'][0]['status'],'cancelled')
        job=self.call('render_job')['job']
        with self.store.connect() as c:
            value=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(job,)).fetchone()[0]);value['status']='running';c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(value),job))
        restarted=Store(self.temp.name);restarted.recover_jobs();self.assertEqual(restarted.state()['jobs'][0]['status'],'interrupted')
        ops=restarted.operations()
        self.assertEqual(ops['counts']['cancelled'],1)
        self.assertEqual(ops['counts']['interrupted'],1)
        self.assertEqual(ops['counts']['completed'],0)
        self.assertEqual(ops['provider']['calls'],0)
        self.assertFalse(ops['provider']['connected'])
        self.assertNotIn('data',ops['audit'][0])
    def test_invalid_media_and_rights(self):
        before=set((self.store.root/'assets').iterdir())
        with self.assertRaises(ValueError):self.call('audio',filename='song.wav',content=base64.b64encode(b'not audio').decode(),rights='self')
        with self.assertRaises(ValueError):self.call('take',shot='a',shot_revision=self.p()['shots']['a']['revision'],filename='broken.png',content=base64.b64encode(b'QA invalid image').decode(),reason='QA',rights='self')
        self.assertEqual(before,set((self.store.root/'assets').iterdir()))
        self.assertEqual(list(self.store.root.glob('upload-*')),[])
        with self.store.connect() as c:
            revision,body=c.execute('SELECT revision,body FROM state').fetchone();d=json.loads(body);d['projects']['song']['shots']['a']['takes'][0]['rights']='사용권 미확인';c.execute('UPDATE state SET body=?',(json.dumps(d),))
        self.call('timeline',timeline=self.timeline())
        with self.assertRaises(ValueError):self.call('approve_timeline')
    def test_unconfirmed_audio_rights_block_approval(self):
        self.call('audio',filename='song.wav',content=base64.b64encode(self.wav.read_bytes()).decode(),rights='사용권 미확인')
        self.call('timeline',timeline=self.timeline())
        for name in ['a','b']:self.call('review_take',shot=name,take=1,decision='approved',reason='검토')
        with self.assertRaises(ValueError):self.call('approve_timeline')
        self.assertNotIn('approval',current(self.p()))
    def test_frozen_job_survives_new_edit(self):
        t=self.timeline();self.save_approve(t);job=self.call('render_job')['job'];t['clips'][0]['duration']=1;self.call('timeline',timeline=t)
        self.assertEqual(self.store.state()['jobs'][0]['snapshot']['shots']['0']['duration'],3)
    def test_render_estimate_stale_expiry_and_duplicate_confirmation(self):
        from estimates import validate
        self.save_approve(self.timeline())
        identifier=self.call('estimate_render')['estimate']
        quote=deepcopy(self.p()['render_estimates'][-1])
        snapshot=render_project(self.p(),current(self.p()))
        self.assertEqual(quote['provider_cost'],0)
        self.assertIsNone(quote['local_compute'])
        with self.assertRaises(ValueError):validate(quote,snapshot,now=quote['expires'])
        first=self.call('render_job',estimate=identifier)['job']
        self.assertEqual(self.call('render_job',estimate=identifier)['job'],first)
        self.assertEqual(len(self.store.state()['jobs']),1)
        t=self.timeline();t['clips'][0]['duration']=1
        self.save_approve(t)
        with self.assertRaises(ValueError):self.call('render_job',estimate=identifier)
        self.assertEqual(len(self.store.state()['jobs']),1)
    def test_changed_asset_fails_job(self):
        self.save_approve(self.timeline());before=deepcopy(current(self.p()));self.call('render_job');Path(self.p()['shots']['a']['takes'][0]['asset']).write_bytes(b'changed');self.store.process_next();self.assertEqual(self.store.state()['jobs'][0]['status'],'failed');self.assertEqual(current(self.p()),before)

    def test_take_review_is_separate_and_revoke_blocks_export(self):
        t=self.timeline();self.call('timeline',timeline=t)
        with self.assertRaises(ValueError):self.call('approve_timeline')
        self.save_approve(t)
        self.call('review_take',shot='a',take=1,decision='changes_requested',reason='수정 필요')
        with self.assertRaises(ValueError):self.call('render_job')
        self.assertEqual(self.p()['shots']['a']['selected'],1)

    def test_reuse_does_not_copy_review_or_mutate_source(self):
        self.call('review_take',shot='a',take=1,decision='approved',reason='승인')
        source=deepcopy(self.p())
        self.call('project',name='next',era='default',story=0)
        self.call('shot',song='next',shot='new',description='새 장면')
        self.call('reuse_take',song='next',shot='new',shot_revision=0,source_song='song',source_shot='a',source_take=1,reason='재사용')
        target=self.store.state()['projects']['next']['shots']['new']
        self.assertEqual(self.p(),source)
        self.assertIsNone(target['selected'])
        self.assertFalse(target.get('reviews'))
        self.assertEqual(target['takes'][0]['asset'],source['shots']['a']['takes'][0]['asset'])
        self.assertEqual(target['takes'][0]['provenance'],dict(song='song',shot='a',take=1))

    def test_running_cancel_keeps_completed_parts(self):
        from renderer import render, Cancelled
        t=self.timeline();frozen=render_project(self.p(),t);parts=Path(self.temp.name)/'parts';flag=[False]
        def progress(value):flag[0]=True
        with self.assertRaises(Cancelled):render(frozen,Path(self.temp.name)/'cancelled.mp4',progress,lambda:flag[0],parts)
        self.assertTrue((parts/'0.mp4').is_file())
        self.assertFalse((parts/'1.mp4').exists())

    def test_stale_selected_take_cannot_final_render(self):
        self.save_approve(self.timeline())
        rev=self.p()['shots']['a']['revision']
        self.call('take',shot='a',shot_revision=rev,filename='image.png',content=base64.b64encode(self.img.read_bytes()).decode(),reason='new',rights='self')
        self.call('select',shot='a',take=2,shot_revision=rev+1)
        with self.assertRaises(ValueError):self.call('render_job')
