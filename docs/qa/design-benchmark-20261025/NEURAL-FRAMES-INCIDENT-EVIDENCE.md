# Neural Frames 사고 · 기존 증거 정리

부모의 중단 지시 이후 해당 사이트에 접근하거나 화면·삭제 영향·복구 방법을 추가 조회하지 않았다. 아래는 당시 도구 출력과 기존 로컬 기록만 정리한 것이다. 원본 사고 기록, 로컬 QA 보고서, F05/F06 패치는 수정하지 않았다.

## 시각과 대상

- 정확한 클릭 시각은 계측하지 않아 확인할 수 없다.
- 로컬 전체 QA 종료 기록은 **2026-10-25 11:11:32 UTC**이고, 그 이후 경쟁사 조사를 시작했다. 첫 사고 기록 파일의 이번 확인 당시 수정 시각은 **11:18:26 UTC**였다. 따라서 확인 가능한 범위는 **11:11:32 이후~11:18:26 이전**이다. 파일 시각을 정확한 삭제 시각으로 주장하지 않는다.
- 사이트와 경로: Neural Frames, `https://www.neuralframes.com/songs`.
- 화면의 대상 이름: **`approved-10s-120bpm`**. 표시 길이 **0:11**, **120 bpm**, **Ab major**.
- 공급자 song ID/asset ID는 확보하지 않았다. 아래 e48/e49/e50은 당시 snapshot의 임시 locator ref이며 영구 대상 ID가 아니다.

## 클릭 전 실제 식별 근거

fresh snapshot의 해당 카드 부분은 다음과 같았다.

```text
- generic [ref=e48]:
  - image "approved-10s-120bpm"
  - text: "approved-10s-120bpm 0:11 120 bpm Ab major"
  - button "Create a new video with this song" [ref=e49]
  - button [ref=e50]
```

실행한 동작:

```javascript
await nf.locator('e50').click();
const s5 = await snapshot(nf);
console.log(s5.diff);
```

**e50에 접근 가능한 이름이 없었는데 추가 메뉴라고 추정했다.** 클릭 전에 시각 아이콘, tooltip, aria-label, title, 삭제 의도 또는 확인 단계를 검증하지 않았다. 클릭 전 실제 screenshot도 확보하지 않았다. 버튼이 메뉴라는 근거는 없었고, 이 판단과 클릭은 에이전트의 잘못이다.

## 클릭 후 관측

같은 도구 호출에서 fresh snapshot diff가 기존 음원 카드를 제거하고 다음을 표시했다.

```text
Music Track Storyboard Video
Drop a song here or click to upload
Upload Song
Or try one of our template songs
...
status: "Song deleted successfully!"
```

이는 사이트 UI가 삭제 성공을 알렸다는 증거다. 원시 DELETE 요청·HTTP 응답, provider의 실제 저장 객체 상태는 캡처하지 않았다. 삭제 범위, 휴지통/undo, 연결된 storyboard 영향, 복원 가능 여부는 미확인이다. 확인했다고 추정하거나 복구 성공으로 표시하지 않는다.

## 로컬 원본과 추가 변경

- 기존 연구 기록은 승인 테스트 파일과 미귀속 storyboard 신호를 언급하지만, 이번 확인 범위에서 이 음원과 동일한 로컬 원본의 경로·해시·존재는 확인되지 않았다. **원본이 없다고 단정하는 것은 아니다.**
- 이번 Loretune QA의 `integrated-flow/qa-synthetic-3s.wav`는 새로 만든 **3초 440Hz** 합성 음원이다. 삭제된 표시 길이11초/120bpm 음원과 다른 파일이므로 복원 원본으로 제시할 수 없다.
- 성공 메시지를 확인한 뒤 사이트의 추가 클릭·탐색·조회·복원·재업로드·새 생성·지원 문의·계정 변경을 하지 않았다. 후속 작업은 로컬 사고 기록과 보고뿐이었다.
- 당시 Aside 조사 REPL과 화면을 더 조작하지 않고 멈췄다. 사용자에게서 새 승인이 오기 전 경쟁사 조사를 재개하지 않는다.

## 보존된 로컬 QA 결과

`integrated-flow/REPORT.md`: 합성 프로젝트의 1.5초 1920×1080 출력, 48kHz 음원, 한국어 자막 및 실제 새로고침 재개 완료.
`F05-plan-disabled.patch`, `F06-comment-draft.patch`: 적용 가능/JS 문법 확인된 **미적용 제안**이며 통합 회귀는 필요하다.
이번 중단 후 확인한 원본 앱 `index.html` 해시는 계속 `cb810ea713f5865b7feecaaf510fc8d5851941216be78560bcb4ade3a6d576a3`다.
