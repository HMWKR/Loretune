# 현재 구현 및 화면 검토 계약

2026-10-26. 앱은 이 기능 담당이 단일 수정. 디자인 후보 경로와 원본 보고서는 보존한다. 원본 통합·337회귀·로컬 출력/재시작 검증 완료. source-final.json 기준 freeze이며 독립 시각 수용 검토는 아직이다.

- URL: http://127.0.0.1:8773, 합성 DB `/tmp/loretune-ms-qa-20261025`. 동일 전후 작품 `디자인 다중장면 QA 20261025 1330`, 새 미디어 기능 작품 `디자인 시스템 기능 QA 20261026`(1/2/4초, 각3Take). 외부 공급자 off.
- `index.html`: 기존 ID/handlers 유지. CSS8블록을 `/studio.css` 한 파일로 이관. body의 `lt-ui`가 단일 적용 기준. 기존 class는 JS호환을 위해 DOM에 유지. 예전 theme prefix는 stylesheet에서 통합했다. 색상·문자 역할 alias는 root의 semantic roles로 해소했다. 조건별 layout 변수/우선순위는 보존한다.
- `studio-media.js`: local audition module, canonical mutation/network write 없음. 기존 `/assets` 읽기·사용권 검사 유지.
- `#timeAxis`: `#timeRuler`, `#timeWave`, `#track.time-clips`, `#timePlayhead`. duration 누적 합을 공통 좌표로 사용. track button의 `%width`는 duration/total. block text가 좁으면 잘리지만 전체이름/시작/끝은 accessible label과 title에 있음. 기존 숫자/순서 편집은 그대로.
- 파형: audio metadata의 `status=measured` PCM peaks를 audio_offset→edited duration에 매핑. 미측정 범위는 null/빈영역, `#waveNote` 설명. beat/BPM 추정 없음.
- `#sequenceTransport`: selected/sequence 모드를 명시. selected는 기존 native 원본 controls. sequence는 `#sequencePlay`, `#sequenceSeek`, `#sequenceTime`, `#sequenceStatus`, `#sequenceCaption`. 진행중 caption은 편집 draft 기준이고 승인 전 여부 명시. 기존 export 미리보기는 별도의 고정 승인 caption revision.
- `#comparisonTransport`: 공통 상대 시간, 각 Take가 실제 편집에 사용된 경우 trim부터, 아니면0부터. 영상 공통 최소 길이에서 멈춤; 이미지정적유지; 무음비교. 브라우저 동기 audition은 프레임정밀 출력 보장이 아님. 선택/검토/편집/권한 변경 없음.
- poster: 동일 asset 경로 실제 decoded 첫프레임. 권한차단Take는 추출 제외. pending/unavailable/ready data-state와 대체설명. 다른 자산의 사진을 대신하지 않음.
- 모바일: native details `#mobileReviewPreview` 안으로 **같은** preview+transport DOM을 이동. 새 독립player 생성하지 않음. 검토로 전환시 원래 선택Take로 돌아와 잘못된다른장면검토 방지. 기존 초안 controller 그대로.

확인됨: 실제 1280 화면의1/1.5/2초→156.88/235.33/313.77px(동일px/sec), 실제 poster, 첫→둘째장면 playback/자막전환.100/150/200%제목20/30/40,본문14/21/28,meta12/18/24px. 독립최종화면평가는 아직.

최종 전달: REPORT-ko.md / runtime-final.json / source-final.json / capture-manifest.json. UI의 previewMode/sequencePlay/sequenceSeek/compareTogether/compareSeek는 로컬 audition만 담당한다. 공통 음악 clock과 실제206 bytes seeking을 사용한다. 기존 승인/선택/저장은 변경하지 않는다. HTTPRange는 기존 권리/출력 검증 이후에만 적용. 최종 1/2/4초 폭100.85156/201.71094/403.42188px. 영상 비교 공통1초에서 source1.25/1.00 종료. 모바일 접기와 같은 DOM 유지 확인.
