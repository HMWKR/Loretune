# 확인된 07 멀티모델 구현 — staging 체크포인트

## 결과

사용자 2026-10-25 14:44 UTC 확인 범위에 따라 서버 코드를 구현했다. **원본 앱에 아직 적용하지 않은 19개 파일 패치**다. 디자인 검토용 실행 앱/공유 DB/index/CSS는 그대로 유지했다. 추가 실 API 호출·키 조회·유료 생성·배포0.

최종 전체 **306개 테스트 통과(39.952초, localhost HTTP 포함)**, Python95개 파일 AST 통과, 원본 대상 `git apply --check` 통과. 전체 제품 또는38 MS-AT 통과율이 아니다. 처음18개와 이번 로컬 도구11개를 추가해 기존277개와 합쳐306개다. 앞선295개 체크포인트 로그는 `full-regression-295.log`로 보존했다. 명시적 새 도구2개 추가로 기존 '9개' 고정 assertion을11개로 갱신했다. 첫 전체 실행의3개 오류는 스냅샷에 시험 보조 scripts가 없어서 발생했고, Python 시험 소스만 복사하여 해결했다. 이후 도구 개수 assertion1개 실패도 보존 로그로 원인을 확인했다. 최종 실패0.

## 실제 변경

| 영역 | staging 구현 | 검증 / 한계 |
|---|---|---|
| 채팅 HTTP/프로토콜 | `chat_models.py`, `chat_adapters.py`, `chat_runtime.py`: Haiku/Responses(OpenAI,Grok)의 request/continuation/visible output/usage를 분리. runtime의 모델·가격·protocol 하드코딩 제거. `ChatRouter`는 선택한 정확한 어댑터만 사용 | OpenAI/Grok 모의 응답→실제 Store 계획 저장→동일 provider tool_result→최종 답변 테스트. 실제 인증/계정/모델 실행은0 |
| 문맥 인계 | 현재 canon·진행 job·최대8개 완료 대화의 공개 입력/답변을 새 run에 전달 | 같은 provider의 ephemeral reasoning items는 왕복에만 쓰고, 다른 모델 인계·DB/진단 output에는 포함하지 않음. 답변은 unreviewed |
| fal 모델 계약 | `fal_models.py`, `fal_model_adapter.py`: FLUX Schnell/Pro1.1 및 Kling2.6/2.5Turbo 공식 endpoint별 입력/큐 receipt/결과 계약 | 4개 모델 모두 동일 실제 adapter 함수에 fake HTTP를 주입. 이미지PNG/영상5초MP4의 실제 저장·Take등록 확인. 모든 catalog 미검증/기존차단, 활성 모델0 |
| 공통 신규 접수 | `fal_dispatch.py`: 저장 plan/action→사람 grant→도구 request→기존 GenerationQueue 원자적 예산 예약/접수. 기존 action이면 같은 job 반환 | 3 provider 도구 envelope가 같은 승인 action/job을 재사용. 동시 요청 예약1개, 외부 요청 불명 시 재제출0. 영상/이미지 actual queue는 같은 DB |
| 준비·견적 도구 | `prepare_image_action`, `prepare_video_action`, `estimate_media_plan` 연결 | 준비/견적만으로 grant·예약·외부제출 생성 안 됨. 입력 모델/옵션을 승인 뒤 조용히 변경하지 않음 |
| 권리/프레임 | 제출 직전 현재 asset rights/원본hash/현재 승인 start-frame/plan/context/price/grant 재검사 | rights 철회는 verified_unsubmitted; 채팅 모델만 변경하면 media grant 유지, media 선택 변경 시 차단. 수집 때도 grant철회/권리 검사 |
| 이미지→영상 | 검증된 로컬PNG만 다음 영상 data URI로 인코딩. private CDN URL을 그대로 전달하지 않음 | 생성 이미지의 사용권 미확인은 자동 승인 안 됨. `declare_take_rights` 사람 경로로 근거 기록 후 시작 프레임 승인. 파일hash/출처/provenance/이전Take 유지 |
| 편집 제안 도구 | `local_creation_tools.py`: 명시한 컷만 변경한 후보 저장. 사람 `review_timeline_proposal` 승인 시 기존 Store.timeline 서비스로 새 버전 생성 | 세 provider envelope 공통 검증. 제안/보류는 EDL 불변; 적용 후 출력 승인 초기화. stale·다른 작품·중복·적용 후 거절 처리 확인 |
| 기억 제안 도구 | 현재 작품의 정확한 source excerpt→기존 scoped ontology.propose; model-proposal actor·inferred 상태·stable ID 유지 | canonical apply는 기존 사람 ontology_apply만 가능. 출처 위조·다른 작품 ID·stale·approved 인수 주입 거부. 전역 canon 보존 |
| 로컬 출력 도구 | 현재 사람 승인ID→기존 estimate_render/render_job/worker; 기존 승인별 job 재사용 | 접수/완료/파일검증/최종 사람승인을 분리. 취소 후 자동 재생성0. 실제 음악·한국어 자막2초MP4·재시작sha·편집중 manifest 보존 |
| 표현 계약 | project.media_actions 요약: 장면·모델·옵션·견적·승인·job·시험방식만 전달 | grant/hash/reservation/경로는 기본 카드 계약에서 제외. 서버 감사 원본 유지. 실제 frontend 적용은 미실행 |

MS-FR01/02/03/07/08/09/11/12/13/14/17/21/25/26/27의 일부 코드·fixture 증거를 추가한 단계다. 각 원문 수용 기준 전체 통과로 표시하지 않는다. 여러 provider envelope와4media 계약의 검증은 **3chat×2image×2video의12개 실제 사용자 여정/live 수용시험**이 아니다.

## 확인한 시나리오

- OpenAI/Grok 응답별 tool 결과를 같은 Store에 적용하고 최종 답변을 저장.
- 선택한 연결이 없으면 Claude나 fake로 대체하지 않음; 옛 Anthropic grant로 다른 provider 사용 불가.
- token counter/disabled connection은 credential supplier를 호출하지 않음. redirect 오류·upstream secret canary를 로그에 노출하지 않음.
- 같은 provider의 encrypted reasoning continuation은 다음 요청에만 존재하며 저장된 turn/handoff에는 없음.
- 4개 fal contract의 필드 구분, private lifecycle/no retry 헤더, owner/app receipt URL 검증.
- 4개 모델의 합성 결과를 실제 파일 검사 후 Take로 등록. 기존 Take/선택본 보존, 새 후보 미승인.
- 승인 없는 AI 요청 차단, 새 grant 없이 기존 job 재조회, 동시 접수 예약1개.
- 사용권 철회·media 설정변경 시 제출0; chat-only 변경은 media 작업 유지.
- 응답유실→unknown 예약 유지, 재시작·재조회로 새 유료 요청 안 만듦.
- 잘못된 receipt owner/app과 공개/다른 host 결과 URL 차단.
- reference를 지원하지 않는 T2I 모델에 역할을 조용히 넣지 않음.
- 생성 이미지의 사용권 확인→프레임 검토→동일 원본의dataURI 영상 입력. CDN URL 직접 전달0.

## 원본/서버 경계

- 기준 HTML SHA256: `0a8ef8436b8d751c4581c648beeaa688f054217b5781d1a9528c30d2cca5c6ae`.
- 기록한90개 baseline source/test 전체 drift0. 현재 런타임은 이 staging 변경 이전 버전이다. 이번에 공용8773 재시작 없음.
- staging: `/var/folders/t7/p6pl4snd6pd3cmz1y80_7fzw0000gn/T/loretune-multimodel-lk3psz_0`.
- `manifest.json`에 파일별 before/after hash. `staged-source/`에 적용할 정확한 소스 보관. 원본 문서/.env/.codex/사용자 DB·자산·실제 비용 원장은 변경하지 않았다.
- 원본 통합은 디자인 simplification patch와 조정할 다음 단계다. 이 단계의 새 UI 브라우저 검증은 아직 하지 않았다.

## 아직 남는 범위 — API 문제만이라고 하지 않는다

**코드/화면 통합**
1. 새 media_actions/prepare/approval를 일반 채팅·작업대 검토 카드에 연결. 현재 index.html에는 기존 모의 action 카드가 유지됨.
2. 새 다중 fal dispatcher의 기존 결과 회수 UI/재개 승인 연결. 기존 generic image recovery는 이전 image_pipeline 경로이므로 새 경로에 완료 주장 금지.
3. 세 로컬 AI-tool의 서버 연결은 완료했다. 새 편집 제안 비교/검토 카드와 로컬 출력 receipt를 현재 화면에 통합·검증해야 한다. 기억 제안은 기존 ontology 검토 저장소를 재사용한다. 현재 frozen UI에서 새 도구가 제공된다고 주장하지 않는다.
4. chat 실행선택은 프로젝트 기본값, media는 명시적 작업값→프로젝트값을 실제 사용. 조직/서비스·대화 default 영속화와 일반 자동 추천은 미완성. 단일 로컬 MVP에 multiuser 조직 인프라를 추가하지 않음.
5. 스트리밍/일반 사용자 데이터 범위의 채팅 실행·비교 품질은 미검증. 현 runtime의 synthetic/prompt/context/budget gate를 일반 사용 권한으로 바꾸지 않았음.

**실제 연결 gate**
- OpenAI/Grok: 해당 공식 API의 계정/기존credential 사용 허용·데이터·예산·검증된 token counter 필요. 이번에는 키 보유 여부도 조회하지 않음. 등록한 model alias의 고정 버전/계정 가용성 미확인.
- fal image/new video: 모델별 현재 quote, 사용자 선택, 정확한 합성 입력/비용/전송·private 출력 검증 승인 필요. fixture0.01은 실제요금이 아님. 새 유료호출0, 기존403 요청 재시도0.
- 기존 Kling 결과 CDN403과 후속 token403의 근본 외부 접근 문제는 그대로 미해결. 새 adapter fixture 성공으로 해결됐다고 주장하지 않음.
- 총 Anthropic usage 계산치는 종전 `$0.0077580`에서 이번 증액0. 실제 billing 확인과 별개. `$50` 승인도 다른 provider 지출로 이전하지 않음.
- 실제 12조합/사용자 품질/실청구/계정권한/배포/다중사용자 검증은 미완료.

## 파일

- `integration.patch` — 적용 전 baseline 검증 필수; dry-run 통과.
- `manifest.json`, `full-regression.log` — 정확한 코드와 최종306개 결과.
- `CONTRACT-SOURCES.md` — 공식 모델·프로토콜·가격·private 조건과 제한.
- `PRESENTATION-CONTRACT.md` — 디자인 담당과 충돌 없이 연결할 최소 API 표현 계약.

현재 거절된 실행은 없다. 외부시험은 새 승인이 없어 수행하지 않았으며, 이 패치는 승인된 무과금 구현/fixture 검증이다. 원본 적용·화면 재검증은 별도 고정 체크포인트에서 진행해야 한다.


## 이번 로컬 도구 검증의 정확한 범위

| 시험 함수 (`tests/test_local_creation_tools.py`) | 관찰한 결과 | 증거 등급 |
|---|---|---|
| test_three_protocols_propose_without_applying_and_human_apply_preserves_other_inputs | Anthropic/OpenAI/xAI envelope가 같은 제안 경로 사용, 보류 중 무변경, 사람 적용 후 다른 컷/Take/음원/자막/이전 버전 보존, 중복 승인 새 버전0 | fake protocol + 실제 Store/DB |
| test_stale_edit_and_foreign_proposal_rejected_without_mutation | 오래된 타임라인·다른 작품 제안 적용 거부 | 실제 Store/DB |
| test_memory_exact_provenance_human_application_and_global_canon_unchanged | exact source/provenance 유지, 사람 적용 전 revision0, 적용 후에도 전역 canon 불변 | 실제 scoped ontology |
| test_memory_missing_source_stale_version_foreign_identity_and_actor_injection_blocked | 출처/발췌 위조, stale, 외부 identity, approved 인수 거부 | deterministic validator |
| test_render_real_audio_caption_output_receipt_reuse_and_final_approval_separate | 승인별 job1개, 외부예약0, 2초 영상/오디오/한국어 자막, 파일hash 재시작 보존, 최종 승인 별도 | 실제 로컬 FFmpeg/DB |
| test_render_approval_stale_revoked_rights_and_cancellation_keep_existing_jobs | 위조/오래된 승인 차단, 취소한 작업 반환·새 접수0, 권리철회 후 새 출력 차단 | 실제 Store/worker |
| test_fake_chat_runtime_roundtrip_uses_tools_not_prose_execution | fake Claude 3rounds에서 편집 제안→승인된 이전 타임라인 출력 접수→실제 receipt를 받은 최종 답변; 제안을 자동 적용하지 않음 | fake model + 실제 tool_result/DB |
| test_duplicate_tool_call_does_not_duplicate_proposal | 같은 run/call 반복에 제안1개 | 실제 멱등 기록 |
| test_render_transaction_rolls_back_estimate_when_existing_service_rejects | 견적 저장 직후 fault 주입 시 DB와 메모리 견적 rollback; job0 | fault injection |
| test_render_snapshot_preserves_approved_audio_captions_while_editor_advances | 렌더 v1 접수 후 편집 v2여도 v1음원/오프셋/자막으로 완료 | 실제 로컬 렌더 |
| test_memory_duplicate_identity_preservation_and_foreign_render_job_isolation | 중복 제안1개, 인물수정 stable ID 유지, 다른 작품에서 job not_found | 실제 Store/DB |

이11개는 모두 최종306개 전체 실행에 포함된다. 사람 행동은 synthetic Store API fixture로 수행했으며 실제 새 화면 클릭·접근성 QA나 외부 Claude 재시험은 이번 단계에서 수행하지 않았다.

로컬 출력 증거: `local-tools/verified-local-render.mp4` (640×360,24fps,2.000초), `render-evidence.json`. H.264/AAC/Korean mov_text 세 stream과 오디오 RMS0.0882744, 자막 “합성 자막 Mira”를 확인했다. 테스트 타임라인1·음원1·오프셋0.5초. SHA256 `d20b1eaef82c540db12bb3ea8b712bf37e5982a79e704e666e32960632dc6951`. 이 파일은 합성 fixture이며 실제 AI 생성 품질 증거가 아니다.

최종 패치 SHA256: `44cea955e8f21ac7e62cf440bb80490dc1e3ac30e06c42a04770b964dff65acd`. 실제 원본90파일 drift0, 공용 서버/DB 미변경. 이19파일 패치가 앞선15파일 패치를 포함·대체하므로 둘을 순서대로 중복 적용하지 않는다.
