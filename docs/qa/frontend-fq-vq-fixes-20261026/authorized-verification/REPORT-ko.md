# FQ/VF 승인 후 검증 완료

2026-10-26 05:05 UTC. 새 기능·앱 코드 변경 없이 **기존 고정 소스**의 미완료 HTTP/브라우저 검증만 수행했다. 이전 거절과 미실행 기록은 상위 보고서에 역사적 근거로 보존했다.

## 결과

|검사|기대|실제 결과·근거|
|---|---|---|
|HTTP 회귀20개|localhost에서 격리 요청을 수행하고 모든 시험 리스너 종료|**20 PASS, 실패0, 오류0**, 10.99초. 시험이 연21개 리스너 모두 `127.0.0.1` 임시 포트이며 종료됨. loopback 연결88, 외부 연결0. [결과](http-result.json), [로그](http-regression.log), [실행기](run-http-authorized.py)|
|VF01 Take 포커스|1280×900, 앱 글자200%, Take1→Tab→2→Tab→3 및 역방향에서 현재 버튼 전체 표시|5개 위치 모두 가시비율1.0, focus-visible true. Take3에서 strip.scrollLeft=97.5px. 선택·승인 불변. [수치](browser-visual-results.json), [실제 화면](vf01-take3-1280-app200.png)|
|VF02 긴 장면명|1920×1080, 실108px title 영역에 전체 긴 문자열 보존|clientWidth=scrollWidth=108px, 높이117px, font13px, wrap anywhere. 전체 문자열 유지, 글자축소 없음. 표시 fixture만 변경 후 복원. [수치](browser-visual-results.json), [실제 화면](vf02-long-title-1920.png)|
|FQ02 실제 자연 종료|무음 시퀀스에서 native ended가 RAF보다 먼저 와도 다음 컷으로 진행·최종 정지|2개5초 영상의 임시10초 시퀀스,4.5초부터 실제 재생. 신뢰된 native ended가 표시위치4.985초/9.974초에서 발생. 다음 컷으로 전환한 뒤10.000초, 버튼 `편집 재생`, video.paused/ended true. [이벤트](browser-media-results.json), [완료 화면](fq02-silent-native-completed-1920.png)|
|FQ01 늦은 응답|늦게 도착한 이전 revision이 최신 상태를 덮지 않음|브라우저 안 제어된 fetch Promise의 두 번째 응답164→첫 번째163 순서.164와 최신 설명 유지. 이후 동일164의 합법적 chat-connection 변경도 반영. [결과](browser-async-results.json)|
|FQ03 저장소 읽기 거부|uncaught 없이 새 제출 차단, 초안/기존 프로젝트 보존|브라우저 메모리 저장소에 SecurityError 주입. act=false, throw 없음, POST0, 안내 표시, 합성 검토 초안과 프로젝트 보존. 저장소 대역 복원. [결과](browser-async-results.json)|

현재 전체 unittest349개는 **기존 비HTTP329 PASS + 이번 HTTP20 PASS**다. 같은 고정 소스를 두 분할 실행으로 검증했으며, 새 단일349개 실행이라고 부르지 않는다. 집중 JS18개는 이미 unittest wrapper1개에 포함되어 중복 합산하지 않는다. 기존 static JS7 PASS와 원 반례13개도 별도 증거다. 이번 브라우저 검사는 unittest 개수에 더하지 않는다.

독립 감사의 [FQ 재검증](../../independent-frontend-fq-recheck-20261026/REPORT-ko.md)은 별도 오프라인 근거다. 원 실패4→4통과, 인접15 및 집중 unittest14 통과를 이번 브라우저 결과로 바꾸어 표기하지 않는다. F07/DM01–03의 기존 경계·승인 보존 검사는 기존/독립 회귀에 포함된다.

## 브라우저 환경·격리

- Ego Lite **TaskSpace36 / p1**, `about:blank`의 격리 소스 재생. **현재 서버에서 받은 페이지가 아니다.** 네트워크를 거친 실제 서비스 연결 검증과 구별한다.
- CLI 실제 경로의 버전 **0.6.0.20**. 설치 앱 plist **0.6.1.11 / build6.1.11**. 업데이트하지 않았다. UA `Chrome/154.0.0.0`, Mac Intel. 두 버전을 혼동하지 않는다.
- CDP로 요청한 값만 쓰지 않고 각 검사 직전 `innerWidth/innerHeight`로1280×900 또는1920×1080을 확인했다. 앱 글자200%는 브라우저 zoom200%가 아니다.
- 현재 index/CSS/media JS를 inline한 fixture에 승인된 합성 프로젝트1개와 미디어4개만 포함했다. 파일 경로·해시/합성 자막·검토 이력 포함. 실제 키나 고객 데이터 없음. CSS/JS inline, asset URL→data URI, synthetic GET 대역, in-memory storage라는 테스트 seam을 명시한다.
- CSP `connect-src 'none'; form-action 'none'`; fetch는 로컬 메모리 `/api/state` 대역만. 최종 기록166개는 **대역 호출 기록**이며 실제 HTTP166건이 아니다. non-GET0, resource network entries0, 브라우저 오류0. 별도의 HTTP20시험은 실제 localhost 요청이다.
- Ego 제어 경로의 외부 중계·보관 여부는 확인되지 않았으며 승인 전 공개한 한계가 그대로다. 페이지의 외부 요청 차단을 Ego 인프라 전체의 로컬 전용 보장으로 확대하지 않는다.
- 첫 로드 후 대기는 음악 단계에서 숨겨진 Take 버튼을 기다려 timeout이었다. 로드는 이미 성공했으므로 다시 로드하지 않고 같은 공간에서 장면 단계로 이동했다. 이 timeout을 제품 결함이나 검증 통과로 세지 않는다.
- native-ended 검사는 저장된 프로젝트를 바꾸지 않고 페이지의 draft만 무음 두 컷으로 구성했다. 실제 `ended`를 강제로 dispatch하지 않았다. FQ01/03은 의도적으로 주입한 브라우저 대역이다. 원본 DB에는 쓰지 않았다.
- 검사 후 **TaskSpace36 정상 종료**. 임시 HTTP 실행 프로세스 exit0 및 모든 listener socket 폐쇄 확인. 앱의 기존 서버/DB는 재시작하거나 수정하지 않았다.
- 추가 OS 프로세스 조회 `ps -p 88395 -o pid=,stat=,comm=`는 환경에서 `operation not permitted`로 거부되어 재시도하지 않았다. 종료 근거는 이미 완료된 exec session의 exit0와 시험 실행기의21/21 socket 폐쇄 기록이며, 별도 process-list 검증을 했다고 주장하지 않는다. 승인된 검사 완료를 막는 항목은 아니다.

## 고정 소스와 보존

|파일|SHA256|
|---|---|
|index.html|`07535dfd93c359de25a6bccdd2713635733ea51063beb6ecebb124867667eed3`|
|studio.css|`a696a80585fff736b2da47ddd08ba8859c5ab94eb8631769b06a9dc8ba335ce0`|
|studio-media.js|`ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`|
|app.py (불변)|`7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`|
|현재 browser-fixture.html|`6f7837799306643fc6484fed078120da2bf867e25b4138755cd2c38c3f600f46`|

합성 QA 프로젝트 정렬 JSON SHA는 `4f29f894cf49cdf48c82bbff27c13f4c447efa50098b827a6881c6955ad59792`로 전후 동일.4개 미디어의 크기/해시와 버전 근거는 [보존 확인](final-preservation.json). 과거 미실행 fixture는 `previous-unexecuted-*`로 별도 보존했다. 현재 캡처3장은 생성 후 실제 픽셀을 열어 확인했다. [최종 브라우저 기록](browser-final.json), [fixture manifest](browser-fixture-manifest.json).

## 남은 범위

이번 승인된 두 검증에는 남은 blocker가 없다. **현재 localhost served hash/실제 서버 화면 재개는 이번 경로로 검증하지 않았다.** 모든24개 독립 QA, 실제 브라우저 zoom/스크린리더, 실제 모델·청구·클라우드 운영의 통과를 주장하지 않는다. 원 감사의 다른 BLOCKED/NOT RUN 항목은 별도 후속 증거가 없는 한 그대로다. 실제 공급자 요청·키 읽기·유료 생성·배포0, canonical 자료 변경0.
