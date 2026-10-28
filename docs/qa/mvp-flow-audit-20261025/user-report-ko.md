# Loretune 로컬 MVP 제작 흐름·디자인·온톨로지 QA

2026-10-25 최종 확인. **수동/로컬 미디어 제작 흐름은 개선·검증했지만, 아직 “영상 API만 해결하면 전체 MVP 완료”라고 판정할 수 없다.** 실제 AI 영상 수신과 Anthropic 제안 통합·품질 검증이 남아 있다. 전체96FR/143API와 이번 로컬 MVP를 동일 분모로 계산하지 않았다.

## 이번에 확인한 결과

- 최종 소스 전체 회귀 **133개 통과**, Python compile·브라우저 JS syntax 통과. 이전96개 수치와 별개인 새 실행이며 완성도 비율이 아니다. 마지막 실행은 ResourceWarning도 없었다.
- 실제 브라우저: 음원 업로드 → 구간확정 → 목표/스타일/보존조건/장면 계획 → 검토·샷 추가 → 영상 연결 → Take 선택·승인 → 다음샷 재사용·별도 승인 → 한국어 자막 → 타임라인 승인 → 10초1920×1080 출력.
- 합성 fixture MP4의 video/audio/subtitle 3트랙, duration10, 플레이어 readyState4/error없음. 모델 생성 영상이 아닌 **로컬 합성 fixture**다.
- 별도 색상 clock/클릭 음원 테스트는 trim/reorder 후 색상순서, 클릭 시작 .25/1.25초, Unicode 자막과 .1초타이밍, 총길이를 검사했다. 시간 허용오차1/24초. 프레임 숫자 OCR·전환·crop은 검증하지 않았다. 현재 renderer는 contain/pad이며 crop/전환 편집을 제공하지 않는다.
- 320 CSS px: 일반 문서 가로 넘침 없음, 430px 타임라인은 내부 스크롤. 이동버튼26×32px. 200% 글자28px와320px 조합 리플로 확인. 계획폼8개 순차 포커스에 visible outline 확인. 전체 AA 준수나 전체 작업 키보드 완주를 뜻하지 않는다.
- 모드 왕복·브리프 새로고침 보존, 모달 저장 후 내부 status focus, 개체 승인/수정/복원·동일ID, 샷1만 stale/샷2영향없음, 기존MP4해시불변 확인.

## 수정한 실제 결함

1. 상단 관리버튼 과밀·음절 줄바꿈, 채팅에 작업대 전체가 중복 노출되던 흐름을 안내형4단계/동일데이터 상세작업대로 변경.
2. 계획 길이5초와 저장전 기본검사3초 불일치, 음악 선택구간 시작점 누락 수정.
3. 자막 DOM 입력과 저장 draft 불일치 재현 후 입력/저장수집 수정.
4. 온톨로지 외부참고 dangling edge, stale충돌400→409, 기존개체 수정시 새ID 생성 UI 문제 수정.
5. 모달 저장후 포커스가 밖으로 빠지던 문제 수정.
6. 기존 사용자 저장소의 filename 없는 레거시Take로 계보 조회가 끊기던 문제 수정. 원본 데이터 변경 없이 fallback 표시, 레거시 테스트 추가.
7. 백업의 SQLite 연결 미종료와 진행중생성/수신 backup허용 문제 수정. 실제 사용자 백업/삭제는 수행하지 않고 fixture만 검사.

변경: `app.py`, `index.html`, `editing.py`, `backup.py`, 신규 `guided.py`, `ontology.py`, `project_ontology.py`, `anthropic_ontology.py` 및 관련 테스트. 변경 전 코드 snapshot과 최종해시는 이 폴더에 보존했다. `.env`·`.codex`·실비용원장은 수정하지 않았다.

## 요구사항과 간소화 판정

`requirement-qa-matrix.json/csv`:96FR 각각 원문/사용자목표/범위/화면/코드/간소화/QA/기대·실제/상태/증거를 연결했다. 현재 분류는 로컬MVP필수51, 공급자경계11, 후속제품34이며 **51개 원문 전체 완료**를 의미하지 않는다. 원문 전체기준이 충족되지 않은 항목은 partial/not run으로 남겼다. `api-qa-classification.json`은143API를 별도 추적한다. 로컬 action 존재를 원문 REST 계약 완료로 계산하지 않는다.

관리8개 버튼을1개 disclosure 안에 넣어 초기 선택지를 줄였지만 관리기능 접근은1클릭 증가한다. 신규계획은 목표·보존조건 입력을 추가했으므로 총클릭 감소를 주장하지 않는다. 동일프로젝트 왕복에서 음원·영상 재업로드0회, 두번째샷은 자산 재사용으로 파일선택을 반복하지 않았다. 간소화 전후 전체클릭수 통제 실험과 실제 novice실험은 미실시다.

방법론·경쟁사 출처와 적용판정은 `design-decisions.md`. 새 화면증거는01~06파일, 기존Refero/REA/경쟁사 문서는 역사적 근거다. 이세션 Refero 직접조회는 link_id 누락으로 실패했고 REA 도구는 미노출이었다. 부모가 전달한 공식근거를 사용했으며 도구사용을 꾸미지 않았다.

## 온톨로지의 실제 범위

- 별도 그래프DB 대신 SQLite scoped append-only 승인버전·proposal·head. strict schema, UUID/type, dangling/cycle, source exact span, uncertainty, stale base, 승인 transaction, 복원 검증.
- 샷/Take/자산 runtime계보는 읽기전용, 인물·장소·스타일은 별도 semantic annotation. 사용자가 선택한 승인개체를 샷에 연결한다. 그 개체 변경만 stale 표시하며 기존Take·출력은 유지한다. 출력manifest는 연결한 semantic_context를 고정한다.
- 기존명칭 기반 project ID는 rename 기능이 없는 현재 로컬모델에 한정한다. 향후 project rename/merge 도입에는 영속 UUID migration이 필요하다. 모든 원본명세의 사건·시간·분기 의미 추론이 완성된 것은 아니다.
- Anthropic `Anthropic_KEY` 이름만 계약에 사용. **실제 값 조회·전송0**. Haiku5.5 structured proposal 및 bounded transport fake검증 완료. LLM 결과는 사실/승인으로 자동취급하지 않는다. 실제 제안 요청을 앱 작업흐름에 활성화하는 통합은 다음 승인된 시험 단계에서 필요하다.

## 정확한 남은 게이트

1. **fal live 차단 유지:** 첫실험은 token200→CDN403, 추가실험은 token발급403→CDN미실행. 마지막실청구 미확인. 이번 새생성/다운로드재시도0, 기존2job import_blocked·원장보존. root403 해결이라고 주장하지 않는다.
2. **Anthropic pending approval:** 합성문장+스키마, Haiku5.5, input4096/output2048, 추정$0.0014336·제안$0.01,1회/retry0. count_tokens도승인후. 기존키memory-only 인증·비밀로그0. 자세한 단일 승인안 `anthropic-approval-proposal.md`. 기존Kling예산 재사용 금지.
3. **미완료 로컬 QA:** 전체키보드 end-to-end, 스크린리더, 키보드만으로 파일 선택부터 납품까지 완주, 텍스트·컨트롤 대비 전수, reduced-motion 실환경. 400%browser zoom은 IAB 단축키가 실제배율을 변경하지 않아 미검증. 200%제품글자설정으로 대체했다고 주장하지 않는다.
4. **후속 운영:** 실제 계정/조직RBAC, 다중사용자배포·클라우드복구·부하/SLO, 구독/청구자동대사, 전체API호환 미완료. 로컬single-owner 앱을 유료멀티테넌트출시 준비완료라 부르지 않는다.

내부 시연: 가능(로컬합성·수동입력/공급자한계공개). 제한된 파일럿: 관리자가 동행하는 로컬편집 usability범위 가능, AI자동제작 성공 검증파일럿은 아직 차단. 유료출시: 준비안됨. 비율 대신 실제 흐름과 차단 기준으로 판정한다.

## 실행 상태

8765 실제사용자앱 정상, 프로젝트6/revision81/공급자disconnected/기존generation2건import_blocked/활성렌더0. 8772 격리QA 기본흐름 프로젝트1/revision21 기록 후 30샷 긴이름 fixture를 추가하여 프로젝트2개. 기본흐름 ontologyv3/활성렌더0. `final-local-state.json` 참조. 사용자앱에 QA작품을 추가하지 않았다.


### 후속 경계 검사

긴 작품명과1307자 설명을 가진30샷 fixture를 별도프로젝트로 추가했다. 실제320px에서 문서폭320, 샷목록만내부스크롤,30번째샷 Enter선택 확인. `07-large-project-320.png`와`large-project-fixture.json` 참조. 수백샷/다중worker부하/SLO 검증은 아니다. 현재보이는 CSS텍스트130개 대비샘플 최소6.07:1,4.5미만0개(`contrast-sample.json`). Placeholder와입력/버튼경계 대비도 강화했다. native미디어컨트롤·이미지배경·모든상태 전수검사와AA선언은 제외한다.
