# 추가 범위: Claude 직접 작성 모션 그래픽

**현행 Aethon은 Claude 작성 keyframe/layout을 로컬에서 렌더하는 제품 경로가 없다. Claude가 못 만든다는 결론은 아니다. 실제 Claude 저작 응답과 통제된 로컬 renderer 연결 시험이 아직 필요하다. fal 생성은 이 요구의 대체가 아니다.**

## 현재 확인한 경계

- `production_tools.py:8–20`: media plan, image/video 준비, timeline 편집, render, memory 도구는 있으나 motion scene/keyframe 제안 도구 없음.
- `local_creation_tools.py:10–18`: 편집 변경은 clip_index/take/trim/duration만 허용. text layer, position, scale, opacity, keyframe/easing은 계약 밖이다.
- `renderer.py:58–89`: 승인된 기존 이미지/영상 Take를 scale/pad/trim/concat하고 원곡 및 mov_text 자막을 mux. 임의 코드·애니메이션 레이아웃 실행기가 아니다. `caption_preview.py`도 WebVTT 변환이며 kinetic typography 기능이 아니다.
- `editing.py:10`의 landscape 1920×1080, `frame_timing`의 24fps, `renderer.verify_output:13`의 metadata/audio/subtitle 검증은 재사용 가능하다. renderer의 180초 timeout·취소, file/pipe 입력 제한도 현재 존재한다.
- 이 실행 환경: FFmpeg **9.0.2**, ffprobe/Node/Swift 실행파일 존재. FFmpeg filter 목록에 drawbox/overlay/zoompan/xfade는 있고 **drawtext는 없음**. 현재 Python에서 PIL/numpy/cairo/cairosvg 미설치. `/System/Library/Fonts/AppleSDGothicNeo.ttc` 존재만 확인; 실제 glyph 렌더는 미검증.
- 현재 프로젝트에는 package.json/lockfile/node_modules 없음. `require.resolve` 기준 remotion, @remotion/renderer, react, react-dom, canvas, @napi-rs/canvas, sharp 모두 미설치. 다른 사용자 환경 전체에 전혀 없다는 판정은 아니다.

## 최소 직접 경로 제안 — primary 구현 전 범위

임의 JS/Python/FFmpeg 식을 모델에게 실행시키기보다 **버전 있는 작은 scene JSON**을 Claude가 작성하게 한다. 작성 내용은 text/rect/circle 레이어, 정수 z-order, bounded 좌표·색상·font ID, 시간/위치/opacity/scale keyframes와 `linear/easeInOutCubic` 같은 allowlist easing에 한정한다. 외부 asset·URL·import·script·사용자 지정 expression은 허용하지 않는다. 원본 JSON을 보존하면 타이밍/배치의 수정 가능성이 남는다.

새로 필요한 최소 연결은 scene schema/validator, 사람이 검토하는 immutable proposal, trusted rasterizer, existing render/export로 들어가는 로컬 Take+manifest다. 한국어 rasterizer는 현재 패키지로 바로 제공되지 않는다. 설치 없이 검토할 가장 작은 후보는 이미 존재하는 macOS CoreText/CoreGraphics와 Swift를 이용한 제한된 frame renderer지만 **컴파일·API 사용·glyph 출력 성공은 아직 검증하지 않았다.** macOS 전용이라는 운영 부담도 있다. 임의 코드 실행이나 기존 렌더러가 이미 지원한다는 주장으로 대체하지 않는다.

## 가장 작은 실제 수용 시험

|시험|fixture/명령|검증|
|---|---|---|
|MG1 Claude 저작|외부 자산 없이 4초·1920×1080·24fps. 한글 `새로운 리듬`과 원/사각형. 글자 0.25–1.25초 fade/slide, 원 1–3초 좌→우, 사각형 2–3초 fade. 명시된 easing.|실제 Claude response/usage/request ID와 scene JSON hash 보존. schema·timing·layer가 사용자 요구와 일치하는지 의미 검토. 사람이 대신 만든 JSON은 이 판정에서 제외.|
|MG2 로컬 렌더|검증된 scene을 96 frame으로 결정적 렌더, 기존 ffmpeg로 H.264/yuv420p MP4.|ffprobe 1920×1080·24fps·4초, 정상 decode. frame 12/36/60/84(0.5/1.5/2.5/3.5초) 추출, 장면/텍스트 bbox·alpha·위치 변화와 glyph 확인. 파일만 존재하거나 frame hash만 다르다고 요구 준수 통과로 삼지 않음.|
|MG3 수정 준수|같은 Claude 대화에 “원만 오른쪽에서 왼쪽으로, 한글/색/시간대는 유지”.|새 scene revision과 렌더. 원 keyframes만 의도대로 변경, 나머지 layer/timing 동일. 이전 scene/output 보존.|
|MG4 renderer 경계|과도한 layer/keyframe 수, NaN/무한 좌표·음수 시간, unsupported easing, URL/script field, 잘못된 font ID.|렌더 시작 전 거절. 4초/1080p/24fps·예: 최대 8 layer/각 8 keyframe/텍스트 80자·wall timeout 등의 제안 한도를 명시해 시험. 숫자는 제품 제안이며 표준 아님.|

프레임 단위 시각 변화 검사는 브라우저 screenshot이 아니라 출력 MP4의 실제 decode frame으로 한다. 정확한 글리프·easing 보간 판정과 metadata 결과를 함께 보존한다. 이번 감사에서는 위 산출물을 만들지 않았고, 실제 Claude 저작·render metadata·frame 비교 모두 **NOT RUN**이다.

MG1/MG3 실제 Claude는 추가 최대 Messages 2 + count 2, input 8,192/output 4,096, 자동 retry 0 제안. repo에 기록된 가격으로 보수적 round 2,868 micro-USD, 합계 $0.005736, 별도 stage cap $0.01. 실행 권한/현행 가격은 primary가 확인한다. fal 호출은 0.

## 조건부 Remotion 경로

공개 도구 inventory에서 `__REA__` namespace, 독립 단어 REA, reverse-engineer/remotion 설명을 정확히 검색했지만 **이 세션에 호출 가능한 REA MCP 도구는 0개**였다. 과거 보고서의 `mcp__REA__binary_session.json`은 현재 도구 접근 증거가 아니다. 다른 이름의 도구를 REA로 간주하거나 숨은 API·설치·MCP 등록으로 우회하지 않았다. primary의 도구 세션에 REA가 있으면 그 정확한 공개 namespace/설명을 기준으로 별도 수행할 수 있다.

직접 scene renderer가 필요한 한국어/레이아웃 품질을 충족하지 못할 때 Remotion을 검토할 수 있다. 다만 현재 Node/React/browser-render 의존성이 없으므로 즉시 실행 가능한 fallback은 아니다. 도입한다면 Python/SQLite의 job·approval·budget·version을 유지하고, immutable scene JSON을 받는 별도 render worker가 MP4와 manifest를 반환하는 경계가 가장 작다. 기존 생성 provider·canonical writer를 교체할 이유는 없다.

새 npm/React/Chromium 또는 해당 rendering runtime의 버전 고정·취약점 갱신·프로세스/네트워크 제한·font 재현성·작업 취소·resource cap 부담이 생긴다. 모델의 임의 TSX를 검증 없이 실행하는 것은 최소 구조안에 포함하지 않는다. **Remotion의 현재 상업적 license 조건·배포/렌더 서비스 적용은 이 감사에서 확인하지 않았으며 parent researcher가 공식 문서로 확인 중이다. 무료·MIT·상용 무제한이라고 가정하지 않는다.** 공식 소스/문서 분석과 적법한 재사용 범위를 확인한 뒤 필요한 부분만 적용한다.

부가 도구 확인: `load_workspace_dependencies`는 “Workspace dependency tools are only supported for local threads”로 unavailable을 반환했다. 새 실행/전달/설치는 발생하지 않았다. 이 기능 부재는 Claude 모델 능력 실패가 아니다.
