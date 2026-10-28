# 07 문서 재독 및 현재 멀티모델 구조 차이

2026-10-25. `07_Chat_Directed_Multimodel_Production_Spec.md` 811행 전체를 다시 읽고 현행 코드를 대조했다. **이 감사 시점에는 코드 변경이 없었다.** 이후 14:44 UTC 사용자가 아래 해석을 확인하여 별도 staging 구현을 시작했다. 이 보고서의 gap은 감사 당시 기준이며, 후속 구현과 구분한다. 기존 실행 앱 고정 버전 `0a8ef843…c6ae`는 유지한다.

## 최신 사용자 의도로 해석할 범위

2026-10-25 14:41–14:42 UTC 사용자 지시가 현재 기준이다.

- **MCP를 사용하지 않는다.** Higgsfield는 동작을 설명한 예시이며 연결하지 않는다.
- 채팅·기획 모델, 이미지 모델, 영상 모델을 독립적으로 고른다. Claude만으로 제품 범위를 축소하지 않고 07의 Claude/OpenAI/Grok 채팅 교체 요구를 유지한다.
- 선택한 채팅 AI가 Loretune의 공통 제작 도구를 요청한다. 서버가 권한·입력·모델 지원·승인·비용을 검사한 뒤 **fal.ai API를 통해 사용자가 선택한 이미지/영상 모델**을 호출한다.
- 공식 IP/온톨로지, 계획, 승인, job, 비용, 파일/Take의 기준은 Loretune이다. 모델 교체가 이미 접수한 제작 작업이나 승인 자산을 바꾸지 않는다.
- Runway는 경쟁사·디자인 벤치마크다. 07의 외부 서비스 예시를 직접 연결 의무로 읽었던 해석은 사용자 정정으로 대체한다. 원문은 변경하지 않는다.
- 이 이해를 사용자에게 확인받기 전에는 구조·공급자 구현을 변경하지 않는다. 새 유료 호출·키·권한·활성화 승인으로 해석하지 않는다.

문서 §6.1도 첫 구현은 서버 내부 업무 함수로 충분하다고 명시한다. 최신 지시는 MCP를 명시적으로 제외하므로 이 부분은 더 이상 미결정이 아니다. fal을 호출 경로로 통일해도 이미지/영상 모델과 작업 계약은 서로 구분해야 한다. 정확히 어떤 fal 이미지 모델·추가 영상 모델을 활성화할지는 아직 선정·검증되지 않았다.

## 현재 구현과 부족한 부분

| 영역 / 관련 MS-FR | 확인한 현재 코드 | 부족한 부분·정확한 판정 |
|---|---|---|
| 실제 채팅 교체 / 01·02·25 | `chat_runtime.py:46`의 실제 HTTP 어댑터는 Anthropic 하나. `guard:115–121`은 Haiku ID와 가격 revision, 승인된 합성 project/prompt에 고정. `process_next:156–192`도 Anthropic body/normalize/result를 직접 사용 | **실제 교체 실행 미구현.** OpenAI/Grok HTTP client·usage·모델별 세션 루프가 없다. Sonnet/Opus 등 다른 Anthropic 모델을 선택하는 실행 경로도 없다. 일반 제품 실행기와 제한된 검증 gate를 분리해야 하며 기존 승인 제한을 제거하는 방식으로 해결해서는 안 됨 |
| 정규화·왕복 / 07·27 | `chat_protocols.py:17,45,63`에 Anthropic/OpenAI/xAI 도구 정의, 호출 ID 대응, 결과 envelope codec 존재. 서로 다른 provider/run으로 결과를 잘못 전달하면 거부 | **비스트리밍 텍스트/도구 codec 부분 구현.** 세 공급자 실제 transport, 스트림 조립·중단·시각 입력·usage normalization·동일 provider의 continuation state는 미완성. 실제 Claude 왕복은 과거 제한된 합성 경로에서만 증명 |
| 선택 우선순위 / 01·03·04·08 | `model_selection.py:43`에 explicit→conversation→project→organization→service resolver 존재. 미허용 명시 선택은 fallback하지 않음. `index.html:733–736`은 세 프로젝트 기본값을 저장 | **resolver가 실행 경로에 연결되지 않음.** 현재 비시험 Python 코드에서 호출자가 없다. `chat_turn` 입력은 song/prompt만 허용. 문장으로 지정한 작업별 모델 override, 대화/조직/service 설정의 영속 적용, 계정·지역·정책·능력으로 허용 후보를 만드는 통합은 없음 |
| 실제 catalog / 03·21·26 | `model_selection.py:8–18`: Haiku 미검증 1개, fal Kling 2.6 결과 수신 차단 1개, 이미지 없음. release/connection은 일부 metadata이며 활성 모델0 | **세 선택기의 구조는 있지만 실제 선택 가능한 다중 모델 제품이 아님.** 모델별 operation/능력·계정 접근·가격·검증 상태를 실행과 연결해야 함. 목록에 이름만 추가하면 완료 아님 |
| 공통 제작 도구 / 02·06·13 | `production_tools.py:8–18` 9개 도구 선언. 실제 연결된 것은 문맥 조회·기능 조회·계획 제안·생성 receipt·job 조회. Store가 실제 plan DB를 저장하고 action/grant를 확인 | `estimate_media_plan`, `propose_timeline_edit`, `request_render`, `propose_memory_update`는 현재 `LOCAL_TOOL_NOT_CONNECTED`로 귀결됨. UI에 해당 작업이 있더라도 **AI 도구 경로는 별개로 미연결**. 계획 인수도 장면 텍스트 중심이어서 대상 shot ID/참조/독립 모델/옵션을 갖춘 작업별 계획 계약이 부족 |
| AI 요청→fal 신규 작업 / 02·06·14 | `action_execution.py:156–177`은 rehearsal을 admit하고 provider는 `media_bridge.receipt` 호출. `media_bridge.py:107–119`는 **이미 사람이 접수한 job만 조회**. 실제 신규 admit은 `app.py:480–511 start_generation` | **중요 미완료:** 유효한 사람 grant 안에서 chat tool이 신규 provider action을 접수시키는 공통 경로가 없음. 현재 bridge의 정확한 역할은 기존 job receipt 재사용이며, AI가 승인된 미디어를 새로 제출하는 경로 완성으로 부르면 안 됨 |
| 미디어 모델 routing / 01·08·13·17·25 | `action_execution.py:11`은 fal-kling 연결1개만 허용. `media_bridge.py:17–37`, `generation_queue.py:28–38`, `fal_provider.py:15,42–52,99`는 Kling2.6/10초/무음/시험 견적 고정. `app.py:719–732`는 단일 provider_adapter 사용 | **fal 다중 모델 routing 미구현.** 영상 선택값을 resolver로 확정해 endpoint/입력/견적/collector를 고르는 factory가 없음. 이미지 `ImagePipeline:11–19`는 명시적인 synthetic fixture만 허용하므로 실제 이미지 adapter 없음. 모델별 기능·생성 길이와 편집 길이·취소·수집·가격 계약 필요 |
| 문맥 handoff / 09·11·12 | `model_selection.media_snapshot:61`은 채팅 변경을 미디어 승인 의존성에서 분리. `action_execution.project_jobs:16`은 legacy/new job 통합. `chat_protocols.handoff:55`는 canonical/public 대화·내부 job 상태만 반환. 늦은 run은 superseded | **보존 계약과 조회는 구현·local-tested. 새 채팅 모델에 주입하는 실행은 미연결.** `ChatRuntime.process_next:153`은 현재 prompt 하나로 messages를 시작하며 handoff payload를 소비하지 않는다. handoff의 conversation은 local 대화 배열이고 실제 chat_turn 답변/승인 이력을 완전하게 구성하는 경로도 필요. 실제 Claude→OpenAI/Grok 교체 증거 없음 |
| 온톨로지·권한·비용 | canonical DB, 안정 ID, 출처/승인/version, action/grant/ledger 및 권리 재검사 존재. Anthropic extraction은 `anthropic_ontology.py`로 별도이며 현재 chat runtime은 그 모듈 MODEL 상수·transport를 공유 | canonical을 공급자 메모리로 바꾸지 않을 기반은 있음. `search_project_context`는 scoped snapshot 전체 반환이며 query 기반 의미 검색 아님. 단일 local-owner, 합성 시험 원장/가격을 조직 제품 권한·여러 채팅 가격 정책으로 오인하면 안 됨. 내부 extraction 모델과 선택 chat 모델의 의존성을 코드에서도 분리할 필요 |

현재 사용자 목표를 막는 것은 **영상 API 접근 문제만이 아니다.** 실제 chat 교체 실행기, 선택 resolver의 연결, common tool→신규 provider admission, fal 모델별 routing/image adapter, 새 모델의 handoff 소비가 코드 차원에서 남아 있다.

## 공식 계약과의 대조

이번에는 아래 tool calling 계약만 공개 공식 문서에서 재확인했다. API 호출·접근 권한 확인·모델 catalog 활성화는 하지 않았다.

- [Anthropic tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview): client tool은 앱이 실행하고 `tool_use`에 대응하는 `tool_result`를 반환한다. 현재 Anthropic 경로의 기본 왕복 형태가 이에 해당한다.
- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling): `function_call`/`call_id`와 `function_call_output`을 연결한다. reasoning 모델의 같은 공급자 왕복에는 필요한 response items의 보존도 요구한다. 현재 codec만으로 continuation 전체 지원이 입증되지 않는다. **다른 공급자 handoff에 private reasoning을 전달하지 않는 원칙과 같은 공급자 protocol state 유지는 별개**다.
- [xAI function calling](https://docs.x.ai/developers/tools/function-calling): Responses의 function call output과 previous response 연결 예시가 있다. 현재 xAI codec은 envelope 모양을 다루지만 transport/continuation을 구현한 것은 아니다.

fal 모델별 endpoint 선택·가격·새 모델 지원 여부는 이번 감사에서 새로 확정하지 않았다. 기존 Kling endpoint가 존재한다는 사실이 선택 가능한 모든 fal 이미지/영상 모델의 adapter가 있다는 뜻은 아니다.

## 기존 증거를 어떻게 읽어야 하는가

- [실제 Claude UI 시험](../claude-chat-ui-live-20261025/REPORT-ko.md): 실제 Claude가 합성 canon 조회→계획 DB 저장→사람 UI 승인→**로컬 모의 이미지** 등록→실제 receipt 조회/답변을 수행했다. 다른 chat 공급자 또는 실제 media 교체 시험이 아니다.
- [영수증 보강 재검증](../claude-receipt-recheck-20261025/REPORT-ko.md): 추가 실제 Claude 1회로 정확한 plan/release/Take/hash 해석을 확인했다. 당시 누적 usage 가격 계산 `$0.0077580`, billing 확인과 별개. 이번 감사의 신규 호출은0.
- 이번 재실행: `tests.test_model_selection` 5개 + `tests.test_chat_protocols` 6개 = **11개 pass**. 세 fake provider envelope가 같은 실제 로컬 Store 도구에 계획을 저장하는 검사는 포함하지만 외부 API 통합 증거가 아니다. [focused-tests.log](focused-tests.log)
- 직전 전체277개 통과·통합 UI4.5초 출력은 이전 고정 릴리스 근거다. 이번 11개를 새 기능 완성도로 합산하지 않는다.
- 원문 28 MS-FR/38 MS-AT는 기존 등록부에 정확히 등록되어 있으나 전체 수용 통과로 표시하지 않았다. 특히 MS-AT36의12조합은 설계된 미래 live gate이며 현재0조합 완주다.

## 사용자 확인용 구체적 동작

확인받을 제품 흐름은 다음과 같다. 이 목록은 아직 구현됐다는 주장이 아니다.

1. 사용자가 채팅 모델과 fal 이미지·영상 모델의 프로젝트 기본값을 각각 선택한다. 특정 작업만 다른 선택을 지정할 수 있다.
2. 선택된 채팅 모델은 Loretune의 승인된 IP/활동기/곡 예외와 현재 job을 조회하고, 샷·참조·선택 모델·비용이 명시된 계획을 제안한다.
3. 서버가 고정한 계획을 사용자가 검토·승인한다. 이미 유효한 grant 안의 요청은 매번 같은 승인을 반복하지 않고 실행한다.
4. 채팅 도구 요청은 공통 검증·예산 예약·job 발행을 통과하여 선택된 fal API에 도달한다. 이미지가 필요한 영상만 승인된 기존/새 이미지를 선행 사용한다.
5. 파일을 검증·저장·Take 등록한 뒤 모델이 실제 상태를 설명한다. 부분 수정은 새 후보이며 기존 승인본·원곡·다른 샷은 보존한다.
6. 채팅 모델을 바꿔도 서버의 문맥·승인·진행 작업을 인계한다. 새 모델이 기존 job을 이어서 조회하며 재생성하지 않는다.

**확인 완료:** 14:44 UTC 사용자가 “맞아 진행 해”로 부모의 8개 확인 사항을 승인했다. MCP/Higgsfield 직접 연결은 제외한다. 무과금 코드/fixture 구현을 진행하되 실제 모델/계정/과금 검증은 각각의 별도 승인 범위로 구분한다.

확인 후의 최소 구현 순서는 ① 공통 실행기의 provider/model 선택 분리와 resolver 실제 연결 → ② 선택된 fal contract로 action/quote/job을 만드는 admission 연결 → ③ chat별 continuation 및 handoff 연결 → ④ mock contract로 교체·승인·비용·권리 회귀 → ⑤ 별도 승인된 실제 조합 검증이다. 사용자가 선택할 정확한 모델 목록은 계정 접근·기능·가격 확인 없이 임의로 활성화하지 않는다.

검사한 앱 소스 해시와 무변경 확인은 [source-evidence.json](source-evidence.json)에 기록했다. 사용자 DB, 서버, 기존 credentials, 원본 명세 및 활성 registry는 이번 감사에서 변경하지 않았다.
