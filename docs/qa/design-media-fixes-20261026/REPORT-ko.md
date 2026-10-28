# 독립 미디어 회귀 DM01·DM02·DM03 수정 결과

2026-10-26. 지정된 미리보기 P2 세 건과 후속 승인된 데스크톱 밀도 P2 한 건을 수정했다. 앱 변경은 **studio-media.js·studio.css 두 파일**이다. HTML/백엔드/공급자/승인·선택·저장 스키마는 변경하지 않았다. 기존 독립 감사 자료는 수정하지 않았다.

수정 시작 기준과 스냅샷은 [baseline.json](baseline.json), 수정 전 원본은 [before/](before/)에 보존했다. 미디어 JS 수정 시각은 **2026-10-26 01:08:25.885250 UTC**, 데스크톱 CSS 수정 시각은 **01:17:42.722436 UTC**다. 최종 소스·실행 응답 일치 확인은 **01:20:26 UTC**이며 이후 앱 소스 변경은 없다.

## 수정과 결과

| 감사 ID | 수정 | 확인 결과 |
|---|---|---|
| DM01 로딩 중 seek | metadata/data 도착 때 captured 최초 위치 대신 현재 `at`로 원본 위치를 다시 계산. 현재 컷·element인 경우만 적용 | VM: 편집1.5→원본3.5초, 재생 없이 반영. 실제 브라우저: readyState0에서 편집0.6초 요청→로딩 후 원본0.85초, 일시정지 유지 |
| DM02 이전 비동기 이벤트 | pause와dispose 구분. controller 교체 시 영구 무효화·RAF 취소·이벤트 해제·detached Audio 해제. 컷 serial 및 play attempt epoch를 이벤트/Promise/RAF에 적용 | 늦은 error/waiting/playing/loaded/ready와 이전 play 성공·실패가 새 상태에 영향 없음. 현재 유효한 error는 계속 표시 |
| DM03 비교 중 배경 음악 | 비교 진입·재생에서 sequence controller를 명시 정지. 반대 전환에서도 compare 정지. DOM 검색만으로 정지하지 않음 | 실제 sequence Audio1개 재생→비교 진입 후0개. 배경 위치0.383초 고정, 두 비교 영상은 공통1초에서 원본1.25/1.00초로 종료·일시정지 |

변경 위치: `studio-media.js`의 `timeline`, `createSequence`, `comparison`, dialog 종료 처리. [적용 차이](media-lifecycle.patch). DOM ID는 같으며 새로운 제작 동작이나 승인 권한은 추가하지 않았다. 후속 CSS 변화는 아래 화면 밀도 절에 구분했다.

## 자동 회귀

- [수정 전 재현](before-reproduction.json): 제어 이벤트12시나리오 중8실패/4통과. 미해결 실패를 숨기지 않았다.
- [수정 후 동일 시험](after-reproduction.json): **12/12 통과**. 독립 감사의 최소 DOM과 생산 코드 body를 사용하며 export seam만 추가한 Node VM 검사다. 실제 네트워크 이벤트 순서가 자연 발생했다는 뜻은 아니다.
- 미디어 집중: **28 unittest 통과 /5.901초** ([로그](targeted.log)).
- 미디어 수정 직후 전체: **338 unittest 통과 /43.667초** ([로그](full-regression.log)). 데스크톱 CSS 통합 후 최종 전체: **338 통과 /44.080초** ([최종 로그](full-regression-final.log)). 이전337+새 wrapper1이며, wrapper 내부12개를 전체 총계에 다시 더하지 않았다.
- `node --check studio-media.js` 통과.

새 회귀 파일은 `tests/media_async_harness.cjs`, `tests/media_async_lifecycle.cjs`, `tests/test_media_async_lifecycle.py`. 정상 audio offset/trim/caption·공통 최소 길이 종료·현재 오류 처리·canonical JSON 불변 대조군을 함께 유지했다. 늦은 Promise가 새 재생을 중단하거나 폐기된 RAF를 다시 시작하지 않는지 검사했다.

## 실제 브라우저 재검증

별도 QA 공간28, 동일 localhost와 합성 작품 `디자인 시스템 기능 QA 20261026`만 사용했다. 서버/DB에서 새 생성·승인·렌더를 실행하지 않았다.

1. [음악→무음 비교 전환](browser-transition.json): UI로 sequence를 재생하고 비교창을 열었다. Audio 생성자는 관측만을 위해 래핑했다. 음악 객체는 DOM 밖에 있어도 정지했고 비교 종료까지 배경 위치가 고정됐다. [실제 비교 화면](browser-muted-comparison.png).
2. [로딩 중 seek](browser-pending-seek.json): 로컬 요청에600ms 지연/전송 속도 제한을 적용했다. 요청 당시 readyState0, playhead0.6, loaded 후 source0.85·paused true·readyState4. 모의 네트워크 제한은 finally에서 해제했다. [정지 프레임](browser-pending-seek.png)의 인코딩 시간0.833초는24fps 프레임이며 currentTime0.85와 같은 프레임 구간이다.
3. [이전 콜백 전달](browser-stale-events.json): 실제 영상 전환 후 저장해 둔 옛 콜백을 의도적으로 호출했다. 이는 **제어된 fault injection**이다. 현재 sequence는3.233→3.442초로 정상 진행했고 새 장면 라벨이 보존됐다. 비교 쌍을 바꾼 후 옛 callbacks를 호출해도 버튼은 사용 가능하고 새 비교가 진행됐다.
4. 위 전환 전후 선택 Take·검토 기록·저장 timeline·head JSON은 동일했다. 실제 브라우저에서 canonical 변경이나 네트워크 쓰기를 수행하지 않았다. 두 PNG를 저장 후 직접 열어 확인했다.

## 데스크톱 밀도 후속 수정

독립 디자인 감사에서 지적한 기본 검토 화면의 하단 이탈만 줄였다. [CSS 차이](desktop-density.patch)는901px 이상에서 미리보기 높이, timeline padding, 시간축 여백·파형 높이만 조정한다. 글자·버튼·장면 블록의 최소 높이, 비용·권리·승인 정보는 줄이거나 숨기지 않았다. 기존 중복 ruler height 선언은 같은 역할의 원래 규칙에 합쳤다.

1280×900 / 글자100% / 선택 Take / 정밀편집 접힘의 [실측](desktop-density.json):

| 영역 | 이전 독립 감사 | 최종 실제 화면 |
|---|---:|---:|
| 미리보기 높이 |324px|252px|
| 타임라인 시작–끝 |682–993px|610–896px|
| 장면 행 시작–끝 |848–908px|758–818px|
| 정밀 편집 진입점 하단 |첫 화면 밖|883px|

[최종 데스크톱](final-density-desktop.png), [최종 모바일](final-density-mobile.png)은 최종 JS/CSS로 직접 캡처하고 저장된 픽셀을 열어 확인했다. 모바일390px은 같은 영상 element가 검토 안에 유지되고 preview 높이186.75px,320/390px 모두 가로 넘침 없음. 데스크톱 전용 media query가 모바일에서 활성화되지 않음을 확인했다.

[앱 글자200% 화면](final-density-text200.png)은 실제 설정 선택으로 시험했다. 장면 시간 글자가12→24px, ruler43.2px/라벨36px, 장면 행60→80.8px로 확장하며 가로 넘침은 없다. 이 설정에서는 자연스러운 세로 스크롤이 필요하고, 촘촘한 시간 눈금 텍스트의 가로 중첩은 기존 타임라인의 잔여 한계다. 이를200% 전체 접근성 통과로 표시하지 않는다. 브라우저 자체200/400% zoom은 이번 범위에서 검증하지 않았다. 앱 배율은100%로 복구했다. [측정값](density-responsive.json).

첫 화면에 들어오는 판정은 위 기본 상태에 한정한다. sequence controls/확장 편집/오류/글자 확대가 펼쳐진 상태 전체를900px 안에 고정하지 않았다.

## 1920×1080 주 화면 추가 확인

최신 사용자 우선순위에 따라 같은 상태의1920×1080 화면을 캡처하고 실제 픽셀을 열어 확인했다. 미리보기300px, 타임라인 하단944px, 정밀 편집 진입점931px이며 주요 조작과 함께 첫 화면 안에 들어온다. 좌184px/우288px/중앙1376px/열간격16px를 유지한다. [화면·토큰·대비·한계 상세](DESKTOP-1920-ko.md), [실제 PNG](final-desktop-1920.png). 새 점수는 부여하지 않았고 이 확인을 위해 추가 소스 변경은 하지 않았다.

## 최종 고정본

URL `http://127.0.0.1:8773`. 기존 서버가 static JS/CSS를 요청마다 읽으므로 backend 재시작 없이 새 파일을 제공한다. 실제 page reload 및 응답 해시 일치를 확인했다. 디자인 검토 중인 기존 탭에는 새로고침 전까지 옛 JS가 남을 수 있다.

- media JS **ae019c88ae442b129ff7d43e8a93b4b9cf1339fd00dd09d900ced142ac3a982e**
- HTML846e18d44d6361cf423ba6ad568ede4280fcb22b34bee17a3eeb0a647974d839 — 불변
- CSS **f6f9ebff08ba722bf05f038697671c1c299d778a72d7729e63a4d7a33c87dd58** — 좁은 데스크톱 밀도 변경
- app.py7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d — 불변

[전체 소스 해시](source-final.json), [실행 응답 대조](runtime-final.json). 이전 디자인 보고서의 JS8f95…은 수정 전 기록으로 유지하며 이번 결과가 세 결함에 대한 후속 판정이다.

지정 미디어3건과 좁은 밀도 조정의 구현·자동 회귀·가능한 실제 브라우저 전환경로 검증을 완료했다. 독립 재검증은 아직 받지 않았다. 모든 브라우저·코덱·장시간 동기를 검증했다고 확대하지 않는다. 새 외부 호출/키 조회/유료 생성/배포0, 접근 차단 없음. 과거 Library 등록 준비 기능 미노출은 별도 문제이며 이 수정에서 재시도하지 않았다.
