# 디자인 시스템·재생 경로 독립 회귀 — 2026-10-26

**범위 내 판정: 부분 통과 / 미리보기 P2 결함 3건 보완 필요.** 승인·선택·저장 편집의 무단 변경은 재현되지 않았다. 실제 브라우저·고객 테스트나 전체 제품 감사를 수행한 결과는 아니다.

## 재현 결함 (영향 순)

### DM02 — 이전 미디어 이벤트가 현재 장면·비교 상태를 변경 (P2)

- **위치:** `studio-media.js:74–77,86–92,102–116`. `loadeddata`에만 컷 serial 검사가 있고 `waiting/playing/error`, 비교 callbacks 및 폐기된 controller의 error/promise에는 현행 세션 검사가 없다. `timeline:67`은 이전 controller를 pause 후 교체하지만 dispose/invalidation은 없다.
- **재현:** A 영상을 로드한 뒤 B로 seek하여 B를 로드/재생한다. DOM에서 제거된 A의 지연 `error`를 전달한다. 별도 케이스에서는 A의 지연 `waiting`을 전달한다. 또 이전 controller/비교 쌍을 교체한 뒤 옛 handler를 전달한다.
- **기대:** 이전 컷/세션 이벤트는 현재 재생·표시·버튼에 영향을 주지 않는다.
- **실제:** A의 error가 현재 B를 pause하고 RAF를 제거한다. A의 waiting은 B source가2초로 진행해도 timeline을3초에 고정한다(기대4초). controller 교체 후 옛 error는 새 B 재생 중에도 오류 라벨과 '편집 재생' 버튼 문구를 쓴다. 비교 쌍 교체 후 옛 canplay는 현재 readyState4/4인 쌍의 버튼을 disable한다.
- **영향:** 새 장면이 실패한 것으로 표시되거나 재생이 멈춤. 실제 canonical project/draft JSON은 변하지 않았다. 다른 Take 자산을 저장·승인하는 결함으로 확대하지 않는다.
- **최소 수정:** 컷 및 controller 세대 토큰/active flag를 모든 media 이벤트와 play Promise 결과에 적용한다. 교체·종료 시 dispose로 listener/RAF/old media를 해제하고 callback이 현재 element/controller인지 검사한다. pause(재개 가능)와 dispose(영구 종료)를 구분한다.
- **관련 계약:** DS12 audition, DS09 compare, DS11 상태 보존; PRESENTATION-CONTRACT의 장면/Take 문맥 유지.

### DM03 — 무음 비교 중 이전 sequence 음악·재생 루프가 계속됨 (P2)

- **위치:** `studio-media.js:27,72,97,102,121`, `index.html:135–142`.
- **재현:** 음원을 포함한 sequence를 재생하고 비교창을 열어 함께 재생한다. actual sequence/compare 함수를 사용하되 `new Audio()`가 document에 연결되지 않는 DOM 성질을 fixture에 반영했다.
- **기대:** 무음 비교가 시작되면 이전 sequence 영상·음원·RAF를 정지한다.
- **실제:** 비교 영상 자체는 muted지만 이전 sequence Audio는 계속 재생하며 sequence 시간도0→1초로 진행한다. `mediaPause()`는 document의 video/audio만 찾으므로 detached Audio를 보지 못한다. `comparison()`은 compare만 pause하며 sequence controller는 정지하지 않는다.
- **영향:** 사용자는 '무음 비교' 중 음악을 듣고, 모달 뒤 편집 미리보기도 진행된다. 데이터/승인 변경은 아님.
- **최소 수정:** 비교 열기/재생 시 sequence.pause()를 명시적으로 호출하고, 반대 전환도 단일 transport 소유권으로 정리한다. DOM 검색에만 의존하지 말고 controller가 소유한 Audio/RAF를 정지한다.
- **관련 계약:** DS09 무음 공통 비교, DS12 재생 수명 관리.

### DM01 — 로딩 중 같은 컷의 seek가 화면 프레임에 반영되지 않음 (P2)

- **위치:** `studio-media.js:78–94`, 특히90행의 captured `c.source`.
- **재현:** trim2초/사용길이3초 영상에 seek(0)하여 로딩 시작 → 완료 전 seek(1.5) → loadeddata 전달.
- **기대:** playhead1.5초 및 원본3.5초 프레임.
- **실제:** playhead는1.5초지만 원본 currentTime은 최초 captured source2초다. loadeddata가 최신 `at`를 다시 계산하지 않는다. **재생 버튼을 누르면 현재 at로 다시 seek되어3.5초로 회복된다.** 영구 탐색 손실이나 재생이 항상0으로 초기화된다는 주장은 하지 않는다.
- **영향:** 일시 정지한 탐색 위치와 보이는 프레임이 다르므로 trim/컷 미리보기 판단을 흐릴 수 있다.
- **최소 수정:** 최신 pending seek 위치를 보관하거나 load 완료 시 locate(d.clips,at)를 재계산한다. 현재 clip/element 토큰이 일치할 때 최신 source만 반영한다.
- **관련 계약:** DS06 공통 시간좌표, DS12 trim 기반 audition.

## 실행 증거와 정확한 범위

- [async-media-repro.js](async-media-repro.js), [async-evidence.json](async-evidence.json): 위3건·6개 이벤트 시나리오. 실제 `studio-media.js`를 VM에 로드하고 private 함수에 **export seam만 추가**했다. 함수 body·guard·control flow는 수정하지 않았다. 최소 DOM과 controlled media events이므로 실제 브라우저에서 해당 이벤트 순서가 관찰됐다는 증거는 아니다. 이 한계를 포함해 재현 가능한 함수 계약 결함으로 보고한다.
- [controls.js](controls.js), [controls.json](controls.json): 독립 control6개 통과. 정상 audio offset/trim/caption 이동·입력 불변, 기존 loadeddata serial guard, 비교 공통 최소길이 종료, 이미지/영상 혼합, 권리철회 후 poster 실패 미적용, 실제 문자배율 handler100/150/200 및 정적 CSS 확인.
- [run-focused.py](run-focused.py), [focused-tests.log](focused-tests.log): 기존 집중 unittest **11개 통과**. 새 시간/파형/trim 계산8개 + F07 초안 wrapper1개 + scoped review/compare wrapper2개. wrapper 내부16/9/5 cases를 별도 test 총계에 더하지 않았다.
- 기존 F07 지연 저장, 프로젝트/장면/Take별 초안, 비교 기본값 회귀는 통과했다. sequence/compare 실행 중 project 선택·승인·timeline JSON 불변을 직접 비교했다. 재생 모듈에 네트워크 write API도 없다.
- 첫 재현 harness는 play 버튼 이후까지 seek가 되돌아갈 것으로 과도하게 기대했다. 실제 play의 재seek로 회복함을 확인하고 assertion을 바로잡았다. 제품을 수정하거나 실패를 통과로 바꾼 것이 아니라 DM01 범위를 정지 프레임 불일치로 한정했다.

## 고정본과 미검증

- HTML `846e18d44d6361cf423ba6ad568ede4280fcb22b34bee17a3eeb0a647974d839`
- CSS `5f50efffbb79f30da17e231d9257559d2e174c969cb04796f8fbd2779d6fe271`
- media JS `8f95c231d4ab45307c9ec0b37c5e54fe8d05b6039b96b92d03a44e6d1d0ba91a`

[snapshot.json](snapshot.json)에 캡처 시각/mtime/bytes/hash, [snapshot/](snapshot/)에 실행 source/test, [finish.json](finish.json)에 종료 시 drift를 보존했다. 대상 소스는 read-only로 읽었으며 수정하지 않았다. 공유 DB/실행 서버/계정/비밀 파일은 조회하거나 변경하지 않았다. 실제 API/업로드/배포/browser/listener 없음.

구현팀337회귀·7초 실렌더·HTTP206 검증은 별도 보고이며 이번에 재실행하지 않았다. 이 감사는 시각 품질, 실제 text200% layout/브라우저 zoom, 모바일 native media/키보드, 실제 PCM 청취·장시간 동기 정밀도·모든 poster codec을 통과로 판정하지 않는다. HTTPRange listener 시험도 실행하지 않았다.

세 결함은 데이터 보호를 우회하지 않지만, 미리보기 UX 범위의 완료 판정 전 수정·동일 지연 이벤트 회귀가 필요하다. 그 외 범용 감사나 이전 ontology/공급자 이슈로 확장하지 않았다.
