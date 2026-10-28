# Loretune 디자인 시스템·미디어 작업 개선 결과

> 후속 수정(2026-10-26): 독립 감사 DM01–03을 studio-media.js에서 수정했고 전체338회귀와 브라우저 전환을 확인했습니다. 현재 미디어 JS 해시·수정 근거는 [후속 보고서](../design-media-fixes-20261026/REPORT-ko.md)를 따릅니다. 아래337회귀·JS8f95… 기록은 해당 시점의 역사적 증거입니다. HTML/CSS/시각 구조는 변하지 않았습니다.

2026-10-26. 승인된 로컬 개선을 실제 앱에 통합했다. 현재 코드는 고정이며 독립 화면 검토가 가능하다. **전체 회귀 337개 통과**, 실제 합성 3장면→7초 음악·한국어 자막 출력→서버 재시작 후 동일 출력 보존을 확인했다. 테스트 수를 디자인 점수나 전체 제품 완성도로 환산하지 않는다.

## 실행본과 증거

- Mac URL: `http://127.0.0.1:8773`. 데이터 `/tmp/loretune-ms-qa-20261025`. 다른 기기의 localhost로 접근할 수 있다는 뜻이 아니다.
- 기존 전후 비교 작품: `디자인 다중장면 QA 20261025 1330`. 이 작품의 영상·승인·타임라인은 변경하지 않았다.
- 새 기능 QA 작품: `디자인 시스템 기능 QA 20261026`. 로컬 FFmpeg 합성 영상2개·이미지1개·음원으로 장면3개, 각3Take, 길이1/2/4초. 실제 모델 생성이나 실제 인물 자료가 아니다.
- 최종 HTML: `846e18d44d6361cf423ba6ad568ede4280fcb22b34bee17a3eeb0a647974d839`
- 최종 CSS: `5f50efffbb79f30da17e231d9257559d2e174c969cb04796f8fbd2779d6fe271`
- 미디어 JS: `8f95c231d4ab45307c9ec0b37c5e54fe8d05b6039b96b92d03a44e6d1d0ba91a`
- 백엔드: `7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`
- 전체 해시: [source-final.json](source-final.json). 실제 제공 파일 대조: [runtime-final.json](runtime-final.json).

최종 사용자 화면은 [데스크톱](release-desktop.png), [모바일](release-mobile.png)이다. 저장한 픽셀을 직접 열어 확인했다. 전후 동일 과제는 [기존 desktop](before-desktop.png)→[변경 desktop](final-desktop-same-task.png), [기존 mobile](before-mobile.png)→[변경 mobile](final-mobile-same-task.png)이다. 기존 `before-text200.png`는 로딩 상태라 시각 비교의 통과 증거로 쓰지 않는다.

[capture-manifest.json](capture-manifest.json)에 파일 체크섬·촬영 시각·소스 구분이 있다. A와 최종 B는 HTML/JS/기능이 같고, CSS에서 `#eee` 밑줄3개와 `#0008` 그림자1개를 **같은 값**의 역할 토큰으로 옮긴 차이뿐이다. `release-*`는 B 캡처이고 다른 비교/오류 이미지는 A다. 이 차이를 숨겨 모든 이미지를 B라고 표시하지 않는다.

## 바뀐 구현

1. **스타일 관리와 문자배율:** HTML의8개 스타일 블록을 `studio.css` 한 파일로 옮기고 `--ui-*` 역할 토큰을 기준으로 정리했다. 누적 theme selector를 `lt-ui` 기준으로 통합하고 동일 조건에서 완전히 덮이던 속성을 정리했다. 핵심 글자는 고정px 대신 `--text-scale`을 적용한다. 루트 밖 HEX 리터럴은0이다. 기존 조건별 레이아웃을 무리하게 재작성하지 않았으므로 모든 중복 selector가 제거된 것은 아니다. `!important`55개는 hidden/reduced-motion/disabled/skip target과 기존 조건별 우선순위를 보존한다. [유지 규칙 목록](retained-priority-rules.csv)에 사유·추가 최소성 감사 한계를 기록했다.
2. **시간 기반 작업:** 장면 폭을 실제 편집 길이에 비례시키고 같은 좌표의 눈금·측정 PCM 파형·playhead를 연결했다. 숫자 길이/trim/순서 편집은 기존 경로를 유지한다. 파형 미측정 영역은 비워 두며 자동 비트 분석·BPM 스냅을 구현했다고 표현하지 않는다.
3. **편집 미리보기:** 선택 원본과 ‘편집 순서 + 음악’을 구분한다. 편집에서는 원본 trim, 음악 offset, 자막 구간을 사용하고 실제 음악 재생 시간을 기준으로 진행한다. 다른 장면으로 전환해도 선택·승인·저장 버전은 변경하지 않는다. 브라우저 audition이며 프레임 정밀 출력과 같다고 보장하지 않는다.
4. **Take 비교:** 서로 다른 Take 기본값과 contain 비율을 보존하고, 공통 상대시간으로 무음 동시 재생·탐색한다. 편집에 사용된 Take는 해당 trim에서, 미사용 Take는0에서 시작한다. 짧은 영상의 사용 가능 길이에 맞춰 둘 다 멈춘다. 이미지/영상 혼합에서는 이미지를 정적으로 유지한다. 원본 시작/사용 길이를 각 면에 표시한다.
5. **실제 poster:** 동일 로컬 asset의 첫 디코딩 프레임만 썸네일로 사용한다. 권리 검사와 버전별 asset 경로를 유지하고 대기·실패 대체 설명을 제공한다. 가짜 그림으로 채우지 않는다.
6. **모바일과 검토:** 같은 플레이어 DOM을 검토 패널로 옮겨 미디어와 검토를 같은 맥락에서 본다. 필요하면 native disclosure로 접는다. 장면번호·Take·검토 상태는 유지하고 긴 장면 제목 반복은 줄였다. 기존 초안 컨트롤러, F07, 확인 실패/결과 미확정/저장 후 갱신 실패 구분은 보존한다.
7. **미디어 HTTP 결함 수정:** 실제 브라우저에서 영상 전체가 버퍼링돼도 seekable이0인 문제가 드러났다. 서버의 Range 미지원이 원인이었다. 권리/출력 검증 뒤 단일 bytes 범위206, 범위 초과416, 전체200을 지원했다. `If-Range` 검증자가 없으면 전체200으로 돌아가며 다른 origin이나 자격증명 전달을 추가하지 않는다. [RFC9110](https://www.rfc-editor.org/rfc/rfc9110.html#name-range-requests)을 근거로 경계와 사용권403 선행을 검사했다.

## 색상과 형태

정확한 선언은 [TOKENS-final.csv](TOKENS-final.csv), 측정 대비는 [contrast-final.json](contrast-final.json)에 있다. 경쟁사 내부 토큰을 복사하거나 추정한 값이 아니다.

| 역할 | 최종 값 |
|---|---|
| canvas / panel / raised / hover | #101010 / #1B1B1B / #242424 / #303030 |
| 강한 문자 / 본문 / 보조 | #F4F4F2 / #DEDEDB / #BDBDBB |
| 장식 구분선 / 필수 control 경계 | #383838 / #858585 |
| 선택면 / marker / 선택 밑줄 | #2A2A28 / #D8D8D2 / #EEEEEE |
| primary / on-primary | #F4F4F2 / #101010 |
| focus / 오류 / 오류면 / 경고 | #E4DDBE / #FFB49D / #28201E / #E6C58B |
| 승인 상태 | 별도 녹색 없이 중성 문자+✓+상태 단어 |

본문/panel12.777:1, 보조/panel9.154:1, control/panel4.668:1, control/hover3.577:1, 오류/오류면9.325:1, focus/panel12.619:1. 이 표본 대비가 WCAG 전체 준수를 뜻하지 않는다. spacing4/8/12/16/24/32px, radius4/6/8/12px, weight400/500/600, 동작 피드백120ms 역할을 적용했다. 한국어 system font 유지, 외부 폰트 없음.

## 요구별 QA 판정

‘표본 확인’은 명시한 로컬 조건에서 실제 동작을 확인했다는 뜻이며 전 플랫폼 통과가 아니다.

| ID | 구현/검증 결과 | 근거·한계 |
|---|---|---|
| DS01 토큰 | 적용·정적 확인 | 단일 CSS/57 root 변수, 역할형 문자 크기, 루트 밖 HEX0. 조건 우선순위55개의 최소성 전체 감사는 미완료 |
| DS02 배율 | 앱100/150/200% 표본 확인 | 제목20/30/40px, 본문14/21/28px, metadata12/18/24px. [측정](type-scale-observed.json), [200%](final-app-scale200.png). 실제 브라우저200/400%는 미검증 |
| DS03 색/상태 | 표본 확인 | 위 대비9쌍 통과, focus/selection/검토 의미 분리. 전체 접근성 인증 아님 |
| DS04 타입/간격 | 구현·실화면 확인 | 긴 한국어/1280/390/320/오류/배율 캡처. 시각 품질 최종 평가는 독립 검토 대상 |
| DS05 중복 | 적용 | 중앙 긴 제목, inspector 짧은 장면번호, rail/시간축 식별 유지. 모바일 현재 맥락 strip |
| DS06 시간축 | 기능·경계 확인 | 1/2/4초 실제 폭100.85156/201.71094/403.42188px. [측정](timeline-proportions.json), 미측정 PCM 외삽 금지 회귀. 작은 진폭 음원은 거의 평평하게 보일 수 있음 |
| DS07 모바일 | 표본 확인 |390×844 영상+승인 메모/행동 인접,320×568 자연 세로 스크롤. 같은 player DOM, 접기 지원. 실제 모바일 OS 키보드/기기 테스트는 미실행 |
| DS08 행동/오류 | 표본·회귀 확인 | 제어된 HTTP400에서 입력 보존/구체적 저장 행동 안내. [오류 화면](after-mobile-simulated-failure.png). 탭 왕복·취소로 원래 검토 복귀. 결과 미확정과 F07은 기존 자동 회귀 포함 |
| DS09 비교 | 실제 로컬 미디어 확인 | [영상/영상](final-video-comparison.png), [이미지/영상](final-image-video-comparison.png). 공통1초 종료 시 source1.25/1.00, 모두 정지. 선택/승인/타임라인 불변 |
| DS10 키보드 | 표본 확인 | disclosure Enter 열기/닫기, 비교 Escape 후 compareButton 포커스, reduced-motion transition0s. 스크린리더/전체 키보드 여정은 미검증 |
| DS11 안전 | 기존 회귀+새 로컬 출력 | 모델/비용/권리/승인 계약 유지.337 회귀. 이번 패스에서 모든 live provider 흐름을 다시 검증한 것은 아님 |
| DS12 audition | 실제 재생·불변 확인 | sequence 실제7초 종료/장면·자막 이동, 비교 중 원본 trim 유지. 이전 선택 원본 재생 위치 복귀 코드·경계 검사. 장시간/저성능 브라우저 정밀 동기 미검증 |
| DS13 poster | 정상 미디어 실화면 확인 | 실제 첫 프레임·asset별 cache/권리 확인. 실패/대기는 코드 대체 상태와 경계 테스트; 모든 코덱의 실패 UI 실험은 미실행 |

[mobile-error-responsive.json](mobile-error-responsive.json):320/390/901/1150/1280px에서 페이지 가로 넘침0, 검토 초안 탭 왕복 보존, native disclosure 키보드 동작, reduced-motion0s. 앱 문자배율과 브라우저 zoom은 다르다. 실제 브라우저 단축키 시도에서 viewport/DPR/visualViewport가 바뀌지 않아 [browser-zoom-observed.json](browser-zoom-observed.json)을 미검증 근거로 남겼다.

## 테스트와 실제 출력

최종 명령: `python3 -m unittest discover -s tests -v`. [최종 로그](regression-final-token.log): **337 tests /43.440s/OK**. inline JavaScript5개와 `studio-media.js` 문법 검사 통과. 신규 회귀10개는 시간/trim/순서/누적분수시간/실측파형/혼합Take/seek후준비상태/불변·lifecycle/스타일route와 실제 HTTPRange·권리 경계를 검사한다. 기존 저장 오류 테스트는 CSS 분리 후 새 파일을 읽도록 수정했다.

실제 QA 중 발견한 문제는 비교 초기 seek 이후 readiness 캐시로 재생이 막히는 문제와 HTTPRange 미지원이다. 두 문제를 수정하고 해당 경계 회귀 및 실제 영상 재생을 확인했다. 도구 스크립트의 선택자 오류는 상태를 읽어 확인한 후 이어갔고, 이미 성공한 승인/렌더를 중복 실행하지 않았다.

새 출력 job `d9112aa12794432c9592fd44be03e4e5`: H.2641920×1080,24fps,7.000초; AAC48kHz7.000초; mov_text 한국어3줄(마지막6.950초). 브라우저 VTT3cue도 같은 시작/끝/텍스트이며 끝7초까지 재생했다. 오디오는336000 samples, 각1초 RMS가0보다 커서 의도치 않은 전체 무음이 아님을 확인했다. 영상의 표시 해상도는 로컬 리사이즈이며 AI1080p 생성으로 표현하지 않는다.

- [영상](verified-output/d9112aa12794432c9592fd44be03e4e5.mp4)
- [한국어 자막](verified-output/d9112aa12794432c9592fd44be03e4e5.srt)
- [고정 출력 manifest](verified-output/d9112aa12794432c9592fd44be03e4e5.json)
- [측정 결과](render-observed.json), [출력 화면](final-export.png)

MP4 SHA256 `dc499d8a01b0600c4c93beac5f2e7f7725f58fb08b0d4dfaf72972da16a5e766`. 원본/tmp 출력과 프로젝트 내 보존본이 같다. VTT는 서버가 승인 manifest에서 제공하는 경로이며 별도 디스크 VTT 파일을 복사했다고 주장하지 않는다. 활성 렌더0을 확인하고 정상 재시작한 후 DB의 completed/승인 버전/파일 체크섬 및 UI 재개를 확인했다. 납품 승인까지 자동으로 바꾸지 않았다.

## 보존 및 남은 검증

기존 source snapshot/원본 명세/과거 증거/데이터 백업은 보존했다. 새 QA 작품만 추가했다. `.env`/비밀키는 읽지 않았고 이번 패스의 외부 모델 호출·실제 과금·provider 활성화는0이다. confirmed07의 독립 chat→서버 도구→선택 fal image/video 구조, noMCP, Runway benchmark-only, 미검증 모델 비활성 상태를 바꾸지 않았다. 과거 fal403은 해결됐다고 주장하지 않는다.

남은 것은 독립 시각 수용 검토, 실제200/400% browser zoom, 전체 스크린리더/모바일 기기·소프트키보드, 장시간/대형 프로젝트 브라우저 성능·동기 정밀성이다. 우선순위 CSS 규칙 최소화도 유지보수 한계로 남긴다. 이번 구현은 자동 beat detection/drag trim/전환효과/정밀 frame-sync 편집기를 추가하지 않았다. 기존 숫자 trim·순서 편집과 검증된 renderer를 사용한다. 전체96FR/143API,12live모델조합,실제고객연구,다중사용자 배포 준비를 완료했다고 표시하지 않는다.

접근 차단은 현재 없다. 일반 sandbox의 `ps` 조회가 OS에서 막혔으나 승인된 정상 escalation에서 서버 소유를 확인했고 우회하지 않았다. localhost만 실행 중이다. 서버가 꺼진 경우 프로젝트 폴더에서 검증된 명령 `python3 app.py --port 8773 --data /tmp/loretune-ms-qa-20261025`로 시작한다. 이미 실행 중이면 중복으로 실행하지 않는다.
