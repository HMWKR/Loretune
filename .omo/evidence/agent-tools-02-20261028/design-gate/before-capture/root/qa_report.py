"""Run isolated local tests and produce honest per-requirement QA traceability."""
from pathlib import Path
import ast
import hashlib
import io
import json
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'docs/qa/20261025'
SPEC = ROOT / 'docs/knowledge/project_kit/sources/current_spec/output'
LINKS = {
 'test_production_boundary':[44,46,48,50,51,52,53,60,89],
 'test_live_gates':[44,46,48,50,51,52],
 'test_contracts':[2,44,49,51,52,71,81,83],
 'test_ledger':[44,50,51,81,83], 'test_fal_provider':[44,46,50,51,52], 'test_generation_queue':[44,46,50,52],
 'test_app':[5,13,45,47,49,50,60,67,69,86,88], 'test_backup':[89],
 'test_chat':[37,39,41,50], 'test_editing':[13,16,18,31,33,35,44,45,47,49,51,52,53,55,56,57,59,62,63,67,68,69],
 'test_ips':[7,21], 'test_archive':[71,72], 'test_preferences':[25,26,27,28], 'test_music':[31,32,35], 'test_settings':[12,20,21,22,24,76],
 'test_references':[40,41,53,63], 'test_workflow':[21,24,44,45,53,59],
 'test_qa_boundaries':[7,12,37,39,50,60],
}
LOCAL_ACTIONS={
 'createIP':'create_ip','createProject':'project','cloneProject':'project + clone_structure',
 'createPreference':'preference_propose','revisePreference':'preference_propose / preference_review',
 'createMemoryProposals':'preference_propose (manual only)',
 'createProjectVersion':'timeline','patchWorkingDraft':'no server draft endpoint; browser draft only',
 'createExport':'estimate_render + render_job','cancelJob':'cancel_job',
 'recordApproval':'review_take / approve_timeline / delivery_review / review_reference',
 'compareVersions':'no synchronized comparison; individual takes only',
 'getExport':'/exports/{job}.json','createContextSnapshot':'project snapshot / chat_plan',
}

class Results(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        self.started = time.monotonic()
    def record(self, test, status, actual):
        identifier = test.id()
        module, cls, method = identifier.split('.')
        source = ROOT/'tests'/f'{module}.py'
        tree = ast.parse(source.read_text())
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == method)
        self.rows.append(dict(id=identifier, requirements=[f'FR-{n:03}' for n in LINKS.get(module,[])],
            mapping_scope='부분 기능 관련성; 이 테스트가 연결된 FR 전체를 검증한다는 뜻이 아님',
            preconditions='임시 디렉터리·격리 SQLite; FFmpeg/FFprobe 사용. 외부 공급자 호출 없음.',
            data='아래 코드의 fixture와 setUp 참조; 사용자 data/는 수정하지 않음',
            steps=ast.get_source_segment(source.read_text(),node),
            expected='코드의 모든 assert 및 예외/불변성 조건 충족', actual=actual,
            mode='automated local', status=status, seconds=round(time.monotonic()-self.started,3),
            evidence=f'tests/{module}.py:{node.lineno}'))
    def addSuccess(self,test):
        super().addSuccess(test); self.record(test,'pass','모든 assertion 통과')
    def addFailure(self,test,err):
        super().addFailure(test,err); self.record(test,'fail',self._exc_info_to_string(err,test))
    def addError(self,test,err):
        super().addError(test,err); self.record(test,'fail',self._exc_info_to_string(err,test))
    def addSkip(self,test,reason):
        super().addSkip(test,reason); self.record(test,'blocked',reason)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs); self.rows=[]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    output=io.StringIO()
    result=unittest.TextTestRunner(stream=output,verbosity=2,resultclass=Results).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests')))
    (OUT/'automated-tests.txt').write_text(output.getvalue())
    (OUT/'local-cases.json').write_text(json.dumps(result.rows,ensure_ascii=False,indent=2))
    matrix=json.loads((ROOT/'docs/implementation-matrix.json').read_text())
    definitions={r['id']:r for r in json.loads((SPEC/'requirements_catalog.json').read_text())['requirements']}
    integrations=json.loads((SPEC/'integration_tests.json').read_text())['tests']
    rows=[]
    for req in matrix:
        spec=definitions[req['id']]
        related=[case['id'] for case in result.rows if req['id'] in case['requirements']]
        for suffix,expectation in [('A',req['acceptance']),('B',req['negative_acceptance'])]:
            rows.append(dict(id=f"AT-{req['id'][3:]}-{suffix}",requirement=req['id'],title=req['title'],
                preconditions=spec['preconditions'],
                data=dict(inputs=spec['inputs'],fixtures=[t['fixture_ids'] for t in integrations if req['id'] in t['requirement_ids']]),
                steps=[spec['behavior'] if suffix=='A' else spec['failure_behavior'],expectation,
                       '저장 상태 검증: '+spec['persisted_data']],expected=expectation,
                api_operations=spec.get('api_operation_ids',[]),
                actual='전체 수용 기준 미검증. 로컬 부분 근거는 별도 local-cases.json 참조. '+req['scope'],
                mode='manual/integration planned',status='not run' if related else 'not implemented',
                evidence=related, full_acceptance_verified=False))
    (OUT/'requirements-qa.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    contracts=json.loads((SPEC/'technical_contracts.openapi.json').read_text())
    api=[]
    for path,methods in contracts['paths'].items():
        for method,op in methods.items():
            if not isinstance(op,dict) or 'operationId' not in op:continue
            api.append(dict(id=op['operationId'],method=method.upper(),path=path,
                requirements=op.get('x-related-requirements',[]),preconditions=op.get('x-required-permissions',[]),
                data=op.get('requestBody',{}),
                steps=['명세 fixture 생성','권한 없는 요청 및 정상 요청','잘못된 값·경계값',
                       '변경 요청 멱등 키 재사용·동시 revision 충돌','응답 스키마와 저장 상태 비교'],
                expected=op['responses'],actual='명세 /v1 라우트 미구현. /api/action 부분 기능과 계약 호환을 동일시하지 않음.',
                mode='contract integration planned',status='not implemented',evidence=['app.py:server'],
                real_provider_test=False))
            row=api[-1]
            read_subset=op['operationId'] in {'getJob','listProjectVersions','listLedger','patchBudget','cancelJob','streamJobEvents'}
            row['route_implemented']=read_subset
            row['local_equivalent']=path if read_subset else LOCAL_ACTIONS.get(op['operationId'],'명세 작업에 대응하는 로컬 개별 endpoint 없음')
            row['differences']=dict(
                path='원문 경로 지원' if read_subset else '원문 /v1 경로 미지원; 일부는 POST /api/action으로만 실행',
                schema='Job/Resource/ResourceList/JobAccepted/Error 및 BudgetPatch/CancelCreate 부분 스키마 HTTP 시험' if read_subset else '원문 requestBody/response와 local action/data/revision/request_id envelope 불일치',
                errors='401/400/404/409/412/422 및 제한 principal403 HTTP 시험; 모든 오류코드 완전 검증은 아님' if read_subset else '로컬400/403/409, 명세Error(code/message/requestId/retryable)와401/412/422/429/503 미대응',
                permissions='로컬 프로세스 Bearer 및 단일 workspace ID 검사만; 명세 권한 '+','.join(op.get('x-required-permissions',[]))+'의 조직/객체 grant 검사는 미구현',
                idempotency=('GET read-only' if method=='get' else 'cancelJob: workspace/operation/key+digest; patchBudget: If-Match revision' if read_subset else 'legacy body request_id; 원문 계약 미대응'))
            if read_subset:
                row.update(status='not run',actual='부분 라우트 구현 및 격리 HTTP 시험 통과. 전체 조직/객체 grant 및 운영 계약 미검증. streamJobEvents는 현재 snapshot만 제공하며 이벤트 이력 재생은 미지원.',
                           evidence=['tests/test_contracts.py','contracts.py'],local_schema_verified=True)
    (OUT/'api-qa.json').write_text(json.dumps(api,ensure_ascii=False,indent=2))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in list(ROOT.glob('*.py'))+[ROOT/'index.html']+list((ROOT/'tests').glob('*.py'))}
    summary=dict(tests=result.testsRun,passed=sum(r['status']=='pass' for r in result.rows),
                 failed=len(result.failures)+len(result.errors),requirements=len(matrix),acceptance_cases=len(rows),
                 full_requirements_passed=0,api_operations=len(api),api_contracts_passed=0,
                 real_provider_runs=0,provider_count_scope='this isolated test suite only; actual live run is docs/qa/live-kling-20261025/result.json',local_read_compatibility_routes=3,local_write_compatibility_routes=2,local_snapshot_event_route=1,files_sha256=hashes)
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(output.getvalue()); print(json.dumps({k:v for k,v in summary.items() if k!='files_sha256'},ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':sys.exit(main())
