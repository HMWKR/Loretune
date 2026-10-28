"""Offline evidence only. Use --before to load this batch's preserved modules."""
import hashlib
import json
from pathlib import Path
import socket
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE/'before')] if '--before' in sys.argv else []
sys.path.extend([str(ROOT/'tests'), str(ROOT)])

def no_network(*args, **kwargs):
    raise AssertionError('CC02 offline reproduction prohibits sockets')

socket.socket.connect = socket.socket.connect_ex = socket.socket.bind = socket.create_connection = no_network
import chat_runtime
import anthropic_ontology
from test_chat_preflight import ChatPreflightTest

results = []
for name in ['original_65529_65549', 'exact_messages_65536', 'count_timeout', 'messages_timeout']:
    case = ChatPreflightTest(); case.setUp()
    try:
        case.setup_adapter(count_failure=TimeoutError() if name == 'count_timeout' else None,
                           message_failure=TimeoutError() if name == 'messages_timeout' else None)
        body = None
        if name in ['original_65529_65549', 'exact_messages_65536']:
            _, body = case.boundary_turn(65516 if name == 'exact_messages_65536' else 65529)
        else:
            case.enqueue()
        case.runtime.process_next()
        status = case.turn()['status']
        try:
            case.enqueue(); next_blocked = False
        except ValueError:
            next_blocked = True
        results.append(dict(case=name, count_body_bytes=len(json.dumps({k:v for k,v in body.items() if k != 'max_tokens'}, ensure_ascii=False).encode()) if body else None,
            messages_body_bytes=len(json.dumps(body, ensure_ascii=False).encode()) if body else None,
            count_opener_calls=len(case.count_opener.requests), messages_opener_calls=len(case.message_opener.requests),
            synthetic_credential_supplier_calls=len(case.secret_reads), status=status,
            ledger=case.rows(), subsequent_enqueue_blocked=next_blocked))
    finally:
        case.doCleanups()

print(json.dumps(dict(mode='before' if '--before' in sys.argv else 'after', actual_provider_calls=0,
    socket_operations='forbidden', shared_database_opened=False,
    sources={m.__name__:dict(path=m.__file__,sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest())
             for m in [chat_runtime, anthropic_ontology]}, cases=results), indent=2))
