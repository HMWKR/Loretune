# REA 라우팅 로컬 확인 — 2026-10-26

## 결과 먼저

- **등록 확인:** Codex `rea` MCP는 enabled, `stdio`, `/opt/homebrew/bin/rea mcp`로 등록되어 있다. 로컬 설치 패키지는 `rea-agents@6.7.0`이다. 실행 파일은 `/opt/homebrew/lib/node_modules/rea-agents/scripts/rea.mjs`로 연결된다.
- **모델 설정 확인 / 실제 수신자 미확정:** 비밀 아닌 설정의 `model`은 `gpt-6-astra`. `model_provider`, 선택 profile, 명시적 provider base URL은 없으며 확인한 `OPENAI_BASE_URL`, `CODEX_OPENAI_BASE_URL`, `CODEX_BASE_URL` 환경 override도 unset이었다. 따라서 기본 provider 경로를 사용한다는 추론까지만 가능하다. 인증 방식/실행별 override/실제 요청을 확인하지 않았으므로 정확한 외부 endpoint를 확정하지 않는다.
- **공개 소스 한정 분석 경로는 계약에 존재:** 별도 폴더에 공개 Remotion 소스만 준비하고 `analyze_javascript_application`의 `input_path`를 그 폴더로 한정할 수 있다. Aethon 소스가 입력 필수인 구조는 아니다. 다만 이것은 설치된 계약을 읽은 결과이며 실제 서버 연결/분석 성공이나 데이터 격리를 실행 검증한 결과는 아니다.
- **REA는 등록됨 ≠ reachable ≠ 실행됨:** MCP 서버를 시작하지 않았고 handshake/tools-list/분석/브라우저/모델 호출도 하지 않았다. 이 세션에 직접 노출된 REA 도구는 발견되지 않았다. CLI 등록은 별개로 확인됐다.

## 실행한 것과 하지 않은 것

실행 완료: 비밀 아닌 config 필드 projection, 위 세 환경변수 존재 확인, 지원되는 `codex mcp get rea --json` 결과의 안전한 필드 projection, CLI 도움말/등록 메타데이터, 설치된 JS 계약 파일의 read-only 확인. 원본 config 전체와 env/auth/token 값은 출력/저장하지 않았다. 제품 소스/DB/config 변경 없음.

실행하지 않음: inference, REA 서버 시작, MCP 도구 호출, `doctor`, 외부 fetch, Remotion 다운로드, CDP 접속, 브라우저 조작, 서버 등록/설정 변경, 인증파일 읽기. 부모의 기존 Aethon 소스 외부검토 거절을 재시도하지 않았다. 이번 확인 과정 자체에는 새 승인 거절이 없었다.

## 확인한 실제 도구 계약

1. `analyze_javascript_application` — `toolContracts-BPoHQdlC.js:5103–5143`. 로컬 ASAR 또는 directory를 정적 분석한다. 입력은 `input_path`, `format=auto|asar|directory`, `integrity_policy`, 선택 `source_paths`, 자원 제한, `detail`이다 (`toolOutputSchemaGroups-MJ_f-PMK.js:4498–4508`; detail 확장 `toolContracts-BPoHQdlC.js:5060`). 코드를 실행하지 않는다는 계약이다. 단, 효과 메타데이터에는 session mutation/filesystem write/process launch가 표시돼 있다 (`toolOutputSchemaGroups-MJ_f-PMK.js:1250–1254`). 단순 파일 읽기만 하는 도구라고 소개하면 부정확하다.
2. `source_paths`는 분석할 파일 선택 범위이며 **전체 artifact inventory/identity는 유지**된다 (`toolContracts-BPoHQdlC.js:5105`). 따라서 Aethon 루트를 입력하고 Remotion 파일만 선택하는 방식은 데이터 최소화에 맞지 않는다. 공개 소스만 있는 별도 루트가 필요하다. `detail=summary`는 반환량을 줄일 뿐 분석 범위를 줄이는 옵션이 아니다.
3. `inspect_web_page` — `toolContracts-BPoHQdlC.js:4407–4419`. 이미 존재하는 CDP page target을 관찰한다. 필수 `cdp_endpoint`(loopback), `target_id`; origin 범위 및 선택적 script/accessibility/console/storage 수집 플래그 (`webContentArtifact-DfGkgDcI.js:151–185`). **단순 URL 문서 fetch 도구가 아니다.** 이번에는 브라우저 경로를 사용하지 않았다.
4. `analyze_web_bundle` — `toolContracts-BPoHQdlC.js:4422–4440`. 선택 CDP target의 JS/graph를 분석하며 선택 origin에 대한 source-map fetch 가능. 브라우저 없이 URL만 넘겨 쓰는 경로로 확인하지 않았다. 현재 권한 범위 밖이므로 실행하지 않았다.
5. stdio entrypoint — `scripts/rea.mjs:15,59–60` → `dist/mcp/main.js`. stdio는 **Codex↔REA의 로컬 전송**을 뜻하며, 도구 결과를 받는 Codex 모델의 외부 전송 경로까지 로컬임을 뜻하지 않는다.

## 다음 연구의 최소 데이터 범위 제안 — 아직 실행하지 않음

- 신규 문맥/별도 공개소스 전용 작업 폴더. 공개 Remotion의 정확한 버전/commit, LICENSE/notice 및 필요한 파일만 준비한다. Aethon 코드, QA 보고서, private 경로/설정/로그/대화 내용은 입력하지 않는다.
- 향후 허용되는 경우 로컬 정적 분석을 우선한다. `input_path`는 공개소스 폴더, `source_paths`는 명시한 공개 파일, `detail=summary`. 절대 Aethon 루트를 분석 대상으로 사용하지 않는다.
- 외부 모델에 보낼 수 있는 내용은 공개 소스에서 얻은 선택 요약/발췌, 버전/라이선스 정보, 공개 구조에 대한 질문으로 한정한다. 이 기존 스레드 전체를 CLI inference 입력으로 넘기지 않는다.
- 공개 문서/소스를 향후 가져오면 요청 대상 사이트도 별도 수신자다. 현재는 fetch를 수행하지 않았으므로 접근 가능성을 보장하지 않는다.
- **외부 분석 전 남은 확인:** 예정 CLI invocation의 실효 provider와 base endpoint를 비밀 없는 메타데이터로 확정해야 한다. 현재 로컬 설정에는 endpoint가 없어서 이번 허용 범위로는 결론 불가. 인증파일 열람이나 시험 inference로 확인하는 행동은 하지 않았다. 등록 서버의 도구 계약은 확인됐지만 startup/reachability/실제 도구 목록은 미검증이다.

설치된 REA package.json의 MIT 표시는 REA 패키지 자체에 관한 메타데이터다. Remotion 라이선스/소유권/재배포 허용을 의미하지 않는다. Remotion 사용 후보 버전의 라이선스는 별도 검토해야 한다.

## 증거 범위

`source-manifest.json`에 위 설치 파일들의 SHA-256, mtime, byte 수를 저장했다. config/auth 파일의 hash나 내용을 저장하지 않았다. 이 보고서는 라우팅 발견만 다루며 기존 Aethon 외부 소스 검토의 승인 상태를 변경하지 않는다.
