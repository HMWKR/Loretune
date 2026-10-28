# 두 잔여 수정 — 결과 인계

2026-10-26 · localhost8773 · 1920 우선/1280 보조 · 전체346회귀 PASS(44.215초), 정적JS6개 PASS. 접근/실행 차단없음.

- **원인 중립 저장 안내:** `index.html`의 `reviewSaveFeedback()`에서 ‘연결이 돌아오면’과 응답 유실 원인 추정을 제거했다. 이제 ‘저장 결과가 아직 확인되지 않았습니다. 입력은 보존했습니다. 아래 ‘기존 저장 확인’으로 같은 요청의 처리 결과를 조회하세요. 확인 전에는 새로 제출하지 않습니다.’라고 표시한다. 조회 후에도 unknown이면 ‘아직 저장 여부를 확인하지 못했습니다.’로 시작한다. 상태/복구/승인 로직은 바꾸지 않았다.
- **1280 미리보기 높이:** 기존 bounded shell의 폭1100–1400px·높이950px이하에서만 정밀 패널 최소높이340→300px. 미디어에40px를 돌려준다. 폰트14px, 캡션, 모든 조작을 유지하며 세부 폼은 기존 내부 스크롤을 사용한다. 큰 구조 추가나 글자 축소는 없다. 1920 규칙은 그대로다.

| 같은 합성 작품, sequence2.172초+자막+정밀 | 수정 전 실제영상 | 수정 후 | 문서높이 | 키보드 |
|---|---:|---:|---:|---|
|1280×900 CSS viewport|218.14×122.70|289.25×162.70|900|기존34controls+진단summary1 모두가시|
|1920×1080 CSS viewport|504.86×283.98|504.86×283.98|1080|35/35가시|

contain/원본비율·공통시간축·재생/편집 대상·자막 유지. 최초화면의 편집구성/출력승인/영상출력 버튼 모두가시. 절충은1280 정밀폼의 내부스크롤량 증가이며 미디어는 여전히1920보다작다. [실측·키보드](layout-keyboard.json), [수정 전1280](before-1280.png), [최종1280](final-expanded-1280.png), [최종1920](final-expanded-1920.png). 저장 픽셀을 직접 열어 확인했다.

**검증:** 관련10개targeted PASS. `tests/save_feedback.mjs`에 unknown/unknown_checked 양쪽의 원인추정문구 없음, 동일요청조회·재제출차단안내, pending불변을 추가검사했다. 실제 브라우저에서 제어된400/응답유실/404unknown/합성committed를 주입했다. POST2건·조회GET2건 모두 가로챘으며 실제서버전달0. 미확정은새저장disabled, 조회만허용. 다른장면초안격리·새초안보존·원상복구 PASS. 마지막committed는 UI복구분기를검사하는합성응답으로 실제DB저장을증명하지않는다. [오류증거](controlled-save-errors.json), [원인 중립 화면](controlled-unknown-1920.png), [전체회귀](full-regression.log), [문법](static-check.json).

**고정:** HTML/CSS/mediaJS의HTTP200응답과소스가byte동일. 백엔드변경/서버재시작없음. 정적파일은기존서버가매요청읽는다.

|파일|SHA256|
|---|---|
|index.html|`0bfdbbb815c631f23e9188a02a1308aa87430d2db33ab61f4a60f8b7adfdf109`|
|studio.css|`2fbba70fa95d035aecd19a0fd9a2e7e3e00c5f6b789cf3fe0c3eed5cbef5cfab`|
|studio-media.js(불변)|`65e2468ec5ac6f53310383f2ec0939aa2adb4793e47da5dcca7b0f20b861e328`|

[전체매니페스트](release-manifest.json), [수정패치](implementation.patch). 기존346baseline/독립81점보고서는보존하며이번수정으로점수를재계산하지않았다. 프로젝트JSON 전후SHA256 `8ac30524626fcd58457cb62a2616710426e7ec33c1958f3d271bc3dca42a740d`, pendingfalse/active모델0. 외부호출·키열람·실승인·배포·원본명세변경0. 앱/미디어수명회귀통과를실공급자/청구/스크린리더/브라우저zoom전체검증으로확대하지않는다. 검증공간33종료. Ego업데이트알림만확인했고업그레이드하지않았다.
