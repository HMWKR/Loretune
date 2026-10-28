# 이미지 어댑터·비용 대조·craft 통합 결과

2026-10-25 13:21 UTC 고정. 원본 앱에 통합 완료. **259개 전체 테스트 통과**, 변경 Python AST 및 inline JavaScript 3개 구문 검사 통과. 이는 기능 전체 완성률이나 실제 공급자 통합 성공률이 아니다.

## 1. 이번에 완료한 코드

- `runway_provider.py`: 기존 명세에 등장하는 **Runway gen4_image** 한 경로의 실제 HTTP 어댑터. POST `/v1/text_to_image`, GET `/v1/tasks/{id}`, `X-Runway-Version: 2024-11-06`. 텍스트와 최대 3개 PNG 참고를 제한된 1080p 비율로 요청한다. 모델은 registry에서 `integration_unverified`, 연결 없음으로 유지했다. 사용자 선택/default를 바꾸지 않았다.
- `image_pipeline.py`: 기존 applied plan → immutable action → 사람 승인 grant → 같은 예산 예약 → 같은 generation queue → 결과 수집 → Asset/Take 등록을 연결했다. 외부 제출 직전에 현재 자산 권리·해시·grant·미디어 모델·가격·샷 revision을 다시 검사한다. 채팅 모델만 바꾸는 경우 기존 미디어 승인을 유지한다.
- `generation_queue.py`, `editing.py`, `media_bridge.py`, `action_execution.py`, `app.py`: 이미지 job의 출력 종류·영수증·등록 및 worker 연결을 추가했다. 파일은 MIME/크기/매직/해상도/실제 디코딩을 검사한 뒤 저장한다. API 키는 다운로드 요청에 전달하지 않고 redirect를 따르지 않는다. 결과를 선택하거나 승인하지 않는다. 시작/끝 프레임 역할을 임의로 스타일/인물 역할로 해석하지 않는다.
- `provider_billing.py`: 저장된 fal billing record와 Runway task cost를 원장에 대조하는 서버용 hook. 요청/모델/워크스페이스/예약 귀속, 동일 기록 멱등성, 동시 대조, nano USD 정밀도, 늦은 청구·상충 기록을 처리한다. fal 집계 usage는 **추정**으로만 저장한다. Runway credits는 **공급자 보고 credits**이며 USD 청구서로 바꾸지 않는다. 실제 기록을 가져오는 인증 호출이나 계정 변경은 하지 않았다.
- `index.html`: craft 패치 통합. 비용·mock·승인 정보는 드러내고 반복 설명/영수증은 disclosure로 정리했다. 진행 중 영수증과 오류는 자동으로 펼친다. 추가로 카드/프로젝트별 disclosure 상태를 보존하여 polling/새로고침 후 사용자가 열었던 영수증이 닫히지 않도록 했다. 기존 F07 검토 초안 보존 코드와 실행 핸들러는 유지했다.

새 이미지 후보는 실제 provider HTTP 코드를 갖고 있지만 **일반 사용자에게 활성화된 이미지 생성 기능은 아니다**. `Store.image_pipeline` 기본값은 `None`이다. trusted server injection으로만 계약 테스트를 수행했으며 이미지 활성화/입력 승인 UI와 운영용 연결 설정은 아직 없다.

## 2. 공급자 선택과 공식 계약

원본 `01_business.md`와 확장 `07_Chat_Directed_Multimodel_Production_Spec.md`의 gen4_image 예시를 좁은 기술 후보로 사용했다. 예시를 최종 제품 선택이나 유료 호출 승인으로 해석하지 않았다.

공식 근거(2026-10-25 확인):

- [Runway OpenAPI](https://docs.dev.runwayml.com/openapi.json): endpoint, 입력, task 상태, terminal cost 계약. 원문과 발췌를 이 디렉토리에 보존했다. SDK 설명의 `CANCELED`와 OpenAPI의 `CANCELLED` 차이는 machine schema 기준으로 처리한다.
- [Runway 가격](https://docs.dev.runwayml.com/guides/pricing/): gen4_image 1080p 8 credits, 1 credit $0.01 기준 **$0.08 예상**. 실제 계정 구매·세금·청구 금액 검증은 아니다.
- [Runway 출력](https://docs.dev.runwayml.com/assets/outputs/): 출력은 24–48시간 유효한 서명 URL이며 자체 저장소로 회수해야 한다. **fal의 본인 private ACL·1시간 만료와 같은 정책이 아니다.** live 사용 전 이 정책 및 Runway 선택을 별도로 확정해야 한다.
- [fal Billing Events](https://fal.ai/docs/platform-apis/v1/models/billing-events): 요청별 USD 비용과 request ID를 제공한다. 이를 받는 hook만 구현했다. [fal Usage](https://fal.ai/docs/platform-apis/v1/models/usage)의 집계값을 개별 요청 실제 비용으로 배분하지 않는다. 읽기 권한 확인·키 확대·실제 조회는 미실행이다.

Runway DELETE task는 완료된 결과를 삭제할 수도 있으므로 접수 후 취소를 지원한다고 표시하지 않는다. 접수 전 취소만 가능하다. 출력 CDN은 승인된 정확한 host allowlist가 필요하며 기본값은 비어 있다. 테스트의 공식 예시 host가 실제 계정 결과 host라는 주장은 하지 않는다.

## 3. 테스트와 발견·수정한 결함

`test-matrix.json`에 신규 이미지 14개/비용 9개 시험 이름과 증거 등급을 기록했다. 실제 SQLite·파일시스템 및 합성 HTTP 응답을 사용하며 실제 외부 생성 호출은 0이다.

| 범위 | 결과와 한계 |
|---|---|
| 이미지 제출→조회→다운로드→Take 등록 | 계약 시험 통과. `roundtrip-evidence.json`에 한 action/grant/job/reservation과 미선택·미승인 Take를 기록. 실 Runway 생성은 미실행 |
| 중복·동시 실행, 변경된 권리/grant/미디어/가격 | 제출 1회 및 제출 전 차단 통과. 채팅 변경만 허용하는 대조군 포함 |
| timeout/응답 불명·재시작 | 기존 request/예약 보존, 자동 재발행 없음 |
| 다운로드 301/401/403/404/410/429/503·잘린 파일·MIME/크기/해상도 | 유한 실패 처리, 키 비전달, 잘못된 파일은 Take 등록 안 됨 |
| DB 등록 실패/rollback | request 보존 및 차단 상태. 정상 복구 UI가 구현됐다는 의미는 아님 |
| 기록 비용 대조 | 중복 청구 방지, 귀속 불일치 거부, 추정/실기록 분리, 상충 금액 수동 검토 |
| F07 초안 race | 기존 실제 JS+지연 fake fetch 회귀 통과. 이번 브라우저에서 네트워크 지연을 주입한 재현은 하지 않음 |
| craft disclosure | 신규 실제 renderer JS 시험 및 브라우저 새로고침 보존 통과. 준비된 job 영수증 자동 펼침 확인 |

첫 이미지 시험에서 probe의 `kind=image`가 실제 이미지 stream 검사와 맞지 않아 수집 실패를 발견했다. video stream 기반 이미지 디코딩 검사와 기대 해상도 검사를 연결해 수정했다. 첫 전체 시험은 synthetic ontology fixture 누락 1건이 있었으며 fixture를 staging에 반입한 뒤 재실행했다. 각각의 초기 실패 로그도 보존했다. 최종 staging 258/258, 통합 후 disclosure 회귀를 포함해 **259/259**이다.

## 4. 통합 브라우저 실제 흐름

격리 QA 데이터 경로 `/tmp/loretune-ms-qa-20261025`, 새 프로젝트 **이미지·원장·craft 통합 QA 20261025**에서만 조작했다. 기존 프로젝트·사용자 파일은 삭제하지 않았다. 새 합성 440Hz 2초 음원과 로컬 단색 mock 후보를 사용했다.

1. 음원 연결 → 음악 미확정 상태에서 계획 v1 저장. 승인 버튼이 disabled이며 입력을 보존함을 확인.
2. 0–2초 구간 확정 → 계획 v2 검토·승인 → 샷 1 생성. v1의 미확정 상태는 그대로 보존.
3. `$0 모의 작업 승인` → prepared 영수증 → 실행 → 후보 등록. AI 아님/외부 전송 없음/로컬 연산비 미계측 표시를 확인.
4. 후보 승인과 Take 선택을 따로 수행. 검토 초안 작성·새로고침 후 Take 선택/승인/영수증 펼침/초안 복구 확인.
5. 타임라인 저장·승인 전 출력 시도는 차단되고 오류 disclosure가 펼쳐짐. 입력은 유지.
6. 한국어 자막 0–2초 저장 → 타임라인 승인 → 버전·음원·자막·비용 확인 dialog → 로컬 렌더 → 결과 검토/납품 승인.
7. 새로고침 후 완료 출력과 승인 상태 재개. 브라우저 MP4 readyState 4, 1920×1080, 2초, 재생 입력 반응 확인.
8. 320/390px에서 문서 scrollWidth=viewportWidth. 장면/미리보기/검토 전환, ArrowLeft/Home 키 선택 확인. 임시 viewport는 복원했다. 실제 200/400% browser zoom·스크린리더·전체 키보드만 완주는 이번에 검증하지 않았다.

출력 `ui/integrated-final.mp4`는 2.000초, H.264 1920×1080 24fps, AAC 48kHz mono, mov_text 한국어 자막이다. 자막 cue는 정확히 0–2초이며 추출 SRT와 일치한다. PCM 96,000 samples와 마지막 50ms의 비무음 RMS를 확인했다. 프레임 fixture가 단색 정사각형이므로 16:9 출력의 좌우 레터박스는 원본 비율 보존 결과다. **AI가 문장대로 기하학 영상을 생성했다는 결과가 아니다.**

이 브라우저의 `textTracks`는 0이었다. 내장 MP4 자막은 파일 검사와 별도 SRT로 검증했으며 브라우저 영상 위 자막 표시를 확인했다고 주장하지 않는다. 향후 WebVTT 미리보기 연결이 필요한 로컬 UX 한계다. 청각 품질이나 고객 만족 테스트도 수행하지 않았다.

## 5. 원본 통합·고정 증거

- 이전 HTML baseline: `be3ff1634a396e378d320cb32020f94a9332e643d2128b5c92209af312ababf5`.
- staging patch: `implementation.patch`, SHA256 `20cd68f32bf9ce212bee3afe5a1eee93a78c42f096ad3f95f73b0c548faa2d0d`. main 변경 전 baseline 대조·dry-run 및 `before-integration/` 백업 완료.
- craft 원본 감사/후보 파일은 변경하지 않고 index에 통합했다. 기존 사용자 DB/.env/.codex 복사·수정 없음. 추가한 것은 QA 프로젝트와 synthetic 자산이다.
- 정상 실행 경로로 localhost 8773 재시작 완료. `fixed-release.json`에 모든 변경 파일 해시/실행 세션/검사 결과 기록.
- 최종 HTML source=served SHA256: **4f1805f00abb1ba2b5f7d6012727b4736e97cd4c35a007942ef6550781ae30dd**.
- 전체 회귀: `integrated-full-regression-approved.log` 259 tests / 31.020초 / OK. 마지막 모델 안내 문구 수정 후 재실행했으며 이후 소스 변경 없음.
- 최종 MP4 SHA256: `cab7433c888ad4579067e20906d6e6b4034b208cf503669408594e4f16fc4509`.
- 화면: `ui/integrated-desktop.png`, `ui/integrated-mobile390.png`, `ui/integrated-mobile320.png`.

## 6. 남은 범위 — API만 남았다고 판단하지 않음

| 구분 | 남은 항목 |
|---|---|
| 구현됐지만 live 미검증 | Runway 이미지 submit/status/collect·공용 queue/asset/권리 검사. registry 비활성 유지. 실제 key/요청/청구/host 검증 없음 |
| 제품·승인 결정 필요 | 이미지 provider의 최종 선택. Runway를 택한다면 별도 credential·전송/서명 URL 보관 정책·소액 시험 승인이 필요. fal만 사용하려면 별도 공식 image endpoint 선택 필요 |
| 로컬 코드/UX 후속 | 결정된 이미지 provider를 일반 승인 화면에 연결하는 준비/활성화 경로, 권한 거절 이후 안전한 image recovery UI, 브라우저 자막 preview. 이들을 외부 API 장애로만 분류하지 않음 |
| 실제 기존 영상 통합 차단 | fal Kling 결과 접근 문제 미해결. 과거 CDN403/후속 token403을 구분해 유지. 거절·만료 URL 재접근 및 추가 생성 없음 |
| 비용 연동 경계 | recorded record 대조 hook 완료. 계정의 authenticated billing fetch/scheduling/권한 확인은 미연결. receipt 없는 금액을 실제 청구로 만들지 않음 |
| 단일 사용자 로컬 MVP 밖 | 공용 다중 사용자 인증·조직 RBAC/운영 격리, 외부 배포·대규모 큐/부하, 모든 12개 모델 조합, 제품 수준 음악 자동 분석·립싱크/고급 편집 |
| 원본 전체 명세 | 96FR/143API와 28MS-FR/38MS-AT 전체 완료를 선언하지 않음. 이번 테스트 이름을 수용 기준 전체 pass로 치환하지 않음 |

이번 작업 유료 이미지/영상/Anthropic 호출 **0**, 키 읽기 **0**, 외부 배포 **0**. 기존 Anthropic 누적 usage 가격 계산치 $0.0077580은 과거 기록이며 이번에 변동 없음(실청구 미확인). 기존 Kling 비용 기록을 정정하거나 새로 정산하지 않았다.

마지막 화면 검사에서 모델 미선택 시 표시되던 “이미지 어댑터가 없다”는 이전 안내도 실제 상태(계약 후보 구현·실제 연결 미검증)로 수정했다. 기본 sandbox로 실행한 마지막 전체 테스트는 localhost bind 17건이 미실행되어 실패했다. 기존 사용자 승인에 따른 정식 localhost 실행 경로에서 259개가 모두 통과했다. 다른 host나 방화벽 변경으로 우회하지 않았다.

단일 사용자 로컬 제작 검증은 완료했지만 실제 이미지 live와 영상 회수, 일부 local UX/activation 및 출시 운영 검증이 남는다. 이번 고정 버전은 **통합 QA checkpoint**이며 production 무결함 또는 MVP 전체 완료 판정이 아니다.
