# 멀티모델·제작 도구 + creator UI 원본 통합 완료

기준: 2026-10-25 UTC. 범위는 승인된 로컬 구현·합성 검증이다. 실제 외부 공급자/키/유료 호출 0. 원본 문서·사용자 데이터·기존 실제 과금 기록을 변경하지 않았다.

## 고정 결과

- 최신 19파일 서버 패치와 `creator-pass/integration-creator.patch`를 실제 `/Users/leesungmin/Desktop/Loretune`에 적용했다. staging-only 결과가 아니다. 적용 전90개 source/test baseline drift0와 두 patch dry-run을 확인했고 `before/`에 소스만 보존했다.
- MM01 읽기 문맥 결함과 제안 카드/API 연결을 추가했다. 최종 baseline 대비25개 소스/시험 파일 변경은 `fixed-runtime.json`에 before/after 해시로 기록했다.
- 전체 **311 tests / 311 pass, 40.855초**. localhost HTTP, fake provider 계약, 실제 SQLite/파일/FFmpeg 포함. Python98파일 AST, inline JavaScript `node --check` 통과. 이 숫자는96FR/143API 또는38MS-AT 완료율이 아니다.
- 일반 앱 서버 `http://127.0.0.1:8773`, QA 데이터 `/tmp/loretune-ms-qa-20261025`, 실행 세션23112. 시험용 fake chat 런처 종료 후 `python3 app.py --port 8773 --data /tmp/loretune-ms-qa-20261025`로 정상 재시작했다. 현재 fake chat 활성화0, 외부 모델 활성화0.
- source/served index SHA256: `1b0ab597f7a16993cf9307ae4a5fdd948b7ed5948c2970b16b7d53670ef269b3`.
- app.py SHA256: `9d316c8269e0addfca609065912630b45b196107a84d86f3f997f0a75861c582`.
- source/test tree SHA256: `7a726330c464ba882e39e6871177f152768df36400597b39a0cd6ccbb3b2421d`. 파일별 목록과 고정 시각은 `fixed-runtime.json`. 이 체크포인트 이후 소스 수정 없음.

## 기능과 안전 경계

Anthropic Messages와 OpenAI/xAI Responses 어댑터를 동일 chat tool runtime에 통합했다. 현재 catalog는 Haiku5.5 / gpt-6-luna / grok-4.7이며 계정 가용성·실제 모델별 연결을 검증한 것이 아니다. fal 이미지 Schnell/FLUX Pro1.1, 영상 Kling2.6Pro/2.5Turbo 계약은 같은 queue/권리/다운로드/Take등록 경로를 사용한다. 모델 변경 시 다른 모델이나 fake로 대체하지 않는다. 4개 미디어 계약은 합성 HTTP 결과로만 검증했다. Runway·Higgsfield·MCP는 활성 연결 경로가 아니다.

`propose_timeline_edit`는 제안만 저장하고 사람 승인으로 기존 Store.timeline 경로에 새 버전을 만든다. 다른 컷·음원·자막을 보존하며 출력 승인은 별도다. UI의 '적용 전 직접 수정'은 로컬 초안을 열고 '편집 초안 취소'는 저장본으로 돌아간다. 제안 보류/거절/기준 버전 변경은 기존 서버 계약을 유지한다.

`propose_memory_update`는 정확한 출처 발췌·작품 범위·revision을 검증해 기존 ontology 후보를 만든다. UI의 '근거·설정 검토'에서 기존 사람 승인 서비스를 사용한다. 모델의 승인 플래그로 canon을 바꾸지 않는다. `request_render`는 이미 승인된 편집을 기존 estimate/render worker로 접수하며 완료 파일·최종 납품 승인을 별개로 표시한다.

내부 ID/hash/grant/tool trace는 일반 카드에서 숨기고 진단 disclosure/서버 증거에 보존했다. 모델 선택, 실행 가능 여부, 비용 범위, 사람 승인, 시험 미디어, 실패·재개 사실은 유지했다. 없는 실행에 활성 버튼을 만들지 않았다.

## MM01(P1) 수정과 좁은 재감사 요청

`production_context.py`를 handoff와 `search_project_context`가 공유한다. 현재 작품에 속한 stable shot ID/name/revision/Take, EDL·음원·자막 버전, 유효 사람 출력승인, 아직 미접수인 action과 유효 grant를 읽기 전용으로 제공한다. fal prepare는 동일 mapping으로 stable shot UUID를 해석한다. 모호하거나 다른 작품에 속한 값은 거절한다. 경로·credential·provider URL은 포함하지 않으며 실행 시 소유권/존재/version/권리/가격 검증을 유지했다. 승인 snapshot/hash에 새 projection을 넣어 임의 invalidation을 만들지 않았다.

`tests/test_execution_context.py`의3개 회귀는 모델 변경 후 조회 결과만 사용한 render, 승인되었으나 미접수인 action/grant를 찾아 재사용, stable UUID preparation, foreign/ambiguous rejection을 확인한다. 전체311에 포함. 부모가 원 독립 재현을 **현재 고정 소스에 좁게 재검증**할 수 있다. 원 감사 보고서는 수정하지 않았다. 자세한 경로는 `MM01-fix.md`.

## 실제 브라우저 합성 여정

기존 허용된 QA 데이터에 새 작품 `QA 통합 제작 20261025`만 생성했다. 전용 공간15/p1을 사용하고 종료 시 `finish({keep:[]})`로 닫았다. 개인 공간/탭을 조작하지 않았다.

| 시나리오 | 실제 관찰 결과 | 증거 |
|---|---|---|
| 모델 선택 | 채팅3/이미지2/영상2가 독립 표시, 연결 확인 필요/기존 Kling 차단 표시. 선택 저장과 실행은 별개 | 브라우저 옵션 읽기, 계약 tests |
| 채팅→공통 도구→최종 답변 | 정확한 합성 요청1건, fake response3회. search→계획/편집/기억 제안→실제 저장 receipt를 받은 최종 문장 | `synthetic-tool-trace.json`, `local_ui_fixture.py` |
| 계획 사람 승인 | 승인 전2개 원본 장면 유지; 승인 후 새 장면2개 추가, 원본2개 보존 | `01-plan-and-memory.png`, DB evidence |
| 테스트 후보 | 승인 전 후보0→$0 사람 승인→명시 실행→새 후보 Take1→사람 검토 승인→별도 선택 | DB execution_cards/rehearsal_jobs |
| 선택/검토/편집 분리 | 새 후보 선택이 기존2컷 편집이나 출력 승인을 대체하지 않음 | DB timeline v1/v2/shot selected |
| 제안 직접 수정·취소 | 첫 컷 trim0.125 초안 표시; 취소 후 trim0 복원, 새 저장 버전0 | UI 관찰 |
| 편집안 사람 적용 | v1→v2, 첫 컷 trim만0.125. 두 번째 컷1초·음원1·자막 보존. 출력 승인 초기화 | `browser-data-evidence.json` |
| 출력 | 새 v2 사람 승인→확인 대화상자→실제2초 MP4→파일 준비됨→별도 납품 승인 | `02-output-caption-desktop.png`, `07-caption-visible.png` |
| 기억 제안 | 정확한 'Mira wears a blue coat.' 출처 확인; 사람 승인 전ontology0→승인 후1 | DB ontology entities/revision |
| 두 Take 비교 | 합성 orange.png를 새 Take2로 로컬 연결. Take1승인/선택과 Take2검토대기/미선택이 구분되고 기본 양쪽이 서로 다름 | `03-distinct-take-comparison.png` |
| 검토 초안 격리 | Take1 미저장 메모 작성→Take2는 빈 메모/미정 결정→Take1 복귀 시 원래 초안 복원→취소 | 실제 UI + 기존 F07/컨텍스트 unit 회귀 |
| 키보드 대화상자 | 비교 Escape 후 포커스가 'Take 나란히 비교'로 복귀 | 실제 focus 읽기 |
| 좁은 화면 | 390/320 CSS px에서 panel 전환, document scrollWidth가 각각390/320 | `05-mobile-390.png`, `06-mobile-320.png` |
| 새로고침·프로세스 재시작 | 계획/4장면/Take/ontology1/timeline2/MP4/납품 승인 보존, 일반 앱 fake chat 연결0 | `08-normal-server-reopen.png`, DB evidence |

저장 응답 지연 중 새 초안 보존(F07), cross-project/context, idempotency, 승인 위조/중복/권리 철회는 전체 unit/HTTP 회귀에서 검증했다. 이번 브라우저에서 지연 응답을 새로 주입한 것은 아니다. 실제200/400% browser zoom, screen reader, 고객 사용성 시험은 수행하지 않았다. viewport 축소를 실제 zoom으로 세지 않았다.

## 최종 미디어 측정

`verified-integrated-output.mp4`는 실제 AI가 아닌 합성 이미지2컷과 sine 음원이다. H.264 640×360 /24fps /2.000초, AAC2.000초, mov_text Korean subtitle0–1.5초. 브라우저의 승인v2 WebVTT cue도 같은 시간과 'Mira의 합성 자막'으로 loaded/showing/active임을 확인했다. Audio RMS0.0882744125로 무음이 아니다. 실제0.5초 프레임 RGB[0,0,255],1.5초 [254,165,0]으로 두 컷 순서를 확인했다. MP4 SHA256 `53de21ee3cfe32dce630e73e123d2c91719dcee99063070f003f801bf0b2c488`.

`08-normal-server-reopen.png`는 재개/자막 표시 증거다. seek 직후 캡처 프레임의 정확한 시간 검증에는 사용하지 않는다. 컷 순서는 FFmpeg frame sample 증거를 사용했다. 로컬 SRT/manifest도 함께 보존했다.

## 발견·수정 및 남은 경계

이번 통합 최초 전체 회귀2오류는 creator helper를 빼고 함수를 추출한 옛 UI 시험과, 제거된 가짜 활성화 버튼/내부 상세 자동펼침 기대값 때문이었다. harness를 현재 실제 렌더링에 맞추되 사용자에게 보이는 비용·진행·오류 사실 검증은 유지했다. 초기 로그 `regression-initial.log` 보존. 최종311pass.

실제 화면에서 후보 승인 후 상단 '검토 필요'가 남는 표시 결함을 수정했다. 승인/거절 상태별 문구와 회귀를 추가했다. 적용한 편집안에 출력 재승인을 계속 요구하는 문구도 현재 타임라인 승인 상태를 확인하도록 정정했다. 마지막 수정 뒤 전체311과 정적 검사 통과.

**아직 외부 API만 남았다고 판정하지 않는다.**
1. 새 `media_actions`는 현재 creator 화면의 읽기용 요약과 도구 receipt로 통합됐다. 실제 fal action의 일반 사용자용 견적/권리/승인 제출 UI와 새 dispatcher의 collection recovery 조작은 아직 추가 연결이 필요하다. 기존 $0 후보 카드는 별도의 로컬 테스트 기능이다.
2. 기존 `이미지 모델·기존 결과`의 legacy `image_connection` 패널과 새 모델 registry가 별도다. 새 fal 모델을 선택해도 legacy 패널은 '이미지 모델 미선택'으로 표시될 수 있다. 실제 활성화를 주장하지 않으나 이 문구/새 recovery 경로 통합은 남은 구체적 UI 결함이다.
3. 실제 OpenAI/Grok/fal 이미지 및 새 영상 계약은 미검증·비활성. 각 계정/기존credential 사용·자료·예산·private 결과수신 승인이 필요하다. 기존 Kling CDN403과 후속 token403은 해결됐다고 하지 않는다. 재접근0.
4. 모델 카탈로그·어댑터 contract tests는12 live 조합을 대체하지 않는다. 프로젝트/작업 선택을 넘어 조직/서비스/default 영속화, 일반 사용자 live chat 범위는 full-spec 후속이다. 이번 고정 릴리스에 multiuser/배포 인프라를 추가하지 않았다.
5. MM01 독립 재감사와 고정 화면의 디자인 재평가가 아직 남았다. 통합 후 캡처를 직접 확인했지만90/100을 선언하지 않는다.

이번 실제 Anthropic/영상/이미지 추가 호출0. 이전 Anthropic usage가격 계산 총액 `$0.0077580` 변경0, 실청구는 별도 미확인. 이번 fake trace의 `$0.00036`은 **모의 사용량**이며 실제 비용 원장에 합산하지 않는다.

현재 새로 거절되거나 불확실한 외부 실행은 없다. 브라우저 조작 중 닫힌 disclosure/오래된 ref/잘못된 wait selector로 관찰 timeout이 있었으나 쓰기 요청을 반복하지 않고 상태를 읽어 확인했다. 프로세스 `ps`는 sandbox 거절되어 반복하지 않았고, 소유한 실행 세션의 정상 Ctrl-C와 DB 진행작업0 확인으로 재시작했다. Ego Lite 업데이트 안내가 있었지만 업그레이드는 하지 않았다.
