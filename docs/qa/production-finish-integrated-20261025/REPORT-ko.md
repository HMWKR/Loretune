# 실제 소스 통합·최종 로컬 검증 완료

**fal 제작 기능7파일과 production-finish 디자인 패치를 원본 Loretune에 적용했다. 전체326개 회귀, 실제 통합본 표시 계약19개, 합성 제작→출력→재시작 복원을 검증했다.** 스테이징만 전달한 상태가 아니다. 소스/서버는 독립 디자인 검토용으로 고정했다. 점수90은 아직 판정하지 않았다.

## 고정 runtime

- URL: `http://127.0.0.1:8773`, PID16258. 동일 기존 QA 데이터 `/tmp/loretune-ms-qa-20261025`로 정상 재시작. 시작 전 진행 작업0 확인.
- 실제 source/served HTML SHA256: `1102648a5e92b5880e6980385426e3b0f3ec61fa531b1aef5f4eaacf37756b2b`.
- backend app.py SHA256: `c13df5375c1f2e4171a3f9b2abe53868d163536e5cce621de458d06c7295dfe7`.
- 고정 시각:2026-10-25T16:57:32Z. [확인](frozen-runtime.json).
- 기존 수정파일은 `before/`에 보존했다. 원본 문서·.env·실제 사용자 자산·이전403기록은 변경하지 않았다.
- 기능 패치 기준1b0ab597…→b094f68a… 일치 확인 후 적용했다. 디자인 패치를 그 위에 적용했다. 완성본 해시는 디자이너의 초기 후보b02db8e7…와 다르며, 최신 기능 소스에 합친 결과다. [적용 로그](integration.log), [전체 변경 해시](integrated-files.json).

## 통합된 내용

- 사람의 승인/보류/거절과 기존 action/grant/budget/queue 연결. 기존 결과 회수는 새 생성과 분리하고403/401 해결근거 검사를 유지한다.
- 저장된 모델을 미선택으로 바꾸지 않는다. 실제8773에서 FLUX Schnell은 **연결 확인 필요**, Kling2.6Pro는 **현재 사용 불가**로 표시됐다. registry 활성화·자동fallback없음.
- 제작 도구를 검토 카드 하위로 묶고, 진행/오류/미확정 요청은 노출한다. 원래 승인/복구/사용권 handler·F07 controller를 보존했다.
- 비교stage는1280×900에서 양쪽288px이고 contain으로 원래비율을 보존한다. 선택·검토·focus표시를 분리했다. 모바일 저장/취소44px과 오류 시 입력보존을 확인했다.

변경파일: `app.py`, `fal_dispatch.py`, `index.html`, `media_creator.py`, `media_recovery.py`, `tests/test_media_creator.py`, `scripts/fal_creator_fixture_server.py`. 별도 provider/기능을 추가하지 않았다.

## 최종 검증 결과

| 검증 | 기대 | 실제 결과·근거 |
|---|---|---|
| 전체 원본앱 회귀 | 기존기능/HTTP/안전경계/새기능 유지 |326pass,42.925초. [로그](full-regression-authorized.log) |
| 표시 계약 | 원래권한·handler·F07·ID보존,모델상태/escape |실제mergedHTML로19pass. [상세](presentation-tests.json) |
| 정적 검사 | Python/JS문법정상 |110Python AST,4inlineJS pass. [상세](static.json) |
| 실제 다중장면 작업대 | 미디어/검토/timeline 접근 |8773의 기존3장면합성fixture,1280×900캡처 및재생 확인 |
| 혼합종횡비 비교 | 다른Take,원본비율,같은stage높이 |128×128/640×360 모두288px,object-fit:contain. [측정](comparison-metrics.json) |
| 비교 Escape | 원래버튼포커스복귀 |compareButton으로복귀 |
| 모바일 검토 | 입력/상태읽기,overflow없음 |390px와375px document width동일,저장44px |
| 오류·초안 취소 | 오류가입력을지우지않음,취소포커스복귀 |로컬act=false주입에서입력보존·저장확인필요,취소후creatorEditReview포커스. 실제서버실패로해석하지않음 |
| 문맥·비동기초안 | F07/다른Take·프로젝트보호 |전체회귀/표시계약통과. 이번브라우저에서모든동시문맥조합을반복하지않음 |
| 제작 전체여정 | tool→계획→사람승인→queue→회수→Take→출력 |아래 실제UIflow완료. provider/chat는fake,파일/DB/renderer는실제 |
| provider없는재시작 | 모델선택·Take·출력·자막보존 |동일DB정상앱재시작후복원. [결과](restart-restore.json) |

첫 기본sandbox시험은19개localhostbind가 PermissionError로 실행되지 않았다. 사용자의 기존 HTTP시험 승인에 따라 정식 require_escalated 경로로 재실행해326건 모두통과했다. [처음 기록](full-regression.log)을 보존했으며 권한거절을 제품오류로바꾸거나 통과로덮지않았다. 자동승인심사의 추가거절은 없었다.

브라우저 일부wait는 모바일숨김레일, 계획적용후자동step이동, `approved`/한국어표시 및 잘못된승인배열조건 때문에 실패했다. 실제상태를읽고커밋된작업은재제출하지않았다. 최종task별결과는위에구분했다.

## 합성 제작을 실제 UI로 끝까지 검사

원본소스의 `scripts/fal_creator_fixture_server.py`를 별도localhost64098/가상DB로 실행했다. canned chat tool결과와 fakefal HTTP만 주입하며 사람승인/Take선택을 주입하지 않았다.

1. chat tool→계획 저장→사람이장면적용→선택된FLUX action준비.
2. 이미지action 보류→실행버튼없음→재승인→fake submit1회.
3. 의도적download_interrupted→기존request에고정된일회회수→이미지Take1. 자동선택없음.
4. 사람이사용권기록/이미지선택/시작프레임승인→선택Kling2.5Turbo 준비/승인→fake submit1회→영상Take2. 수집후에도Take1선택보존.
5. 사람이Take2사용권/선택/검토→5초원곡·한국어자막편집저장→별도출력버전승인→로컬ffmpeg렌더.
6. 실제파일5.000초/1920×1080/24fps/H264/AAC48kHz,한국어mov_text0–4.5초. 음원peak4317로무음아님. browser동영상재생readyState4/currentTime1.098초와활성자막본문확인.
7. 모든job완료후같은DB를provider설정없이정상app으로재시작. 두Take/선택2/출력완료/자막/모델선택보존. image/video 모두unverified·available=false·can_prepare=false. 재생성없음.

[UI/DB 연결 근거](browser-workflow.json), [전송 횟수](fake-transport-events.json), [파일 검증](media-verification.json).
출력ID `df6064eedeeb414da235bf3b86df4a7f`.
SHA256 `50e8ca9dbe30b4e68f0a98a06e135af8953e6120bdd7818bd0753ab90f41be47`.
[영상](synthetic-final.mp4), [자막](synthetic-final.srt), [manifest](synthetic-final.json).

이번외부API호출/키조회/실제비용0. fake이미지1회+fake영상1회. 가상견적은실청구가아니다. 기존Anthropic사용량과fal과금이력을변경하지않았다. 생성완료와납품검토승인은분리됐고납품승인은수행하지않았다.

## 실제 통합 화면 packet

모든 아래 주요 캡처는 후보iframe이 아니라 실제 통합source에서 제공된 화면이며 저장후이미지도구로열어확인했다.

- [데스크톱·3장면](desktop-1280.png):8773,1280×900,기존합성fixture. 실제video재생후일시정지.
- [혼합비율·승인/미검토 비교](comparison-mixed-aspect-1280.png):8773,1280×900.
- [이미지/영상 비교](comparison-image-video-1280.png):8773,1280×900. nativecontrols유지.
- [모바일 검토](mobile-review-390.png):8773,390×844.
- [모바일 오류·입력 보존](mobile-review-error-projection-390.png):8773 frontend,act=false로컬계측. sharedDB저장없음.
- [모바일 선택 모델 문맥](mobile-selected-model-scrolled-390.png):8773,390×844. 제작도구는하위에있어캡처하단일부만보인다. 두모델명/상태는실제DOM으로확인했으며둘다화면상단에보인다는주장은하지않는다.
- [회수 가능한 기존 결과](existing-result-recovery-1280.png):64098,동일실제source+fake전송.
- [재시작 후 출력·실제자막 표시](output-reopened-1280.png):64098,동일source,provider없는정상app재시작.

## 종료와 남은 범위

실제8773/PID16258을고정유지한다. 별도64098합성서버는소유자/명령확인후종료했고Ego공간19도finish완료했다. Ego업데이트알림은있었으나설치하지않았다.

이 통합 작업의미실행단계나차단은없다. 다음은부모가조정하는동일rubric독립디자인평가다. 이번test수를디자인점수로환산하지않는다. 실제200/400%zoom,screenreader,고객사용성시험·전체키보드여정은미검증이다.375/390viewport를zoom검사로대체하지않았다.

fal실제private출력접근/인증·새모델실검증,다른chatprovider실호출,3×2×2live조합,실청구대조는여전히별도게이트다. 외부모델활성화없음. 기존403근본원인을이번fake성공으로해결했다고주장하지않는다. 다중사용자배포나전체96FR/143API완료도선언하지않는다.
