# REA 호출 및 5개 사이트 공개 UI 조사 보고서

- 세션: 2026-10-25_k9Df7KWrRTWvmEzh
- 조사일: 2026-10-25
- 보고서 저장 시각: 2026-10-25 (Asia/Seoul)
- 작성 기준: 이 세션에서 이미 반환된 도구 결과와 공개 UI 관찰. 이번 저장 요청에서는 사이트 재조사나 추가 REA 호출을 수행하지 않았다.

## 1. 현재 상태

- 완료: REA binary_session 빈 객체 실제 호출, 서버·패키지 버전 확인.
- 완료: Neural Frames, MusicMV, BeatViz, Anijam, Tunee의 공개 UI, 제작 진입 경계, 로그인 경로 조사.
- 완료: 공개 페이지에서 관찰한 사이트별 외부 JavaScript 1~3개, 총 12개 수집 및 일반 정적 표식 확인. 원본 URL·크기·SHA-256 매니페스트를 세션 artifacts/public-client 아래에 보존.
- 오류: Neural Frames에 대한 첫 REA JavaScript 분석 호출은 cleanup_incomplete로 실패했다. 분석 결과 일부는 보존됐다.
- 완료: 보존된 Neural Frames Evidence의 요약을 inspect_analysis_view로 읽기 전용 조회.
- [blocked] 중단 유지: 나머지 4개 사이트의 REA 분석. cleanup_incomplete 미해결 상태이므로 추가 실행하지 않는다.
- [blocked] 미검증: 인증 이후 작업공간, 실제 업로드·생성·렌더·다운로드. 로그인은 사용자가 직접 수행해야 하며, 로그인만으로 금지된 생성·업로드가 허용되지는 않는다.
- 조사에 사용한 전용 탭은 모두 닫았다. 기존 사용자 탭은 수정하지 않았다.

## 2. 검색 범위와 실제 REA 호출

### 2.1 지연 도구 검색

Aside 실행 환경의 functions.search_tools에서 다음 검색을 수행했다.

1. REA (limit 20)
2. binary_session (limit 20)
3. +REA web page public javascript inspect fetch url (limit 12)
4. reverse-engineer-anything REA skill browser workflow (limit 3)
5. +REA inspect_analysis_view (limit 1)

검색 결과로 도구가 노출됐다는 사실과 실제 호출 성공은 구분한다. 브라우저 CDP 도구도 검색 결과에 있었으나, list_browser_targets, inspect_web_page, analyze_web_bundle, capture_browser_scenario 등은 호출하지 않았다. 새 원격 디버깅 노출이나 포트 스캔은 하지 않았다.

### 2.2 상태 조회: 성공

- 정확한 호출 도구명: functions.mcp__REA__binary_session
- MCP 이름: mcp__REA__binary_session
- 입력: 빈 객체 {}
- 성공 여부: 성공. 실제 응답을 수신했다.
- 서버 이름·버전: rea 6.7.0
- 패키지 이름·버전: rea-agents 6.7.0
- 초기 반환 상태: open=false, cleanup_pending=false
- Evidence ID: 없음

위 상태는 최초 상태 조회 시점의 값이다. 이후 발생한 cleanup_incomplete가 해결됐다는 의미가 아니다.

### 2.3 Neural Frames 정적 분석: 오류 반환, 결과 일부 보존

- 정확한 호출 도구명: functions.mcp__REA__analyze_javascript_application
- MCP 이름: mcp__REA__analyze_javascript_application
- 서버 버전: 위 상태 조회에서 확인한 6.7.0
- provider_id: javascript-static-analysis
- 입력 폴더: /Users/leesungmin/.aside/u/0/sessions/2026-10-25_k9Df7KWrRTWvmEzh/artifacts/public-client/neuralframes
- format: directory
- source_paths:
  - index-101cccd2a3df7a34.js
  - Login-bf41993a33b74436.js
  - _buildManifest.js
- detail: summary
- analysis_timeout_ms: 30000
- max_heap_mb: 512
- 성공 여부: 실패. 전체 호출을 성공으로 보고하지 않는다.
- 오류 코드: cleanup_incomplete
- category: execution_failure
- retryable: false

정확한 오류 메시지:

> Provider cleanup could not be fully confirmed. Review the reported local resources before opening another target.

정확한 진단:

> process ownership token could not be read for 1 live process(es): reader_failure=1; live candidates 84658=reader_failure

보고된 자원:

- worker_pid: 84658
- rea-javascript-analysis-b62ad857-f725-4e12-b6fc-7121f2bfde07
- /var/folders/t7/p6pl4snd6pd3cmz1y80_7fzw0000gn/T/rea-javascript-analysis-9b1eqB

오류 응답의 partial_observation에 포함된 보존 원본 Evidence ID:

~~~text
ev_1a6e8701a11c0a4085a4c1fe5b69a4e02a53d54a349e51a4f81f5fa2584ddab7
~~~

이 ID는 도구가 발급한 실제 ID다. 임의 생성한 ID가 아니며, 정리 성공의 증거도 아니다.

보고된 PID만 확인하려던 명령:

~~~text
ps -p 84658 -o pid=,ppid=,comm=
~~~

결과: exit code 126. 정확한 stderr:

~~~text
bash: line 1: /bin/ps: Operation not permitted
~~~

거절을 우회하지 않았으며 프로세스 종료·설정 변경·추가 분석 재실행을 하지 않았다. 작업 프로세스의 최종 종료 여부는 확인되지 않았다.

### 2.4 보존 Evidence 요약 조회: 성공

- 정확한 호출 도구명: functions.mcp__REA__inspect_analysis_view
- MCP 이름: mcp__REA__inspect_analysis_view
- 입력 source.kind: retained-evidence
- 입력 evidence_id: 위 보존 원본 Evidence ID
- 입력 view.kind: summary
- 성공 여부: 성공. 새 분석이 아니라 이미 보존된 결과의 읽기 전용 조회다.
- provider: rea-analysis-view / REA analysis view projection / version 1

요약 조회에서 발급한 Evidence ID:

~~~text
ev_9b683d37018636a971403cc2f1d7402f8efcbf8dca1977840f70363c4fa94e05
~~~

반환된 범위 내 결과:

- parsed_javascript_files: 3
- skipped_javascript_files: 0
- parse_failures: 0
- modules: 7
- text_bytes_read: 52769
- application coverage: partial
- semantic coverage: unknown
- application unknowns: 1
- semantic unknowns: 1675
- confidence: derived
- JavaScript를 비활성 텍스트로 파싱했으며 번들 부트스트랩 코드를 실행하지 않았다고 명시.
- 선택하지 않은 파일 1개는 분석 범위 밖이며 전체 사이트 구현·동작의 완전성을 의미하지 않는다.

요약 조회 성공은 원래 분석 호출의 cleanup_incomplete를 취소하거나 해결하지 않는다. 두 Evidence는 Neural Frames의 선택된 공개 JS 입력에만 해당하며 다른 사이트 또는 UI 스크린샷의 REA 증거가 아니다.

## 3. 사이트별 공개 UI·제작 흐름·클라이언트 관찰

이 절의 UI는 일반 브라우저 snapshot 및 전용 탭 관찰 결과다. 공개 JS 표식 확인도 별도 일반 정적 확인으로 구분하며, REA 관찰로 바꿔 부르지 않는다. 공개 설명은 실제 기능 실행 검증과 구분한다.

### 3.1 Neural Frames

- 사이트: https://www.neuralframes.com
- 공개 UI 관찰: 오디오 반응형 음악 영상 소개, 립싱크·가사·루프 등 템플릿, 장면별 채팅 수정 예시.
- 공개 설명상의 제작 흐름: 음악 업로드 → 스타일·캐릭터·비트 싱크 설정 → 다운로드. 4K 출력은 사이트 설명으로만 확인했다.
- 직접 확인한 진입: Start Now → https://www.neuralframes.com/start/Login
- 로그인 화면: 처음에는 Create Account. Log in 전환 후 Google 또는 이메일·비밀번호 로그인 표시.
- 로그인 목적: 인증 뒤 프로젝트 생성·영상 편집기 UI 확인. 사용자가 직접 로그인해야 한다.
- 공개 클라이언트 관찰: /_next/static/ 경로, webpackChunk_N_E, 빌드 매니페스트의 /start/newproject, /videoeditor, /start/traincustommodel 등 경로 문자열.
- 추정: Next.js/Webpack 기반이며 프로젝트 생성·편집·커스텀 모델 화면을 구분하는 구조로 보인다. 문자열 존재만으로 해당 경로 접근 가능성이나 기능 동작을 확정하지 않는다.
- REA 상태: 첫 분석은 오류 반환. 위 원본 및 요약 Evidence가 선택된 JS 3개에 한해 존재한다.
- 제한: 로그인·편집기·업로드·생성·4K 다운로드 미실행. 서버·모델 구현 미확인.
- 공개 다운로드: artifacts/public-client/neuralframes/의 index-101cccd2a3df7a34.js, Login-bf41993a33b74436.js, _buildManifest.js, manifest.json.

### 3.2 MusicMV

- 사이트: https://musicmv.ai
- 직접 확인한 진입: Make a music video → https://musicmv.ai/create
- 공개 UI 관찰: 노래 업로드(MP3/WAV/M4A, 표시 범위 5초~6분), 내 노래·AI 노래 생성 선택, 메인 사진·추가 인물, 설명·스타일.
- 제작 옵션: 9:16·16:9·1:1·4:3·3:4, 768p·1080p, Auto 또는 Review & Edit. 입력 전 생성 버튼은 비활성.
- UI에 표시된 비용: 768p 1크레딧/초, 1080p 2크레딧/초. 실제 청구나 과금은 검증하지 않았다.
- 공개 설명상의 후속 흐름: 스토리보드 검토·재생성 → 렌더 → MP4 다운로드, 최대 1080p. 직접 실행하지 않았다.
- 로그인 경로: /create 좌측 Sign in → 동일 URL 모달.
- 로그인 옵션: Google, 이메일·비밀번호, 이메일 로그인 링크. Signing in creates your account 문구 확인.
- 로그인 목적: 인증 뒤 프로젝트·스토리보드 UI 확인. 사용자가 직접 수행해야 한다.
- 공개 클라이언트 관찰: /_next/static/immutable/chunks/ 경로와 내려받은 JS의 TURBOPACK 표식, 768p 문자열.
- 추정: Next.js/Turbopack 기반의 폼 중심 제작 UI. 실제 서버 처리·렌더링 구조는 미확인.
- REA Evidence ID: 없음. 추가 REA 분석은 중단 상태.
- 제한: 업로드·로그인·생성·결제·스토리보드 검토·렌더·다운로드 미실행.
- 공개 다운로드: artifacts/public-client/musicmv/의 turbopack-43kxxuh7jfe85.js, 3oxeyg_7j8-st.js, manifest.tsv.

### 3.3 BeatViz

- 사이트: https://beatviz.ai
- 공개 UI 관찰: Music to video, instantly with Beatviz 문구, Chat/Workflow/Editor 구분.
- 직접 확인한 /agent UI: 음악 추가, 선택 프롬프트, 모델·캐릭터·모드·화면비·해상도·공개범위, Start Creating.
- 직접 확인한 /create UI: Add music, 선택 프롬프트, Storytelling, Standard Fast 8s, 720p 16:9, Character/Style, Generate Video.
- 음악 미첨부 상태에서 생성 버튼은 비활성.
- 공개 설명: BPM·리듬 분석, 장면 생성과 beat-sync, AI Director/One-Click Generator/Custom Editing Studio. 실제 분석·렌더링을 검증한 것은 아니다.
- 로그인 경로: Get Started 또는 Start for Free → https://beatviz.ai/login
- 로그인 옵션: Google, Discord, Email.
- 로그인 목적: 인증 뒤 제작·편집 작업공간 확인. 사용자가 직접 로그인해야 한다.
- 공개 클라이언트 관찰: Next.js 형식 정적 경로, TURBOPACK, React 요소 표식, useState, useEffect, useRouter, aspectRatio.
- 추정: Next.js/Turbopack·React 기반으로 여러 제작 UI를 제공하는 구조. 전체 구현이나 정확한 프레임워크 버전은 미확인.
- REA Evidence ID: 없음. 추가 REA 분석은 중단 상태.
- 제한: 프롬프트 입력·업로드·생성·편집 결과·결제 미실행. 비공개 API 및 네트워크 분석 미수행.
- 공개 다운로드: artifacts/public-client/beatviz/의 e137cce79d52b9c0.js, fd0666be309281f1.js, c61c281700d45cce.js, manifest.json.

### 3.4 Anijam

- 사이트: https://www.anijam.ai
- 공개 UI 관찰: Create Your Videos Like ChatGPT 문구, 프롬프트 입력창, 참조 추가 미디어 버튼, 비활성 전송 버튼, Cinema Lab·Anime Studio·UGC Marketing 프리셋.
- 직접 확인한 제작 범위: 아이디어 입력 및 선택 참조 추가 UI까지. 입력·업로드·전송은 하지 않았다.
- 공개 설명·링크: Text/Script/Image/Audio to Video, AI Movie Maker, AI Ads.
- 로그인 경로: Start for free → https://www.anijam.ai/auth/ ; Log in → https://www.anijam.ai/auth/#signin
- 로그인 옵션: Google, Apple, Email.
- 로그인 목적: 인증 뒤 대화형 프로젝트·제작 흐름 확인. 사용자가 직접 로그인해야 한다.
- 공개 번들: https://staticglobal.anijam.ai/assets/www/v0.6.110/_nuxt/CbEoudTK.js
- 공개 클라이언트 관찰: __NUXT__, __nuxt, vue, pinia, storyboard 표식.
- 추정: Nuxt/Vue 계열 대화형 클라이언트. v0.6.110은 관찰한 배포 경로 표기이며 프레임워크 버전으로 확정하지 않는다.
- REA Evidence ID: 없음. 추가 REA 분석은 중단 상태.
- 제한: 인증 뒤 UI·참조 처리·생성·모델 동작 미검증.
- 공개 다운로드: artifacts/public-client/anijam/의 CbEoudTK.js, manifest.json.

### 3.5 Tunee

- 사이트: https://www.tunee.ai
- 공개 UI 관찰: Home, Music Agent, MV Studio, Pricing 내비게이션과 제작 CTA. 음악 및 뮤직비디오 제작 진입 옵션.
- 공개 설명: AI music producer, 첫 아이디어부터 완성 트랙까지 하나의 흐름이라고 소개. 실제 통합 제작을 실행 검증하지 않았다.
- 직접 확인한 진입: Start creating → 홈 URL에서 로그인 모달.
- 로그인 경계 문구: Log in or create an account to continue.
- 로그인 옵션: Google, Apple, email.
- 로그인 경로: https://www.tunee.ai/ → Start creating → 모달.
- 로그인 목적: Music Agent·MV Studio의 인증 뒤 작업공간 확인. 사용자가 직접 로그인해야 한다.
- 공개 클라이언트 관찰: res-cdn.tunee.ai/web_static/ai-agent-client-en/ 아래 /_next/static/chunks/와 내려받은 JS의 webpackChunk_N_E.
- 추정: Next.js/Webpack 기반이며 음악과 MV 제작을 함께 제공하려는 구조. 인증 뒤 두 작업공간의 실제 연결은 미확인.
- REA Evidence ID: 없음. 추가 REA 분석은 중단 상태.
- 제한: 로그인·작업공간·모델 실행·업로드·생성·출력 미검증.
- 공개 다운로드: artifacts/public-client/tunee/의 main-app-4675ba015c1c3757.js, public-home-layout-5af05fba1500701d.js, 3b9b4202-d6c063d1c0653f58.js, manifest.txt.

## 4. 제한과 다음 단계

1. 추가 REA 분석은 cleanup_incomplete로 중단한 상태를 유지한다. 해결 확인 없이 재실행하지 않는다.
2. 나머지 4개 사이트의 REA 분석에는 정리 오류가 해결된 실행 환경이 필요하다. 이번 요청은 해결 작업이나 재실행 승인이 아니다.
3. 로그인 뒤 UI 확인은 사용자가 각 사이트의 관찰된 경로에서 직접 로그인해야 가능하다. 자동 로그인이나 자격증명 조회는 하지 않았다.
4. 공개 JS 일부와 화면 표식은 전체 애플리케이션 복원, 서버·모델 구조, 실제 런타임 실행 증거가 아니다.
5. 공개 안내의 출력 품질·생성 성능·비용·모델 명칭은 실행이나 청구 검증을 의미하지 않는다.
6. 웹 CDP/네트워크/스토리지 캡처를 수행하지 않았다. 일반 브라우저·다운로드 관찰을 REA 캡처 성공으로 보고하지 않는다.
7. 사용자 개인 파일, .env, 메모리 파일, 브라우징 이력, 자격증명 저장소, 쿠키·토큰 저장소를 조회하지 않았다. REA 분석 입력은 이번 작업에서 공개 다운로드한 파일로 한정했다.
8. 설치·업데이트·보안 설정 변경·포트 스캔·새 원격 디버깅 노출·접근 거절 우회·비공개 API 무단 접근·유료 생성·업로드·계정 생성은 하지 않았다.
9. Loretune 프로젝트 파일·코드·서버·프로세스를 변경하지 않았다.
10. 실패한 REA 호출과 거절된 ps 조회는 실패로 유지한다. 정리 완료나 전체 5개 사이트 REA 성공을 주장하지 않는다.

## 5. 세션 내 증빙 위치

공개 JS와 URL·크기·SHA-256 매니페스트:

/Users/leesungmin/.aside/u/0/sessions/2026-10-25_k9Df7KWrRTWvmEzh/artifacts/public-client/

관찰 당시 스크린샷은 아래 임시 파일이다. REA 발급 Evidence가 아니며, 임시 디렉터리는 향후 정리될 수 있다.

- ../tmp/neuralframes-proof.png
- ../tmp/neuralframes-login-proof.png
- ../tmp/musicmv-proof.png
- ../tmp/beatviz-proof.png
- ../tmp/anijam-proof.png
- ../tmp/tunee-proof.png

이 보고서는 위 실제 관찰의 기록이며 현재 페이지를 새로 확인했다는 의미가 아니다.
