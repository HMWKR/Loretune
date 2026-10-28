import hashlib,json
from pathlib import Path
from tests.test_general_chat_history import GeneralChatHistoryTest
case=GeneralChatHistoryTest('test_independent_turn_retains_previous_request')
root=Path('.omo/evidence/general-chat-history-20261028/backend')
try:
    case.setUp()
    case.test_independent_turn_retains_previous_request()
    with case.http.store.connect() as c:
        turns=[json.loads(r[0]) for r in c.execute('SELECT body FROM general_chat_turns ORDER BY rowid')]
        previews=[json.loads(r[0]) for r in c.execute('SELECT body FROM general_chat_previews ORDER BY rowid')]
    receipt=dict(scenario='two independent local HTTP turns',actual_provider=False,
                 credential='synthetic only',turns=turns,previews=previews,
                 transport_requests=[dict(endpoint=u,body=json.loads(b),wire_sha256=hashlib.sha256(b).hexdigest()) for u,b,_ in case.socket.requests])
    assert len(turns)==2 and all(t['status']=='completed' for t in turns)
    assert previews[-1]['history_context']['request_count']==1
    (root/'two-turn-http-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    print('PASS two completed independent requests; second exact approved body includes first request and unreviewed public answer')
finally:
    case.doCleanups()
