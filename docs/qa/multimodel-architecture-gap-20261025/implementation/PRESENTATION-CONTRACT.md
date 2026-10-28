# 디자인 통합용 API 계약 — 현재 staging만 적용

기존 index.html/디자인 파일은 수정하지 않았다. 현재 화면 고정 버전에 이 계약이 제공된다고 가정하지 않는다.

- `/api/model-catalog` / state.model_catalog: chat 3종(Anthropic Haiku / OpenAI GPT-6 Luna / xAI Grok), fal image 2종과 video 2종. 모두 `integration_unverified` 또는 기존 Kling `integration_blocked`. 등록/선택 저장은 인증/활성화가 아니다. 기본값 없음.
- project.media_actions: 현재 작품의 `id`, `shot`, `role`, `model`, `prompt`, `options`, `estimate`, `estimate_kind`, `estimate_expired`, `approval`, `job_id`, `mode`. 화면은 장면/모델/범위/비용/승인·진행 상태를 우선한다. ID는 버튼 연결에만 사용한다. hash/grant/reservation/파일 경로는 이 요약에서 제외했다. 기존 서버 감사 증거는 보존한다.
- `media_prepare` mutation: song, shot, prompt, options, refs, shot_revision, optional model. image options={ratio}; video={duration,generate_audio:false}. refs는 기존 작품 Take의 shot/take/sha256/role. 검증된 서버 adapter·견적 없이는 차단. 모델명만 고른다고 실행 가능하지 않다.
- `media_approve`: song, action_id. 모델 도구가 호출할 수 없는 사람 경로. 저장한 입력·가격·정책에 대한 별도 서버 전송 gate와 예산이 충족돼야 승인 생성. 이 API 자체가 provider를 활성화하지 않는다.
- 공통 AI 도구 `prepare_image_action` / `prepare_video_action`: 제작 후보와 견적만 저장. `estimate_media_plan`: 저장된 모델별 견적 조회. `request_media_generation`: 기존 사람 grant로 같은 큐에 신규 접수하며, 이미 접수한 action은 기존 job을 반환. 승인 UI의 재클릭을 요구하지 않는다.
- `declare_take_rights`: song,shot,take,sha256,shot_revision,evidence. 사람이 실제 사용권 근거를 기록하는 경로. AI tool로 노출하지 않는다. 기존 사용 중지 기록을 해제하지 않고, 파일/provenance/과거 출력은 유지한다. 생성 이미지의 사용권 미확인을 자동으로 승인하지 않는다.
- 선택 모델과 실제 진행상태는 보이되 도구 trace·요청ID·해시는 진단 disclosure로 분리. contract-fake는 짧게 '시험용 미디어'로 표시하되 실제 생성으로 바꾸지 않는다.

남은 UI 통합: 위 media_actions의 승인·보류·실행 상태를 기존 제작 검토 흐름에 반영, 생성 이미지 사용권 확인/시작 프레임 검토 연결, 현재 캡션/리뷰 초안 보존. 새 fal jobs의 일반 복구 UI는 아직 기존 image_pipeline 경로만큼 연결되지 않았으므로 지원 가능으로 표시하면 안 된다. 검증 후 활성화 전까지 생성 버튼은 비활성이다.


## 로컬 편집·기억 제안·출력 도구 연결 (추가 staging 계약)

세 도구 모두 공통 `production_tool`과 같은 Store 트랜잭션·멱등 기록을 사용한다. Anthropic/OpenAI/xAI의 정규화된 호출 형태에 공통 적용한다. 실제 모델을 활성화하거나 유료 미디어 작업을 요청하는 변화는 없다.

### 편집 제안과 적용을 분리

- AI `propose_timeline_edit`: `description`, `timeline_version`, `changes`를 받는다. changes는 `{clip_index,take,trim,duration}` 배열(1–30개)이다. 기존 EDL을 복사하고 명시한 컷만 바꾼다. 음원 버전·오프셋·자막·비율·다른 컷·원본 Take는 유지한다.
- 영수증은 `status:proposed`, `proposal_id`, `base_version`, `changes`, `audio_version`, `captions_preserved:true`, `applied:false`, `output_approved:false`이다. 화면은 “편집 제안 — 아직 적용하지 않음”으로 표현한다.
- `project.timeline_edit_proposals`에서 현재 작품의 제안을 읽는다. 내부 hash/trace는 기본 UI에 노출하지 않는다.
- 사람 mutation `review_timeline_proposal`: `song`, `proposal_id`, `timeline_version`, `decision:approved|held|rejected`. 승인 시 기존 Store.timeline/editing.save_timeline 경로로 새 EDL 버전을 저장한다. 기준 타임라인/선택 Take/자산 hash가 바뀌면 거절한다. 기존 버전은 남으며 새 버전에는 출력 승인이 없다.
- 같은 적용 승인을 재전송해도 새 버전을 만들지 않는다. 이미 적용한 제안을 “거절”해 과거 변경을 조용히 취소하지 않는다. 기존 버전 복원 또는 새 편집을 사용한다.

### 근거 있는 기억 변경 후보

- `search_project_context` 결과의 `sources`는 현재 작품의 canonical snapshot·승인 ontology 설명·해당 run 사용자 입력만 포함한다.
- AI `propose_memory_update`: `description`, `kind:character|place|style`, `label`, `entity_id`(신규는 빈 문자열), `source_id`, `excerpt`, `ontology_revision`.
- 현재 작품의 실제 출처와 정확히 일치하는 excerpt가 필요하다. source 없는 내용, 다른 작품 entity, 오래된 ontology revision은 차단된다. 모델 인수의 approved 플래그는 허용하지 않는다.
- 기존 ontology.propose 저장소에 provenance와 model-proposal actor, inferred 상태를 기록한다. 영수증은 `status:proposed`, `proposal_id`, `base_revision`, `scope:current-project`, `applied:false`, `canonical_approved:false`이다.
- 기존 `ontology_apply` 사람 검토 경로만 canonical 상태에 반영한다. 세계관 사실이나 다른 곡의 전역 canon을 자동 수정하지 않는다. UI는 “설정 변경 제안”이며 “기억 저장 완료”가 아니다.

### 출력 접수와 검증된 파일·최종 승인을 분리

- 사람의 기존 `approve_timeline` 결과에 approval `id`, `actor:local-owner`, `execution_scope:local-render`, 정확한 `timeline_version`을 기록한다. AI 도구에는 승인 생성 기능이 없다.
- AI `request_render`: `timeline_version`, `grant_id`(현재 타임라인 approval.id)를 받는다. 새 승인을 반복 요구하지 않고, 같은 승인으로 이미 접수한 작업은 기존 receipt만 반환한다. 취소/실패 후에도 자동 새 작업을 만들지 않는다.
- 기존 Store.estimate_render → Store.render_job → local worker를 재사용한다. 권리·누락 미디어·현재 승인·출력 검사와 취소·manifest 고정 계약을 그대로 적용한다. local 비용은 기존 “미계량” 표시이며 외부 API 비용0이다.
- 영수증: `status:accepted|existing`, `job_id`, `state`, `mode:local-render`, `finished_verified`, `output_approved`, `cost`, `external_calls:0`. queued이면 두 승인/완료 플래그는 false다. 실제 검증 저장 후 finished_verified=true가 되며, 별도의 사람 `delivery_review` 전에는 output_approved=false다.
- 기존 `get_generation_job`/모델 교체 handoff에도 로컬 render가 포함된다. 다운로드 경로·토큰·파일 시스템 경로는 이 도구 결과에 없다.
- 이전 approval.id가 없는 역사적 타임라인은 AI render에 사용할 수 없다. 기존 UI 로컬 출력은 보존하며, 해당 버전을 사람이 다시 승인하면 새 ID가 생긴다.

이번 단계에서는 UI를 변경하지 않았다. 편집 제안 비교/보류/적용 카드와 로컬 출력 상태 표시를 디자인 패치와 함께 실제 화면에 연결·검증해야 한다. 기억 제안은 기존 ontology 검토 UI 데이터와 같은 저장소를 사용한다. 테스트 통과는 새 UI 여정 또는 실제 모델 호출의 증거가 아니다.
