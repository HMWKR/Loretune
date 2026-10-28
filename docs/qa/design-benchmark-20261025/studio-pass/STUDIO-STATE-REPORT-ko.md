# Studio state pass — 통합 준비 완료, 2026-10-25

**비교 기본값·Take 검토 초안 격리·상태 위계 후보를 구현했습니다.** 14개 집중 테스트, JS 문법, 원본 대상 patch dry-run을 통과했습니다. 공용 `index.html`, backend, 서버, 프로젝트 저장 데이터는 수정하지 않았습니다. 이 보고서의 after는 **로컬 후보**이며 실제 제공 앱에 통합됐다는 뜻이 아닙니다.

## 바로 통합할 파일

- [integration-studio-states.patch](integration-studio-states.patch): `index.html`에 적용할 완전한 패치. CSS와 JS 포함. 별도 CSS 링크 추가 불필요.
- [review-state.js](review-state.js), [studio-state.css](studio-state.css): 검토용 독립 소스.
- [state-candidate-index.html](state-candidate-index.html): 재현 가능한 전체 후보 HTML.
- [build_state_candidate.py](build_state_candidate.py): 기준 hash를 검사하고 후보/patch를 만드는 스크립트. 공용 소스를 쓰지 않음.
- [test-review-state.mjs](test-review-state.mjs), [test-comparison.mjs](test-comparison.mjs): 집중 회귀 테스트.

기준 source/served SHA-256: `4f1805f00abb1ba2b5f7d6012727b4736e97cd4c35a007942ef6550781ae30dd`.

후보 SHA-256: `f2fc910ec77fbc306a5889102a00a6e90b2de33c847f48f200418c28aaa957b2`.

`comparison-distinct-default.patch`는 이번 완전 패치에 포함된 이전 최소안입니다. **두 패치를 중복 적용하지 마세요.** 기능 세션의 caption/provider-state 패치도 같은 기준 `index.html`을 만지므로 한쪽의 완성 HTML로 다른 쪽을 덮어쓰지 말고 함수 단위로 합쳐야 합니다.

## 동작 변화

| 영역 | 이전 관측 | 이번 후보의 정확한 동작 |
|---|---|---|
| 비교 기본값 | 선택된 마지막 Take가 양쪽에 중복 | 선택 Take를 왼쪽, 다른 최신 Take를 오른쪽에 배치. 0개/1개는 설명만 표시하며 중복 비교창을 열지 않음 |
| 검토 입력 | 다른 장면의 결정·이유가 남음 | workspace + 작품 + 장면 + Take의 JSON tuple 키로 초안을 격리. 같은 탭의 sessionStorage에 보존 |
| 저장된 검토 | 승인된 Take에도 일반 검토 CTA | 해당 Take의 저장된 결정/이유를 표시. `검토 변경 기록` 문구, 변경이 없으면 비활성화 |
| 새 검토 | `승인`과 `검토 완료`가 기본 | 미검토 Take는 결정·이유를 직접 입력해야 버튼 활성화 |
| 비동기 보호 | 새 입력을 지울 위험 | 제출 시 revision을 캡처하고 성공 시 그 revision만 제거. 입력을 바꿨다가 원문으로 돌아와도 새 revision은 보존. 다른 맥락의 초안은 제거하지 않음 |
| 반복 클릭·실패 | 공유 버튼 재활성화에 의존 | 같은 Take의 pending 요청을 중복 제출하지 않음. 실패는 초안 유지. 기존 act/request 복구 계약 사용 |
| 상태 언어 | rail/Take/timeline의 승인 표시 불균일 | `Take 검토 대기 / Take 승인됨 / Take 거절 / Take 수정 요청` 공통 렌더링. 현재 선택과 편집 사용은 별도 텍스트, 출력 승인은 `출력 승인`으로 명시 |
| 타임라인 | 장면명+초 단위만 표시 | 장면명, Take ID, 편집 길이, Take 검토 상태 표시. 현재 preview와 일치하는 clip에 `미리보기 중`. 클릭·스크러빙 기능은 만들지 않음 |
| 상단 안내 | 평상시 저장 설명이 항상 펼쳐짐 | 일상 연결/저장 상태만 한 줄로 접음. 사용자가 펼칠 수 있으며 오류·미지의 상태는 자동 노출 |
| 검토 인스펙터 | 출처와 상태가 한 문단 | Take → 저장 검토 상태 → 편집 사용/출력 승인 구분 → 출처/mock → 이유 → 이번 결정 → 맥락별 CTA |
| 모바일 | 비교 버튼이 Take 행의 공간을 차지 | Take 행 아래에 비교 버튼 배치. 긴 한국어 검토 이유는 textarea, 단어를 우선 유지하며 줄바꿈. 검토 CTA 최소 44px |

선택은 승인도, 출력 스냅샷 승인도 아닙니다. `편집에 사용`은 현재 draft/저장 timeline에 해당 Take가 들어 있다는 뜻입니다. dirty 상태는 `미저장 편집에 사용`으로 구분합니다. 실제 이미지가 있을 때만 thumbnail을 사용하며, 비디오는 `영상` 표시입니다. 가짜 thumbnail/파형/transport를 추가하지 않았습니다.

검토 초안은 **현재 브라우저 탭의 세션** 범위입니다. 서버 저장이나 다른 기기 동기화를 약속하지 않습니다. 저장소가 실패하면 메모리 보존과 그 한계를 표시합니다. `미저장 검토 초안 지우기`는 현재 Take의 로컬 초안만 지우며 서버 검토 기록을 삭제하지 않습니다.

## 실제 관측과 측정

Ego Lite 0.6.0.20, TaskSpace 12, `127.0.0.1:8773`. 기존 합성 QA `디자인 다중장면 QA 20261025 1330`을 사용했습니다. 3장면×2 Takes, 승인/대기/거절이 섞여 있고 timeline 1/1.5/2초 = 4.5초입니다. 음원과 한글 자막은 기존 fixture에 저장돼 있으며 이번 pass에서 다시 생성/출력하지 않았습니다.

초기에는 실행 중인 고정 앱에 후보 UI 함수/CSS만 주입해 상호작용을 시험했습니다. 이어 전체 후보 HTML을 **같은 origin의 새 iframe 실행 문맥**에 로드해 bootstrap/실제 DOM을 확인했습니다. 마지막 모바일 CSS 2항목은 그 iframe의 후보 stylesheet에 반영했습니다. 이미지 파일을 저장한 다음 모두 열어서 확인했습니다.

| 1280×900 같은 fixture | 실제 고정 앱 before | 후보 after |
|---|---:|---:|
| 평상시 안내 띠 높이 | 59.15px | 33px |
| 작업 영역 시작 y | 168.15px | 142px |
| 미리보기 y / 높이 | 250.30 / 324px | 224.15 / 324px |
| Take 행 높이 | 47.59px | 81.09px |
| 타임라인 track 높이 | 36px | 85.40px |
| 전체 timeline 하단 y | 828.69px | 885.44px |

상단은 26.15px 줄었지만 검토 상태를 읽을 수 있게 Take/track의 높이는 증가했습니다. 따라서 타임라인이 더 위로 올라왔다고 주장하지 않습니다. 미리보기·transport·Take·3개 clip의 검토 상태는 이 900px 화면 안에서 함께 보입니다. 모든 세부 편집/인스펙터 내용이 한 화면에 들어간다는 뜻은 아닙니다.

390×844와 320×844 검토 화면의 document scrollWidth는 각각 390/320px, 검토 버튼 높이는 44px입니다. 모바일 Take/track의 가로 스크롤은 내부에 남아 있습니다. 390px에서는 두 Take가 비교 버튼에 가리지 않고 보입니다. 모바일 timeline 전체를 첫 화면에 넣었다는 주장은 하지 않습니다.

## 전후 이미지

- [실제 고정 앱: 다중 장면 before, 1280×900](state-before-loaded-1280.png)
- [후보: 다중 장면 검토, 1280×900](state-candidate-loaded-1280.png)
- [후보: Take 2 대 Take 1 비교](state-candidate-comparison-1280.png)
- [후보: 오류 표시와 결정 필드 키보드 focus](state-candidate-error-focus-1280.png)
- [후보: 모바일 preview, 390×844](state-candidate-preview-390.png)
- [후보: 모바일 review, 390×844](state-candidate-review-390.png)
- [후보: 모바일 review, 320×844](state-candidate-review-320.png)

before와 after의 프로젝트 저장 데이터는 같지만 after에는 QA용 미저장 검토 초안이 있습니다. 비디오 정지 시점과 focus도 다릅니다. before의 미디어 로딩 표시, 단색 mock 미디어의 영상미는 디자인 점수 근거로 사용하지 않습니다. after 비디오의 실제 로컬 재생/정지는 currentTime 0.167초·readyState 4로 확인했으며 사람의 청취 시험은 아닙니다. 오류 캡처는 `QA 표시 검증`이라고 명시한 **로컬 합성 UI 오류**이며 실제 서버 장애 재현이 아닙니다.

## 검증 결과와 통합 주의점

- 9개 검토 초안 테스트: tuple 격리, reload/store 재생성, 실패 보존, 성공 시 해당 revision만 제거, 저장 중 새 텍스트/undo 보호, 맥락 전환, 중복 제출 방지, 저장값과 동일한 재제출 방지, 저장소 실패 fallback.
- 5개 비교 테스트: 0/1개, 선택 Take가 마지막/첫 번째, 선택 없음. 비교를 열어도 selection/review 데이터는 불변.
- 실제 후보 UI: 다른 장면의 approved/rejected 저장값 로드, 첫 장면의 미저장 초안 복원, 다른 기존 QA 작품 왕복, draw 재실행에도 선택 범위 `[4,9]` 보존, 전체 후보 bootstrap 후 초안 복원.
- 비교창 실제 기본값 Left 2 / Right 1. Escape로 닫은 뒤 비교 버튼 focus 복귀. 이유에서 Tab → 결정 필드, 2px outline/3px offset 확인.
- 전체 후보에 기존 ID 누락 0, 중복 ID 0. 검사 구간 runtime error 0. 종료 시 fixture의 프로젝트 JSON은 before와 동일했습니다.
- JS script 3개 문법 검사 통과, `patch --dry-run -p1` 통과. 공용 소스/served hash는 14:07:01 UTC에도 기준과 일치.

`draw`, `drawTimeline`, `drawComparison`, 비교/검토 onclick, workspace review 재배치, craft notice observer를 수정합니다. `sendRequest`의 버튼 일괄 재활성화와 act의 복구 정보 저장 실패 경로 뒤에는 `renderTakeReview()`를 호출하여 상태별 disabled를 다시 계산합니다. **caption/provider-state 통합 시 이 두 finally/실패 경로를 유실하지 마세요.** 기존 F07 comment handler는 그대로 유지하며, 새 Take review controller도 revision 보호를 적용합니다. backend payload는 기존 `review_take` 계약 그대로입니다.

이번 pass에서는 실제 review POST, 저장 실패 복구, caption/provider-state와의 결합, 전 제작 흐름을 다시 실행하지 않았습니다. 해당 영역은 통합 후 기능 세션의 regression + 같은 fixture 화면 확인이 필요합니다. 기존 API나 paid generation 경로를 새로 호출하지 않았습니다.

전체 HTML의 첫 `document.write` 검증은 기존 페이지 JS 전역이 남아 bootstrap되지 않아 중단했습니다. 새 iframe 문맥에서는 정상 로드됐습니다. 또 첫 iframe 확인은 fixture 선택 전 조건을 기다려 timeout됐으며, 현재 상태를 읽고 명시적 QA 작품 선택으로 이어갔습니다. 이 도구 절차의 timeout을 앱 결함/서버 실패로 분류하지 않습니다. 최종 실행 blocker는 없습니다.

상세 근거: [초안 UI 결과](state-draft-ui-results.json), [14개 테스트 결과 1](review-state-test-results.json), [결과 2](comparison-state-test-results.json), [전체 후보 확인](state-full-candidate-results.json), [geometry](state-geometry.json), [최종 모바일](state-mobile-final.json), [종료 hash](state-end-version.json), [이미지 manifest](state-evidence-manifest.json).

## 참고 기준과 점수 해석

이번 pass는 이미 확인한 Krea의 절제된 surface/type 방향, Clipchamp의 미디어와 timeline 인접성, ElevenLabs의 검토/출력 동선, Neural Frames 공식 Track/Storyboard tutorial 이미지를 재사용했습니다. 출처/채택 이유는 [craft 결정](../craft-pass/DECISIONS.md), [구조 결정](../structure/DECISIONS.md), [기존 gap-to-90](GAP-TO-90-ko.md)에 있습니다. Neural Frames 이미지는 **공식 설명 이미지**이며 이번에 직접 접근한 계정 editor 캡처가 아닙니다. 새로운 경쟁사 계정 조작이나 연구 확장은 하지 않았습니다. Runway는 경쟁사 참고 대상이며 provider 연결 후보로 추가하지 않았습니다.

동일 rubric을 유지합니다. 직전 독립 관측의 59/100은 단일 장면 craft 화면에 대한 잠정 전문가 판단입니다. 이번 미통합 후보에 새 총점을 부여하거나 90 달성을 주장하지 않습니다.

| 동일 5항목 /20 | 직전 잠정 값 | 이번 근거와 남은 확인 |
|---|---:|---|
| 정보·행동 명확성 | 14 | 선택/검토/출력 승인 구분과 CTA 개선. 결합된 실제 저장/복구 흐름 확인 필요 |
| 타이포·간격·위계 | 13 | 상단 중복 축소, multiline 이유, 명시적 label. inspector 하부의 긴 안내와 모바일 상단 밀도는 남음 |
| 미디어·작업 효율 | 13 | 다른 Take 기본 비교, clip ID/길이/상태 대조 가능. 많은 장면/다양한 실제 미디어 규모는 미검증 |
| 컴포넌트·상태 일관성 | 12 | 공통 검토 상태 렌더링, scoped draft와 focus. 합쳐진 caption/provider 상태까지 확인 필요 |
| 브랜드·시각 완성도 | 7 | 기존 palette/표면 체계 보존. 기본 컨트롤 느낌과 독자적 음악 제작 도구 정체성은 여전히 약함 |

18점대 판정은 각 항목이 여러 실제 통합 상태에서 충분히 해결됐을 때만 가능합니다. 현재 근거는 사용자 연구, 경쟁사 동등 조건 시험, WCAG 준수나 출시 준비의 증거가 아닙니다. 실제 브라우저 200%/400% zoom, screenreader, 실제 사용자 과업 시험은 미검증입니다. 다음 순서는 두 패치의 한 번의 통합 → 실제 동일 fixture의 비교/검토/편집·출력/모바일 캡처 → 독립 동일 rubric 검토입니다.

검증 TaskSpace는 정상 종료했습니다. Ego Lite 업데이트 알림만 확인했으며 설치나 설정 변경은 하지 않았습니다.
