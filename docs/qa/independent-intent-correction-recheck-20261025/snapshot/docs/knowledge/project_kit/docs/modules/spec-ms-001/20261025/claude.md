> 후속 갱신: 보강된 영수증의 실제 Claude 재검증은 완료됐습니다. [후속 결과](../claude-receipt-recheck-20261025/REPORT-ko.md). 누적 usage 계산$0.0077580. 아래 내용은 이전 시험 당시의 기록으로 보존합니다. 공급자 action 연결과 새 구조 UI는 [통합 체크포인트](../provider-action-bridge-20261025/REPORT-ko.md)를 참고하세요.

# 일반 채팅 UI → 실제 Claude → 계획·검토·로컬 작업 → 결과 조회

2026-10-25. **실제 Claude의 온톨로지 조회, 근거 답변, 계획 DB 저장, UI 승인 후 로컬 모의 후보 Take 등록, 그 저장 결과를 조회한 최종 답변까지 실행했다.** 최종 답변에서 계획 연결 정보 부족을 발견해 코드·계약을 보강했다. 보강된 영수증은 실제 저장 DB로 오프라인 검증했으며 Claude에 다시 전송하지 않았다. 그러므로 보강 후 최종 답변 품질까지 재검증 완료한 것은 아니다.

실제 사용자는 가상의 합성 프로젝트다. 사람 승인 경로는 사용자가 위임한 QA 에이전트가 UI로 조작했다. 실제 고객 사용자 실험이 아니다. 이미지 후보는 로컬 단색 PNG이며 **실제 AI 영상 생성은 0회**다.

## 실제 단계와 근거

| 단계 | 실제 결과 | 증거 |
|---|---|---|
| 일반 채팅 UI 제출 1 | 서버 turn `b49039e0508c437eadbc90721c67a1a0` 접수 | `browser-mutation-receipts.json`, `phase1-gate.json` |
| Claude 온톨로지 조회 | `search_project_context` tool_use → 서버 canonical revision 2 반환 → tool_result | `live-evidence.json`, request 기록 |
| 근거 답변·계획 쓰기 | 기본 파란 코트/곡 한정 빨간 코트 구분, 나이 모름, 실제 plan ID 인용 | `phase1-state.json`, `phase1-plan-answer.png` |
| 승인 전 상태 | 계획 proposed 1, 샷 0, action job 0, grant 0 | `phase1-state.json` |
| UI 계획 승인 | 저장된 plan v1 승인, 새 샷 1 추가 | browser receipts + DB diff |
| UI 작업 승인·실행 | $0 rehearsal 승인 → 단색 이미지 생성 → SHA 검증·로컬 파일·Take 1 등록 | `local-candidate.png`, `live-evidence.json` |
| 일반 채팅 UI 제출 2 | 서버 turn `7a97202aeeb5402aa2724e01e65d7fb6` | `phase2-gate.json` |
| Claude 실제 결과 조회 | canonical 조회 + `get_generation_job` → 실제 job/Take/hash/미승인/외부0회 확인 | tool_use/tool_result 실제 왕복 |
| 최종 답변 | 정확한 작업·Take·해시·결과 미승인, 실제 영상 아님을 명시. 근거에 없는 계획 연결·단색 여부는 확인 불가로 표시 | `final-answer-card.png`, `phase2-result-answer.png` |
| 재시작 | 실제 어댑터를 끈 기본 서버로 같은 저장소 재시작. 답변 2건, 계획/Take/작업 그대로, 새 API 요청 없음 | `final-runtime.json`, 실제 브라우저 재조회 |

**9개 저장·격리 검사는 모두 pass**: 완료 대화 2건, 계획 1개, 온톨로지 원본 불변, 사람 승인 전 job/grant 0, 최종 grant/job/Take 각1, 파일 hash 일치, 외부 미디어 호출0, 결과 미승인 보존, 타 프로젝트 저장 필드 불변. `live-summary.json` 참고.

초기 비교에서 Store의 읽기 전용 projection이 포함된 before와 raw DB after를 비교하여 foreign project false가 나왔다. 공통 영속 필드는 변경0이고 차이는 ontology/lineage/capability 등 계산 필드뿐임을 확인했다. 최초 판정은 `first-comparison.json`으로 보존했고 정정 근거를 숨기지 않았다.

## 실제 식별자

- 계획: `595787d6ebc649448d47843c8dbb4a3f`
- 로컬 모의 작업: `e6b8a59e35634dfba9811b99763fc2ac`
- 등록: 장면 1 / Take 1
- PNG SHA256: `7ca5909eefb620d62704cae14d64850dc7bf4cc21f6d05ca465300f800cd7a6a`
- 실제 Anthropic request IDs:
  - `req_011CgNv2n52a81Mdb5eajsyr` — 1단계 조회
  - `req_011CgNv3SsedF8jN8sbQRxHD` — 1단계 계획 도구
  - `req_011CgNv3j4EHSWyGjqvaMMDQ` — 1단계 최종 답변
  - `req_011CgNvBmRajQMN6gywvohNL` — 2단계 문맥·작업 조회
  - `req_011CgNvCE8g6wcamaRtNcGeW` — 2단계 최종 답변

실제 모델 request 5회 + 사전 count 5회. 자동 retry0, fallback0. 중복 제출은 런처의 attempt marker, 동일 prompt 제한, DB 요청 멱등성, 한 실행 worker claim으로 방지한다. 이번 2개 UI 제출은 서로 다른 단계와 입력이다. 유료 중복 호출 시험을 일부러 하지 않았으며 관련 부정 사례는 fake 회귀로 검사했다.

## 비용·전송·승인

모델 `claude-haiku-5-5`, input cap8,192/output cap4,096, 대화2건×최대4모델 응답. 사전 최악 예약 합계 $0.022944, 대화당 $0.012, 단계 $0.10, 개발 전체 $50. 기존 사용량을 같은 원장에서 유지했다.

| 비용 | usage×공식 단가 계산 | 보수적 micro-USD 원장 |
|---|---:|---:|
| 이번 대화1 | $0.0011368 | 각 응답 단위 올림 포함 |
| 이번 대화2 | $0.0011676 | 각 응답 단위 올림 포함 |
| 이번 합계 | **$0.0023044** | $0.002307 |
| 이전 포함 전체 | **$0.0072619** | $0.007267 |

**공급자 최종 청구서는 미확인**이다. [공식 Haiku 5.5 가격](https://platform.claude.com/docs/en/models/haiku-5-5/overview)의 100k 이하 입력 $0.10/MTok·출력 $0.50/MTok를 당일 확인했다. [공식 count 설명](https://platform.claude.com/docs/en/build-with-claude/token-counting)은 count 무료/별도 rate limit/캐시 미사용을 명시한다.

실제 전송은 가상 Mira 의상·Song A 예외·승인 출처·합성 음악 메타데이터·로컬 계획 및 작업 영수증이다. 실제 고객 자료·음악 파일·이미지 파일·타 프로젝트는 전송하지 않았다. request 기록에서 허용 모델·도구만 사용, 타 프로젝트 문자열 없음, auth headers/credential prefix 없음을 확인했다. 실제 키를 추가로 열어 검사하지 않았으며 secret-canary 부정 테스트는 fake 값으로 수행했다.

최초 실행 심사는 exact authorization 부족 사유로 거절됐다. 이후 부모가 실제 사용자 승인 연속성을 추가 전달하여 **동일 작업 정식 재심사 1회가 허용**됐다. 우회 없음. 최초 차단 보고는 `REPORT-initial-blocked-ko.md`에 보존했다. 부모의 일부 설명은 요약이며 verbatim 사용자 인용으로 기록하지 않았다.

## 발견한 결함과 수정

### 작업 영수증의 계획 연결 누락

실제 Claude가 계획 ID는 조회 근거에 없다고 정확하게 지적했다. 과거 성공 답변을 꾸미거나 응답 내용을 고치지 않았다.

- 수정: `action_execution.project_jobs`에서 불변 action의 `plan_id`, `plan_revision`, `release_id`를 읽기 전용 projection에 추가.
- `production_tools.get_generation_job`에서 위 필드와 현재 프로젝트의 등록된 Take를 함께 반환.
- 실제 DB의 계획1/version1/단색 fixture release/Take1 연결을 **읽기 전용 오프라인 실행**으로 검증: `corrected-receipt-offline.json`.
- **미검증:** 이 수정 후 새로운 actual Claude 최종 답변. 이번 승인한 2개 UI 입력을 모두 사용했으므로 추가 호출하지 않았다.

### F07 저장 중 새 의견 초안 유실

독립 감사 원본은 수정하지 않았다. 자체 새 폴더에서 실제 HTML handler + 지연 fake fetch로 재현했다. 수정 전4반례, 수정 후16개 모두 pass.

- 제출 시 scope, shot, 초안 revision, 정확한 값을 고정한다.
- 저장 성공 후 해당 revision과 저장값이 그대로일 때만 초안을 제거한다.
- 현재 프로젝트/샷/폼 값까지 제출본과 같을 때만 reset한다.
- 저장 대기 중 새 입력·같은 값으로 재입력·프로젝트/샷 이동·실패 시 새 입력을 보존한다.
- 실제 브라우저에서도 새로고침 복원, 성공 제출본 정리, A/B 프로젝트 초안 격리를 검증했다. 실제 네트워크 지연 중 타이핑은 VM fake fetch 검증이며 브라우저 지연 주입으로 포장하지 않는다.

`docs/qa/f07-comment-draft-20261025/REPORT-ko.md` 참고.

## 최종 코드·회귀·런타임

- 최초 관련30 tests pass; 전체225 pass.
- 후속 영수증/F07 포함 **최종226 tests pass,26.018s**; Python AST/JS 문법 pass.
- 현행 HTML SHA256 `7426e52fdb37487dbf7dba35344146a8d13408795aff9aa363334a860f6d5fa3`.
- `http://127.0.0.1:8773`: 기존 검증 저장소 보존, revision45, source/served hash일치, 실제 공급자 연결0. exec88376.
- `http://127.0.0.1:65338`: 이번 합성 결과 재조회, revision23, 실제 공급자 연결0. exec92169. 원 실제 키 연결 서버exec61586은 종료됐다.
- 실제 시험 당시 HTML은 이전 `258602...`였고 F07 수정 후 HTML과 구분한다. 실제 시험의 backend source hash는 `checkpoint.json`, 최종 source hash는 `final-runtime.json`.

## 남은 범위와 판정

실제 Claude의 서버 ontology 조회와 **실제 계획 쓰기**는 확인했다. 승인 후 로컬 후보 실행·등록·조회도 확인했다. 그러나 media는 fake이며 Claude가 직접 유료영상 실행한 증거가 아니다. UI 승인 주체도 QA 에이전트이지 실제 고객이다.

아직 영상 API만 남았다고 할 수 없다:
1. 보강한 계획 영수증을 반영한 실제 Claude 최종 답변 재검증.
2. 새 immutable action/grant/reservation 경로의 외부 image/video dispatcher 연결. 현재 `rehearsal_workflow.action_execute`는 `SyntheticImageAdapter`이고, `action_execution`은 rehearsal 원장이다.
3. 기존 fal legacy 경로의 토큰/CDN 접근 문제 및 generated→downloaded→saved→registered 실검증. 이번에는 fal 접근·추가 생성0.
4. 일반 사용자 자료에 대한 승인·문맥 범위 UX, 모델 대체/12개 조합, 다중사용자 인증·tenant 운영·배포는 미검증이다.
5. 현재 UI는 긴 모델 답변을 plain text로 안전하게 출력해 Markdown 기호가 보이며, 승인된 계획의 생성 당시 설명에 '검토 전' 문구가 남는다. 상태 제목은 샷 반영됨으로 바뀌지만 문구 정리는 후속 UX 개선이다. 실제 사용자 테스트/AA 전체 접근성 통과 주장은 하지 않는다.

테스트 수를 96FR/143API 또는 28MS-FR/38MS-AT 전체 수용 비율로 환산하지 않는다. 현재 결과는 **제한된 합성 프로젝트의 실제 Claude 도구 왕복과 로컬 제작 경로 증거**다.
