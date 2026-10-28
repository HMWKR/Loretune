# fal.ai Dashboard 확인 결과

확인 시각: 2026-10-25 07:25:52 UTC

요청: `01a171d6-bf9e-7e72-a8c8-4eb2c5f83b1d`
모델: `fal-ai/kling-video/v2.6/pro/image-to-video`

- 사용자 지정 기존 Google 계정으로 Aside의 공식 fal.ai Dashboard 로그인 성공. 추가 인증/새 권한 동의 없음.
- Recent History에서 해당 요청을 직접 열고 Request 패널 확인.
- Status: 200. Execution Finished 표시.
- 실행 시간: 330.355초. 대기: 0.043초. 총 표시: 330.398초.
- 요청 비용: $0.70 (Dashboard Cost).
- 형식: MP4. 생성 시각 표시: 2026/10/25 15:54 (화면 시간대 GMT+9).
- 소유팀은 명시적인 화면 근거가 없어 미확정.
- 정상 Download 버튼 1회 클릭. 07:25:52 UTC Chrome 다운로드 기록 조회 결과 없음. 로컬 MP4 확보 실패, 크기/재생 가능 여부 미검증.
- 브라우저 UI 다운로드 실패 원인은 확인하지 못함. 이전 API 403과 동일 원인이라고 단정할 수 없음.

추가 생성/결제/API 재요청/ACL 변경/쿠키·토큰 추출은 수행하지 않음. 파일을 확보했다는 보고 또는 합성·QA 완료 보고를 할 수 없음.

Aside 도구 근거: repl 기반 정상 브라우저 Request 패널 snapshot 및 chrome.downloads.search. REA 호출 없음. 도구 발급 Evidence ID 없음.

스크린샷 후보를 직접 검토했으나 잘못된 영역과 다른 결과 썸네일이 포함되어 전달 자료에서 제외함. 비밀 없는 해당 요청 텍스트 관찰만 기록함.

## 이전 다운로드 클릭 후속 진단

같은 Aside 세션과 기존 fal.ai 탭을 재사용하여 읽기 전용 확인. Download 재클릭 없음.

- 07:28:14 UTC: fal 관련 기존 탭 1개, 관련 새 탭 없음. 클릭 이후 다운로드 기록 0건.
- 요청 페이지 내부 dialog 0개, alert 0개, 알림 영역에 오류/승인 대기 메시지 없음.
- Chrome 창 조회: 일반 창 1개. OS 저장 대화상자의 존재 여부는 지원된 관찰 범위에서 확정하지 못함.
- 영상 요소 1개: readyState=0, networkState=3, paused=true, currentTime=0, duration=null, videoWidth=0, videoHeight=0, bufferedRanges=0.
- MediaError code=4, message=`MEDIA_ELEMENT_ERROR: Format error`. 현재 영상 데이터가 로드되지 않아 재생 가능 상태가 아님.
- 이 오류는 HTTP403/만료/실제 코덱 문제 중 어느 원인인지 단독으로 판별하지 못함. 이전 Download의 직접 실패 원인은 여전히 미확정.
- 현재 선택팀/요청 소유팀을 확정하는 추가 근거 없음. 계정전환과 권한변경 없음.

최소 후속 조치: 사용자가 동일 요청의 Dashboard 화면에서 브라우저 저장/재생 오류를 직접 확인. 동일 현상이면 fal 지원에 요청 ID, Status200, 실행330.355초, Cost$0.70, 미디어 오류4, Download 이후 기록0을 전달하여 본인 결과 접근 복구를 문의. 재생성/ACL공개전환을 해결책으로 수행하지 않음. 서명 URL이나 키/토큰 전달 불필요.
