# fal 제작 승인·기존 결과 회수: 기능 스테이징 완료

2026-10-25 UTC. **요청한 기능 스테이징은 완료했다. 실제 앱은 동결 상태이고 통합하지 않았다.** 디자인 작업과 합쳐 통합할 수 있는7파일 패치를 제공한다. 외부 API 호출·키 조회·실제 비용 발생0. 실제 fal 성공이나 전체 MVP 완성으로 판정하지 않는다.

## 전달물과 고정 버전

- [적용 패치](integration-fal-creator.patch), [파일별 원본/변경 해시](patch-manifest.json), [패치 적용 검사](patch-check.json). 원본 파일3개 수정과 신규4개. 원본을 복사한 별도 임시 폴더에서 dry-run/실제 patch 적용 후7파일 모두 스테이징 해시와 일치.
- [디자인 표시 계약](PRESENTATION-CONTRACT.md): 선택 모델·준비 상태·견적·승인·작업·결과·다음 행동의 서버 필드, 실제 DOM/handler 접점. 디자인 작업자는 이 계약으로 표시를 통합한다.
- [전체326건 로그](full-regression-final.log), [자동/수동 검증 표](QA-MATRIX.md), [출력/DB 근거](workflow-evidence.json), [재시작/브라우저 근거](restart-browser-evidence.json).
- [5초 합성 출력](synthetic-final.mp4), [한국어 자막](synthetic-final.srt), [불변 출력 manifest](synthetic-final.json).
- 실행 source: `/var/folders/t7/p6pl4snd6pd3cmz1y80_7fzw0000gn/T/loretune-fal-creator-z4_ck507`.
- 별도 합성 fixture: `/var/folders/t7/p6pl4snd6pd3cmz1y80_7fzw0000gn/T/loretune-fal-creator-fixture-miuh1if7`.

| 대상 | SHA-256 |
|---|---|
| 원본/실제8773 index | `1b0ab597f7a16993cf9307ae4a5fdd948b7ed5948c2970b16b7d53670ef269b3` |
| 원본 app.py | `9d316c8269e0addfca609065912630b45b196107a84d86f3f997f0a75861c582` |
| 스테이징/검증64864 index | `b094f68a68dbaf2f0c950abc57dedf31d8853438626e7f19a18b57ee69f9da7a` |
| 스테이징 app.py | `c13df5375c1f2e4171a3f9b2abe53868d163536e5cce621de458d06c7295dfe7` |
| 통합 패치 | `d9799d93676dbb621714f0e3eb64c723c1622114634ecf1df940c250ef43a53e` |

원본 baseline drift=[]; 공유 DB/.env/실제 자산을 복사하거나 수정하지 않았다. 별도 QA 서버를 최신 스테이징 source와 같은 합성 DB로 재시작해 저장 복원을 검사했다. 마지막에 소유 PID13836/포트64864만 SIGTERM 종료(exit143)했고 Ego 전용공간17도 finish 완료했다. 실제8773 서버는 그대로다. [정리 기록](cleanup.json)

## 실제 변경

1. **선택과 사용 가능 상태 분리.** `media_creator.capability`가 저장된 role 선택을 기준으로 표시한다. FLUX가 선택됐지만 실행 연결이 없으면 이름을 유지하며 연결 미검증으로 표시한다. 미선택·미검증·차단/종료를 구분한다. 기존 이미지 panel도 같은 정보에 연결했다. 실 registry를 활성화하지 않았다.
2. **사람 승인→기존 queue 연결.** `media_action_decide`는 기존 saved action/grant/reservation 서비스를 사용한다. 승인·보류·거절·재검토·실행이 실제 API에 연결된다. 모델이나 입력이 달라지면 재준비가 필요하고, 같은 action 실행을 반복하면 기존 job만 반환한다. 모델이 보류/거절을 우회하지 못한다.
3. **회수와 생성 분리.** `media_recovery`는 원래 request/action/grant/project/rights와 일회 복구 근거를 검증하고 기존 큐를 사용한다. status와 collect를 구분한다. 403/401은 해결 근거 없이는 재시도할 수 없다. 로컬 오류가 이전 권한거절을 지워 복구 조건을 약화시키는 결함도 막았다. recovery에서 submit을 호출하지 않는다.
4. **후보 수집과 채택 분리.** 수집 완료→로컬 파일 검증·저장·Take 등록 이후에도 기존 선택/승인은 유지된다. 사용권·첫 프레임·새 Take 선택과 검토는 기존 서비스로 처리한다. 이미지의 private provider URL을 영상 입력으로 복사하지 않고 승인된 로컬 이미지 bytes 경계를 사용한다.
5. **일반 제작 UI 완결.** 현재 장면 준비, 견적, 조건 승인, 보류/거절, 실행/취소, 기존 결과 회수, 사용권 기록, 후보 검토까지 실제 handler를 연결했다. legacy 패널의 중복 recovery 버튼은 제거했다. 내부ID/hash/grant는 기본 카드에 숨겼다. draft는 프로젝트/장면/역할/작업 문맥에 묶고 F07 보호를 보존한다.
6. **상태 갱신과 provenance 수정.** job이 그대로여도 회수 허가·견적 준비 상태가 바뀌면 poll이 갱신한다. `contract-fake` 저장 provenance를 읽어 테스트 미디어 badge를 표시한다. 새 미디어가 실제 생성처럼 표시되지 않는다.

파일: `app.py`, `fal_dispatch.py`, `index.html`, 신규 `media_creator.py`, `media_recovery.py`, `tests/test_media_creator.py`, QA 전용 `scripts/fal_creator_fixture_server.py`. 새로운 공급자/모델을 추가하지 않았다. 기존 noMCP·Runway 비활성·자동 대체 없음 유지.

## 검증한 실제 사용자 흐름

Ego Lite0.6.0.20 / guide2.1.0 / 전용공간17 / 별도localhost64864. 프로젝트는 가상 `합성 모델 제작 QA`,1장면·2Take다. 이 브라우저 표본을 다중장면 전체검사라고 부르지 않는다. 문맥/프로젝트 격리·동시성은 별도 자동시험이다.

1. canned chat의 실제 tool roundtrip으로 계획을 저장했다. 사람이 계획을 적용하고 이미지 action을 준비했다. 채팅은 `contract-fake`이며 이번에 실제 Claude 호출은 없다.
2. 이미지 작업을 보류한 뒤 재승인·실행했다. fake submit1회 후 의도적으로 다운로드를 끊었다. 같은 request의 일회 결과 회수로 Take1을 등록했다. 이때 선택/검토는 자동으로 바뀌지 않았다.
3. 이미지 사용권을 기록하고 Take1을 선택한 뒤 시작 프레임을 승인했다. 선택된 영상 모델의 입력/비용을 검토·승인하고 fake submit1회로 Take2를 받았다. Take2 생성 이후에도 Take1 선택이 유지됐다.
4. 사람이 Take2를 선택·검토 승인했다. 원본5초 음악과 한국어 자막을 포함한 timeline을 저장하고 별도 출력 버전을 승인한 뒤 실제 로컬 렌더를 수행했다.
5. H2641920×1080/24fps/5.000초 + AAC48kHz/5초 + mov_text한국어자막0–4.5초를 확인했다. 음성 신호 peak4317로 무음이 아님을 확인했다. browser duration/resolution와 WebVTT cue도 같은 값이었다. 전체 음질·지각적 싱크 평가를 완료했다는 뜻은 아니다.
6. 서버를 provider 연결 없이 재시작했다. 모델 선택, 두 Take, 선택/검토, 출력, 같은 자막이 보존됐다. FLUX는 미선택으로 바뀌지 않고 연결 미검증으로 표시됐다. 재생성 없음. 출력 파일 준비와 납품 승인도 구분되며 납품 승인은 수행하지 않았다.

출력 SHA256 `22a304c2f0fb6fd53b9d655f43b9034babdae86e47f4943a66fd709921021567`. 합성 fake submit 총2회, 외부 submit0. 다운로드2번은 이미지의 의도적 실패1회+명시적 회수1회이며 재생성 횟수가 아니다. [전송 기록](fake-transport-events.json)

## 화면 증거

- [기존 결과 회수 카드](screens/01-existing-result-recovery.png):900×845. 권한 확인 후 기존 결과 연결 버튼, 모의 전송·시험 견적 표시.
- [첫 출력 확인](screens/02-local-output-1280.png): badge 보강 전 중간 frontend 화면. 최종 시각 근거와 혼동하지 않는다.
- [최신390px·모델 선택 보존](screens/03-selected-unverified-restart-390.png): FLUX 선택+연결 확인 필요를 함께 표시, 수평 overflow없음.
- [최신1280px·재열린 출력](screens/04-reopened-output-1280.png): 테스트 미디어 포함, 승인 자막, 선택Take2, 납품 검토 전 구분.

모든 저장 이미지를 이미지 도구로 열어 확인했다. 화면에는 아직 기능 카드와 legacy 표시가 함께 있어 디자인 통합 대상이다. 최신 실제앱 독립점수70/100을326tests로90으로 바꾸지 않는다. 실제200/400%zoom, screenreader, 전체keyboard여정, 고객사용성시험은 이번에 하지 않았다.

## 유한 완료/대기 목록

| 범위 | 판정과 남은 단계 |
|---|---|
| 이번 로컬 기능 연결 | **staging code/fixture/UI검증 완료**. 승인·실행·회수·등록·검토·출력·재시작까지 연결. 현재 알 수 있는 이 범위의 미구현 버튼 없음. |
| 실제앱 통합 | **부모 조정 대기**. 디자인 표현 패치를 같은 frontend에 합친 뒤 원본 회귀·localhost재시작·통합 UI검사가 필요. 실행을 거절당한 것이 아니라 명시적 source freeze 준수다. |
| fal 이미지·영상 실제 경로 | **live 미검증/비활성**. 선택endpoint의 현재 가격·계정 접근·입력/권리/비공개전송조건·승인범위를 고정하고 별도 실제시험 필요. 기존 실패 Kling URL/요청 재시도0. fixture통과로 private ACL/token/ownership 문제가 해결됐다고 주장하지 않는다. |
| 복구 권한 | **안전한 코드 연결 완료, 실제 증거 발급은 미검증**. runtime의 정확한 기존request/operation/expiry/해결근거 gate가 없으면 UI가 비활성. 사용자 버튼이 스스로 새권한을 발급하지 않는다. 실제403은 새 관련근거 없이 재시도 불가. |
| 비용 | **견적/예약/unknown/기록된 실제 사용량 표시 연결**. 이번 quote는 fixture0.01USD×2로 실청구가 아니다. 인증된 billing조회/청구서 대조는 이 시험 범위 밖이며 실제비용으로 만들어내지 않았다. |
| 다른 chat/모델 조합 | 기존 normalized adapter의 fixture근거만 유지. OpenAI/Grok 및3×2×2조합 실제검증은 별도 계정/전송/비용승인과 live시험 필요. 과거Claude 실제 한 경로 성공과 이번fake흐름을 합쳐 전체실검증이라고 하지 않는다. |
| 단일사용자 로컬MVP 밖 | 다중사용자 배포·SSO·외부운영·청구계정변경·전체96FR/143API완료는 이번 패치 범위 아님. 새 인프라를 추가하지 않았다. |

스테이징 완료에 새 제품결정은 필요 없었다. 다음 단계는 디자인과의 한 번의 통합이며 새로운 실모델 활성화가 아니다. Ego 업데이트 알림이 있었으나 업데이트/설정변경은 하지 않았다.
