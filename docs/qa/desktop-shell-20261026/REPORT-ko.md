# 1920 우선 작업 공간 — 구현·검증 고정본

2026-10-26. 이번 범위는 **1920×1080 CSS viewport에서 장면 제작·검토와 편집·출력을 문서 세로 스크롤 없이 사용하는 것**이다. 긴 목록·정밀 편집·검토는 각 패널 안에서 스크롤한다. 1280×900은 보조 회귀이며 모바일 추가 디자인·심층 평가는 보류했다. 앱 문자 확대나 작은 창에서는 기능 접근을 위해 일반 문서 흐름을 허용한다.

현재 코드와 localhost 제공 파일을 대조해 고정했다. **전체 342개 테스트 통과 / 44.300초**, inline JS 6개와 미디어 JS 문법 검사 통과. 이 수치는 디자인 점수·전체 명세 수용률이 아니다. 독립 1920 시각 평가 결과는 아직 이 보고서에 포함하지 않는다.

## 실행본과 변경 범위

- URL: `http://127.0.0.1:8773` — 같은 Mac의 기존 검증 서버. 데이터 `/tmp/loretune-ms-qa-20261025`, 작품 `디자인 시스템 기능 QA 20261026`.
- `index.html`: `202ea641e5c1f06d316babd21aa82ad29795f4f2d5de2ff077aef596ccb850c5`
- `studio.css`: `8274aacf793e454fcc727801bdc3f7d9309345776e1e1fd6a049583e8469a3e9`
- 미디어 JS: `ae019c88ae442b129ff7d43e8a93b4b9cf1339fd00dd09d900ced142ac3a982e` — 이번 변경 없음.
- 백엔드: `7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d` — 이번 변경 없음.
- [소스·서빙·이미지 해시와 시각](release-manifest.json), [서빙 파일 대조](served-hashes.json), [수정 전 원본 해시](baseline.json).

이번 앱 변경은 HTML의 presentation adapter와 CSS다. 기존 플레이어·return anchor·입력 노드를 이동하며 복제하지 않는다. 재생 clock, provider, 저장·승인·원장 경로를 새로 만들지 않았다. 정적 파일은 서버가 요청마다 읽으므로 백엔드 재시작 없이 현재 소스가 제공됨을 해시로 확인했다. 사용자 원본 데이터는 변경하지 않았으며 `.env`는 읽거나 변경하지 않았다. 기존 QA 작품에서도 저장·승인·렌더 요청을 새로 제출하지 않았다. 로컬 회귀 테스트는 자체 격리 fixture 및 기존 합성 QA 산출물을 사용한다.

## 수정 이유와 실제 동작

1. **작업 영역의 높이 배분:** normal text, 폭1100px 이상·높이800px 이상에서 단계3/4를 viewport 높이에 맞춘다. rail과 inspector의 읽기 폭184/288px은 유지하고 중앙 공간에 미디어와 시간축을 배분한다. 문서의 overflow를 숨기는 방식은 사용하지 않는다. 긴 내용은 실제 scroll container에 남고 Tab 이동으로 접근 가능하다.
2. **실제 영상 면적:** bounded 모드에서 300px preview 상한을 제거했다. 선택 원본은 남는 높이를 쓰고, sequence transport·자막 또는 정밀 편집을 펼치면 그만큼 영상 높이가 줄어든다. contain 비율은 유지한다. 영상 확대는 화면 표시 크기이며 원본 해상도나 AI 품질 향상이 아니다.
3. **확대 시간 눈금:** 실제 label 폭을 측정해 겹치는 중간 label만 숨긴다. 시작·끝은 보존하고 매우 좁으면 두 줄로 배치한다. 시간좌표·장면 비율·파형·playhead와 재생 코드는 그대로다.
4. **컨트롤과 포커스:** desktop 주요 소형 제어에36px 최소 높이 역할 토큰을 적용했다. caption 삭제 열은30→36px이며, 정밀 편집 영역은 scrollbar gutter와 우측 여백을 확보했다. 검증 중 삭제 버튼 중심이 스크롤바에 가려지는 현상을 실제 브라우저에서 확인해 수정했다. 고정된 상세 summary 아래로 포커스가 숨지 않도록 scroll padding을 확보한다.
5. **확대·작은 창:** 앱150/200%와 충분하지 않은 창에서는 bounded shell을 해제한다. no-page-scroll은 표준 배율의 작업 맥락 목표이며 접근성보다 우선하는 절대 규칙이 아니다. 글자를 작게 만들어 맞추지 않았다.

구현 위치: `index.html`의 `loretuneDesktopLayout`, `desktopShellMode()`, `visibleTimelineLabels()`; `studio.css`의 `--ui-control-min`, `.caption-row`, `[data-desktop-shell=bounded]` 조건, `#timeRuler[data-stacked=true]`. 신규 자동 회귀는 `tests/test_desktop_layout.py`의4개다.

## 같은 작품의 전후 측정

실제 브라우저 content viewport1920×1080, DPR1, 앱 글자100%. 테스트 미디어는320×180/180×320 로컬 합성 영상이며 실제 모델 생성물이 아니다.

| 상태 | 수정 전 문서 높이 | 수정 후 문서 높이 / viewport | 이번 관측 |
|---|---:|---:|---|
| 선택 원본·장면 검토 |1080|1080 /1080| preview stage399.91px, 실제16:9 표시 약707.40×397.91px. 이전 약533×300보다 넓게 표시 |
| 편집 순서+음악 |1080|1080 /1080| transport·시간·상태·자막을 유지. 자막 표시 중 실제 영상 약528.92×297.52px; 자막이 없는 위치와 높이가 다름 |
| 정밀 편집 펼침 |1710|1080 /1080| 내부 상세 스크롤. 미리보기290.34px, timeline bottom1064px |
| sequence+정밀 편집 |미기록|1080 /1080| 미리보기214.95px. 음악 transport와 타임라인·출력 조작 유지 |
| 출력 단계 기본 |미기록|1080 /1080| 출력/승인 버튼과 기존 결과 기록 표시. 문서 가로 넘침 없음 |
| 60개 추가 장면·긴 검토40문단 |미기록|1080 /1080| DOM-only 스트레스 fixture. rail scrollHeight5458/client944, inspector3560/938. 끝 버튼 Tab 포커스 보임 |
| 보조1280×900·정밀 편집 |미기록|900 /900| 내부 스크롤, timeline bottom884px. 미리보기165.70px로 축소; 주 시각 기준은1920 |
| 앱 글자200% /1920 |미기록|1236 /1080| 일반 문서 흐름. 본문28px, 가로 넘침0, 측정 눈금 겹침0 |
| 앱 글자200% /1280 |미기록|1371 /900| 6초 중간 label만 생략,0/2/4/7초 유지, 측정 겹침0 |

근거: [수정 전 측정](before-measurements.json), [수정 후 상태별 측정](final-state-measurements.json), [긴 내용](long-content.json), [1920 확대](text200.json), [1280 확대](text200-1280.json), [1280 보조](secondary1280.json).

정밀 편집을 펼칠 때 모든 폼을 한 번에 보인다는 뜻은 아니다. form 자체의 내부 스크롤과 필요시 timeline 패널의 짧은 내부 스크롤이 발생한다. 플레이어·작품 맥락과 주요 타임라인 조작을 유지하면서 세부 필드에 도달하는 구성이다. 긴 목록 시험은 실제 프로젝트60개 생성이나 대규모 데이터 성능 시험이 아니다.

## 검증된 화면

- [1920 선택 원본·검토](final-selected-1920.png)
- [1920 sequence·음악·자막](final-sequence-1920.png)
- [1920 정밀 편집 펼침](final-expanded-1920.png)
- [1920 sequence와 정밀 편집 동시](final-expanded-sequence-1920.png)
- [서로 다른 비율의 영상 Take 비교](final-comparison-1920.png)
- [1280에서 앱 글자200%](final-app-text200-1280.png)

저장된 위 픽셀을 직접 열어 확인했다. [수정 전 펼친 상태](before-expanded-1920.png)는 역사적 baseline이다. `candidate-*`, `after-*`, `focus-inspection.png`, `keyboard-final.json`은 중간 결함/시험 기록이며 최종 통과 증거가 아니다. `final-output-1920.png`에는 native video 로딩 표시가 캡처되어 출력 단계 **배치** 증거로만 사용하며 미디어 준비 완료 증거로 사용하지 않는다. 실제 준비·재생은 별도 media smoke와 기존 출력 검증에 연결한다.

## 동작·회귀 결과

| 시험 | 판정·범위 | 증거 |
|---|---|---|
| 펼친 정밀 편집 Tab 이동 |34/34 실제 입력·버튼 focus center 가시, 문서 scrollY0. 긴 패널 말단 버튼도 별도 확인 |[keyboard-verified.json](keyboard-verified.json), [long-content.json](long-content.json) |
| 검토 초안·단계 왕복·취소 |3→4→3에서 임시 한국어 초안 유지, 명시적 취소로 원래 검토 카드 복귀. 저장 없음 |[review-draft.json](review-draft.json) |
| 편집 초안·취소 |길이1→1.2 임시 변경 후 취소로 원래 draft 복귀. canonical 프로젝트 불변 |[기존 이번 패스의 core 결과](browser-core-results.json). 해당 파일의 초기 keyboard 실패는 후속 결과로 대체 |
| 시퀀스→무음 비교→닫기 |시퀀스 재생 버튼이 정지 상태로 전환, 서로 다른 비율 영상2개 muted 재생 관측, 비교 닫기 후 compareButton focus·플레이어 위치 복귀. 프로젝트 JSON 불변 |[media-smoke.json](media-smoke.json). 후속 explicit close 표본은 영상+이미지 조합1video의 paused 확인이며2video 전체 장시간 정밀 동기 시험이 아님 |
| reduced-motion |실제 CSS preference emulation에서 transition0s/animation none |[reduced-motion.json](reduced-motion.json) |
| 모바일 기본 회귀 |390px 가로 넘침0, player DOM1개. 심층 모바일 QA는 보류 |[mobile-basic-only.json](mobile-basic-only.json) |
| 전체 자동 회귀 |342/342,44.300초. HTTP, 저장/승인/초안, provider fake contract, 실제 로컬FFmpeg trim·순서·음원click·한국어자막·tail 보존 포함 |[full-regression-final.log](full-regression-final.log) |
| 정적 검사 |inline JS6개 및 studio-media.js 문법 통과. source/served3파일 SHA256 일치 |[static-check.json](static-check.json), [served-hashes.json](served-hashes.json) |

기존7초1080p 음악·한국어 자막 결과와 재시작 보존은 [이전 구현 검증](../design-system-implementation-20261026/REPORT-ko.md#테스트와-실제-출력)에 있다. 이번에는 새 UI 렌더 job이나 서버 재시작을 반복하지 않았다. 전체 회귀의 renderer 시험은 실제 FFmpeg를 격리 fixture로 실행한다. 이 둘을 같은 새 브라우저 렌더 시험으로 합치지 않는다.

DM01–03은 이전 미디어 수정이다. [독립 재검증](../independent-design-media-recheck-20261026/REPORT.md)은 Node VM 수정 전7실패1통과→수정 후8/8, 관련 unittest12통과이며 실제 브라우저와 구분한다. 이번 미디어 소스 해시는 그 독립 고정본과 동일하다.

## 토큰과 방법론의 연결

설계 이유와 참고 근거의 단일 기준은 디자인 담당의 [방법론 fit matrix](../design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md) 및 [L01–L14 과업 추적표](../design-system-redesign-20261026/desktop1920/METHODOLOGY-AND-DECISION-LEDGER-ko.md)다. 이 문서는 그 표의 **구현·시험 결과**만 보완한다. 경쟁사의 모든 화면이 무스크롤이라고 주장하지 않는다.

| 추적 ID | 이번 구현·검증 연결 |
|---|---|
| L01·L02 작업 맥락·미디어 | bounded shell, 남는 높이의 contain media; 위5상태 문서1080 및 실제 표시 면적 측정 |
| L03·L04 객체 인지·검토 | 기존 scene/Take/승인 구분 보존. 검토 초안 단계 왕복·취소를 실제 검사 |
| L05–L08 색·타입·간격·아이콘 | 기존 중성 역할 유지, 컨트롤 최소 높이만 보완. 실제 computed 토큰57개와9개 지정 대비쌍 기록. 아이콘 전체 재설계 없음 |
| L09·L10 채팅·모델·비용·승인 | 기존 구현 보존, 관련 자동 회귀 포함. 이번 브라우저에서 새 모델 저장/전송/승인 실행은 하지 않음 |
| L11 실패 복구 | 기존 F07/unknown/확정 실패 자동 회귀 유지. 이번에 실제 서버 장애를 새로 주입하지 않음 |
| L12 시간좌표 | 표시 label만 충돌 제거. 원래 장면시간·trim·audio/caption revision·waveform 계산 코드 불변 |
| L13 audition | 실제 비교 재생·닫기와 canonical 불변 표본. 채택이나 승인을 자동 변경하지 않음 |
| L14 접근성 |34키보드 targets·앱200%·reduced-motion 표본. 실제 browser zoom/스크린리더는 미검증 |

[computed 토큰표](computed-tokens.csv), [요소별 computed 타입·경계·여백](final-computed-tokens.json), [대비 계산](contrast.json). canvas `#101010`, panel `#1B1B1B`, strong `#F4F4F2`, body `#DEDEDB`, muted `#BDBDBB`, control `#858585`, focus `#E4DDBE`, error `#FFB49D`를 유지했다. 본문/panel12.777:1, 보조/panel9.154:1, control/panel4.668:1, control/hover3.577:1, 오류/오류면9.325:1이다. 장식선/panel1.469:1은 필수 제어 식별용 기준을 충족한다고 표시하지 않는다. 지정 불투명쌍 계산이며 모든 상태/합성 배경의 WCAG 인증은 아니다.

## 남은 범위와 인계

### 합성 QA 데이터 보존 (2026-10-26 후속)

현재 합성 QA 저장소를 [새 날짜의 백업](backup/20261026T021935Z/)에 보존했다. 10월25일 백업은 덮어쓰지 않았다. 원본 SQLite를 `mode=ro`·`query_only` 읽기 트랜잭션으로 열어 SQLite backup API를 사용했으며 서버 중단/재시작·원본 DB 쓰기는 하지 않았다.

- DB1개 + 참조된 asset16개 + 완료된 render7건의 MP4/SRT/manifest21개 = **38파일 /6,627,800bytes**(검증용 JSON 제외).
- `PRAGMA integrity_check=ok`; 전체23테이블의 snapshot/복사본 행 수 일치. 주요 행: requests161, audit161, jobs7, action_jobs5, state1. 진행 중 generation/provider job0 확인.
- 모든 미디어의 원본 복사 전·복사본·원본 복사 후 SHA256 일치. asset16개는 내용 해시와 파일명도 일치. 원본 DB의 복사 전후 SHA256 및 고정 앱 소스 해시 불변.
- 알려진 합성 QA 프로젝트11개와 그 참조 미디어만 포함했다. `.env`, credential/auth 파일, 다른 `/tmp` 내용과 완료 렌더의 `parts-*` 중간 파일은 포함하지 않았다.
- 기존 `backup.py verify`의 모든 파일 해시·SQLite 검사도 통과했다. 이는 보존본 검증이며 새 경로 복원 실행이나 서버 재시작 시험을 다시 수행한 것은 아니다.

[백업 위치·행 수 요약](backup-location.json), [파일별 해시·검증 상세](backup/20261026T021935Z/verification.json), [호환 백업 manifest](backup/20261026T021935Z/backup-manifest.json). 디자인 담당 문서는 수정하지 않았고 현재 코드와 실행 서버는 고정 상태를 유지한다.

- 독립 1920 디자인 rubric 재평가 대기. 자체 점수90 또는 경쟁사 동등성 주장은 하지 않는다.
- 실제 브라우저200/400% zoom, 전체 스크린리더, 실사용자 관찰, 장시간 비교 동기·대규모 프로젝트 성능은 미검증이다. 앱 text-scale200%와 구분한다.
- 모바일 심층 디자인·실기기/소프트키보드는 최신 사용자 우선순위에 따라 보류했다. 기본390px 회귀만 수행했다.
- 기존 fal403, 외부 모델 live gates, 미검증 모델 비활성 상태는 이번 범위 밖이다. 새 API 호출·키 조회·유료 생성·provider 활성화·배포0이다.
- 실행/접근 차단은 없다. Ego Lite 업데이트 알림을 받았으나 업그레이드하지 않았고 QA 전용 space29는 정상 종료했다. 앱 서버는 유지했다.

서버가 이미 열려 있으면 중복 실행하지 않는다. 꺼졌을 때 같은 합성 QA 데이터로 실행하는 기존 명령은 `python3 app.py --port 8773 --data /tmp/loretune-ms-qa-20261025`다. 앱의 기본 `python3 app.py`는 다른 기본 데이터/8765를 사용하므로 이번 QA 데이터와 혼동하지 않는다.

## 변경 기록

- 수정 전 HTML/CSS/JS/backend와 측정·이미지 보존.
- bounded shell와 실제폭 기반 시간 label 표시,36px control token 적용.
- 키보드 검증에서 발견한 sticky summary 아래 focus 및 삭제버튼 scrollbar 겹침을 최소 CSS로 보완.
- 1920에서300px media 상한 제거, 메모리/승인/재생 서비스 변경 없음.
- 342회귀/정적/실제 브라우저 표본과 source=served hash 고정. README에 현행 인계 링크 추가. 디자인 담당 문서와 원본 명세·독립 감사 보고서는 편집하지 않음.
