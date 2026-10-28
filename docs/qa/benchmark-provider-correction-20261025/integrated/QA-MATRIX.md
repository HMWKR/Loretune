# 통합 QA — 증거 종류별 결과

Baseline: `4f1805f0…1ae30dd` → integrated `0a8ef843…c6ae`. 전체 원문 MS 수용시험의 완료 판정과 아래 회귀 scenario 결과는 별개다.

| ID | 시나리오·기대 | 실제 결과 | 증거 종류·경로 | 판정 |
|---|---|---|---|---|
| Q01 | Runway 신규 선택/실행 불가, 과거 기록 보존 | catalog/resolver/stub/worker 차단 및 old job 조회 통과 | `tests/test_runway_image_pipeline.py` 5개 | pass/local |
| Q02 | 미설정 이미지 모델을 사용 가능으로 표시하지 않음 | UI 미선택·업로드 안내·실행 비활성 | `model-settings-1280.png`, `mobile-review-390.png`; `test_readiness_flags_never_enable_fake_or_read_environment` | pass/browser+fixture |
| Q03 | 403 복구는 새 관련 권한 근거와 일회 gate 필요 | scope/expiry/revoke/one-use 검증, 새 submit 없음 | `test_403_needs_new_matching_permission_evidence_and_one_use`, `test_gate_payload_scope_expiry_and_revocation_block_before_io` | pass/fake; live 미실행 |
| Q04 | 조회는 결과 수집/생성을 몰래 실행하지 않음 | 기존 receipt 조회만 1회, pending/unknown 비용 유지 | recovery status/restart/unknown receipt tests | pass/fake |
| Q05 | 비교 기본값 서로 다름 | 첫 장면 Take 2 대 Take 1 | `comparison.png`; `test-comparison.mjs` 5 controls | pass/browser+JS |
| Q06 | 장면·Take 전환 시 초안/결정 독립 | 첫 Take 2 새 초안, 두 번째 저장 승인, 첫 Take 1 기존 승인 구분 | 실제 전환·재선택·새로고침; `test-review-state.mjs` | pass/browser+JS |
| Q07 | 저장 중 새 입력을 이전 응답이 지우지 않음 | 제출 revision만 clear, 컨텍스트 바뀌어도 오염 없음 | `comment_draft_controls.js` 16 controls + review-state 9 controls | pass/exact-JS delayed fake fetch; 실제 browser delay 미실행 |
| Q08 | 선택/Take 승인/편집 사용/출력 승인 분리 | 선택 변경은 승인 이력 유지, timeline v3는 출력 승인 대기 | `studio-1280.png`, project before/after JSON | pass/browser+DB |
| Q09 | 승인 캡션과 출력 미리보기 동일 revision | v2 render/VTT/내장 SRT 같음 | `media-evidence.json`, `export-caption.png` | pass/browser+actual media |
| Q10 | 이후 v3 편집·재개가 과거 v2 출력에 영향 없음 | v3 미승인, 완료 output v2/hash 유지 | project after, `media-evidence.json` | pass/browser+media |
| Q11 | 3컷 4.5초 1080p 음악·한국어 자막 출력 | H264/AAC/mov_text 모두4.5초, 108frames, RMS>0 | 실제 job `7eda38fc…31eb`, ffprobe/SRT/VTT/RMS | pass/local media; 새 AI 생성 아님 |
| Q12 | 원본 Take·이전 리뷰 보존 | 6Take 동일, 기존 리뷰 prefix 유지 | `original_takes_unchanged`, `earlier_reviews_preserved` | pass/DB diff |
| Q13 | 320/390px 패널 전환·reflow | document overflow0, 내부 전용 스크롤 유지 | mobile 두 screenshot | pass/browser viewport |
| Q14 | 모델 dialog Escape·focus return | close 후 `모델 설정`에 focus | CUA DOM read, fixed-release.json | pass/browser |
| Q15 | 200/400% 실제 zoom·screen reader·전체 keyboard 완주 | 실행 안 함 | viewport 검사와 구분 | not_run |
| Q16 | 문서 registry에28FR/38AT·원문·계보 보존 | 양쪽rev9/1772objects/982heads, 기존1666objects+882heads 동일 | registry baseline/CLI mutation/strict-validation logs | pass/registry; 38AT 전체 not_run |
| Q17 | 최종 원본 회귀·소스/served 일치 |277pass, 0failure, HTML hash동일 | main-full-regression.log, fixed-release.json | pass/local |
| Q18 | 실제 새 이미지/video 생성·billing 청구대조 | 수행하지 않음 | 활성화0, 키조회0, 새유료호출0 | blocked/unselected or unverified |

기능 범위 밖의 디자인 점수·사용자 성공률·production 신뢰도를 위 pass 수로 계산하지 않는다. 이번 browser pass는 기존 합성 media를 사용했다. 모의 후보 생성 및 권리/작업 복구는 fixture 테스트이며, 실제 외부 provider 성공으로 세지 않는다.
