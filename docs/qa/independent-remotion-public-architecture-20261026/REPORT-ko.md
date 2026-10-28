# 공개 Remotion 구조 검토 — 독립 조사, 2026-10-26

## 결과와 실행 경계

공식 **v4.0.538 / 5217b0c90623f2decb4575714fac89d3c4b69896**의 공개 파일 17개(193,664 bytes)를 별도 폴더에 확보하고 정적 소스 확인을 완료했다. 17개 모두 SHA-256 및 공식 Git tree의 blob SHA와 일치한다. 다운로드된 코드는 실행하지 않았다. 제품 소스/DB/서버/설정 변경, 패키지 설치, 라이선스 수락 없음.

**REA 분석은 완료하지 못했다.** 새 public-only Codex CLI 실행 1회가 자동 승인 검토에서 **프로세스 생성 전에 거절**됐다. REA 등록 사실은 이전 로컬 확인이며 이번 handshake, tool call, Evidence ID, 추론, 렌더 결과는 모두 없다. stdout/stderr/answer 대상 파일도 생성되지 않았다. 아래 구조 설명은 공개 소스를 직접 읽은 결과이며 REA가 산출한 결론으로 표기하지 않는다.

- 시도 대상: `/tmp/remotion-public-research-20261026/source`의 공개 파일만, generic question은 `public-question.txt`에 보존.
- CLI 방식: fresh ephemeral `codex exec`, `--ignore-user-config`, `--sandbox read-only`, `gpt-6-astra`, 실행별 REA command/args. 영구 설정을 바꾸지 않는 명령이었지만 실행되지 않았다. 이전 대화 resume/fork 및 비공개 작업 루트 입력 없음.
- REA 예정 분석 allowlist: `use-current-frame.ts`, `Sequence.tsx`, `interpolate.ts`, `input-props-serialization.ts`, `use-playback.ts`, `seek-to-frame.ts` 6개. 전체 inventory도 공개 파일 17개뿐인 루트였다.
- 거절 사유 원문: 명시된 공개 소스 분석 자체는 승인됐지만, 실행은 모델 추론과 REA 외부 경로를 호출하며 실효 provider/base endpoint와 수신자를 확인하지 못했습니다. 사용자 지침상 이 경우 실행하지 않고 정확한 blocker를 보고해야 합니다.
- 같은 시도의 재실행, 직접 REA CLI/stdio 호출 등 대체 경로 우회는 하지 않았다. 외부 수신자 확인 및 그 수신자에 대한 공개자료 전송 승인이 남았다. 비공개 Aethon 소스 전송 승인을 요청하는 상황이 아니다.

## 근거별 구조와 자체 엔진에 대한 시사점

다음 표에서 왼쪽은 **Remotion 관찰 사실**, 오른쪽은 **독립 구현 제안**이다. 오른쪽이 현재 Aethon에 구현돼 있다는 뜻은 아니다.

| 영역 | 고정 소스 관찰 | Python/SQLite/JS 편집기 설계 제안 |
|---|---|---|
| 프레임 좌표 | 현재 timeline frame에서 누적 sequence offset을 빼고 재생 비율을 적용한다. [packages/core/src/use-current-frame.ts:25](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/use-current-frame.ts#L25) | 문서의 fps와 정수 frame count를 고정하고, 전역 frame→레이어/클립 local frame 변환을 명시한다. 렌더 값은 scene revision + frame으로 결정되게 한다. wall-clock/CSS transition을 결과의 기준으로 삼지 않는다. |
| Composition | id, dimensions, fps, duration, component, default props, schema, metadata resolver를 묶어 등록한다. [packages/core/src/Composition.tsx:191](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/Composition.tsx#L191) | React component 소스 대신 검증 가능한 scene JSON을 사용한다. scene id/revision, canvas, fps, frame count, layer list, asset manifest를 하나의 export snapshot으로 묶는다. |
| Sequence | 시작점/trim/rate/부모 범위로 자식 시간과 표시 기간을 계산한다. 루프의 시계 원점과 visible window를 구분한다. [packages/core/src/Sequence.tsx:399](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/Sequence.tsx#L399) | timeline clip 위치와 원본 source trim을 다른 필드로 둔다. 구간은 시작 포함·끝 제외로 명시한다. 초기 버전은 중첩/가변 rate를 제한하고, 지원 범위를 schema에 선언한다. |
| 보간 | 구간 입력을 정규화하고 easing을 적용해 출력 범위로 변환한다. clamp/wrap/extend 정책이 있으며 입력 범위 증가·유한값을 검사한다. [packages/core/src/interpolate.ts:583](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/interpolate.ts#L583), [packages/core/src/interpolate.ts:1145](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/interpolate.ts#L1145) | 자체 작성한 evaluator에 position/scale/rotation/opacity 등의 명시적 키프레임과 easing enum만 허용한다. 중복 frame, NaN/Infinity, 범위 밖 값, 과도한 레이어/키프레임 수는 거절한다. 초기 easing 종류/한도는 제품 결정이지 Remotion 또는 기존 사용자 요구라고 간주하지 않는다. |
| 미리보기 시계 | performance clock, composition/fps/rate identity를 관리하고 seek revision, buffering, ended, background RAF/timeout, audio anchor를 처리한다. [packages/player/src/use-playback.ts:169](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/player/src/use-playback.ts#L169), [packages/player/src/use-playback.ts:246](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/player/src/use-playback.ts#L246) | UI play/pause와 canonical scene을 분리한다. 재생은 프레임 위치만 갱신하고 편집 버전을 쓰지 않는다. scene/revision/token이 달라진 async completion은 폐기한다. audio clock과 seek를 별도로 동기화한다. |
| 프레임 렌더 | renderFrames는 이미지열과 audio 정보를 만들며, seek는 readiness→정확한 frame 지정→readiness→font readiness를 기다린다. renderMedia는 이후 stitch/mux 단계로 넘긴다. [packages/renderer/src/render-frames.ts:741](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/renderer/src/render-frames.ts#L741), [packages/renderer/src/seek-to-frame.ts:197](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/renderer/src/seek-to-frame.ts#L197), [packages/renderer/src/render-media.ts:886](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/renderer/src/render-media.ts#L886) | 미리보기 시간에 따라 녹화하는 대신 고정된 revision으로 frame 0…N−1을 평가·rasterize하고 기존 인코더에 넘긴다. ready/failed/cancelled 상태, timeout, asset/font 준비 상태가 필요하다. 기존 FFmpeg 합성만으로 새 텍스트 레이어 renderer까지 생기지는 않는다. |
| 입력 직렬화 | JSON serialization과 Date/file 전용 token 처리, deserialize 및 Studio 사전 roundtrip이 있다. Map/Set 사용을 표시하는 것 자체는 무손실 roundtrip 보장이 아니다. [packages/core/src/input-props-serialization.ts:16](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/input-props-serialization.ts#L16), [packages/core/src/input-props-serialization.ts:94](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/input-props-serialization.ts#L94) | plain JSON과 엄격한 버전 schema를 택하고 함수/실행 코드/비직렬화 객체를 받지 않는다. input/default/resolved 값을 승인 시 고정한다. DB에는 원본 제안과 검증 결과, 승인 revision/hash를 분리해 보관한다. |
| 자산 준비 | staticFile은 public asset base/목록을 조회하고 HTTP URL·일부 상대/절대 경로를 거절한다. delayRender handle이 남으면 준비 완료가 아니며 timeout/retry/cancel을 기록한다. [packages/core/src/static-file.ts:91](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/static-file.ts#L91), [packages/core/src/delay-render.ts:68](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/delay-render.ts#L68), [packages/core/src/delay-render.ts:176](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/core/src/delay-render.ts#L176) | 모델은 asset id만 선택하고 서버가 project/권리/hash를 검증한 local manifest로 해석한다. Remotion의 경로 유틸리티를 권한 시스템으로 착각하지 않는다. export에는 준비 완료된 허용 자산/font만 전달한다. |

공식 문서도 frame 기반 애니메이션과 props 기반 parameterization을 설명한다: [packages/docs/docs/animating-properties.mdx:97](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/docs/docs/animating-properties.mdx#L97), [packages/docs/docs/parameterized-rendering.mdx:26](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/packages/docs/docs/parameterized-rendering.mdx#L26). 임의의 사용자 코드가 항상 결정적이라는 보장은 아니다. 외부 fetch, 시간, random, font/asset 차이를 제한해야 재현성을 검증할 수 있다.

## Aethon 내부 기능으로 연결할 최소 경계 — 구현 전 제안

1. **모델 authoring → 검증된 scene proposal**: 한국어 문구, 도형, layout, keyframe timing/easing을 구조화한다. Python 서버는 알 수 없는 필드·실행 코드·경로/URL·권한 상승을 거절한다. 임의 TSX/React 코드 실행은 초기 경로로 제안하지 않는다.
2. **영속 version/undo**: SQLite의 immutable scene revision + parent revision + edit commands. 모델 편집은 현재 revision을 지정하며 stale/conflict면 apply하지 않는다. 사람 승인으로 새 revision을 적용하고 restore도 이력으로 남긴다. 원본 미디어는 보존한다.
3. **평가와 표시 분리**: 프레임 evaluator가 draw list를 산출하고 JS preview가 표시한다. export도 동일한 평가 규칙과 명시적 font/text layout을 사용해야 한다. Python과 JS에 따로 구현하면 golden vectors로 수치 일치를 검사해야 하며, 실제 rasterizer의 글꼴/색/antialias 차이는 별도 검증 대상이다.
4. **내부 local render job**: scene revision, renderer version, fps/frame count, dimensions, font/asset hashes, render settings가 포함된 manifest를 고정하고 렌더한다. 기존 승인·취소·재시도·idempotency·권리 검증 서비스를 재사용한다. 렌더 엔진 구현과 실제 글자 rasterizer 선택은 아직 필요하며 이번 조사에서 해결/설치하지 않았다.
5. **범위**: 모델이 한국어 텍스트+도형의 레이어/키프레임을 직접 작성하고 사용자 수정으로 편집 가능해야 한다. fal 영상 생성이나 외부 Remotion 서비스로 대체하지 않는다. Remotion 표현/구현 코드를 복사해 자사 엔진으로 명명하는 방안도 제안하지 않는다.

## 가장 작은 실제 검증안 — 전부 NOT RUN

- 4초, 1920×1080, 24fps, 정확히 96프레임. 외부 asset 없이 한국어 문구 1개와 원/사각형, 명시적 easing/keyframe. layer id와 revision을 보존한다.
- 실제 Claude response/usage로 authoring 출처를 증명한다. 손으로 작성한 fixture나 mock response는 validator 검증용일 뿐 Claude 제작 증거가 아니다.
- frame 0/12/24/48/72/95의 decoded 이미지에서 텍스트/위치/opacity를 비교하고, 미리보기와 export의 동일 frame 및 font manifest를 확인한다. 메타데이터·frame count·끝 프레임을 함께 검사한다. 이번에는 어떠한 렌더도 실행하지 않았다.
- 수정 요청은 “문구 유지, 원의 진입만 12프레임 늦춤”처럼 범위를 정하고, 다른 레이어 불변/새 revision/undo/권한 승인을 검증한다. invalid schema, font missing, timeout, cancel, stale revision도 검사한다.
- imported media/captions/audio는 이 작은 motion 시험 이후 별도 경계 시험으로 연결한다. 이 소스 조사만으로 AV sync 또는 production readiness를 주장하지 않는다.

## 라이선스 확인

고정 commit의 루트와 core LICENSE는 Remotion 고유 라이선스다. 평가 및 일정 자격의 무료 사용 조건과 회사 라이선스 구분이 있으며, 수정본 판매·임대·재라이선스 목적의 복제/수정을 금지하는 문구가 있다. v5 변경 예정 안내는 v4 후보의 사용 허가를 대체하지 않는다. [LICENSE.md:18](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/LICENSE.md#L18), [LICENSE.md:29](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/LICENSE.md#L29), [LICENSE.md:41](https://github.com/remotion-dev/remotion/blob/5217b0c90623f2decb4575714fac89d3c4b69896/LICENSE.md#L41).

따라서 MIT/무제한 fork/resale로 취급하지 않았다. 라이선스 선택·구매·수락·법적 적합 판정은 하지 않았다. 이번 산출물은 개념 설명과 자체 구현 경계 제안이며 제품 코드에 Remotion 소스를 넣지 않았다. REA 패키지의 MIT 표시는 이 Remotion 라이선스와 무관하다.

## 파일과 남은 blocker

- `source-manifest.json`: 원본 URL/commit/path/byte/SHA-256, allowlist 17개.
- `execution-evidence.json`: 파일 무결성, 실제 실행/미실행 구분, 거절 사유 원문.
- `public-question.txt`: 시도된 generic 공개 자료 질문. 비공개 프로젝트 내용 없음.
- 공개 snapshot은 `/tmp/remotion-public-research-20261026/source`; 제품 루트는 REA inventory에 입력하지 않았다.

남은 blocker의 정확한 행동은 **공개 snapshot을 새 Codex 모델 세션과 REA MCP로 분석하는 명령**이다. 상태는 **DENIED, known not executed**다. 완료된 것은 공개 다운로드와 정적 소스 검토다. 재개하려면 실효 provider/base endpoint·수신자를 비밀 값 없이 확인하고 그 수신자에게 위 공개 자료만 전달하는 실행 승인이 필요하다. 현재는 승인 대기 중인 프로세스도 없다.
