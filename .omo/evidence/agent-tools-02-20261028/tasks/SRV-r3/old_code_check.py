"""Run the SRV-r3 tests against the start/ copy of the server modules (current tests): they must fail there.

Run from the project root:
  PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B .omo/evidence/agent-tools-02-20261028/tasks/SRV-r3/old_code_check.py <dir with copies of start/*.py>
"""
import sys
sys.dont_write_bytecode = True
import io, unittest
# Only the server modules of start/ (its tests/ copy must not shadow the current tests package).
OLD = sys.argv[1]  # a folder holding copies of start/*.py only
sys.path[:0] = [OLD, '.', 'tests']
NEW = [
    'tests.test_general_chat_body_cap.InTurnPagingBudgetTest',
    'tests.test_general_chat_body_cap.StablePagesTest',
    'tests.test_general_chat_body_cap.BoundedContextListsTest',
    'tests.test_general_chat_body_cap.OverCapLiveTransportTest.test_old_single_page_result_is_withheld_with_a_budget_notice_and_the_turn_continues',
    'tests.test_general_chat_body_cap.OverCapLiveTransportTest.test_over_cap_continuation_ends_the_turn_recoverably_with_zero_provider_writes',
    'tests.test_general_chat_media_d15.GeneralChatImageD15Test.test_reason_limit_is_visible_to_the_model_in_schema_and_description',
    'tests.test_strict_wire_schema.StrictWireSchemaTest.test_openai_strict_definitions_carry_no_string_length_keywords',
    'tests.test_general_chat_scene_preference_tools.ProposeScene3DTest.test_duplicate_reports_the_stored_proposal_origin_and_held_status',
    'tests.test_general_chat_scene_preference_tools.ProposePreferenceRuleTest.test_duplicate_candidate_reports_the_stored_origin',
    'tests.test_general_chat_scene_preference_tools.ProposePreferenceRuleTest.test_open_candidates_per_category_are_capped_with_a_structured_refusal',
]
import chat_general
import tests.test_general_chat_body_cap as current
assert chat_general.__file__.startswith(OLD) and current.__file__.endswith('Loretune/tests/test_general_chat_body_cap.py'), (chat_general.__file__, current.__file__)
for name in NEW:
    suite = unittest.defaultTestLoader.loadTestsFromName(name)
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    print('%s: ran=%d failures=%d errors=%d -> %s' % (name.split('.', 1)[1], result.testsRun, len(result.failures), len(result.errors),
          'FAILS ON OLD CODE' if result.failures or result.errors else 'PASSES ON OLD CODE'))
