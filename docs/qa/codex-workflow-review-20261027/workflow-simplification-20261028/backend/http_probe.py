"""Local HTTP import evidence; no provider or native-render configuration."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
import app
from scene_asset_fixtures import glb_parts, pack_glb, png

OUT = Path(__file__).parent
VALID = ROOT / '.omo/evidence/triposr-cpu-artifact-20261028/chair-attempt-1/chair-resolution256-original.glb'
OVERFLOW = ROOT / '.omo/evidence/triposr-preprocess-controlled-20261028/chair-preprocessed-resolution256-original.glb'
COMPLEXITY = 'GLB 모델이 너무 복잡해 가져올 수 없습니다. 더 단순한 정적 GLB 파일을 선택하세요.'
FORMAT = '지원하지 않거나 손상된 GLB 모델입니다.'


def sha(data):
    return hashlib.sha256(data).hexdigest()


receipt = {'scope': 'actual loopback HTTP import, validation and persistence only; no model generation/native render/UI test', 'requests': []}
with tempfile.TemporaryDirectory(prefix='http-import-') as temp:
    server = app.server(Path(temp) / 'data', 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    receipt['origin'] = base
    try:
        def state():
            with urlopen(base + '/api/state') as response:
                return json.load(response)

        def post(action, **data):
            current = state()
            payload = dict(action=action, data=data, revision=current['revision'], request_id=uuid.uuid4().hex)
            request = Request(base + '/api/action', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json', 'X-Loretune-Token': current['token']})
            try:
                with urlopen(request) as response:
                    code, body = response.status, json.load(response)
            except HTTPError as response:
                with response:
                    code, body = response.code, json.load(response)
            receipt['requests'].append({'action': action, 'status': code, 'error': body.get('error')})
            return code, body

        def successful(action, **data):
            code, body = post(action, **data)
            assert code == 200, (action, code, body)
            return body

        successful('project', name='A', era='default', story=0)
        successful('shot', song='A', shot='shot', description='import preservation scenario')
        shot = state()['projects']['A']['shots']['shot']
        successful('take', song='A', shot='shot', shot_revision=shot['revision'], filename='original.png', content=base64.b64encode(png()).decode(), reason='existing selection', rights='직접 제작')
        shot = state()['projects']['A']['shots']['shot']
        successful('select', song='A', shot='shot', take=shot['takes'][0]['id'], shot_revision=shot['revision'])
        raw = VALID.read_bytes()
        asset = successful('scene_asset_import', song='A', filename=VALID.name, content=base64.b64encode(raw).decode(), rights='로컬 생성 검증용 표본')['scene_asset']
        saved = server.store.root / 'model-assets' / (asset['sha256'] + '.glb')
        assert asset['profile'] == 'gltf2-static-pbr-color-v2'
        assert saved.read_bytes() == raw
        receipt['valid_original'] = {'path': str(VALID.relative_to(ROOT)), 'sha256': sha(raw), 'metadata': asset['metadata'], 'saved_original_bytes_equal': True}

        def snapshot():
            current = state()
            return {'revision': current['revision'], 'projects': current['projects'], 'files': {
                str(p.relative_to(server.store.root)): sha(p.read_bytes())
                for folder in ('model-assets', 'assets') for p in (server.store.root / folder).rglob('*') if p.is_file()}}

        before = snapshot()
        assert before['projects']['A']['shots']['shot']['selected'] is not None
        (OUT / 'http-before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2))
        malformed_doc, binary = glb_parts(raw)
        malformed_doc['accessors'][0]['count'] = True
        cases = [('resource-overflow', OVERFLOW.read_bytes(), COMPLEXITY), ('malformed-count', pack_glb(malformed_doc, binary), FORMAT)]
        receipt['rejections'] = []
        for label, rejected, expected in cases:
            code, body = post('scene_asset_import', song='A', filename='rejected.glb', content=base64.b64encode(rejected).decode(), rights='로컬 생성 검증용 표본')
            assert code == 400 and body['error'] == '입력을 확인하세요: ' + expected, (code, body)
            after = snapshot()
            (OUT / ('http-after-' + label + '.json')).write_text(json.dumps(after, ensure_ascii=False, indent=2))
            assert before == after, 'rejection mutated project/revision/media assets'
            receipt['rejections'].append({'case': label, 'input_sha256': sha(rejected), 'input_bytes': len(rejected), 'status': code, 'error': body['error'], 'projects_revision_assets_selection_equal': before == after})
        receipt['result'] = 'PASS'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
        receipt['server_closed'] = not thread.is_alive()
        (OUT / 'http-result.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
print(json.dumps(receipt, ensure_ascii=False, indent=2))
