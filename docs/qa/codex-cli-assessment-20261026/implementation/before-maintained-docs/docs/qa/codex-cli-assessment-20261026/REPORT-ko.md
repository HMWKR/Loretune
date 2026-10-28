# Aethon — 계획 정합화 후 구현·현재 빌드 검증

2026-10-26 08:20 UTC 고정. **제품 표시명 전환과 승인된 로컬 검증 묶음을 완료했다.** 새 팔레트·장식·가설에 근거한 구조 변경은 하지 않았다. 이후 Claude 문맥/영상 프롬프트 검증은 별도 읽기 전용 감사와 조율하며 이 소스/DB 기준을 보존한다. [단일 실행 계획](PLAN-ko.md), [최종 manifest](implementation/FINAL-MANIFEST.json).

## 실제 변경과 완료 범위

- **DP26-11 완료:** `index.html:1,13`의 브라우저 제목/제품명, `app.py:1015`의 실행 안내, 현재 README가 Aethon이다. 내부 `LoretuneMedia`, 모듈, 저장/복구 키, `X-Loretune-Token`, 폴더와 원본·과거 문서는 보존했다. [이름/동작 보존 검사](implementation/branding-check.json), [HTML diff](implementation/index-html.diff), [서버 diff](implementation/app-py.diff).
- **DP26-04/07 표본 보완:** S01–12의 현재 화면·fixture·과거·미검증을 아래에서 구분했다. 최신 기획/모델/설정/후보/출력 상태를 실제 서버에서 확인했다. 모든 화면/상태 조합이 통과했다는 뜻은 아니다.
- **DP26-08 완료:** 이 인계, canonical PLAN, README 및 현행 설계 입구/통합 계약을 최신 증거로 연결했다. 역사적 보고서는 그대로 둔다.
- **DP26-01/02/03 및 기존 F07/DM/FQ/VF 보존:** 두 폼의 제출 문맥/편집 revision 보호, 값 보존 토큰, 장면 문맥 헤더를 되돌리지 않았다. 이번 인라인 JS 5개, CSS, 미디어 JS는 배치 전과 byte 동일하다.
- **DP26-05/06은 무조건 수정하지 않음:** active computed를 확인했으며, 수동 컨테이너/비교 버튼 거리/아이콘 가설을 새 결함으로 확정할 관측은 없었다. 승인 완료 상태를 CTA 누락으로 보지 않았다. 따라서 임의 테두리·글자·간격 변경을 생략했다.

## 검사 결과와 실행 주체

|검사|실제 결과·증거|한계|
|---|---|---|
|현재 소스 전체 unittest|**350/350 PASS, 52.579초**, 하나의 `python3 -B -m unittest discover -s tests -v` 실행. 구성은330 비HTTP+20 HTTP. [로그](implementation/full-regression.log), [ID 분류](implementation/test-classification.json)|과거349/330/20을 합산한 숫자가 아니다. 내장 Node 시나리오·선행10/43을 다시 더하지 않는다|
|선행 관련 회귀|두 폼/비동기/시각잔여/리허설10 PASS; local tools/모델선택/미디어creator/bridge/context43 PASS|상위 실행기 검사이며 새 Codex CLI 검사가 아님|
|정적 검사|인라인 JS5개와 media JS `node --check`, root Python44개 AST PASS. [결과](implementation/static-check.json)|전체 접근성/성능 검사가 아님|
|현재 served 화면|HTML/CSS/media JS SHA 일치. 1920/1280×선택/sequence×기본/정밀 **8개 상태**의 같은 조건 치수 유지|픽셀 전체 동일 주장 없음. native controls/dynamic pixels 별도|
|브라우저 두 폼|연출 취향 `preferenceForm`, 로컬 기획 `chatForm` **12/12 PASS**. unchanged/new/동일문구 재편집/A→B→A/rejection/unknown+기존요청조회. [실제 결과](implementation/browser-form-results.json)|통제 fetch 응답. 실제 모델 `modelChatForm` 성공/DB 쓰기 시험이 아님|
|모델/설정 상태|8개 dialog 열기/Escape 닫기, 미선택/선택·연결필요/차단·미검증 사유, 실제 모델 미연결 전송 disabled+초안 유지. [기록](implementation/core-state-inventory.json)|모델 선택은 저장하지 않음. retired/긴 이름 조합은 자동 회귀 중심, 새 live 실행0|
|키보드/앱배율|설명 Enter 열고 닫기, 비교 Escape 포커스 복귀,1280/app200% Take3 전체 노출 PASS. [기록](implementation/tokens-keyboard.json)|앱 배율이지 실제 browser zoom이 아니다. 앱200% 문서 높이1385px reflow는 허용된 접근성 예외|
|실제 UI 로컬 제작|음악1.5초 구간 확정→직접 계획→계획 승인→$0 시험 후보→후보 검토→별도 선택→4컷 편집/자막/음원→승인→출력→납품 검토→reload|격리 DB, 기존 단색 SyntheticImageAdapter. Claude/fal 생성 성공이라고 부르지 않는다|

전체 테스트에 새 테스트를 만들어 개수를 늘리지 않았다. 표시명 수정은 기존 회귀와 실제 소스·브라우저 비교로 검증했다. 첫 명령의 잘못된 test module 이름1건은 loader 오류로 바로잡았으며 제품 실패 수에 포함하지 않았다.

## 현재 화면·치수

같은 기존 합성 프로젝트/장면1/Take1, DPR1, 앱100%, paused 선택1초/sequence편집0.5초 조건이다. 현재 실제 served HTML은 아래 최종 hash다. [8상태 측정](implementation/browser-summary.json), [served 검증](implementation/served-source.json).

|CSS viewport|선택 기본|sequence 기본|선택 정밀|sequence 정밀|문서 높이|
|---|---:|---:|---:|---:|---:|
|1920×1080|431.914|364.914|378.984|311.984|1080|
|1280×900|251.914|184.914|257.703|190.703|900|

숫자는 contain 미디어의 실제 높이(px). Aethon 전환 전 최신 헤더 배치와 모두 동일하다. 일반 화면은 [1920 기본](implementation/1920-selected-basic.png), [1920 정밀 sequence](implementation/1920-sequence-detail.png), [1280 기본](implementation/1280-selected-basic.png), [비교](implementation/comparison-1920.png). 현재 저장 이미지 픽셀을 열어 확인했다. 전 단계 헤더의+36px 개선을 이번 새 개선량으로 세지 않는다.

active computed 표본: body `#F4F4F2 / #101010`,14px/400/21px; button `#F4F4F2 / #242424`,경계 `#858585`,14px/500; input `#F4F4F2 / #141414`,경계 `#858585`; timecode12px/`ui-monospace, monospace`; 진단pre12px/18.6px; skip-link의 의도된 고대비 `#000 / #FFF`. base white/mono 선언을 grep만으로 모두 실제 화면 문제로 취급하지 않았다. `#audioWave`는 이 DOM에 없는 ID여서 null이고, 실제 waveform 측정의 대체 증거가 아니다. 이전 E3 값 보존 검사와 소스 불변을 함께 참조한다. 새 token cleanup은 추가하지 않았다.

## 실제 로컬 결과와 보존

[검증된 MP4](implementation/workflow/verified-output/synthetic-local.mp4), [SRT](implementation/workflow/verified-output/synthetic-local.srt), [출력 측정](implementation/workflow/output-verification.json), [브라우저 재개](implementation/workflow/reopen.json).

- job `2fa8544d046a455294acb892f4b7ad6b`, 타임라인v2, **3.000초/1920×1080/24fps/72프레임**,video+48kHz audio+mov_text 자막.
- 원곡0.5–3.5초와 출력AAC 디코딩144,000샘플 상관계수 **0.9996304**,RMS0.0088442. 사람 청취/음악품질 평가가 아니다.
- 한글 cue0–1.5초 “Aethon 합성 제작 검증”,1.5–3초 “단색 시험 후보 · 실제 AI 생성 아님”. 파일 추출과 브라우저VTT cues 모두 일치. 번인 자막이 아니라 선택형 트랙이다.
- 시험 패턴과 단색 후보 frame을 추출해 실제 픽셀을 확인했다. 정사각형 후보의 좌우 검정은 contain 레터박스이며 전체 검정 프레임이 아니다. 기존 세 컷은 같은 원본패턴이므로 순서 식별 능력까지 주장하지 않는다.
- 출력 확인 창 닫기는 job0 유지. 명시 확인 이후 render job은1개. 후보 승인 당시 selected=null, 이후 UI에서 명시 선택했다. 최종 출력 파일 준비/납품 승인은 별도 상태다.
- 원래3개 장면·Take·검토/음원 버전·타임라인v1 불변. 새 계획은 장면4로 추가, 편집v2에서 길이·음원구간·자막을 명시 입력했다. “선택한Take로 편집 구성”은 새 초안을 구성하므로 이전 trim/자막이 자동 계승됐다고 주장하지 않는다.
- 브라우저 reload 후 persisted project/job이 새 Store 연결의 값과 동일했다. **서버 프로세스 재시작 시험은 이번 여정에서 하지 않았다**. 재시작 상태 회귀는 전체350에 포함한다.
- [보존 backup](implementation/workflow/backup-verification.json): 격리 SQLite supported backup integrity `ok`,14requests/1renderjob/1action/1grant/1reservation, 참조 자산5개+출력3개8파일 hash 일치. 원본 QA DB는 수정하지 않았다. backup DB는 기존 절대 경로를 유지하므로 원 임시 경로 제거 후 복원에는 manifest 경로 매핑이 필요하다.

B5의 입력은 승인된 기존 합성 프로젝트1개와 시험미디어4개뿐이다. 원본 DB는 read-only로 읽고 별도 temp DB에서만14개 로컬 POST를 실행했다. 생성한 단색 후보1개/영상1개도 합성 검증 산출물이다. 로컬 렌더 CPU 비용은 측정하지 않았다.

## 화면/흐름 coverage — 결함과 미검증 구분

|범위|이번 현재 빌드 증거|남은 한계|
|---|---|---|
|S01 작품/설정/재개|작품·IP·보관 dialog 표본, 저장 상태 reload/Store readback, 소스 unchanged|신규/보관/복원 전체 사용자 여정은 fixture/과거 증거|
|S02 음악|같은 WAV 실제재생자료/구간확정·파형표시, 출력 audio 측정|여러 포맷 업로드는 자동회귀; 자동 비트/전사는 미지원|
|S03 직접 기획/실제 모델 대화|직접 계획/기존기획 폼/미연결 actual model 폼을 분리 검증|이번 실제 Claude 호출0; 다음 사용자 요청으로 continuity/prompt 별도 감사|
|S04 모델|미선택·선택불가·blocked·unverified 사유, 저장선택 불변,Escape|실제 provider 활성화/교체live 미검증|
|S05 계획/허용/후보|실제 로컬 DB 계획→허용→$0candidate; 인간 승인≠선택|fal queue/rights/cost는350의fake/contract, 이 UI 여정은rehearsal|
|S06 장면/재생|8상태media치수·현재/재생맥락·실제media; DM/FQ 회귀|모든codec/browser/재생오류 표본은 아님|
|S07 Take/검토|distinct비교,승인≠채택,app200focus,기존draft 회귀|새 실제 사용자 성공률/시간개선 측정 없음|
|S08 시간편집|4컷·수동trim/길이·음원·한글cue 저장v2,승인/렌더|임의30컷·장시간performance 이번추가측정 없음|
|S09 자산/권리|현재자산함·권리dialog읽기,소유권/철회·격리 자동회귀|실제 계정rights 검증·법적 권리판정 아님|
|S10 온톨로지/취향|빈canonical dialog·초안12조건·fixture source/version/rollback 회귀|실제 모델 기억/프롬프트 품질은 아래 별도 gate|
|S11 저장/오류/비용|통제rejection/unknown/중복방지·기존요청조회,예산dialog,회귀|통제fetch≠실제 네트워크 장애;fal403 미해결|
|S12 출력/재개|실제3초1080p fileprobe+한글/audio,납품분리,reload/Store|실provider 생성물아님;프로세스restart는자동회귀 범위|

## 도구·브라우저 provenance와 실패 기록

EgoCLI0.6.0.20,guide2.1.0,UAChrome154,TaskSpace42. 현재 served URL은 임시127.0.0.1:59139(read-only)와54723(isolated workflow)였고 둘 다 종료했다. 첫 서버 non-GET0, 둘째14 allowlisted local actions, provider/chat worker 없음. 로컬 renderer worker 종료 확인. [첫 종료](implementation/server-stop.json), [최종 종료](implementation/workflow/server-stop.json), [공간 종료](implementation/workflow/browser-closed.json).

Ego가 다음 라운드에서 emulated viewport를 원래888×833으로 복귀시켜 workflow 일부 초기 캡처 이름의1920과 실제 크기가 달랐다. `plan-review-1920.png`, `candidate-prepared-hidden-1920.png`는 **888×833이며1920비교 증거로 제외**했다. 뒤의 candidate-result 및 output-reopened는1920×1080을 직접 기록했다. 8셀baseline은 각셀viewport를 기록해검증했다.

준비된승인버튼이 접힌제작도구/비활성모바일panel 안에 있어 첫클릭이 실패했고,상태를조회한뒤 기존펼침을열었다. 정밀편집을중복toggle해닫은harness문제와내부scroll pointer접근실패는저장여부를읽고기존키보드로이어갔다. 실패한조작을무작정재제출하지않았고 DB에는14request/1render만남았다. ffmpeg진단의`.5`옵션은`0.5`로수정했다. reload후 per-document`__flow`계측변수가사라져마지막로깅이실패했으며이미성공한납품승인은반복하지않고DB와새문서를대조했다. reload뒤문서의전체JS오류0주장은하지않는다. 이러한harness오류를제품결함으로세지않았다.

Hallmark2.0.0/Impeccable4.7.1의기존앱·Operate/craft-floor기준을수동적용했다. 새renderlint/detector/overlay/경쟁사연구를실행하지않았다. 새CLI Astra/xhigh read-only/ephemeral검토는정식`require_escalated`심사에서**실행 전 거절**됐다. 이유는“내부소스/계획이 외부모델서비스로전송될수있으며 해당데이터·목적지에대한신뢰할수있는승인이확인되지않음”이다. 대상은이프로젝트의제한된계획·코드검토,명령은`implementation/cli-scope.txt`와본턴기록에있다. 재시도/우회/모델fallback0,새CLI결과없음. 아래기존CLI2세션은역사적성공이며이번검사와구분한다. Ego업데이트안내는있었지만설치/업그레이드하지않았다.

실browserzoom200/400,screenreader,IME,forced-colors전체,axe,cross-browser,성능/메모리장시간,실제고객시험은이번not-run. 키보드표본과앱배율을WCAG전체준수로바꾸지않는다. Ego제어중계/보관여부미확인을로컬page의외부요청없음으로해소했다고하지않는다. 신규 Library upload/기존차단batch재시도0.

## 다음 Claude 온톨로지·세션·프롬프트 감사 인계

코드/DB writer는이통합세션으로유지하며새변경없이독립읽기전용감사에제공한다. 현재코드에는영구LLM기억이아닌서버문맥재구성이있다.

- `chat_runtime.py:128` prepare는현재project로scoped한DB chat_turns를읽고완료된최근8개prompt/answer를handoff에넣는다. `:170`은그handoff+현재prompt를새API요청messages로구성한다. `chat_protocols.handoff`, `model_selection.snapshot`, `production_context.read`가canon/shot/version/action/job handle을제공한다. 별도session경계와이어말하기정확성은새검증대상이며이를영구모델기억이라고하지않는다.
- `production_tools.py:8`에`prepare_video_action`의prompt/model/shot/source/version계약, `fal_dispatch.py:60` prepare_tool→`:39` prepare→`:27` data→model-specificpayload가있다. prompt는선택한chat모델의도구인수이며서버가불변action/권리/승인/모델/가격/입력hash로검사한다. **Claude가실제로좋은영상프롬프트를만들어이경로로연결했는지는이번신규live검증아님**.
- 근거/준비용: `tests/test_chat_runtime.py`, `test_multimodel.py`, `test_execution_context.py`, `test_fal_dispatch.py`, `test_local_creation_tools.py`; [이전실제UI시험](../claude-chat-ui-live-20261025/REPORT-ko.md), [이전영수증실Claude1회](../claude-receipt-recheck-20261025/REPORT-ko.md). 실제모델응답과fake영상경계를별도표시해야한다.
- 08:20:57 UTC read-only원장확인: `docs/qa/anthropic-smoke-20261025/usage.sqlite3`,15row. usage-price합계 **$0.0077580**,각요청micro올림합계 **$0.007764**,미확정양수예약0. [비민감readback](implementation/anthropic-ledger-readback.json). 공급자청구서조회아님. 이번실모델/영상호출0. 다음실호출전다시조회/원자예약해야하며이숫자를영구예산상태로가정하지않는다.

FG26-01(큰문맥검색/인덱스는scoped전체snapshot단계),FG26-02(일반프로젝트용연결·동의·설정코드경계),FG26-03(fal기존CDN403/후속token403,실계정·가격·회수/청구,다른모델live)는남는다. API만해결하면전체제품완성이라고하지않는다. 96FR/143API전체,12live조합,다중사용자출시/WCAG/새디자인점수는완료주장대상이아니다.

---

## 아래는 초기 CLI·스킬 평가 당시의 역사적 기록

# Codex CLI · 설치 스킬 적용 평가 — 2026-10-26

## 먼저 확인된 결과

Codex CLI가 도움말 조회를 넘어 현재 소스·07 요구사항·QA를 직접 대조하고 지정한 순수 계약 테스트 9개를 실행했다. 모두 통과했으며 CLI 프로세스는 exit 0으로 종료했다. 상위 실행기에서는 별도의 프런트엔드 unittest 3개가 통과했다. 이 결과는 과거 전체349개를 재실행한 것이 아니다.

두 번째 CLI 검토에서 **새 P2 결함 1건**을 재현했다. 연출 취향 제안과 로컬 기획 초안 폼은 제출 후 새로 작성한 입력을 이전 요청의 성공 처리에서 지운다. 실제 현재 핸들러와 `act/sendRequest`를 Node VM에서 실행했으며 성공 4개 시나리오가 유실, 거절 2개는 보존이었다. 실제 브라우저 재현은 아니며 제품 코드는 고치지 않았다. [반례 코드](draft-reset-reproduction.cjs)와 [실행 결과](draft-reset-results.json)를 남겼다.

그 밖의 실제 후속 과제는 문맥 검색 범위, 일반 프로젝트 연결 정책/설정 경계, 최신 문서 정합성, 실제 브라우저·제공자 검증의 빈칸이다. 채팅 라우터·정규화 도구 왕복·fal 승인/권리 재검사는 이미 있으므로 다시 만드는 일을 제안하지 않는다. 이번 평가로 새 디자인 점수를 만들지 않는다.

사용자의 최신 지시로 **문제 확인 → 이유·대안·계획 설명 → 작은 구현 → 검증** 순서를 적용한다. 제품 소스 편집은 시작하지 않았다. 구체적인 다음 단계는 [PLAN-ko.md](PLAN-ko.md)에 있다. 기존 원본 명세·감사·공유 DB·미디어는 그대로 보존했다.

## 실행과 증거 구분

| 실행 주체 | 실제 작업 | 결과와 한계 |
|---|---|---|
| Codex CLI 세션1 | AGENTS/README, 07, 최신 QA, 선택/프로토콜/온톨로지/fal 소스 대조; 지정 순수 unittest9 | 9 PASS, exit0. 영속 DB·실제 공급자 검증 아님. [원 응답](CLI-REVIEW-ko.md), [정확한 지시/검사 목록](prompt.txt) |
| Codex CLI 세션2 | Impeccable harden 기반 실제 폼/요청 controller의 비동기 경계; 기존 FQ01/FQ03 부분 회귀 | 기존 JS13 PASS. 새6 시나리오에서 성공4 입력 유실, 거절2 보존. 기존 회귀와 중복이므로 합산 안 함. [응답](HARDEN-CLI-ko.md), [지시](harden-cli-prompt.txt) |
| 상위 실행기 | CLI 발견을 재실행 가능한 docs 진단 스크립트로 보존하고 현행 소스에서 실행 | 동일6 시나리오 결과, exit0. exit0은 반례 기대값의 재현 성공이며 제품 수용시험 PASS가 아님. [결과](draft-reset-results.json) |
| 상위 실행기 | `python3 -B -m unittest tests.test_frontend_async tests.test_frontend_visual_residual -v` | unittest3 PASS. 첫 시험 내부 JS 시나리오를 별도 수로 더하지 않음. [출력](executor-results.json) |
| 상위 실행기 | root/tests Python109파일 `ast.parse` | 문법 통과. 모듈 실행/DB 생성/바이트코드 쓰기 없음 |
| 상위 실행기 | CSS 토큰12쌍 sRGB 대비 계산 | 본문/패널12.7767, 보조/패널9.1538, 컨트롤 경계/패널4.6678, 경계/hover3.5767. 실제 cascade·opacity·강제색상 측정 아님. [계산 코드](check_token_pairs.py), [값](token-pairs.json) |
| 상위 실행기 | 합성 사실2개, 서로 다른 query2개로 메모리 안에서 문맥 조회 | 두 결과 동일, `scoped-snapshot`과 전체 사실2개 반환. 명시된 현재 동작이며 유출/고장이라고 해석하지 않음. [관측](context-observation.json) |
| Hallmark 스크립트 | `node /Users/leesungmin/.agents/skills/hallmark/scripts/sloplint.mjs index.html studio.css --scope app --genre modern-minimal --json` | 정적 FAIL9/REFLEX73/WARN15, exit1. rendered audit 아님. 분류 전 숫자를 제품 결함 수로 사용하지 않음. [원 결과](hallmark-static-before.json) |

CLI 실행 경로 `/opt/homebrew/bin/codex`, 버전 `codex-cli 0.164.0`. 실제 로그의 모델은 `gpt-6-astra`이며 이번 기본 reasoning은 medium이다. 사용자 설정을 변경하거나 다른 모델을 임의 지정하지 않았다. Python3.15.0, Nodev26.11.1. 추가 세션도 같은 읽기 전용·임시 모드이며 결과는 별도 [HARDEN-CLI-ko.md](HARDEN-CLI-ko.md)에 보존한다.

```sh
/opt/homebrew/bin/codex --no-daemon -a never exec \
  --sandbox read-only --ephemeral --skip-git-repo-check --color never \
  -C /Users/leesungmin/Desktop/Loretune \
  -o /Users/leesungmin/Desktop/Loretune/docs/qa/codex-cli-assessment-20261026/CLI-REVIEW-ko.md \
  - < docs/qa/codex-cli-assessment-20261026/prompt.txt
```

CLI 초기화에는 기존 OS 제한을 고려한 공식 `require_escalated` 심사를 사용했고 내부 agent는 read-only를 유지했다. danger/full-access/ignore-rules/로그인·설정 변경은 사용하지 않았다. CLI2는 입력을 `harden-cli-prompt.txt`, 마지막 응답을 `HARDEN-CLI-ko.md`로 바꾼 동일 옵션이다. CLI 정상 모델 실행 자체와 Loretune의 유료 Anthropic/fal 모델 호출은 별개다. 이번에는 후자0, 키 조회0, 업로드0이다. 원 CLI telemetry 로그는 사용자 전달물에 포함하지 않는다.

CLI2 반례 준비 중 소스 문자열의 `(async`를 잘못 분리한 진단 harness가 두 번 SyntaxError로 종료됐다. 구분자를 정확한 줄 경계로 바꾼 뒤 실제 현재 handler/controller를 실행해 위 결과를 얻었다. 이 harness 작성 오류를 제품 결함으로 세지 않는다. 재실행용 docs 스크립트에는 수정된 분리 방식이 들어 있다.

## 코드·명세 대조에서 실제 남는 범위

| 영역 | 현재 근거 | 남는 차이/다음 판정 |
|---|---|---|
| MS-FR01/02/07/27 | `chat_protocols.py:45`, `chat_runtime.py:191`의 normalize→서버도구→원 호출ID 결과→continuation; `ChatRouter`는 `chat_runtime.py:222` | codec/fixture와 실제3chat×2image×2video를 구분. 9개 검사로 전체AT 통과 표시 금지 |
| MS-FR03/09/11 | `model_selection.py:8`, `:32`, `:45`, `:63`의 역할별 registry/선택/미디어 문맥; `production_context.py:18`의 현재 작품 handles | 미검증 연결 차단은 의도된 안전 동작. 새 registry 항목 또는 키 유무만으로 활성화 불가 |
| 문맥 검색, MS-FR11/12 관련 | `production_tools.py:70` query는 검증하지만 검색 결과를 좁히지 않고 scoped snapshot 전체 반환. `07…md:316`은 독립 검색 인덱스/버전을 설명 | 실제 검색·인덱스 품질은 구현/검증되지 않았다. 작은 승인 문맥에는 작동하지만 큰 문맥 처리까지 완료라 부르지 않는다. 먼저 범위·근거ID·빈 결과·버전 계약을 계획 |
| 일반 제작 채팅 | `chat_runtime.py:116`은 synthetic_only/정확한 입력hash/만료/모델/가격 검증; `app.py:886`은 trusted injection, `:1008` 기본 실행은 port/data만 받음 | 일반 사용자 프로젝트를 실행할 검증된 연결·동의·설정 경로는 아직 제한됨. 단지CLI가 동작한다고 풀 수 없다. 안전한 설정 코드와 실제 전송 승인을 별개로 다뤄야 함 |
| OpenAI/Grok 비용 사전검사 | `chat_adapters.py:20`은 신뢰한 counter가 없으면 차단, `:27`은 연결 미설정 시 차단 | 해당 공급자의 검증된 counter/connection 주입과 실계약 시험이 필요. 추정 count endpoint를 만들거나 Claude로 대체하면 안 됨 |
| 온톨로지 | `project_ontology.py:79`의 grounded 제안, `ontology.py:170`의 승인 적용; `local_creation_tools.py:64` 정확한 출처와 revision | 서버 canon/승인/rollback 경로는 존재. 스키마 성공을 사실 정확성이나 전체 품질로 바꾸지 않음. 이번 신규 시험은 이 전체경로의 재실행이 아님 |
| fal 제작/회수 | `fal_dispatch.py:79` gate, `:114` 제출 직전 권리·grant·입력·가격·job 재검사 | 공개 fallback 금지/기존403 보존. 결과 수집·계정권한·실청구는 외부 증거가 필요하며 새로운 생성 승인으로 간주하지 않음 |
| 프런트엔드 | FQ/VF 새 소스와 기존 반례 회귀3 unittest 통과 | 최신 이미지/후속 브라우저 증거는 현재 소스의 격리 replay. 현재 서버 served hash나 다중엔진 검증을 대신하지 않음 |
| 새 async 폼 결함 | `index.html:356` preferenceForm / `:375` chatForm의 성공 후 무조건 reset | 수정 중 입력/프로젝트 문맥을 확인하지 않음. local `chat_plan` 폼이며 실제 모델 요청 `modelChatForm`과 구분. 새 입력 revision/문맥 guard가 첫 계획 |
| 문서 | README:3은346/이전 인계, 최신 `docs/handoff-20261026-frontend-fq-vq.md:6`은349 분할실행 | 최신入口 링크와 상태표를 바로잡되 초기07 인계/원본명세는 역사적 기록으로 유지. 이미 구현된11도구를 다시 미구현으로 적지 않음 |

## 설치 스킬을 실제로 어떻게 적용했는가

- **Hallmark2.0.0**: `/Users/leesungmin/.agents/skills/hallmark/SKILL.md`, `references/redesign.md`, `flow.md`의 app/harness, `gates.md`1–5를 읽었다. audit/app scope 정적 검사에 적용했다. 마케팅 hero/80단어/중앙컨테이너 규칙을 편집기에 이식하지 않는다. 원문도 app scope에서 해당 규칙을 제외한다. 새로운 테마·Together API·이미지 생성·설치는 실행하지 않았다.
- **Impeccable4.7.1**: `/Users/leesungmin/.codex/skills/impeccable/SKILL.md`, `reference/audit.md`, `harden.md`, `operate.md`를 읽었다. Operate의 절제·고정 rem·표준 조작/상태 원칙을 적용했고 별도 CLI에서 입력/폼 경계를 점검해 위 반례를 얻었다. 시각 점수표는 이번 증거 범위를 벗어나므로 작성하지 않는다.
- Impeccable context는 자동 다운로드를 차단한 `IMPECCABLE_LAUNCHER_PROBE=1 sh …/scripts/impeccable context --target index.html`로1회 시도, exit127. sibling/cache 엔진 없음. SKILL의 **“Context loading did not run; I’ll read the existing project context directly.”** 대체 절차로 기존 문서/소스를 직접 읽었다. 스킬 텍스트는 실제 사용했지만 detector 엔진을 실행했다고 주장하지 않는다.
- root PRODUCT.md/DESIGN.md는 발견되지 않았다. 이를 근거로 기존 화면을 새 제품처럼 취급하지 않았다. 이미 유지 중인 디자인 문서와 중성 token/CSS가 설계 근거다.

Hallmark의9FAIL 중 확인된 작은 정리 대상은 `index.html:45` 음원 파형의 `background:#101010`, `stroke="#ddd"` literal이다. 현재색 자체가 잘못됐다는 뜻이 아니라 token기준 밖의 값이라는 뜻이다. 반면 `:not(:disabled)`를 disabled로 검출한39a는 오탐이고, 기본 opacity규칙은 뒤의`.lt-ui` 스타일을 함께 봐야 한다. stamp부재, `100vw` 문자열, middle-dot 문구는 각각 도구전용 규약·렌더 미확인·스타일 취향이므로 승인/정보/접근성을 훼손하면서 자동 수정하지 않는다. FAIL9를 결함9나 품질점수로 변환하지 않았다.

## MCP와 환경 한계

실제로 호출한 개발 MCP는 `mcp__lsp__status({})`다. 결과는 `LSP daemon unreachable`, `/Users/leesungmin/.omo/lsp-daemon/v0.1.0/daemon.sock` 연결 실패였다. 정책 거절이 아니라 서비스 사용 불가이며 재시도·재설정하지 않았다. 동일 코드의 Python AST/NodeVM으로 가능한 검사를 수행했다. 이 대체가 LSP 전체 diagnostics와 같다는 뜻은 아니다.

Refero 검색/화면조회, OpenAI 공식문서 MCP는 현재 도구목록에 노출된다. 해당 도구의 존재만으로 이번 호출 성공을 주장하지 않는다. Refero는 독립 디자인 작업이 기존 참조 검토에 사용하므로 중복 광범위 조사하지 않는다. 제품의 noMCP는 미디어 제작 아키텍처 제약이며 이런 개발 도구의 사용 금지와 다르다.

Library는 별도 차단이다. 시작된 helper batch에서 `prepare_uploads`가 없던 문제를 CLI나 다른 업로드 경로로 우회하지 않았다. 이번 Library 재시도0. 새 공급자 키·권한·청구·CDN403·도구 가용성은CLI 설치만으로 해결되지 않는다.

## 우선순위와 실행 조건

| 우선순위 | 지금 가능한 일 | 기대 결과/검증 |
|---|---|---|
|1|계획 설명 후 두 폼의 입력 revision/문맥 guard|새 초안 보존, 정상 무수정 성공은 초기화, unknown/duplicate guard와 F07 유지. 첫 변경은이 범위로 한정|
|2|최신 served baseline 확인 및 Hallmark findings의 cascade/의미 분류, 파형색 token화의 값 보존 변경안|마케팅 규칙 적용 없이 지정된literal 정리; 동일색·음원 데이터·접근 이름·SVG점 유지|
|3|확인된 공간·위계 미세 조정과 유지 문서 정합성|1920 주 기준/1280 보조. 과거 다른 상태의 미디어 크기를 새 결함으로 쓰지 않음. 이미 있는11도구를 중복 구현하지 않음|
|4|문맥검색 범위의 최소 계약/합성 평가 설계|범위/근거ID/빈 결과/승인버전/큰 문맥 예산을 명시. 새 임베딩 공급자 추가 없이 별도 제안|

브라우저/환경이 필요한 작업: 같은 fixture와 정확한 served source를 고정한1920/1280 재확인, native 한글IME, 실제200/400% browser zoom, forced-colors 오류+focus, 실제 보조기술, decoded-frame/AV계측. 앱배율과 실제browserzoom을 동일시하지 않는다. 새 환경/설치/전송이 필요한 경우 정확한 범위를 별도 확인한다.

CLI만으로 불가능: 계정·자격증명 권한 승인, fal 결과 인증복구나 실제청구 증명, 실고객 평가, 실제 다른OS/브라우저 보장, Library capability복원. 기존 사용자승인을 불필요하게 다시 요청하지 않되 이번 과제 밖의 실호출은 하지 않는다.

## 보존 및 증거

시작 시 root source/tests119개 SHA256을 [baseline.json](baseline.json)에 고정했다. [preservation-check.json](preservation-check.json)에서 변경0을 확인했다. 아래 주 파일은 이번 계획단계 동안 동일하다.

|파일|SHA256|
|---|---|
|index.html|07535dfd93c359de25a6bccdd2713635733ea51063beb6ecebb124867667eed3|
|studio.css|a696a80585fff736b2da47ddd08ba8859c5ab94eb8631769b06a9dc8ba335ce0|
|studio-media.js|ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9|
|app.py|7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d|

원본 최종 이미지2개를 읽어 픽셀 확인했다: `../frontend-fq-vq-fixes-20261026/authorized-verification/vf02-long-title-1920.png`, `vf01-take3-1280-app200.png`. 새 캡처가 아니며 각각1920긴제목과1280앱200%포커스의 이전 허가된 격리replay다. 실서버/실고객/실제모델 이미지로 재명명하지 않는다.

독립 디자인 검토는 별도 세션에서 스킬을 수동 적용했으며 render lint/detector 미실행이다. 이 보고서의 Hallmark 정적 실행은 통합 담당이 수행한 별도 증거다. 디자인팀의 역사적718×404/505×284 관측은 상태가 다르므로 현재 소스의 미리보기 퇴행 증거로 쓰지 않는다. 최신 실행 화면을 고정한 후에만 같은 상태의 전후 평가를 진행한다.

변경 기록: 2026-10-26 — CLI1 계약 검토, CLI2 hardening 반례, 상위 재현과 사용자 요청의 계획 선행 순서를 통합. 작성/수정 파일은 이 평가 디렉토리의 산출물뿐이며 제품 소스·원본 명세·역사적 보고서·공유 DB는 변경하지 않았다.
