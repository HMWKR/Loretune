# D1-frame-observation-design 재작업 3차 결과 (S13, 설계 문서만)

대상: `docs/design/FRAME-OBSERVATION-DESIGN-ko.md`
- 수정 전(r2): 33,492바이트, sha256 `3554061a584b883e8095688229508c231715e631ce7fe9f2ad5e6f14bc112ee7`. 시작할 때 이 폴더에 `FRAME-OBSERVATION-DESIGN-ko.before-r3.txt`로 사본을 떴고, 해시가 r2 acceptance 값과 같음을 확인했다.
- 수정 후(r3): 49,262바이트, sha256 `1552a6748d2bf9ec58afb73cc2746f70d683501391cf66463e9931b42e409192`.
- diff: `changes.diff`. 설계 문서와 인용 검사 스크립트(r2 → r3)의 diff를 담았다.

근거 자료: `rework-r2-verdicts.json`의 D1 판정(serious 1건, minor 4건), A1 판정의 cross-track 지적(chat_runtime 줄 이동), PLAN-ko.md §6 D15, §8-4 D19·D20·D21, §8-5, `codex-gate/review-1.md`, `before/` 사본, 그리고 r2 result 4개(A1·B1·C1·D1).
쓰기 범위: 위 문서와 이 폴더만 고쳤다. 코드, 다른 트랙 파일, 문서 게이트 등록은 건드리지 않았다. 등록하지 않았다(No registration).

## 항목별 조치
문서 줄 번호는 수정 후 문서 기준이다.

| # | r2 critic 지적 | 조치 (문서 위치) |
|---|---|---|
| 1 (serious) | 프레임 바이트가 도구 결과에서 `result_message`까지 가는 경로를 설계하지 않음. run calls·멱등 재실행·`requests` 테이블·쓰기 트랜잭션 문제 누락 | **§4-4를 새로 만들었다(73-109행).** (1) 현재 경로 5단계를 `before/` 기준 줄로 정리했다: `chat_general.py:763/771`, `app.py:496-497`(BEGIN IMMEDIATE, requests 재생), `app.py:806/813`, `production_tools.py:64/67/139`(run calls 재생·저장), `app.py:1001/1003`(state 본문·requests 저장), `chat_general.py:777/778/789`. (2) **결정 권장안 i**: 1단계 mutate 안에서는 렌더하지 않고 바이트 없는 요청 영수증만 저장한다. 2단계 mutate 커밋 뒤 쓰기 트랜잭션 밖에서 `timeline_preview`로 렌더하고, 바이트는 메모리에만 둔다. 3단계 미리보기 생성 트랜잭션(`chat_general.py:783-790`)에서 블록 배열 결과를 만들고, 해시 메타만 turn step에 남긴다. (3) **멱등 재실행 의미**: 영수증은 정확히 재생된다. 바이트는 미리보기 행 생성 전까지 휘발성이다. 중단되면 `recover`가 outcome_unknown으로 동결한다(`chat_general.py:549-555`). 다시 렌더한 바이트가 같다는 보장은 하지 않고, "사람이 본 바이트 = 전송 바이트"를 wire sha로 고정한다. (4) 대안 ii(바이트 영속, 스펙 :418 예외)는 비권장으로 적었다. (5) **보관 위치 전수 표(11행)**: requests·run calls·turn 행·preview 행·브라우저 응답(새로 찾은 `/api/state` `app.py:384`의 대기 미리보기 두 본문 반환과 생성 응답 `:469`)·동의 카드·공급자 전송·**오프라인 백업**(`backup.py:51,63`, 새로 찾음)·원장(해시만, `ledger.py:135`)·렌더 임시 폴더·legacy 행과 journal. (6) §4-3 저장 행(71), §9 A5(181), §10 테스트(202-204: requests·state 본문·turn 행 base64 0, 멱등 재실행 렌더 0, 렌더가 쓰기 트랜잭션 밖, 미리보기 전 중단)에 반영했다 |
| 2 (minor) | 중복·라운드 간 누적 경계 미정의, 테스트 없음 | §4-3 개수 행(68행): 한 호출 안 중복 `(clip_index, frame)`은 호출 전체 거절(조용한 중복 제거 금지, 이유 명시). 이전 라운드와 같은 `(timeline_revision, clip_index, frame)` 재요청도 거절. 누적은 턴별 production run(`chat_general.py:529`)의 `run['calls']` 영수증으로 판정하고, 합이 4를 넘으면 호출 전체를 거절한다(3+2 → 거절, 1장만 렌더하지 않음). 렌더가 실패한 요청도 누적에 넣는다. §10(193-195행)에 테스트 3개를 추가했다 |
| 3 (minor) | 공식 표 값(1456×819)과 Haiku 등급 진술이 출처와 다름 | 공식 문서(platform.claude.com/docs/en/build-with-claude/vision)를 이번 작업에서 WebFetch로 다시 열어 원문을 확인했다. 등급 표 "High-resolution \| Claude 4.7 and later models \| 2,576 px \| 4,784", "Standard \| All other models \| 1,568 px \| 1,568"과 1920×1080 행 "1456x819 px \| 1,560 \| Not resized \| 2,691"이다. §4-3 토큰 행(70행)을 1456×819로 고쳤다. Haiku 5.5는 표의 범위상 고해상도 등급이라 **[검증됨: 문서]**로 올렸다. 그래서 landscape·portrait 프레임은 장당 2,691이다. 이미지 입력 지원 여부 자체는 [미확인]으로 남겼다(§4-2, §11 214-215행) |
| 4 (minor) | 인용 검사의 `''` 무효 단언 4건, STALE 검사가 r1 문구만 봄 | `check_citations.py`(r3)에서 4건을 실제 기대 문자열로 바꿨다: `renderer.py:112` `16*1024*1024`, `music.py:16` `def waveform`·`:17` `Bounded actual PCM envelope`, `motion_scene.py:9` `enum=['text','rect','circle']`·`:31`, `production_tools.py:10` `TOOLS={`. 빈 기대 문자열이 있으면 스크립트가 AssertionError로 멈추게 했다. 무효 단언 4건은 실질 단언 6건으로 바뀌었다. STALE 목록에는 r2에서 정정한 문구 9개를 추가했다. §4-4·§7·D20용 내용 단언 45개(현재 파일 5개 포함)를 추가했다. 그래서 내용 단언은 108개에서 155개로 늘었다(108 − 4 + 6 + 45). `./` 접두 인용은 현재 파일로 해석하는 기능을 넣었다. 전체를 다시 실행했다(아래) |
| 5 (minor) | D20을 "결정 대기·선결"로 다룸. 사용자 결정(§8-4)과 §7 예약액 재계산 필요 | §4-1(56행): D20 사용자 결정(PLAN-ko.md:196, 상한만 상향, [가정] 16384)으로 바꿨다. 작업 중 A2a가 현재 코드를 `MAX_INPUT = 16384`로 바꾼 것(`./chat_general.py:29`, 18:31 확인, 수락 전)도 적었다. §4-3 토큰 행에서 "D20 선결" 문구를 지우고, 16384와 64KiB의 관계(텍스트는 토큰 상한이 먼저, 프레임은 바이트 상한이 먼저 [추정])를 적었다. **§7 재계산(141-151행)**: 라운드당 2,458 → 3,687 micro, 한 턴 최대(전송 4회, `chat_general.py:773` 근거) 9,832 → 14,748 micro, 요청 상한 최소 허용값 2,458 → 3,687 micro(`:437`), 대화 총상한 400,000 micro는 그대로. 프레임 토큰 비용도 다시 계산했다(장당 USD 0.0000299, landscape 0.0002691, 라운드 누적 최대 3,588토큰). §9 A3·A4(179-180행), §11 가정(217행)을 갱신했다 |
| 6 (minor, A1 판정의 cross-track) | `chat_runtime.py` 줄이 +3 이동했는데 r2가 옛 번호로 인용 | 문서 규약은 `before/` 기준이라 옛 번호 자체는 그 규약상 맞다. 다만 **내용이 낡았다**("기본 도구 = TOOLS 전체"). §4-1(55행)을 편집 전/현재로 나눠 고쳤다. 편집 전은 `chat_runtime.py:175`, `:331-332`이고, 현재는 `./chat_runtime.py:17`(LEGACY_DEFAULT_TOOLS 13개), `:178`(limits 기본값), `:334-335`(result_message·continuation)다. A1 critic이 쓴 "현재 333-334"는 직접 확인해 보니 334-335였다(331+3). 머리말(8행)에 `./` 규약을 추가했다. legacy는 승인 설정 `tools` 직접 지정으로 여전히 넣을 수 있다는 A1 r2 남은 빈칸을 원문 인용했다. 그래서 프레임 도구는 legacy에서 항상 거절하도록 하고, §10(210행) 테스트에 legacy 행·journal 바이트 0을 추가했다 |
| 추가 | 문서 내 PLAN 줄 이동 | `PLAN-ko.md:161`은 현재 다른 항목이다. 줄 번호 재확인 항목은 `PLAN-ko.md:164`로 고쳤다(8행) |

## 실행한 명령과 출력 꼬리
코드를 바꾸지 않았으므로 unittest는 해당이 없다(실행하지 않음).

1) 인용 전체 검사(r3 스크립트, 수정을 마친 최종 문서로 재실행)
```
cd /Users/leesungmin/Desktop/Loretune && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B .omo/evidence/agent-tools-02-20261028/tasks/D1-frame-observation-design-r3/check_citations.py
explicit anchors 274 content checks 155 (before/md 150 + current 5) empty-expected 0 fail 0
exit=0
```
- 로그는 `check_citations.log`다. 내용 단언 155개 중 빈 기대 문자열은 0개다(스크립트가 assert로 강제).
- 첫 실행은 `FAIL ./chat_general.py 28 'MAX_INPUT = 4096'`으로 1건 실패했다. A2a가 병행으로 `MAX_INPUT = 16384`(29행)를 넣었기 때문이다. 문서(56행)와 스크립트 기대값을 현재 사실에 맞춘 뒤 전체를 다시 실행해 위 결과를 얻었다.
- **변이 확인**(scratchpad 사본으로 실행, 프로젝트 파일은 바꾸지 않음): 문서에 `1456×816`을 되살리고 앵커 하나를 1002행으로 틀리게 하면 `FAIL app.py 1002 …`, `STALE 1456×816`, `fail 2`, exit=1이 나왔다. 기대 문자열 하나를 `''`로 바꾸면 `AssertionError: empty expected substring is a vacuous check`로 멈췄다. 따라서 검사가 실제로 결함을 구분한다.

2) 문서 게이트(읽기 전용 checker, 등록하지 않음)
```
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B tools/document-gate/check.py --root .
exit=1, status blocked, findings 22
FRAME 관련: UNCLASSIFIED_DOCUMENT docs/design/FRAME-OBSERVATION-DESIGN-ko.md (+ D1 r1·r2 result.md)
```
- 원문은 `document-gate-readonly.json`에 있다. 이 result.md도 다음 실행부터 같은 UNCLASSIFIED로 보고될 것이다 [추정: r1·r2 result.md와 같은 처리].
- 이 문서는 등록 승인 전까지 `UNCLASSIFIED_DOCUMENT`로 보고된다. 예상된 결과다(D10 "등록은 별도 승인"). `.document-gate.json`에 FRAME-OBSERVATION은 0건이다(grep).
- findings 수(r2 14, critic 17, 이번 22)의 차이는 병행 트랙의 새 파일 때문으로 보인다 [추정].

## 워크플로 진행 중 생긴 오류·이상 (사용자 요청 "에러 없이 잘 진행이 됐는지" 대응)
- Edit 도구마다 훅 안내 "Scope limit: Path escapes project root"가 붙었다. 편집은 모두 성공했다. 훅 기준 루트가 evidence 폴더(작업 디렉터리)라서 나온 안내로 보인다 [추정]. 대상 파일은 지정된 쓰기 범위 안이다.
- 인용 검사 1차 FAIL 1건: 위 1)의 병행 변경 때문이다. 문서 결함이 아니라 현재 사실이 바뀐 것이다.
- 문서 게이트 1차 실행에서 시작 시 사본 `FRAME-OBSERVATION-DESIGN-ko.before-r3.md`가 UNCLASSIFIED로 새로 잡혔다. 내가 만든 파일이라 `.txt`로 이름을 바꿨고(삭제 없음), 재실행에서 사라졌다.
- r2 이후 `PLAN-ko.md` 줄이 밀려 `:161` 인용이 다른 항목을 가리키고 있었다. `:164`로 고쳤다. r2 스크립트는 이 줄의 내용을 검사하지 않아 통과했었다.

## 남은 공백
- [미확인] Haiku 5.5의 이미지 입력 지원(Models API = 외부 호출), count_tokens 과금 여부, 640×360 PNG 실제 크기, FFmpeg 출력 결정성(§4-4 재렌더 시 같은 바이트인지).
- [추정] 렌더 4장이 최대 약 120초 동안 쓰기 잠금을 쥔다는 값. 실행 시간이 아니라 시간 제한에서 나온 상한이다. 권장안 i에서는 이 문제가 생기지 않는다.
- [추정] 텍스트는 16384토큰 상한이, 프레임은 64KiB 바이트 상한이 먼저 걸린다는 판단. A1 관측 비율(1.97~2.31 B/토큰)과 PNG 크기 미측정에 기댄다.
- [추정] 남는 여유 48,387바이트는 A1 r2 측정(첫 요청 17,149바이트) 기준이다. A2a·A2b의 Wave 2 도구 추가로 줄 수 있다.
- `./` 현재 파일 인용 5개(`chat_runtime.py` 17·178·334·335, `chat_general.py` 29)는 병행 트랙이 다시 고치면 어긋날 수 있다. 통합 시 이 스크립트를 다시 돌리면 잡힌다.
- 이전 result.md(r1·r2)는 쓰기 범위 밖이라 고치지 않았다. r2 result의 chat_runtime 인용 정정은 이 문서의 항목 6에 기록한다.
- D15·D19·D21은 프레임 관찰 설계의 수정 항목에 들어 있지 않아 반영하지 않았다(Karpathy 범위 원칙). 다만 §7의 예약액 표는 PLAN-ko.md:196이 말한 "카드/설정 요약" 표시 대상이라고 적어 두었다.

## 사용자 결정이 필요한 항목 (이유·근거)
구현하려면 모두 사람 승인이 필요하다. 이번 범위(설계만)는 결정 없이 끝난다.
1. **프레임 바이트 영속 방식(§4-4 권장안 i 대 대안 ii)**: i는 바이트를 run·requests에 남기지 않는다(스펙 `:418` 준수). 대신 미리보기 생성 전 중단 시 바이트를 버리고, 재실행 렌더가 같은 바이트라는 보장이 없다. ii는 재현성을 얻지만 스펙 예외 승인이 필요하고 쓰기 잠금 문제가 남는다. 근거: `app.py:496-497`, `:1001`, `:1003`, `production_tools.py:64-67`, `:139`.
2. **새로 찾은 보관·노출 위치의 보관 정책(A5)**: `/api/state`가 대기 중 미리보기의 두 본문을 상태 조회마다 돌려준다(`app.py:384`). 오프라인 백업이 미리보기 행을 그대로 복사한다(`backup.py:51,63`). 프레임이 들어 있는 미리보기 행을 전송 후 비울지, 백업에서 뺄지는 삭제·보관 결정이라 대상별 승인이 필요하다.
3. **D20 값 확인**: 16384는 lead의 [가정]이다. 라운드당 예약 3,687 micro, 한 턴 최대 14,748 micro가 된다. 기존에 요청 상한을 2,458~3,686 micro로 쓰던 사용자는 미리보기 생성이 거절된다(`chat_general.py:437`). A2a가 이미 코드에 반영 중이다.
4. (r2에서 이어짐) 64KiB 처리 방식(축소·상한 상향·Files API), 전송 2회·노출 2벌 수용, 블록 배열 적용 범위 (a)/(b).
