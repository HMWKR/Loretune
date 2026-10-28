# Loretune 디자인·UI/UX 벤치마크 및 구현 명세
검토일: 2026-10-25 UTC. 부모 작업에서 전달한 조사 보고서의 로컬 적용본. 경쟁사 관측, 공식 문서 설명, Loretune 제안을 구분한다. 증거 이미지 파일은 이 Mac에 전달되지 않았으며 아래 파일명은 목록만 의미한다.

## 1. 결론
신규 사용자 요구에 따라 Loretune은 채팅형 제작과 제작 워크벤치를 동등한 진입점으로 제공하는 것을 목표로 한다. 두 모드는 같은 프로젝트·샷·승인·타임라인을 공유한다. 현재 채팅 구현은 로컬 줄 단위 초안과 샷 추가까지이며 자동 생성 전체 흐름은 미완료다. 프로젝트에서 기획·샷·take·편집·최종본을 연결한다. 새 take는 기존 승인 결과를 덮어쓰지 않는다. 진행/실패 상태를 작업별로 표시하고 이전 결과·입력을 유지한다. 재사용은 명시적으로 선택한 정확한 자산/스타일/캐릭터 버전을 연결하고 승인 상태를 새 문맥에 자동 전이하지 않는다. 실제 구현 범위만 UI로 약속한다. Refero와 REA는 별개 도구다.

이번 로컬 구현에서 음원 결합은 추가되었으므로 기존 무음 MP4만 지원한다는 초기 설명은 더 이상 최신 상태가 아니다. 선택한 음원이 없을 때만 무음이며, 자막은 MP4 선택 트랙과 SRT이다. 번인 자막·정밀 드래그 편집은 미지원이다.

## 2. 근거와 증거 등급
부모 조사: Refero 전체 스타일 Krea/Runway/Frame.io 3개, 실제 이미지 6개(Runway 입력·생성중·자산·구형 Gen-2, Boords, Hello Ivy), Runway composer 13단계/저장 위치 5단계 및 Hello Ivy 승인 3단계 흐름. LTX 공식 설명 이미지 3개, Tunee 공개 포스터 1개와 공식 제품/도움말.
- OBSERVED: 이미지나 실제 공개 화면에서 확인한 배치·텍스트·컨트롤.
- DOCUMENTED: 공식 문서가 설명하나 직접 실행하지 않은 동작.
- PROPOSED: Loretune 설계 제안.
- UNKNOWN: 비공개 DB/큐/스토리지, 서버 구현, 실제 성능, 로그인 후 전체 최신 UX.
Refero는 아카이브다. 구형 Gen-2를 최신 기능으로 간주하지 않는다. LTX/Tunee 이미지는 설명 이미지/포스터이며 로그인한 실행 증거가 아니다. 정적 이미지에서 DOM·API·애니메이션 시간을 알아냈다고 주장하지 않는다.

## 3. 제품별 벤치마크
### Runway
OBSERVED: 좁은 입력 패널과 넓은 결과 영역; 이미지/비디오 탭·참조·스타일·생성 행동이 입력 쪽에 모임. 생성 중에도 입력 유지, 타일 안 Generating 상태. 별도 자산함에 타입/태그/그리드/목록/정렬/업로드. 유료 제한 UI를 그대로 복제할 필요 없음.
DOCUMENTED: 세션은 유사 샷/변형 묶음이며 세션 삭제와 자산 삭제가 다름. 참조는 기본 임시이며 저장 후 다른 세션 재사용. 오류 원인에 따라 입력 수정/재시도/모델 변경을 안내하나 공급자 원인 정보는 제한적일 수 있음.
PROPOSED: shot 아래 불변 take, 사용중/라이브러리 저장 구분, 오류에 문제·보존 결과·다음 행동 표시.
근거:
- https://refero.design/pages/eb542fab-d007-4e38-a13f-6bf5b1b3f978
- https://refero.design/pages/0f45fd53-dee9-457a-8d37-b2155b970077
- https://refero.design/pages/b8b26590-af11-434a-8ee8-34b80c590b56
- https://help.runwayml.com/hc/en-us/articles/33545310653203-Generating-with-Sessions
- https://help.runwayml.com/hc/en-us/articles/52963720640275-Using-reference-media-to-guide-your-generations
- https://help.runwayml.com/hc/en-us/articles/32880432736659-Why-am-I-receiving-errors-when-trying-to-generate
작은 수치/아이콘은 판독 불충분하므로 FPS 사양 근거로 쓰지 않음.

### LTX Studio
OBSERVED(공식 설명 이미지): Gen Space/Storyboard/Timeline을 프로젝트 공통 맥락으로 제시. 스토리보드에 장면 그룹·번호·썸네일·설명·이미지 편집/모션 생성. 타임라인 이미지에 영상/오디오 파형·플레이헤드·눈금·줌·재생. 세션은 이름/시간/썸네일로 구분.
DOCUMENTED: 생성/스토리보드/타임라인/My Assets 연결, 비파괴 참조 편집, 샷 Retake, 일관성 Elements.
PROPOSED: 공통 프로젝트 헤더 유지, 장면=내러티브/샷=편집/take=결과 버전 구분, 부분 수정은 유지/변경 대상을 명시하고 새 take로 처리.
https://ltx.io/blog/introducing-projects
https://ltx.io/blog/ltx-studio-tutorial
2025 업데이트와 2026 튜토리얼의 역할 설명 차이가 있으므로 메뉴를 맹목적으로 복제하지 않는다.

### Tunee
OBSERVED(공개 포스터): 좌측 대화와 넓은 캔버스, 음악/캐릭터 참조 칩, Analyze Audio/Image와 개별 Running 상태, 입력기 첨부/음악/모델과 빈 상태 안내.
DOCUMENTED: 곡·캐릭터·장면·자산·스토리보드 통합 및 내장 편집. FAQ 검색에는 샷 재생성/수정/드래그/트림/분할과 제한이 함께 있어 로그인 후 재확인 필요.
PROPOSED: 대화는 보조, 샷/take/승인은 명시적 컨트롤. 분석/계획/참조/생성/조립을 분리. 참조 칩에 버전·범위 표시.
https://www.tunee.ai/features/music-video-generator
https://www.tunee.ai/features/_public/assets/posters/music-video-workspace.webp
https://forum.tunee.ai/t/can-i-edit-my-music-video-after-its-generated/3145
포럼 본문은 부모 조사에서 502/503 실패. 로그인 프로젝트 미실행. Refero 전용 결과 미발견은 전체 자료 부재의 증거가 아님.

### Boords / Hello Ivy
OBSERVED: Boords는 이미지·액션·보이스오버·카메라·메모를 같은 행에 연결. Ivy는 버전·미디어·댓글·승인/수정요청/대기/거절을 연결.
PROPOSED: 샷 필드는 구간/가사·스토리 비트/설명/카메라·모션/캐릭터/메모. 검토 패널은 정확한 take 버전과 수정 이유, 색 외 텍스트 상태를 표시.
https://refero.design/pages/439138ac-c66b-42b4-9b6e-6dce25e5cd3e
https://refero.design/pages/bf2a4956-c059-48c1-9709-b08fd5541630
https://refero.design/flows/4526

## 4. 시각 방향 잠금 — 중립적 제작실 (PROPOSED)
주방향 Krea: 검정/차콜 크롬·밝은 글자·화이트 주요 행동, 실제 영상이 가장 강한 색채, 절제된 8px 모서리/경계, 대상·상태·다음 행동 우선. 장식 그라데이션·큰 hero 없음. 한정 차용: Runway 조밀한 입력/지속 결과, Ivy 버전별 검토. Frame.io 보라 글로우/캡슐/마케팅 여백은 미채택.
토큰 제안: canvas #0B0B0B, panel #171717, raised #222222, line #363636, text #F5F5F5, muted #ADADAD, primary #F5F5F5/text #101010. 성공 #86D5A1·경고 #F4CD77·오류 #F29A9A는 상태 전용. focus white 2px+2px offset. radius 4/8/12px, spacing 4/8/12/16/24/32px. 로컬 한국어 system-ui 사용; 유료 전용 폰트 번들하지 않음. 메타12/control14/설명16/패널20/프로젝트28px, 한글 line-height1.55. 수치만 tabular-nums.
Krea style 3a63b3fa-dc79-4dc3-935e-3f8f4ab447a7; Runway 341e4d88-ae06-422e-99b6-c8b159351a8f; Frame.io 6a82f165-eb8e-4a87-a0dd-31593f08128b.
미디어: 실제 업로드 썸네일, 비면 정직한 자리표시자. 데모는 데모 표시. thumbnail cover, review contain.

## 5. 화면 구조 계약 (PROPOSED)
공통 헤더 56px: 프로젝트·저장 상태·모드·작업 수·출력. 저장은 이 기기에 저장됨을 명시. 1440px 제안: rail56, 샷220~260, 중앙 프리뷰/take, inspector300~340, 하단 시퀀스160~220. 정확한 경쟁사 치수 아님. 중앙 유효폭480 미만이면 인스펙터 drawer. 1024 이하 샷 접기/인스펙터 drawer, 모바일은 검토·승인·다운로드 우선.
시작: 제목·음원/무음·길이·비율·스타일, 고급 옵션 접기. 실제 duration/MIME/크기만 표시하고 BPM 추측 금지. 재사용은 사전 선택·요약.
샷 목록: 번호·구간·16:9 썸네일·설명·상태·take 수. 다른 작업 실행 중 탐색 가능. 행 선택과 drag 구분, ↑↓ 키보드 대안.
Take: 번호·시간·모델/설정·참조·길이/규격; 미리보기/선택/승인/수정요청 구분. A/B 같은 플레이헤드, 길이 차이 표시. 새 take 자동 승인 금지.
자산함: 검색·유형·태그·사용중 필터, 출처/버전/권리/검토 정보. 대상 샷 선택 후 연결. 프로젝트 제거와 원본 삭제 구분·참조 무결성.
출력: 규격·총길이·음원·미승인/누락 수, 승인된 정확한 take manifest 고정. 초안은 별도 표시. 변경 후 이전 결과를 최신으로 오인하지 않게 stale 표시.

## 6. 상태·상호작용 계약
Job queued/running/succeeded/failed/cancelled; take unreviewed/approved/changes_requested/rejected; selection은 별도. dirty/stale은 계획·선택과 출력 차이.
- 빈 상태: 지원 형식/다음 행동, 샷 설명 보존.
- 업로드: 파일별 진행/취소, 완료 파일 보존.
- 입력 오류: 필드 원인+요약, 값 보존.
- 대기/진행: ID·제출 시각·실제 단계, 다른 샷 탐색, 이전 결과 보존.
- 성공: 검토 대기, 비교·선택·승인.
- 실패/정책차단: 원인·복구·상세 접기, 기존 성공 결과 보존.
- 네트워크 단절: 상태 미확인으로 표시하고 job/idempotency key로 재조회. 무조건 새 요청 금지.
- 새로고침: 서버 작업 복원. 취소는 실제 가능한 단계만 제공.
- 부분 수정: 기준 take·바꿀 요소·유지할 요소·영향, 새 take 생성 후 자동 교체하지 않음.
- 출력: 실행 스냅샷·단계, 실패 시 이전 export 보존.
숫자 진행률/ETA를 꾸미지 않는다. 완료된 샷 수만 측정해 표시. 결과 불만족과 시스템 실패 구분. 공급자가 부분 보존을 보장하지 않으면 명시하며 미지원 버튼을 노출하지 않음.
재사용: 정확 버전/권리/출처를 연결. 새 문맥의 승인 자동 상속 금지. 원본 수정 없이 새 버전/fork.

## 7. Loretune 시스템 계약 (경쟁사 내부 분석 아님)
최소 객체: Project, Scene, Shot, Take, Asset, AssetVersion/ReferenceLink, Job, ReviewEvent, Export, ProjectRevision.
불변조건: take 입력 스냅샷 불변; 같은 샷 성공 take만 선택; 승인 target 고정; export 실행 manifest 고정; timeout 후 기존 job 조회; 삭제/이동 참조 보존; 오류 설명/code/retryable/민감정보 없는 상세 분리; SQLite와 로컬 worker로 시작 가능.
API 의미: 선택/take/job/승인/수정요청/재사용 계획/export. 변경 revision 불일치409. SSE/backoff polling. capability는 실제 기능 상태를 반환.

## 8. 모션·접근성·성능 (제안, 경쟁사 실측 아님)
hover120ms/작은 상태200ms/drawer240~320ms, reduced-motion에서 이동·확대 제거. 전체 화면 점프 금지. 텍스트 상태·aria-live, field error focus, modal focus trap/ESC/원래 버튼 복귀. drag-only 금지. 자동재생/자동소리 금지. 썸네일 비율 고정·필요 미디어만 로드. 100개 이상 pagination 검토. 실제 배경 대비 검사; 12px 메타가 핵심 정보 유일 표현이 되지 않음.

## 9. 구현 순서와 필수 E2E
P0 상태 분리·결과 보존·실패 복구·복원·정확한 manifest·한국어 상태. P1 워크벤치·검토·A/B·재사용·비파괴 편집·반응형. P2 실제 capability가 있을 때 비트/파형/정밀 분할/다중 모델/팀/공급자 부분수정.
필수: (1) 세 샷 중 하나 실패해도 나머지 보존 (2) 새로고침 후 job 중복 없음 (3) 새 B가 승인 A 대체 안함 (4) B 선택 후 export stale (5) 렌더 중 선택 변경에도 snapshot 유지 (6) 재사용 원본 불변 (7) 누락/미승인 최종 차단 (8) 키보드 주요 흐름 (9)1440/1280/1024 및 모바일 controls (10)empty/loading/success/error/blocked/stale 실제 시각 확인.
현재 모든 조건을 통과했다고 주장하지 않으며 implementation-matrix와 stage checkpoint에 실행 근거를 기록한다.

## 10. 증거 이미지 목록 — Mac 파일 미전달
runway-generation-controls.jpg (eb542fab...), runway-pending.jpg (0f45fd53...), runway-assets.jpg (b8b26590...), runway-legacy-progress.jpg (55fcc497-b6c5-49d3-b4d1-11893e876e1c), boords-storyboard.jpg (439138ac...), ivy-review-status.jpg (bf2a4956...), ltx-storyboard.webp (Projects image8), ltx-sessions.webp (image7), ltx-timeline.webp (image9), tunee-workspace.webp (공개 포스터). 로컬 존재/다운로드를 주장하지 않는다.
부모 공개 조사에는 로그인 blocker 없음. 향후 Runway 생성 워크스페이스/LTX Retake/Tunee MV 편집기 최신 동작 관찰은 사용자 직접 로그인이 필요할 수 있음. 계정 생성·결제·유료 생성은 미실행.
