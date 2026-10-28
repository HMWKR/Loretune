"""B2: D15 display on cards, chat turns, work status and agent settings; review navigation kinds; tool labels.

Real server projections come from the isolated HTTP/SQLite fixtures of the A2a tests (contract-fake
transport, fal transports fail if reached). No model, provider, count_tokens, paid call or browser.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import chat_general
from app import Store
from tests import test_general_chat_media_d15 as d15

ROOT = Path(__file__).resolve().parents[1]


class ToolLabelTest(unittest.TestCase):
    def test_tool_labels_match_allowed_tools(self):
        source = (ROOT/'general-chat-ui.js').read_text()
        line = next(x for x in source.splitlines() if x.startswith(' const toolLabels='))
        out = subprocess.run(['node', '-e', line+';process.stdout.write(JSON.stringify(toolLabels))'],
                             capture_output=True, text=True, check=True).stdout
        labels = json.loads(out)
        self.assertEqual(set(labels), set(chat_general.ALLOWED_TOOLS))
        for name, label in labels.items():
            self.assertTrue(label.strip(), name)
            self.assertNotIn(name, label, 'internal tool names stay out of labels')


class B2CardsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d15.VideoD15Test.setUpClass()

    def image_case(self):
        case = d15.GeneralChatImageD15Test('test_different_model_is_a_proposal_and_never_changes_project_settings')
        case.setUp()
        self.addCleanup(case.doCleanups)
        return case

    def projections(self):
        agent = self.image_case()
        agent.set_agent('full_access', 'high')
        arguments = agent.m.arguments()
        arguments['model_id'] = 'fal-flux-pro-1-1'
        project = agent.m.send_tool('prepare_image_action', arguments)
        reopened = Store(agent.f.tmp.name).state()['projects']['A']
        agent.m.assert_no_media_execution()

        owner = self.image_case()
        owner.m.post('media_prepare', song='A', shot='장면 1', shot_revision=owner.m.project()['shots']['장면 1']['revision'],
                     prompt=owner.m.prompt, options={'ratio':'16:9'}, refs=[])
        owner_card, = owner.m.project()['media_actions']

        old = self.image_case()
        old.m.post('media_prepare', song='A', shot='장면 1', shot_revision=old.m.project()['shots']['장면 1']['revision'],
                   prompt=old.m.prompt, options={'ratio':'16:9'}, refs=[])
        with old.store.connect() as c:
            identifier, body = c.execute('SELECT id,body FROM production_actions').fetchone()
            value = json.loads(body)
            value['options'].pop('proposal')
            c.execute('UPDATE production_actions SET body=? WHERE id=?', (json.dumps(value), identifier))
        old_card, = old.m.project()['media_actions']

        video = d15.VideoD15Test('test_blocked_different_video_model_is_saved_as_proposal_only')
        video.setUp()
        self.addCleanup(video.doCleanups)
        result = video.tool(video.arguments(model_id='fal-kling-2-6-pro'))
        video_card = next(x for x in video.t.project()['media_actions'] if x['id'] == result['action_id'])
        video.assert_nothing_reserved_or_sent()
        return dict(agent_project=project, agent_reopened=reopened, owner_card=owner_card, old_card=old_card,
                    video_card=video_card, reason=arguments['model_reason'], video_reason=d15.REASON)

    def test_cards_turns_work_status_settings_and_navigation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'projections.json'
            path.write_text(json.dumps(self.projections(), ensure_ascii=False))
            result = subprocess.run(['node', 'tests/general_chat_b2_cards.cjs', str(path)], cwd=ROOT,
                                    capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertIn('real projections rendered', result.stdout)
        self.assertIn('B2 D15 surfaces', result.stdout)

    def test_existing_review_navigation_and_notice_contracts(self):
        for script in ('general_chat_review_navigation.cjs', 'studio_notice.cjs'):
            result = subprocess.run(['node', 'tests/'+script], cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, script+result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
