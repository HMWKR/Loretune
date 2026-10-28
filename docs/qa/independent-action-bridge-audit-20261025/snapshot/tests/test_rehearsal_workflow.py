import json,tempfile,unittest,uuid
from app import Store
from loretune import Conflict

class RehearsalWorkflowTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.st=Store(self.tmp.name)
  self.call('project',dict(name='A',era='default',story=0))
  with self.st.connect() as c:
   body=json.loads(c.execute('SELECT body FROM state').fetchone()[0]);body['projects']['A'].update(music_head=1,music_versions=[dict(id=1,audio=1,start=0,end=2)])
   c.execute('UPDATE state SET body=?',(json.dumps(body),))
  plan=self.call('guided_plan',dict(song='A',goal='fixture',scenes='Keep authored geometry'))['plan']
  self.call('apply_guided_plan',dict(song='A',plan=plan))
  self.plan=self.st.state()['projects']['A']['guided_plans'][0]
 def call(self,action,data):return self.st.mutate(dict(action=action,data=data,revision=self.st.state()['revision'],request_id=uuid.uuid4().hex))
 def propose(self):return self.call('action_propose',dict(song='A',plan=self.plan['id'],scene=self.plan['scenes'][0]['id']))['execution_card']
 def command(self,action,card,**extra):return self.call(action,dict(song='A',id=card['id'],card_revision=card['revision'],**extra))['execution_card']
 def test_plan_human_approval_receipt_candidate_review_preserves_selection(self):
  card=self.propose();self.assertEqual(card,self.propose())
  card=self.command('action_decide',card,decision='approved');self.assertIsNotNone(card['job'])
  card=self.command('action_execute',card)
  self.assertIsNotNone(card['take'])
  card=self.command('action_review',card,decision='approved')
  p=Store(self.tmp.name).state()['projects']['A'];shot=p['shots'][card['shot']]
  self.assertIsNone(shot['selected']);self.assertEqual(len(shot['takes']),1)
  self.assertEqual(shot['reviews'][-1]['decision'],'approved');self.assertIn('not AI',shot['takes'][0]['provenance'])
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT state,actual FROM reservations').fetchone(),('settled',0))
 def test_hold_reject_no_reservation_and_stale_card_conflict(self):
  card=self.propose();old=card.copy();card=self.command('action_decide',card,decision='held')
  with self.assertRaises(Conflict):self.command('action_decide',old,decision='approved')
  card=self.command('action_decide',card,decision='rejected')
  with self.assertRaises(ValueError):self.command('action_decide',card,decision='approved')
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
 def test_revoke_before_execution_and_changed_context_never_make_take(self):
  card=self.command('action_decide',self.propose(),decision='approved')
  card=self.command('action_decide',card,decision='held')
  with self.assertRaises(ValueError):self.command('action_execute',card)
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'cancelled')
  card=self.command('action_decide',self.propose(),decision='approved')
  self.call('shot',dict(song='A',shot='another',description='context change'))
  card=self.command('action_execute',card)
  self.assertEqual(card['decision'],'blocked');self.assertIsNone(card['take'])
 def test_unknown_scope_and_model_fields_rejected(self):
  card=self.propose()
  with self.assertRaises(ValueError):self.call('action_decide',dict(song='A',id=card['id'],card_revision=1,decision='approved',provider='live'))
  self.call('project',dict(name='B',era='default',story=0))
  with self.assertRaises(ValueError):self.call('action_execute',dict(song='B',id=card['id'],card_revision=1))
