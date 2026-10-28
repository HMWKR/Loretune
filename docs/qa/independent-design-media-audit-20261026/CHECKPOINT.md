# 좁은 독립 재생 감사 — 조기 결과

고정 HTML/CSS 해시 일치. studio-media.js SHA256 8f95c231d4ab45307c9ec0b37c5e54fe8d05b6039b96b92d03a44e6d1d0ba91a.

- DM02 / P2: 이전 컷 video의 늦은 error/waiting가 새 컷을 pause하거나 sequence clock을 정지시킴. controller 교체 뒤 늦은 error는 새 status/button을 오염. 비교 쌍 교체 뒤 이전 oncanplay가 현재 ready 쌍의 재생 버튼을 disable함. loadeddata에만 serial 검사가 있고 다른 callback/controller dispose가 빠짐.
- DM01 / P2: 영상 로딩 중 같은 컷에서 0→1.5s 탐색(trim2s)한 뒤 loadeddata가 오면 현재3.5s 대신 최초2s 원본 프레임으로 이동. UI는1.5s를 표시. 재생 버튼을 누르면 현재시간으로 다시 seek되어 회복되므로 영구편집 손실/재생 리셋으로 확대하지 않음.

actual 함수 body를 변경하지 않고 export seam만 붙인 Node VM/최소 DOM/controlled events 재현이다. 실제 브라우저에서 지연 미디어 이벤트를 관찰한 결과는 아니다. 실제 canonical p/draft JSON 불변 확인, 외부 IO0. 증거 async-evidence.json / 재현 async-media-repro.js. 소스 수정하지 않음.

추가 DM03/P2: 비교 재생 시 detached sequence Audio와 RAF가 정지하지 않아 무음 비교 중 이전 음악이 계속 재생됨. 최종 REPORT.md/async-evidence.json 참조.
