Codex CLI는 현재 **외부 연결 없이 모델·도구 계약을 검증하고, 구현과 QA 증거 사이의 빈칸을 정리하는 작업**을 할 수 있습니다. 이번 제한 평가에서는 새 결함을 확정하지 않았으며, 제품 변경도 하지 않았습니다.

**1. 실제 실행과 결과**

상위 AGENTS, README 검증 지침, 지정 명세·인계·QA 문서와 관련 소스를 `rg`, `cat`, `sed`, `nl`로 읽었습니다. 테스트 실행은 다음 **한 번뿐**입니다.

```sh
python3 -B -m unittest tests.test_chat_protocols.ChatProtocolsTest.test_three_protocols_preserve_call_link_and_do_not_execute tests.test_chat_protocols.ChatProtocolsTest.test_incomplete_refusal_bad_args_and_builtin_tools_never_normalize tests.test_chat_protocols.ChatProtocolsTest.test_duplicate_json_and_partial_arguments_rejected tests.test_chat_protocols.ChatProtocolsTest.test_handoff_omits_reasoning_provider_ids_and_foreign_jobs tests.test_chat_protocols.ChatProtocolsTest.test_definitions_are_strict_and_malformed_blocks_fail_closed tests.test_model_selection.ModelSelectionTest.test_role_independence_preserves_existing_media_and_context tests.test_model_selection.ModelSelectionTest.test_wrong_role_unknown_and_stale_are_atomic tests.test_model_selection.ModelSelectionTest.test_policy_precedes_execution_no_fallback_or_metadata_activation tests.test_model_selection.ModelSelectionTest.test_change_rejects_late_run_without_modifying_job_snapshot -v
```

결과: **9개 PASS, 0.001초, exit 0**. 프로토콜 호출 연결·잘못된 인수 거부·문맥 정제·역할 독립·원자적 선택 변경을 확인했습니다. 전체 명세, 영속화된 도구 왕복, 12개 live 조합을 검증한 결과는 아닙니다.

파일 쓰기, DB·자산 접근, 브라우저·네트워크·제공자 호출, 설치·업로드·에이전트 실행은 하지 않았습니다.

**2. 현재 구현과 남은 차이**

| 구분 | 관측 및 근거 | 확신 |
|---|---|---|
| 구현됨 | 정규화 → 서버 도구 실행 → 원래 호출 ID로 결과 반환 → 다음 모델 요청 경로가 있습니다. [chat_runtime.py:191](/Users/leesungmin/Desktop/Loretune/chat_runtime.py:191), [chat_protocols.py:45](/Users/leesungmin/Desktop/Loretune/chat_protocols.py:45). 이번 실행 검증은 codec 범위입니다. | 높음 |
| 의도된 제한 | 선택 모델의 연결이 없으면 fallback 없이 차단합니다. 일반 채팅 실행은 합성 문맥·고정 입력·만료 승인 범위로 제한됩니다. [chat_runtime.py:116](/Users/leesungmin/Desktop/Loretune/chat_runtime.py:116), [chat_runtime.py:232](/Users/leesungmin/Desktop/Loretune/chat_runtime.py:232). 미검증 모델을 활성화할 근거는 없습니다. | 높음 |
| 구현 범위 부족 | `search_project_context`는 query 기반 검색 대신 작품 문맥 전체 스냅샷을 반환합니다. [production_tools.py:70](/Users/leesungmin/Desktop/Loretune/production_tools.py:70). 명세의 필요한 근거 검색에 비해 제한적이며, 코드도 의미·임베딩 검색이 아님을 명시합니다. | 높음 |
| 계약 존재·실행 미검증 | 모델의 온톨로지 변경은 제안으로 저장되고 공식 반영에는 별도 승인이 필요합니다. [project_ontology.py:79](/Users/leesungmin/Desktop/Loretune/project_ontology.py:79), [ontology.py:170](/Users/leesungmin/Desktop/Loretune/ontology.py:170). fal은 선택 모델·견적·승인·불변 job 결합을 제출 전에 재검사합니다. [fal_dispatch.py:79](/Users/leesungmin/Desktop/Loretune/fal_dispatch.py:79), [fal_dispatch.py:114](/Users/leesungmin/Desktop/Loretune/fal_dispatch.py:114). 이번 아홉 테스트는 이 계약 전체를 실행하지 않습니다. | 높음 |
| 프런트엔드 검증 부족 | polling의 순번·revision·문맥 guards와 미디어 종료 처리가 현재 소스에 있습니다. [index.html:566](/Users/leesungmin/Desktop/Loretune/index.html:566), [studio-media.js:101](/Users/leesungmin/Desktop/Loretune/studio-media.js:101). 새 반례 없이 FQ/F07/DM 문제를 재개하지 않습니다. | 높음 |
| 토큰·접근성 검증 부족 | semantic 색상·크기 토큰, reduced-motion·forced-colors 규칙이 존재합니다. [studio.css:4](/Users/leesungmin/Desktop/Loretune/studio.css:4), [studio.css:749](/Users/leesungmin/Desktop/Loretune/studio.css:749). 전체 상태의 대비·실제 zoom·스크린리더 검증을 뜻하지 않습니다. | 높음 |
| 문서 드리프트 | 초기 인계의 “이미지 모델 없음·9개 도구·protocol/원장 연결은 다음 단계”는 현재 코드 설명으로 부정확합니다. 현재는 이미지 후보 계약과 11개 도구가 있습니다. [초기 인계:7](/Users/leesungmin/Desktop/Loretune/docs/handoff-20261025-spec-ms-001.md:7), [model_selection.py:15](/Users/leesungmin/Desktop/Loretune/model_selection.py:15), [production_tools.py:8](/Users/leesungmin/Desktop/Loretune/production_tools.py:8). 후보 존재는 활성 제공자 증명이 아닙니다. | 높음 |

판정 기준은 **독립 채팅 모델 → 서버 소유 도구 → 선택 이미지·영상 모델을 fal로 실행**하는 사용자 확정 해석입니다. MCP나 직접 Runway/Higgsfield 통합을 결손으로 취급하지 않았습니다.

최신 QA의 후속 증거는 **현재 소스의 격리 브라우저 replay**입니다. 실제 제공 페이지의 최종 소스 일치나 live provider 검증과 다릅니다. [최신 인계:7](/Users/leesungmin/Desktop/Loretune/docs/handoff-20261026-frontend-fq-vq.md:7). 과거 349 PASS는 문서에 기록된 분할 실행 결과이며 이번 재실행 결과가 아닙니다.

**3. 유용한 다음 작업 — 유한한 우선순위**

| 실행 조건 | 다음 작업 | 산출 결과·검증 |
|---|---|---|
| 오프라인 지금 가능 · P1 | 07 요구사항과 현재 라우터·도구·승인 경로의 대응표 작성 | 구현됨/제한됨/미검증을 소스 라인에 연결하고 초기 인계의 교체 문구 제시. 현재 권한에서는 보고서로만 전달 |
| 오프라인 지금 가능 · P2 | query 기반 문맥 검색의 최소 계약 설계 | 근거 ID·작품 범위·빈 결과·승인 버전 기준과 순수 테스트 사례 확정. 구현은 후속 쓰기 승인 범위 |
| 오프라인 지금 가능 · P3 | 토큰 역할과 기존 QA 미검증 항목 매핑 | 오류·비활성·선택·포커스별 적용 규칙과 실제 화면 검증 필요 항목을 구분. CSS 중복만으로 결함 판정하지 않음 |
| 브라우저·격리 실행 승인 필요 · P1 | 현재 제공 페이지 소스 일치 및 미검증 접근성 표본 확인 | served 소스 일치, 한글 IME, 실제 zoom, forced-colors 오류+focus를 한정 재검증 |
| 브라우저·미디어 fixture 승인 필요 · P2 | decoded-frame seek와 AV drift 계측 | 시간표시가 아닌 실제 프레임·오디오 clock 측정으로 판정 |
| 특정 외부 호출 승인 필요 · P3 | 승인된 단일 채팅→fal 경로의 실검증 | 호출 영수증·결과 수집·비용 상태까지 확인한 뒤 확대 여부 판단 |
| CLI만으로 해제 불가 | 제공자 계정 권한·결과 다운로드 제한·실청구 확인, 실제 보조기술/사용자 평가 | 해당 제공자·계정 소유자 또는 실제 환경의 증거 필요. CLI 교체만으로 가용 상태가 되지 않음 |

검증 근거: 지정 순수 테스트 9개 통과와 현재 소스 정적 대조이며, 브라우저·영속화 통합·실제 제공자 경로는 이번 평가에서 미검증입니다.