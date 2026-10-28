# Native motion 도구 회귀 — 현재 소스 독립 재검증

**알려진 `14 != 11` 실패는 현재 소스에서 해결됐다. 새 수정 패치는 만들지 않았다.** 격리 사본에서 원래 실패한 테스트를 포함한 관련 회귀 **17/17 PASS**, 별도 계약 probe **9조합 PASS**다. probe 내부의 거절 조건 81개는 17개 테스트에 합산하지 않는다. 전체 375개가 현재 통과했다는 의미는 아니다.

## 이전 실패와 현재 검사

- 원 증거: [m1-full-regression.log](../native-motion-20261026/m1-full-regression.log)의 375개 중 1실패. 당시 `tests/test_chat_protocols.py:53`은 도구 수 11을 요구했고 실제 14였다.
- 현재 [tests/test_chat_protocols.py:53](../../../tests/test_chat_protocols.py#L53)은 14개를 검사하고, **54행에서 전체 14개 이름의 정확한 집합을 독립적으로 검사**한다. 55–58행은 필수 필드/unknown field 제한과 malformed 응답 차단을 유지한다. 개수만 14로 바꾼 상태가 아니다.
- 현재 테스트 파일 mtime **2026-10-26T15:51:13.308011Z**, SHA256 `e79f9db0fe38ec9c17bdbc156f02b8b726bb6bb28f5398a9a317479f92877631`. 원 전체시험 로그 이후 변경된 파일이다. 이번 감사가 수정한 파일이 아니다.
- Python import 의존성과 필요한 Swift 원문 44파일을 `copy2`로 임시 사본에 복사하고 hash/mode를 확인했다. Swift 원문은 font/render fingerprint의 입력으로만 읽혔으며 컴파일하거나 실행하지 않았다. 시작·종료 비교에서 canonical 44파일 변경 0.

## 새 도구가 의도된 확장인지

기준: [PLAN K.4/K.5](../codex-cli-assessment-20261026/PLAN-ko.md), 특히 431/438/441/462/466행. 계획 당시의 ‘아직 구현 없음’ 문구를 현재 기능 상태로 재해석하지 않았다.

|도구|정확한 모델 입력|계획 및 현행 승인 경계|
|---|---|---|
|`propose_motion_scene`|`shot_id:string`, `base_motion_revision:integer`, `scene:object`|K.4 438행. 제안 저장만 수행. 사람 검토 전 head/version/job 변경 없음. 승인 시 base revision/context/text/font 재검사|
|`request_motion_render`|`shot_id:string`, `motion_revision:integer`, `grant_id:string`|K.4 441행. 현재 motion revision, 사람에게 발급된 local-motion-candidate grant, scene/context/font hash가 맞아야 job 접수. 최종 출력 승인이 아님|
|`propose_timeline_changes`|`description:string`, `timeline_version:integer`, `commands:array`|K.5 462/466행. typed commands로 기존 timeline proposal 생성. 사람이 적용한 뒤에도 최종 출력 승인은 별도|

근거 위치: `production_tools.py:18–20,32–44`, `chat_protocols.py:63–74`, `motion_scene.py:73–109`, `local_creation_tools.py:70–106`. `scene`/`commands`를 string으로 그대로 내보내지 않고 명시적인 중첩 schema로 교체한다. 모델 입력에 actor/approved/permission/path/endpoint를 추가하면 거절한다.

## 실제 실행 범위와 결과

재현: 이 폴더의 `run_recheck.py`가 `base-manifest.json`에 기록된 snapshot을 사용한다. 임시 SQLite Store와 합성 media만 만들며 canonical 경로의 파일 접근, secret 파일, socket connect/bind를 실행 중 차단한다. FFmpeg/ffprobe만 기존 fixture의 로컬 생성·메타데이터 읽기에 허용했다. 차단 guard에 걸린 동작 0, 외부 호출 0.

**17개 기존 테스트, 2.385초, failure/error/skip 0:**

- protocol 6개: 정확한 tool set, strict schema, malformed/incomplete/duplicate JSON 차단, call/result 연결, provider handoff와 제안 저장.
- motion 5개: scene 경계·코드/경로 거절, frame/easing/12-frame 변경 평가, 세 protocol의 중복 제안 및 비적용, hold/stale/foreign/restore/원본 보존, 가짜 grant 차단·취소 job 재사용·font 변경 차단. glyph 검증은 해당 기존 테스트의 fake를 사용했다.
- timeline commands 4개: 세 protocol의 제안→사람 적용, 기존 shot/audio/version 보존과 출력 승인 무효화, reorder-only 시 caption/audio 보존, 잘못된 순열/cue/audio/중복 거절, base occurrence 기준 clip 편집.
- 인접 timeline 2개: stale/foreign proposal 거절과 proposal-only/hold/사람 적용·중복 적용 보존.

**별도 offline probe 9조합:** Anthropic/OpenAI/xAI × 새 도구 3개. 정확한 입력 필드와 타입, 중첩 object의 required/additionalProperties, 정상 envelope 정규화를 확인했다. 조합마다 권한·경로 필드 5종 삽입, 필수 필드 3종 누락, integer 자리에 bool 입력을 각각 거절했다(총 81조건). 이는 실제 모델 응답 품질이나 provider API 지원 검증이 아니다.

기계 판독 증거: [test-results.json](test-results.json), [test-results.log](test-results.log), [base-manifest.json](base-manifest.json), [end-check.json](end-check.json). 기준은 실행 전에 [CRITERIA.md](CRITERIA.md)에 고정했다.

## 기존 count 진단 패치와의 관계

기존 [diagnostic.patch](../isolated-count-diagnostics-20261026/diagnostic.patch)는 `anthropic_ontology.py`, `chat_runtime.py`, 새 `tests/test_count_diagnostics.py`만 대상으로 한다. 현재 알려진 tool-set 수정은 `tests/test_chat_protocols.py`이며 직접 수정 경로가 겹치지 않는다.

- runtime 현재/base SHA256: `50ec18343dc4619aa2df8a5ffda7008a0a96c6bef71917c805c482700a51c54a`
- transport 현재/base SHA256: `e7021df88da62058a746b370f6eca26aa26f45012a3ae7a2195c3cea2be6d0f0`
- 현재 격리 snapshot에 `git apply --check diagnostic.patch` **exit 0**. 적용하지 않았으며 통합 후 실행 결과를 주장하지 않는다. 두 변경의 텍스트 충돌은 관측되지 않았다.

## 판정과 남은 한계

**원 도구 개수 회귀는 검사 범위 내 종료 가능. 추가 패치 불필요.** 현재 테스트의 exact-name 검사가 새 도구와 기존 도구의 누락/대체를 검출하므로 검사를 약화할 이유가 없다.

실제 Claude motion 저작, CoreText/decoded-frame/render 품질, 실제 UI, 전체 375개 suite, 새 진단 패치와의 통합 실행은 이번에 하지 않았다. 모션 전체 요구나 최종 릴리스 완료 판정은 별도다. Codex 앱 접근 거부는 유지했고 UI·CLI inference·외부 provider 재시도·공유 DB·canonical 소스 변경은 모두 0이다. 이 결과는 멈춘 기본 구현 세션의 재개 또는 취소 결과가 아니다.
