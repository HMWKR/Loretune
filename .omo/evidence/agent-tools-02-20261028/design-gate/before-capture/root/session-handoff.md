# Loretune / Aethon 다음 담당자 인계 · 2026-10-28

**사용자 최신 지시: 현재 제작안 검토 이동까지만 마무리하고 문서를 갱신·다음 작업을 정리한 뒤 멈춘다. 다음 기능은 사용자 재개 전 시작하지 않는다. 전체 플랫폼/원래 목표는 미완료다.**

## 먼저 읽을 자료

1. 이 문서 → [README](README.md) → [현재 보고서](docs/qa/codex-workflow-review-20261027/REPORT-ko.md) → [남은 작업](docs/qa/REMAINING-WORK.md).
2. [채팅 계약](docs/design/CHAT-SESSION-PLAN.md), [전체 계획](docs/qa/codex-cli-assessment-20261026/PLAN-ko.md), [재사용 작업 방식](docs/WORKFLOW-EXECUTION-GUIDE-ko.md).
3. 원본07/수용 추적과 현재 디자인·토큰·참조 기준을 재개 대상에 맞게 읽는다. 이 문서는 인계/실행 안내이며 원본 명세나 제품 런타임 온톨로지를 대체하지 않는다.

## 제품과 작업 환경

- 경로 `/Users/leesungmin/Desktop/Loretune`. Git 저장소가 아니다. 코드/UI 제품명은 Aethon이며 명칭 충돌은 현행 문서로 확인한다.
- 중심은 음원 기반 음악영상 제작·편집·출력. 음원만으로 시작하며 사진·3D는 선택이다. 외부 AI 연결은 예외지만 편집/저장/렌더/복구는 플랫폼 내부에서 완주한다.
- 프로젝트 문서의 온톨로지/등록과 제품 IP 온톨로지를 구별한다. 원본·과거 문서·사용자 변경·미디어·실패 기록을 지우거나 임의 reset/stash/commit하지 않는다.
- 사용자 서버8765, 기존1차 검토 서버57888와 그 데이터, 사용자 제어 Ego Space는 임의 조작/재시작하지 않는다. 이번 검증의 소유 fixture59978과 브라우저는 종료했다. 기존 사용자 서버가 지금 실행 중인지는 새로 확인해야 한다.

## 이번에 끝낸 범위와 증거

- [현재 기능 수락](.omo/evidence/chat-review-navigation-20261028/driver-acceptance.json): 채팅 결과의 저장된 turn→run→image 준비 결과→현재 대화의 제작안을 교차검증해 기존 검토 카드로 이동한다. server-owned `run_id`는 읽기 projection이고 화면에 내부 ID를 노출하지 않는다.
- 기존 장면 버튼·탭·native modal close·카드 포커스를 재사용한다. 초안·권한·승인·생성을 자동 변경하지 않는다. legacy/missing/duplicate/stale/다른 대화·작품/지연 callback 경계와 dirty 편집을 보호한다.
- 신규 API/VM6개(4.572초), 관련 기존 UI6개(10.112초) 통과. 실제1920/1280/375, Enter/Space, 접힌 도구, 장면 이동, 모션/3D/대화 초안·재열기 확인. 이동 POST0·SQLite 전체 fingerprint 동일·실모델/미디어 실행0.
- [실제 화면 녹화9.29초](.omo/evidence/chat-review-navigation-20261028/worker/review-navigation-demo.mp4): 무음·무편집·무배속·생략0, full decode0·실제1배속 ended 확인. 앞선2회 관찰 스크립트 실패를 보존했고 같은 저장 제작안을 재사용했다.
- [소스 동결](.omo/evidence/chat-review-navigation-20261028/worker/source-final.json)과 [작업자 보고서](.omo/evidence/chat-review-navigation-20261028/worker/report.json)를 현재 파일과 비교한다. 제품 변경은 `chat_general.py`, `general-chat-ui.js`, `chat-sidebar.js`; 신규 검증2파일이다.
- [이전925전체 통과](.omo/evidence/chat-media-preparation-20261028/regression/driver-acceptance.json)는 이동 기능 수정 전235소스/572.930초의 증거다. 현재 수정 후 전체925를 돌린 것으로 쓰지 않는다.
- 200%는 halfCSSviewport/scale2 reflow 조건이며 native 메뉴 확대·전체 접근성 수용은 미검증이다. 실제 Claude 이해/실청구·전체 플랫폼 출시는 입증하지 않았다.

## 이전에 확보한 자료 — 반복하지 말 것

- [1차 시연 인계](.omo/evidence/first-demo-20261028/phase1-demo-handoff.json): 실제 제작·합성 대화·수동 다듬기 녹화3개와9초 native 출력. 사용자 검토 대기다. 실제 AI 영상 결과가 아니다.
- 일반 대화 도구는8개다. 모델 목록과 이미지 제작안 준비까지 합성 대화/견적+실제 UI/HTTP/저장으로 연결했다. 실제 모델 동작과 구분한다.
- [형상 진단](.omo/evidence/geometry-benchmark-20261028/driver-acceptance.json): 기존 TripoSR raw2개와 자체 primitive reference를 교정 후5뷰 비교. v1 정규화 confound 보존, v2 RMS 교정·표본 분리·정답 도움 정렬. 단위가 달라 개선율로 합치지 않으며 상용 동등성은 미입증이다.
- [공개TripoSG](.omo/evidence/continuation-native-benchmark-20261028/public-triposg-driver-acceptance.json), [상용UV영상](.omo/evidence/continuation-native-benchmark-20261028/commercial-uv-driver-acceptance.json)은 이미지/영상 근거다. 동일 입력 raw 비교쌍·샘플 제품 재사용 권리·정량 UV/재질 품질을 입증하지 않는다.
- 원본 GLB 플랫폼 가져오기/S813·S819 색 조건·유효한 기존 회귀는 새 변경/가설 없이 반복하지 않는다.

## 승인과 안전 경계

- 실제 Claude·AI 영상·기타 외부 모델/청구 호출은 이번에 하지 않았다.1차 녹화 사용자 검토와 구체 모델/자료/길이·규격/횟수/최대 비용/보관/실패 비용 승인 전 AI 영상을 호출하지 않는다.1차 수락은 무제한 비용 승인이 아니다.
- 실제 Claude 검토안은 모델/metadata·typed 도구/예산을 별도 제안한 상태다. 무응답을 승인으로 해석하지 않고 키/계정을 임의 조회하거나 unknown 작업을 재호출하지 않는다.
- FullAccess에도 계정 삭제는 영구 금지. 파일 등 다른 삭제는 정확한 대상·영향에 대한 사용자 명시 허용이 필요하다. 비용·자료 전송·권리·최종 출력 승인은 별도다.
- 문서 본문 갱신과 등록/분류/승격/생성문맥 실행은 다르다. 현재 문서 게이트는 미완료이며 자동 등록하지 않았다. [최신 등록 검토안](.omo/evidence/chat-review-navigation-20261028/document-update/registration-review-current.json)의 현재 해시·범위를 승인 전 다시 확인한다.

## 다음 순서 — 아직 시작하지 않음

1. 최신 문서 등록/분류/현재문맥 검토안 승인, 기존1차·추가 녹화 사용자 검토.
2. 일반 대화의 영상 제작/견적/job·3D·안전 설정·추천·실제 미디어 관찰 도구 공백을 현재 코드와 대조해 연결.
3. 승인된 모델·자료·예산으로 실제 Claude 선택 모델/편집 이해·토큰/사용량/청구 검증.
4. 구체 승인 후 실제 AI 영상 생성부터 플랫폼 내 편집·승인·출력·다운로드·재열기와2차 녹화 완주.
5. 동일 입력 원본 산출물 비교쌍과 음악영상/재질/모션 품질 보강.3D는 보조 수단 유지.
6. 전체 디자인·접근성·성능·실무 수용, 선택적 협업 ACL/presence, 공급자 복구·정산과 출시 운영 검증.

상세 항목과 한계는 [남은 작업](docs/qa/REMAINING-WORK.md), [다음 작업 계획](.omo/evidence/chat-review-navigation-20261028/next-work-plan.json)에 유지한다.

## 다음 담당자의 작업 방식

- 최신 사용자 지시→현행 문서→현재 코드·직접 증거 순으로 대조하고 이전 유효 조사·검증을 재사용한다. 파일명/날짜/테스트 수만으로 완료를 판단하지 않는다.
- 구현 전에 문제·원인·범위·대안·합격 증거를 정한다. 기존 구조·토큰·컴포넌트를 활용하고 불필요한 프레임워크·의존성·전면교체를 피한다.
- Karpathy/feature-verification/문서 게이트와 필요한 설치 스킬을 정확한 경로로 읽는다. 스킬 읽기·명령 실행·수동 검토·실제 결과를 구분한다. 이번 Hallmark는지침/help 확인, Impeccable는관련지침 적용이며 새전역감사통과로쓰지않는다.
- 병렬 위임은 방법론 출처·적용 방식·소유 파일·검증·한계를 계약에 넣고 write set을 겹치지 않는다. 읽기 전용 역할에 쓰기를 맡기지 않고 worker 보고와 lead 수락을 구분한다.
- 실제 UI→API→권한/권리/비용/승인→작업→저장→재조회→미리보기→편집/출력/다운로드/재열기를 검증한다. synthetic/local render/actual model/usage/billing/user study는 별개다.
- 품질 비교 전에 동일 형상/입력 대조군으로 측정기를 교정한다. 원본·수정본·카메라·seed·단위·후처리를 구분한다. 상용 서비스와 공개 모델을 출처명만으로 동일시하지 않는다.
- GitHub/Hugging Face/공식 문서/경쟁사 실제 산출물을 필요한 범위에서 조사하고 라이선스·원본·출처를 확인해 플랫폼에 맞게 적용한다. REA는 실제 노출 도구·대상·증거가 맞을 때 사용한다. 실패 뒤 원인을 좁혀 대안을 시도하되 실제 호출·배포·삭제 권한을 확장하지 않는다.
- 문서 checker는 읽기 전용으로 시작/종료에 실행한다. 등록/승격/생성문맥은 승인 범위 안에서만 처리하며 오래된 snapshot/hash를 덮어 경고를 없애지 않는다.
- 사용자 화면에는 현재 결정과 비용·권리·승인·오류·복구 정보만 필요한 시점에 제시한다. 내부 진단은 증거에 남긴다. 중요한 결정을 자동화하지 않는다.
- 현재처럼 사용자가 작업 경계를 정하면 그 범위와 인계까지만 마치고 다음 구현을 시작하지 않는다.
