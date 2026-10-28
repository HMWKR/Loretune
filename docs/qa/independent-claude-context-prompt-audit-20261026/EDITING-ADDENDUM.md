# 모델 지시 영상 편집 — 한정 capability 검토

현재 지원: Claude/OpenAI/Grok의 공통 `propose_timeline_edit` → versioned proposal → 사람이 hold/reject/approve → 기존 timeline service로 새 버전 저장. 모델은 현재 컷의 Take·trim·duration만 제안할 수 있다. 기존 원곡·자막은 보존하며, 적용된 편집은 별도 출력 승인을 다시 받아야 한다. `request_render`는 이미 승인된 버전/grant만 사용한다.

- `local_creation_tools.py:10–35`: schema와 proposal. `37–52`: base version/context hash 재검사 후 사람 적용. `72–86`: 승인 render 및 기존 job receipt 재사용.
- `editing.py:90–94`: 새 immutable timeline version. `app.py:704–707`: 과거 버전 복원을 새 버전으로 저장. `716–726`: 사람의 출력 승인. 기존 media 원본 파일을 제안이 덮지 않는다.
- 독립 추가 실행 **4 tests PASS**: 세 protocol의 proposal→human apply 및 타 입력 보존, stale/foreign 거절, 중복 proposal 멱등성, editor가 앞서가도 기존 승인 render의 audio/captions snapshot 보존. [결과](editing-addendum-results.json), [로그](editing-addendum.log). 실제 provider는 0이며 기존 테스트의 합성 로컬 render만 포함한다.
- source와 validator probe에서 모델 tool의 `order`, `captions`, `audio_offset` 추가 필드는 모두 거절. **컷 reorder/add/remove, 자막 내용·시간/스타일, 음악 교체·offset·mixing, export profile을 모델이 새로 제안하는 기능은 현행 schema에 없다.** UI 편집에 존재하는 기능과 모델에게 노출된 기능을 구분한다. motion layer/keyframe 도구도 없다.

최소 확장 제안: 하나의 versioned edit-command union에 `set_clip/ move_clip/ set_caption/ select_audio`처럼 실제 필요한 작업만 추가. 현재 validation·권리·snapshot·idempotency·proposal review 경로를 재사용하고, 변경 전후 diff를 보여준 뒤 사람이 적용한다. restore와 export는 기존 별도 승인을 유지한다. AI가 승인/권리/가격/actor를 전달하는 필드를 추가하지 않는다. 모델 변경이나 ontology 변경 중 대기한 제안은 최신 revision 확인 뒤 재검토한다.

preview는 현재 UI의 기존 재생을 활용할 후보이며 **새 모델 편집안의 실제 시각 preview를 이번에 브라우저로 확인하지 않았다**. 모든 편집 기능 완성 또는 실제 Claude가 원하는 편집을 작성했다고 판정하지 않는다. 작가 모델의 실제 응답 + normalized edit commands + 승인 전후 timeline diff + 기존 원본 hash + 최종 출력 snapshot/metadata를 한 증거 사슬로 추가 검증해야 한다.

## REA/Codex CLI와 native renderer 방향 보정

사용자가 “Codex CLI는 REA MCP를 사용 가능”이라고 확인한 사실을 반영한다. 이 도구 세션의 공개 REA 함수 0개라는 관측은 **CLI에서도 사용할 수 없다는 뜻이 아니다**. `/opt/homebrew/bin/codex`의 MCP 관리 명령을 확인한 뒤, `codex mcp list --json` 결과에서 name/enabled/transport type만 추려 **`rea`, enabled=true, stdio** 등록을 확인했다([비밀값 없는 metadata](cli-rea-metadata.json)). URL/command/args/env/인증 정보·원문 config는 출력하거나 산출물에 저장하지 않았다. 등록은 실제 REA tools/list·세션 연결·분석 성공과 다르다. 이 감사에서 REA server를 시작하거나 live tool schema를 호출하지 않았으므로 그 단계는 미검증이다. 새 모델 실행/설치/등록/로그인은 하지 않았다. 도움말은 성공했고 PATH alias 생성 불가 경고가 있었으며, alias/권한 설정을 바꾸지 않았다.

사용자의 최신 방향은 외부 Remotion 연동 자체보다 **Aethon 고유 기능**이다. 제안할 경계는 모델 저작 → 자체 scene/edit schema → 검증된 명령 → frame-based preview/render → SQLite version/undo → 기존 export manifest다. Remotion에서 시간축/프레임 평가·파라미터화·preview와 export 일치 같은 개념을 조사하되 자체 구현과 제3자 코드 재사용을 구분한다.

parent의 공식 라이선스 조사에 따르면 Remotion을 MIT·무제한 fork/resale로 가정하면 안 되며 candidate 버전의 LICENSE/해당 버전 terms를 고정해야 한다. 이 감사는 코드 복사/재브랜딩/설치/라이선스 수락/결제를 하지 않았다. 읽기 전용 공식 소스 분석 후 독립 구현 또는 허용된 dependency 사용 범위를 선택한다. 구체적 source 분석은 primary의 실제 REA CLI schema 확인과 공식 연구 결과에 이어 진행할 별도 범위다. 기존 ontology/session 반례 결론을 그 조사 완료까지 지연하지 않는다.

최종 부모 인계: primary의 최신 CLI 외부 소스 검토는 **외부 소스 전달 승인 부재로 실행 전에 거절**됐다. 위 metadata discovery는 그 분석과 다른 실제 실행 완료 read이며, 이 감사에서는 거절된 source review를 실행하거나 다른 경로로 재시도하지 않았다. 사용자의 목표는 외부 Remotion 서비스 연결이 아닌 Aethon 내부 editable layer/keyframe/preview/local export다. 부록의 worker 경계는 Aethon 내부 책임 분리 제안이며 외부 서비스 대체 제안이 아니다.
