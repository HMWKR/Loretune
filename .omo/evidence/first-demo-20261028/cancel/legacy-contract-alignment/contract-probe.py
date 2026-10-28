"""Inspect the old cancellation expectations against actual fixture state."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from tests import test_chat_general_http as general
from tests import test_chat_live_contract as live
import chat_general

OUT = Path(__file__).parent


def snapshot(http):
    with http.store.connect() as c:
        turn = json.loads(c.execute('SELECT body FROM general_chat_turns ORDER BY rowid DESC LIMIT 1').fetchone()[0])
        reservation = c.execute('SELECT state,actual FROM reservations WHERE id=?', (turn['reservation'],)).fetchone()
        attempts = c.execute('SELECT operation,state FROM provider_attempts WHERE reservation=? ORDER BY operation', (turn['reservation'],)).fetchall()
        projects = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects']
    return dict(turn=turn, reservation=reservation, attempts=attempts,
                guided_plans={name: p.get('guided_plans', []) for name, p in projects.items()})


results = []
for kind in ('after-settlement-before-tool', 'cancel-response-race', 'rights-response-race', 'loopback-after-message'):
    case = (live.LiveContractHTTPTest() if kind == 'loopback-after-message' else general.GeneralChatHTTPTest())
    case.setUp()
    failure = None
    try:
        if kind in {'cancel-response-race', 'rights-response-race'}:
            created = []
            factory = general.server

            def tracked(*args, **kwargs):
                http = factory(*args, **kwargs)
                created.append(http)
                return http

            with tempfile.TemporaryDirectory() as folder, patch.object(general, 'server', side_effect=tracked):
                try:
                    case._observed_usage_race(folder, 'cancel' if kind == 'cancel-response-race' else 'rights')
                except AssertionError as exc:
                    failure = str(exc)
                observed = snapshot(created[-1])
        else:
            try:
                if kind == 'loopback-after-message':
                    case.test_cancel_after_message_preserves_observed_estimate_and_blocks_tools()
                else:
                    case.test_cancel_after_settlement_before_tool_does_not_create_proposal()
            except AssertionError as exc:
                failure = str(exc)
            observed = snapshot(case.http)
        expected = 'outcome_unknown' if kind == 'rights-response-race' else 'cancelled'
        assert observed['turn']['status'] == expected
        assert observed['turn']['pricing_status'] == 'priced'
        assert 'pending_tool' not in observed['turn']
        assert observed['reservation'][0] in {'settled', 'estimated'} and observed['reservation'][1] == 60
        assert observed['attempts'] == [('chat-count', 'observed'), ('chat-message', 'observed')]
        assert all(not plans for plans in observed['guided_plans'].values())
        assert (failure is None) == (kind == 'rights-response-race')
        results.append(dict(case=kind, old_expectation_failure=failure, observed=observed))
    finally:
        case.doCleanups()

report = dict(recorded_at=datetime.now(timezone.utc).isoformat(), results=results,
              product_source_sha256=hashlib.sha256((ROOT / 'chat_general.py').read_bytes()).hexdigest(),
              actual_provider_calls=0, transport_scope='contract fake or explicit local loopback HTTP')
(OUT / 'before-contract-state-proof.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'cases': len(results), 'cancelled': sum(x['observed']['turn']['status'] == 'cancelled' for x in results),
                  'rights_unknown_preserved': results[2]['observed']['turn']['status'] == 'outcome_unknown',
                  'priced_observed_no_tool': True, 'actual_provider_calls': 0}))
