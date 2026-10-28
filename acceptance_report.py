"""Separate functional criteria from contract/identity and external validation gates."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'docs/qa/20261025'
spec=json.loads((ROOT/'docs/knowledge/project_kit/sources/current_spec/output/requirements_catalog.json').read_text())['requirements']
matrix={r['id']:r for r in json.loads((ROOT/'docs/implementation-matrix.json').read_text())}
fields=['preconditions','behavior','failure_behavior','acceptance','negative_acceptance']
render_criteria=[
 ('승인된 타임라인과 권리 스냅샷으로 렌더','tests/test_editing.py:test_unconfirmed_audio_rights_block_approval; test_frozen_job_survives_new_edit'),
 ('렌더 완료와 납품 승인을 분리','tests/test_editing.py:test_audio_captions_and_actual_render; 실제 job6c5a20d2 UI 검토 전→승인됨'),
 ('새 작품 기본1080p·지원 프리셋 정확한 수치 표시','tests/test_editing.py:test_supported_output_profiles_are_measured; index.html #profile'),
 ('미지원4K 거부·실패해도 승인 타임라인 불변','tests/test_editing.py:test_supported_output_profiles_are_measured; test_changed_asset_fails_job'),
 ('출력 길이·해상도·24fps·48kHz·자막이 승인사양과 일치','tests/test_editing.py:test_supported_output_profiles_are_measured; render-1080-record.json'),
 ('출력 캔버스 리사이즈를 원래4K 생성물로 표시하지 않음','index.html 리사이즈/AI업스케일미지원 설명; 지원 규격에4K없음'),
]
known={
 ('FR-031','negative_acceptance'):('met','test_audio_captions_and_actual_render: 새 음원 업로드 후 기존 timeline/audio version 보존'),
 ('FR-050','negative_acceptance'):('met','test_request_id_payload_mismatch_is_not_a_second_write: 동일 ID 다른 내용 Conflict·상태 불변'),
 ('FR-055','acceptance'):('met','test_versions_restore_and_approval_invalidation: 순서변경·이전 버전 복원·원본 불변'),
 ('FR-071','negative_acceptance'):('met','test_archive_freezes_edits_and_clone_resets_media_approval_budget: take/승인/음원/확인기록 초기화; UI-10'),
 ('FR-028','acceptance'):('partial','취향 중지 후 새 초안 문맥 제외·과거문맥 보존 시험 및 UI 완료. 실제 생성 적용/결과는 provider 미연결.'),
 ('FR-060','acceptance'):('partial','동일 revision의 동시 로컬 쓰기 충돌 거부. 실제 두 계정/클립 충돌 비교UI는 미구현.'),
}
external={43:'모델 제공자·모델ID·자격증명 선택 및 연결 승인',46:'승인된 테스트 음원/참고의 외부 전송·생성 예산 한도',48:'실제 생성 결과와 품질 평가 표본',54:'실제 제공자 장애/대체 경로 계정',70:'게시 대상 계정·공개/예약 게시 승인',74:'동의받은 평가자·실제 생성 표본',75:'실제 고객 사용 데이터',77:'비교할 모델 버전·실제 호출 예산',79:'실제 플랜/결제 제공자 계정',81:'제공자 원가/청구 내역 접근',82:'실제 차감/환불 기록',84:'결제 테스트 환경 계정',93:'외부 연동 대상·웹훅 자격증명 승인',94:'기업 IdP 테스트 계정',96:'가창 모델·인물자료 전송동의·생성 예산'}
rows=[]
for r in spec:
    row=dict(id=r['id'],title=r['title'],functional_criteria=[],
             functional_requirements_verified=False,
             release_gate_verified=False,api_operations=r.get('api_operation_ids',[]),
             api_gate='명세 API/조직·객체 권한 계약의 전체 검증 미완료',
             external_validation_approval=external.get(int(r['id'][3:])),
             local_work_remaining=matrix[r['id']]['scope'])
    for field in fields:
        status,actual=known.get((r['id'],field),('not verified','연결된 로컬 부분 테스트는 원문 전체 조건을 입증하지 않음. '+matrix[r['id']]['scope']))
        if r['id']=='FR-067':status,actual='partial','특정 fixture 근거만 검증됨. 독립 감사 F04 및 contract-fixes-20261025 반례 수정 범위 참조'
        row['functional_criteria'].append(dict(kind=field,original=r[field],status=status,actual=actual))
    if r['id']=='FR-067':
        row['atomic_criteria']=[dict(criterion=c,status='fixture_verified',evidence=e) for c,e in render_criteria]
        row['local_work_remaining']='기존 증거는 특정 fixture 범위다. 소수 컷 경계 수정 후 전체 기능 기준 재판정이 필요하다. createExport API의 ExportCreate·예산/권한 계약 바인딩은 별도 미완료.'
    rows.append(row)
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'criterion-decomposition.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
(OUT/'criterion-summary.md').write_text('''# 원문 기준 분해 결과

**FR-067은 부분 검증이다. 기존 6개 증거는 특정 fixture 범위이며 전체 허용 입력을 입증하지 않는다.** 승인 사양의 실제1080p·24fps·48kHz·음원·자막, 미지원 규격 거부, 실패 시 승인본 보존, 해상도 표현, 렌더와 납품 검토 분리를 코드와 실제 UI로 검증했다. 상세 근거는 criterion-decomposition.json의 FR-067이다.

이는 143개 API 계약과 조직 인가를 포함한 출시 게이트 완료를 뜻하지 않는다. **원문 전체 기능 기준 완료 0 / 전체 출시 게이트 완료 0**을 분리한다. 이전의 일괄0은 부분 시험과 기능 수용, API 바인딩을 구분하지 못했다.

다른 요구사항의 큰 미충족 원인은 실제 기능 누락이다. 예: FR-044는 로컬 원장·예약·미확정 유지가 추가됐으나 조직 예산/실청구 대사는 미검증이다. FR-051은 단일 생성의 취소·늦은 결과 보존을 fake로 검증했으나 다중샷 부분완료와 실제 공급자 과금은 미검증이다. FR-059는 동기 A/B 비교가 없다. FR-060은 로컬 optimistic lock만 있고 오프라인 편집초안/두계정 충돌 비교가 없다. FR-069는 로컬 제작기록만 있고 고객 권한/원본 재배포 정책이 없다. 외부 API키만 추가하면 해결되는 상태가 아니다.

모든96FR은 원문 사전조건·동작·실패처리·정상수용·반례를 각각 기록했다. met는 구체 근거가 있는 조건만, partial은 일부조건만, not verified는 원문전체를 입증하지 않은 조건이다. 외부 승인 필요 목록은 별도 필드이며 로컬 미구현을 외부 차단으로 바꾸지 않는다.

독립적으로 계속할 MVP 로컬 범위: 제공자 영구오류 분류/조회 종료, 승인 입력 해시 고정, 비공개 CDN 결과 접근, 10초 출력 파일 크기 처리, 전체 경로 키보드·반응형 및 저장복구 QA. 조직 권한/전체API/고급비교는 후속 범위. 외부 실제 시험에는 제공자/모델ID·보낼합성자료·호출수/최대금액·보관/공개조건을 확정한 승인과 자격증명이 필요하다. 사용자가 fal.ai Kling을 지정했으며 자격증명 조회/설정은 하지 않았다.
''')
print('96 FR criteria decomposed; functional criteria complete: none (fixture evidence only); release gates complete: 0')
