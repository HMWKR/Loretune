# 새 fal 제작 UI 표시 계약 (staging)

현재 실행본8773은 고정 유지. 작업본: `/var/folders/t7/p6pl4snd6pd3cmz1y80_7fzw0000gn/T/loretune-fal-creator-z4_ck507`.
읽은 디자인 근거: `../design-benchmark-20261025/creator-integrated-review/{REPORT-ko.md,NEXT-PASS-ko.md}`. 선택 FLUX를 미선택으로 표시한 결함은 staging backend에서 수정. 원본 통합/디자인90점 판정은 아직 아님.

## 서버 표시 데이터

`GET /api/state`의 현재 `projects[name]`:

- `media_connections.image` / `.video`: `model`(저장된 선택 모델 endpoint명), `state`(`unconfigured`=진짜 선택없음, `unverified`=선택됨·연결검증전, `blocked`=차단/종료/사용불가), `reason`, `mode`, `can_prepare`, `available`.
- `image_connection`: 위 image 선택 상태를 그대로 반영. 선택되어 있으나 runtime adapter가 없더라도 model을 지우지 않음. legacy capability가 새 선택을 덮지 않음.
- 현재 모든 실제 registry는 비활성/미검증. `available`은 false. `can_prepare=true`는 정확한 입력의 유효한 견적과 trusted runtime 연결이 있다는 뜻이며 외부 실행 승인 아님. `mode=contract-fake`는 실제 AI/과금이 없는 시험 경계.
- `media_actions[]`: 불변 저장 작업의 `id`(hidden handler handle), `shot`, `role`, `model`(작업 원래 모델), `prompt`, `options`, `estimate{amount,currency}`, `estimate_kind`, `estimate_expired`, `mode`, `approval`(required/approved/held/rejected), `can_approve`, `can_execute`, `can_decide`, `reason`, `output_policy`.
- `job`: `id`(hidden), `state`, `failure_code`(diagnostic), `take`, `stale_input`, `cancel_requested`, `can_cancel`, `recovery{can_status,can_collect,reason}`, `cost{reservation_state,estimate,actual,billing_confirmed,evidence}`. 실제 비용과 fixture/estimate/unknown 구분. 현재 선택 모델을 과거 job에 덮어쓰지 않음.
- `candidate{take,selected,review,rights_known}`: 결과 수집 성공이 선택·승인이 아님. 기존 Take 보존. 사용권 확인 이후 시작 프레임 지정·승인. 비공개 원본 URL을 다음 provider로 전달하지 않고 승인된 로컬 PNG bytes로 재인코딩.

## 사용자 행동과 기존 서비스

| 조건 | 버튼 | 기존 API action |
|---|---|---|
| can_prepare | 입력·예상 비용 확인 | media_prepare (현재 shot_revision, 선택 역할/options/refs) |
| can_approve | 이 조건 승인 | media_action_decide decision=approved |
| can_execute | 승인한 작업 실행 / 승인한 모의 작업 실행 | media_action_decide decision=execute |
| can_decide | 보류 / 거절 | media_action_decide decision=held/rejected |
| job.can_cancel | 취소 요청 | cancel_generation |
| recovery.can_status | 기존 요청 확인 | recover_media_job operation=status |
| recovery.can_collect | 기존 결과 연결 | recover_media_job operation=collect |
| candidate | 새 Take 선택·검토 / 선택한 Take 검토로 이동 | 기존 select, 검토는 기존 review_take 별도 |
| !rights_known | 사용권 기록 (근거 필수) | declare_take_rights |

`id`/job/action hash/grant/내부 도구명은 기본 표면에서 숨김. 상세 기록 disclosure만 허용. 변경된 입력은 기존 action을 덮지 않고 새 준비. unknown/403/만료는 새 생성·자동 선택·환불 성공으로 바꾸지 않음. 403은 새 근거와 기존 요청/결과에 고정된 일회 복구 확인 없이는 버튼도 비활성. 서버가 최종 재검사.

## DOM 소유·접점

staging 기능 소유: `#mediaConnections`, `#mediaPrepareDetails`, `#mediaPrepareForm`, `#mediaRole`, `#mediaRatioLabel`, `#mediaDurationLabel`, `#mediaPreparationHint`, `#prepareMedia`, `#mediaActionCards`.
작업카드 `.media-action-card`, `data-action-card` hiddenhandle. 핸들러 attributes: `data-media-decision`+`data-action`, `data-media-recover`+`data-job`, `data-media-cancel`, `data-media-edit`, `data-media-take`, `data-media-rights`. 실제 API에 연결됨; 디자인에서 복제 mutation/가짜 버튼 만들지 말 것.
기존 `#imageConnection/#imageRequirements/#showImageModels/#imageRecoveryJobs`, `#generationPreparations` 보존. 새 dispatch 작업은 legacy 목록에서 제외해 중복/잘못된 recovery 버튼 방지. 디자인에서 이 표시를 한 장면 제작 카드로 묶되 기능 소유 핸들러·ID 유지. 기존 Take review/F07, comparison, timeline/caption 핸들러 범위는 변경하지 않음.
`drawMediaCreator`, `mediaActionMarkup`, `mediaPreparation`이 기능 renderer. 권한 계산은 서버만. 준비 입력·사용권 draft는 프로젝트/장면/작업에 묶어서 다른 문맥과 분리. 가격/권한 준비 상태가 job 변경 없이 변하는 경우도 poll로 새로 반영.

## 최종 확인 및 디자인 통합

새 focused 15건을 포함한 전체 회귀326건 통과. 기존311건 결과와 별도로 실행했다. JS syntax와110 Python AST 통과. 코드/패치/실행본 전체 해시는 `patch-manifest.json`, `source-verification.json` 참조.

Ego17/별도 localhost64864에서 fake chat tool→계획 저장→사람 승인→이미지 준비→보류/재승인→1회 fake submit→수신 중단→동일 요청 수집→Take1→사용권→첫 프레임 승인→선택 영상 모델 준비·승인→fake submit→Take2→사람 선택/검토→음악·자막 포함 실제 로컬MP4→서버 재시작 후 재열기까지 관찰. 결과5.000초/1920×1080/AAC48kHz/한국어 자막0–4.5초. 결과 완성과 납품 검토 승인은 별도이며 납품 승인은 아직 없음.

재시작 때 provider 연결을 주입하지 않아도 FLUX 선택은 보존되고 `unverified / available=false / can_prepare=false`로 표시. 기존 작업 원래 모델·두 Take·선택·출력은 보존. 외부 호출/키 조회0. 두 submit은 fake transport만. 브라우저 테스트 공간은 종료, 실제8773은 변경 없음.

디자인 패치는 이 staging의 `index.html`과 통합해야 한다. 모델명 제품 라벨 개선·카드 통합은 디자인 측 소유이며 서버 상태/handler는 위 계약을 그대로 쓴다. `available`을 CSS나 모델 선택만으로 true로 만들지 않는다. 현재326tests는 디자인90점이나 실제 fal integration 통과 근거가 아니다.
