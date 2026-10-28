import tempfile,unittest,uuid
from copy import deepcopy
import production_tools as t
import model_selection as m
from app import Store
from loretune import Conflict

class ProductionToolsTest(unittest.TestCase):
    def call(self,name,args,**kw):return dict(id=uuid.uuid4().hex,name=name,arguments=args,complete=True,**kw)
    def test_strict_args_never_accept_actor_endpoint_grant_or_partial_json(self):
        p={};r=t.begin(p)
        c=self.call('search_project_context',{'query':'x'});c['complete']=False
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):t.execute(p,r['id'],c)
        for key in ['approved','endpoint']:
            c=self.call('search_project_context',{'query':'x',key:True})
            result=t.execute(p,r['id'],c);self.assertEqual(result['status'],'invalid_arguments')
        self.assertEqual(p['production_runs'][0]['state'],'invalid_arguments')
        with self.assertRaisesRegex(ValueError,'NOT_ACCEPTING'):t.execute(p,r['id'],self.call('search_project_context',{'query':'x'}))
    def test_duplicate_conflict_late_request_and_other_project(self):
        p={};r=t.begin(p);c=self.call('get_model_capabilities',{'role':'video'})
        out=t.execute(p,r['id'],c);self.assertEqual(t.execute(p,r['id'],c),out)
        self.assertEqual(len(p['production_runs'][0]['calls']),1)
        bad=deepcopy(c);bad['arguments']['role']='chat'
        with self.assertRaises(Conflict):t.execute(p,r['id'],bad)
        with self.assertRaisesRegex(ValueError,'NOT_FOUND'):t.execute({},r['id'],c)
        m.update(p,{'chat':'anthropic-haiku-5-5'},0)
        with self.assertRaisesRegex(ValueError,'NOT_ACCEPTING'):t.execute(p,r['id'],self.call('get_model_capabilities',{'role':'chat'}))
        self.assertEqual(t.execute(p,r['id'],c),out) # original receipt remains available
    def test_context_and_plan_preserve_user_input_no_paid_work(self):
        p={'snapshot':[dict(text='blue coat')],'shots':{}};r=t.begin(p)
        plan=t.execute(p,r['id'],self.call('propose_media_plan',dict(goal='그대로',scenes='내 장면',style='',constraints='',kind='narrative')))
        self.assertEqual(plan['plan']['scenes'][0]['description'],'내 장면')
        self.assertFalse(plan['cost_approval'])
        out=t.execute(p,r['id'],self.call('request_media_generation',dict(plan_id=plan['plan']['id'],action_id='a',grant_id='invented')))
        self.assertEqual(out['status'],'blocked');self.assertNotIn('generation_jobs',p)
        p['snapshot'][0]['text']='red'
        with self.assertRaises(Conflict):t.execute(p,r['id'],self.call('search_project_context',{'query':'coat'}))
    def test_round_limit_and_secret_free_result(self):
        p={};r=t.begin(p)
        job=dict(id='j',state='import_blocked',failure_code='cdn_token_http_403',input='secret-canary',receipt='secret-canary')
        for _ in range(8):
            out=t.execute(p,r['id'],self.call('get_generation_job',{'job_id':'j'}),jobs=[job])
            self.assertNotIn('secret-canary',str(out))
            self.assertEqual(out['job']['state'],'import_blocked')
        with self.assertRaisesRegex(ValueError,'ROUND_LIMIT'):t.execute(p,r['id'],self.call('get_model_capabilities',{'role':'image'}))
    def test_store_persists_error_budget_and_scopes_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            st=Store(folder)
            def act(a,d):return st.mutate(dict(action=a,data=d,request_id=uuid.uuid4().hex,revision=st.state()['revision']))
            for name in ['A','B']:act('project',dict(name=name,era='default',story=0))
            r=act('production_run',{'song':'A'})['run']
            c=self.call('search_project_context',{'query':'x','actor':'admin'})
            out=act('production_tool',dict(song='A',run=r['id'],call=c))
            self.assertEqual(out['tool']['status'],'invalid_arguments')
            self.assertEqual(Store(folder).state()['projects']['A']['production_runs'][0]['repair_count'],1)
            with self.assertRaises(ValueError):act('production_tool',dict(song='B',run=r['id'],call=c))

    def test_malformed_tool_name_and_semantic_plan_errors_consume_repair_budget(self):
        p={};r=t.begin(p)
        c=self.call('propose_media_plan',dict(goal='goal',scenes='scene',style='',constraints='',kind='unsupported'))
        self.assertEqual(t.execute(p,r['id'],c)['status'],'invalid_arguments')
        c=self.call('x',{});c['name']=[]
        self.assertFalse(t.execute(p,r['id'],c)['retryable'])
        self.assertNotIn('guided_plans',p)
