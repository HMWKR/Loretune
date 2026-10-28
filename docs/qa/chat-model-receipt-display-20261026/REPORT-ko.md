# Aethon 현재 채팅 모델·stale 영수증 표시 검증

2026-10-26 UTC. CQ-01/02의 좁은 표시 변경을 실제 소스에 적용했다. 같은 작품의 독립 대화 세션은 제품 결정 대기이며 구현하지 않았다. 유료 공급자 호출·키 읽기·공유 DB 변경·설치·배포·업로드는 0이다.

## 요구와 관측

- [원본07](../../../07_Chat_Directed_Multimodel_Production_Spec.md) §3.2, 109행: **“채팅 입력창 주변에는 현재 채팅 모델을 항상 표시하고”**. 같은 절은 다음 응답 적용 시점/범위를 구분한다. §3.1은 기본값 변경을 이미 승인된 묶음에 소급하지 않는다.
- [디자인 계획](../../design/CURRENT-DESIGN-QA-PLAN.md)의 CQ-02: 실제 선택은 GPT 6 Luna인데 입력 주변은 연결 없음만, 과거 답변에는 Claude만 보였다. before 캡처는 현재 소스를 실제 localhost 서버가 제공한 화면이다.
- CQ-01: 현재 문맥 불일치와 이전 승인 실행불가가 동일한 흰색 목록의 두 번째 줄에 있었다. 실제 baseline을 본 뒤 기존 경고색과 첫 줄 배치만 적용했다. 모션 배치/긴 이력 가설은 수정하지 않았다.

## 구현 범위

|파일|변경과 보존|
|---|---|
|`index.html`|`#modelChatSelection`을 입력 바로 위에 추가. `project.model_settings.selections.chat`를 catalog의 같은 chat 역할과 연결하며, capability나 과거 응답 모델로 추정하지 않는다. 작품 기본값/다음 요청 기준을 명시. 미선택과 catalog 정보 미확인을 구별한다.|
|`index.html`|`chatModelName`/`modelChoiceName` 공유 표시 함수: 기존 3개 모델을 사용자용 이름으로 표시하고 설정창에도 같은 표기를 재사용. selector value·저장·해석·라우팅은 그대로다. catalog의 `display_name`을 우선하며 임의 raw provider ID는 노출하지 않는다.|
|`index.html`|현재 영수증의 `matches_current_context === false`만 실행불가 문구를 첫 줄·굵게 표시. `receiptFacts`의 사실·문구는 변경하지 않았다. 과거 조회 영수증은 강조 대상에서 제외, 모델 원문도 별도 disclosure 그대로 유지.|
|`studio.css`|라벨에 기존 body/14px/500 역할과 `overflow-wrap:anywhere`, stale에 기존 `--ui-warning`만 적용. 새 색·버튼·승인·고정 높이 없음.|
|테스트3파일|`tests/test_chat_display.py` 신규4개. `tests/chat_receipts.cjs`와 `tests/test_desktop_refinement.py`는 새 표시 helper를 실제 함수 로딩에 포함하는 scaffolding만 보정; 기존 assertion은 유지.|

`app.py`, `chat_runtime.py`, `model_selection.py`, `chat_protocols.py`, `production_context.py`, `chat_models.py`, `studio-media.js`, `motion-studio.js`는 baseline 해시와 동일하다. 실행 권한·세션·모델 전환 계약을 바꾸지 않았다. [구현 diff](implementation.patch), [최종 manifest](FINAL-MANIFEST.json).

## 실제 검증

전체 unittest **414/414**, 61.378초, [원본 로그](full-regression.log). 기존410에 신규4개를 더한 한 실행이며 focused16을 다시 더하지 않는다. focused **16/16**, 1.075초([로그](targeted.log)); JS syntax도 통과했다. 범위에는 기존 F07/DM/CC 및 승인 표시 회귀가 포함된다. 테스트 수는 제품 완성도나 38개 전체 수용조건 통과율이 아니다.

새4개는 선택/없음/catalog누락/다른역할, disabled·unverified·blocked·retired도 선택명 유지, 긴/악성 표시 문자열, current true/false/null과 past 분리, 사실 불변·새 버튼 없음·입력 설명 연결을 확인한다. 기존 실제 응답 재생6개를 쓰는 영수증 회귀도 유지했다. 이번에 실제 모델 답변을 새로 받지는 않았다.

Chrome extension의 현재 served UI를 CUA로 조작했다. CSS viewport 1920×1080 우선,1280×900 보조, DPR1/앱100%. Chrome 버전은 이번 도구에서 확인하지 못했다. 실제 브라우저 zoom·스크린리더·모바일·전체 키보드 여정 검증으로 확대하지 않는다.

|실제 브라우저 표본|결과와 증거|
|---|---|
|선택 GPT / 과거 Claude|입력 위 GPT 6 Luna와 작품 기본값/다음 요청 기준, 과거 Claude 응답은 별도. 연결 없음·요청 비활성 유지. [1920](after-1920.jpg), [1280](after-1280.jpg)|
|기존 모델 설정에서 Grok 저장|현재 표시가 Grok 4.7로 바뀌고 미전송 초안 유지. Escape로 설정창을 닫으면 기존 opener로 focus 반환. 격리 DB에서만 수행.|
|미선택 저장·GPT 복원|과거 Claude를 현재값으로 대신하지 않음. [미선택1920](empty-1920.jpg). 복원 후1280 캡처에 실제 선택 반영.|
|current false / past true|현재 실행불가만 기존 경고색. Enter로 과거 disclosure를 열어도 과거 상태는 중립, 원문과 구분. [1280 이력](history-1280.jpg)|
|폴링·재열기|`focus-before.json`과 `focus-after.json`: 초안, focus 대상, 열린 disclosure, scrollY953.5가 동일. reload→계획→상담 재진입 시 저장 선택과 초안 복원([reopen](reopen.json)).|
|긴 무공백 한글 이름|별도 격리 서버의 catalog `display_name`만 합성 긴 문자열로 반환하는 controlled HTTP fixture. 제품 HTML/CSS는 실제 소스. 양 viewport에서14px, 높이67.20px 줄바꿈·요소/페이지 가로 넘침 없음, 초안/포커스 유지·요청 비활성. [1920](long-name/1920.jpg), [1280](long-name/1280.jpg), 해당 JSON. 실제 공급자 catalog 검증은 아님.|

### 공간과 대비

두 viewport의 상담 form 폭1240px. 높이183.09→215.49px로 **32.40px 증가**했다(현재 모델 한 줄). 영수증 높이는212.39px로 동일하다. 입력 모델 정보를 추가한 비용을 감추지 않는다. 작업대 canvas DOM/CSS와 미디어 코드는 변경하지 않았지만 이번 fixture는 미디어0개이므로 새 media-rich 작업대 면적 검증이라고 주장하지 않는다.

기본 캡처는 같은 데이터/viewport/DPR/앱배율이지만 focus 자동 스크롤로 전후 scrollY가 다르다:1920 407.5→438,1280 407.5→528. 따라서 높이/문구 비교는 가능하지만 전체 화면 pixel identity를 주장하지 않는다. before/after JSON에 정확한 rect/scroll을 보존했다. 추가 긴 이름은 별도 상태다. 저장한 after1920/1280,미선택,긴이름1280 픽셀을 직접 열어 확인했다.

현재 stale computed color는 `rgb(230,197,139)`(`#E6C58B`), 배경은 기존 canvas`#101010`. 라벨은 body`#DEDEDB`. 의미는 색만으로 전달하지 않고 기존 실행불가 문구·첫 줄·굵기를 함께 사용한다. 수치 대비는 manifest의 sRGB 계산치를 참조하며 이 표본이 WCAG 전체 준수를 뜻하지 않는다.

## 환경·보존·정리

기존 합성 native-motion DB를 SQLite read-only backup으로 새 임시 디렉토리에 복제했다. 첫 서버는61299, 긴 이름 서버는51716, 둘 다127.0.0.1 전용이고 공급자 runtime/worker 없음. fixture에는 저장된 실제 응답을 **재생**했으며 모델 호출은0. 미디어 파일은0, 고객 자료·.env·키는 포함하지 않았다.

첫 격리 DB는 브라우저에서 모델 선택을3회 저장했다(Grok→없음→GPT). 따라서 복제 DB revision/model_settings 및 기존 모델 전환에 따른 production_runs/chat_receipts 파생 상태가 달라졌으며 DB 무변경이라고 주장하지 않는다. shots/ontology 등 다른 project 필드는 동일했다. 원본 합성 DB SHA-256는 전후 `1cb3664268da4969c566e3a2b0b0c9b65281f8cba099f6eabb58750bf324932d`로 보존됨. [차이 기록](preservation.json).

기본 sandbox가 임시 listener 생성/localhost GET/서버 종료 신호를 제한한 경우 공식 `require_escalated` 경로의 승인 후에만 수행했다. 외부 경로로 우회하지 않았다. 중간 Mac 연결 끊김은 비변경 `pwd`가 실행환경 없음으로 실패했고 재연결 후 재개했다. 서버61299/PID28102와51716/PID30352는 정상 SIGINT 종료, 두 포트 listener 없음 확인. 검증 탭1489480717 닫기/viewport override 해제를 완료했다. 다른 개인 탭은 건드리지 않았다.

## 스킬 적용·잔여 범위

Impeccable4.7.1의 SKILL/clarify/craft-floor/operate를 읽고 기존 시스템에 작은 명료성 개선으로 적용했다. 설치된 context 명령은 `SCOPED_EXISTING_ALLOWED`; detector도 실행했다. detector14건은 shadow 반복 advisory12와 side-tab warning2이며 **clean pass가 아니다**. 각각 기존 dialog의80px shadow와 기존3px/2px 경계 선언에서 보고됐고 이번 diff가 도입한 선언이 아니다. 자동 결과는 사용자 과업 결함 확정/리디자인 승인/품질 점수로 쓰지 않았다. 결과는 [detector.json](detector.json), 광범위 정리는 이번 범위 밖이다.

CQ-01/02의 이 표시 표본은 완료. 새 독립 세션, 실행 중 실제 외부 모델 교체, 긴20turn 오류 접근, 모션 편집 재배치, media-rich 전체 작업대, 실제 zoom/AT/forced-colors는 이번 검증에 포함하지 않았다. 외부 공급자 live·추가 비용·미확정 Library 업로드를 재개하지 않았다. 기존 디자인 계획/원본 명세/과거 QA와 다른 담당자의 OMISSION-REGISTER/REMAINING-WORK는 수정하지 않았다. 독립 최종 시각 평가는 별도이며90점이나 경쟁사 동등성을 주장하지 않는다.
