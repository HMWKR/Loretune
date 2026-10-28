# F07 의견 저장 중 초안 손실 수정

`index.html`의 실제 submit/input/draft 함수에서 재현·수정했다. 독립 감사 폴더는 수정하지 않았다.

제출 당시 key/shot/revision/폼 값을 고정하고 성공 처리에서 같은 revision 및 저장값만 지운다. 폼 reset은 현재 scope/shot/값까지 같을 때만 수행한다. 입력 revision은 새 텍스트가 이전 값으로 돌아와도 증가하여 새 편집을 구별한다.

- 수정 전: 12pass,4fail. 원 F07 및 project-switch/shot-switch/same-value-new-edit에서 손실 재현.
- 수정 후: 16pass,0fail. fake fetch 지연 + 실제 HTML JS 함수/DOM fixture.
- `tests/test_comment_draft.py`가 같은16개 사례를 전체 회귀에 포함. 최종226개 전체 pass.
- 실제 브라우저: 1.25초 한글 의견 초안 reload복원, 저장 후 제출본만clear, A/B프로젝트의 다른 초안 보존. `browser-after.png`.
- 브라우저 네트워크 지연 주입을 실행하지 않았다. 그 경합은 Node VM의 지연 fake fetch 증거다.
- 서버 데이터는 격리된 합성 trial 저장소만 사용. 사용자 원본 파일·실제 API 호출 없음.

증거: `before.json`, `before.log`, `ui-results.json`, `after.log`, `ui_controls.js`, `index-before.html`.
