# NM-Q01 — 서버 승인 사실과 모델 원문의 분리

2026-10-26 UTC. **서버가 확인한 승인 사실을 모델 설명과 독립적으로 표시하는 범위는 구현·검증했다. 모델 자유서술의 오류가 사라졌다는 판정은 아니다.** 기존 마지막 Claude 답변은 그대로 남아 있다. 신규 Claude/fal 호출·키 열람·설치·배포·업로드는 모두 0이다.

## 변경과 경계

- `production_context.motion_receipts`는 현재 작품·장면의 저장된 구성/승인 기록만 투영한다. 구성 버전, 승인 주체·범위·대상, true/false/null 문맥 일치, 미적용 제안, 관측 revision과 `execution_check=not_run`을 분리한다. `motion_context`와 실제 권한/렌더 서비스는 변경하지 않았다.
- 같은 helper를 기존 `Store.state`와 기존 조회 도구의 `execution_targets`에서 사용한다. 새 endpoint, DB migration, 승인 절차가 없다. 조회 도구의 결과는 기존 chat step 저장 경로로 남는다. 과거 응답에 영수증이 없으면 만들어 소급 부여하지 않는다.
- `drawModelChat`는 현재 선택한 작품·장면의 서버 상태를 먼저 표시한다. 과거 조회 영수증은 “그 조회 시점 / 현재 승인 아님”으로 별도 펼침에 보존한다. 원문은 “모델 설명 · 검토 전”에서 읽는다. 원문을 조용히 교정하거나 서버 문장처럼 꾸미지 않는다.
- `local-motion-candidate` 승인과 타임라인 채택/최종 납품은 별개라고 표시한다. 프로젝트 전체의 납품 승인 존재 여부를 추론하지 않는다. ID·hash·grant는 일반 상태 문구에 나오지 않는다. 상태 카드는 실행 버튼/권한을 만들지 않는다.
- CSS·토큰·타이포·미디어 lifecycle 코드·승인/실행/금액 원장은 바꾸지 않았다. 장면 선택 정상화 후 채팅을 그려 초기 장면과 표시가 일치하게 했으며, 상태 갱신 시 disclosure·focus·초안을 보존한다.

## 검증

최종 **410/410** = 기존403 + 새 unittest7. 동일 실행 내 비HTTP390 + HTTP20, 60.504초. [로그](final-full-regression.log). 관련19개와 보강 후 receipt7개 재실행은 중복 검사이므로 410에 더하지 않는다. JS syntax 통과. Node 하위 시나리오도 별도 unittest 수로 더하지 않는다.

|사례|결과·근거|
|---|---|
|이전 실제 응답6개 재생|6/6 visible output hash 일치. 이 중3개는 tool-use로 본문이 비어 있고3개가 설명문이다. 실제 `drawModelChat` 실행에서 원문 escaping·보존과 서버 상태 우선 표시 확인. 새 모델 품질 시험이 아니다.|
|잘못된/악성 원문·승인 필드 삽입|raw answer 또는 model `server_receipts`가 state projection에 들어가지 않음. HTML 삽입은 escape. 생성/승인 권한 없음.|
|true/false/null, ontology null|null ontology만으로 기존 true를 바꾸지 않음. 실제 문맥/ontology snapshot 변경은 false·stale. 승인 기록 불일치는 null.|
|v1+제안/보류/거절, 버전 변경|적용 버전과 미적용 제안 구분. v2 저장 후 과거 receipt는 v1, 현재 receipt는 v2.|
|다른 작품·장면|서버 project scope와 UI project/shot filter를 함께 검사. 다른 작품에 승인 영수증 없음.|
|폰트 변경|조회 true여도 실제 render preflight 거부, job0. 기존 execution gate 보존.|
|재시작·읽기 보존|Store 재열기에서 동일 투영. 승인/제안/실행 기록을 조회가 변경하지 않음.|

테스트: `tests/test_chat_receipts.py`, `tests/chat_receipts.cjs`, 기존 quality/CC01/CC02/F07/DM/FQ 및 전체 회귀. 수정 전 UI는 [독립 보고서](../../independent-native-motion-quality-recheck-20261026/REPORT-ko.md)의 원문 중심 표시이며, 이 변경 전 파일은 [before](before)에 보존했다.

## 실제 브라우저 표본

Mac의 **Chrome extension** 도구로 현재 localhost 제공 HTML/CSS/JS를 열었다. 문서 주입 replay가 아니다. [served/source 해시](served-source.json) 4/4 일치. 기존 합성 모션 fixture를 SQLite read-only backup으로 새 임시 디렉터리에 복사했다. 시험 데이터는 저장된 합성 scene/승인·제안·과거 답변이며 미디어 파일0. 실제 고객 DB·키·공급자 runtime 없음. `browser_server.py`는 검증 전용이다.

- 1920×1080 / 1280×900 CSS viewport, DPR1, 앱100%. 실제 browser zoom 시험은 하지 않았다. Chrome 버전은 해당 read-only scope에 노출되지 않아 미확인으로 남긴다.
- 현재 서버 상태가 true일 때 모델 원문은 접힌 “검토 전” 영역. 원문을 키보드 Enter로 열고, 표시된 text SHA256 `c2de2d6ca44a6720c53e14d971181492ac408f8c869c3a4e6f21f5e73e1217c6`이 이전 답변과 일치함을 확인했다.
- B 작품으로 전환하면 A의 영수증/초안이 표시되지 않는다. A로 돌아오면 초안 복원. reload 후 계획 상담을 다시 열어도 초안과 최신 stale 상태 복원.
- **제어된 stale fixture:** 별도 임시 DB의 장면 description만 변경했다(12→13). 현재 표시는 false로 바뀌고 과거 영수증은 true 유지. 펼침/키보드 focus/초안 유지, scrollY923→923. 원본 fixture는 읽기만 했다.
- 두 viewport에서 현재 receipt 높이212.39px, 폭1240px. 가로 overflow 없음. 기존 계획 화면은 세로 스크롤을 사용하며 no-page-scroll 전체 준수로 주장하지 않는다. 장면 작업대로 돌아오면 새 영수증은 숨겨지고 1920 문서 client/scroll height가1080/1080으로 유지된다. 이 자료는 미디어 없는 해당 상태의 관측이며 전체 편집 과제 전수 재평가가 아니다.
- 새 CSS나 더 작은 글자를 쓰지 않았다. 캡처3장을 저장하고 픽셀을 직접 확인했다. [현재1920](receipt-1920.jpg), [현재1280](receipt-1280.jpg), [현재 stale와 과거 일치1920](stale-and-history-1920.jpg).
- [browser-checks](browser-checks.json), [cleanup](cleanup.json). 탭1489480713 종료, viewport reset, localhost50286 종료/lsof listener0. 브라우저는 변경 API를 제출하지 않았으며 fixture 사전 구성과 명시한 description 변경만 격리 DB에 수행했다. 원승인/제안/chat row/jobs/production runs는 전후 동일하다.

## 비용·보존·남은 한계

추가 사용량/예약0. 이전 usage 가격 누적 **$0.0381186**, 보수적 journal 기록 **$0.038135**, 실청구 미확인 상태를 그대로 유지한다. 이번 작업은 원장을 다시 쓰거나 실제 모델 요청을 보내지 않았다. 기존6응답의 입력 전체 재해시는3/6만 가능하고 다른3개는 thinking 제거 한계가 그대로다.

기존 영상3개·SQLite 산출물·스크린샷 및 QUALITY evidence hash를 재대조한다. 원본 소스/증거는 덮어쓰지 않고 diff·manifest로 연결한다. [최종 manifest](../RECEIPT-MANIFEST.json).

NM-Q01의 **승인 사실 전달/표시 결정성**을 이번 표본과 회귀 범위에서 해결했다. 모델 원문 자체의 일반 정확성, 모든 모델 조합, 실제 공급자 생성, cross-browser/스크린리더/실제 zoom 전체 검증은 주장하지 않는다. 같은 작품 내 별도 독립 채팅 세션, 신규 ingestion/자동 ontology 진화, Blender는 기존 별도 계획/한계이며 이번에 구현하지 않았다. 신규 도구 차단은 없고 이 로컬 수용 범위는 완료했다.
