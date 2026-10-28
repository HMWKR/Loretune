# 컴포넌트·상태 계약과 수락 체크리스트

☑=이 후보의 코드/제한된 렌더에 존재, □=통합·기능 검증 필요. 값의 정확성/실제 모델 성공과 외형은 분리한다.

|컴포넌트|default/selected|empty/loading|error/disabled|keyboard/mobile|현재|
|---|---|---|---|---|---|
|ProjectBar|작품명·모드 각각 독립, 선택모드 underline|불러오기 전 작품명 placeholder|읽기실패 시 retry; 새 작품 draft보존|select label, DOM order 유지|☑wrapper/CSS □read failure|
|StageNav|현재단계 dark+underline+aria-current|현재단계 유지, 이동은 실행 승인 아님|미완료 조건 text 설명|Tab/Enter,2×2mobile|☑style □모든 state|
|ModelSummary/Dialog|세 역할/실제 release 상세|미선택 text|unavailable 이유, 선택≠연결|Escape/복귀, 전체ID 줄바꿈|☑dialog/Enter·Escape·focus복귀 □전체ID 패치 통합|
|ChatComposer|사용자 의도/참조 IP|목표 질문과 예시 1개, 가짜 대화 없음|미연결/응답실패와 local draft 분리|label 유지, submit 중복 방지|□실제 chat 연결; 현재 brief form|
|PlanReview|버전,원곡구간,장면,IP,비용승인 분리|구간미확정이면 승인불가|expired/stale 별도 이유; 입력보존|검토 card 내부 CTA,disabled 이유 외부 text|☑card style □조건제어|
|EntityChip|개체명·type·승인v·근거|개체 없음→등록 안내|변경됨→재검토,자동대체 금지|긴 한국어 wrap;link/button 역할 구분|☑CSS contract □DOM 연결|
|SceneList/TakeStrip|선택take와 승인take 별도|미디어없음→로컬 연결 안내|upload실패/검토거절 표시|가로strip focus scroll, 썸네일alt|☑style □많은샷회귀|
|Preview|contain,원본비율|placeholder는 방향/입력조건|수신대기≠미디어손상|video controls,label|☑빈화면 □실제media 재생|
|ActionQuote/Grant|release,입력해시/길이,비용,만료,scope|계산중에는unknown;0원으로 표시금지|권한없음/만료/상태불명 분리|사람 승인 focus 및 close/reopen 보존|□기능팀 구현중|
|JobCard|queued/running/imported/reviewed 분리|값 있으면 determinate progress|failed/unknown/recovery 별도 문구|role=status,에러 연결/복구 버튼|☑CSS contract □전체전이|
|Timeline|원곡절대시간+trim+자막|빈 track은 추가 안내|invalid field inline reason|keyboard reorder/numeric 대안,가로scroll 영역 label|☑기존 구조 style □full flow|
|ExportReview|해상도/음원/자막/버전/다운로드|render 중 기존 승인본 유지|출력실패≠납품미승인|CTA 1개/취소 복귀|□통합 full flow|

상태 DOM 계약 예시(미연결 CSS specimen이며 실제 backend 상태로 채워야 함):
```html
<span class="lt-status" data-state="review">검토 필요</span>
<span class="lt-entity">Mira · 인물 <span>승인 v3</span></span>
<p id="model-video-full" class="lt-model-name">영상 모델: 실제 registry의 전체 release ID</p>
<select aria-describedby="model-video-full model-video-status">…</select>
<p id="plan-blocker" class="lt-inline-error">음악 구간을 확정한 뒤 새 계획을 검토하세요.</p>
<button disabled aria-describedby="plan-blocker">계획 승인</button>
```

## state별 수락
- □빈/queued/running/failed/unknown/completed/reviewed를 고정 fixture로 모두 캡처. screenshot만으로 상태전이 검증 통과 금지.
- □disabled는 opacity가 아닌 명시 text·surface. action blocked 이유가 Tab로 읽히는 본문에 존재.
- □focus·selected·hover 동시에 구별; outline clipping 없음. focus order와 visual order 일치.
- □320/390/768/1100/1280,긴 작품명/전체release ID/한국어2000자/30샷.
- □실제 browser200/400%,screen reader. viewport 축소·text-scale 대체 검증과 구분.
- ☑reduce emulation에서 transition 0s 확인, □OS 설정·고대비 모드 검사.
- □기능팀 audit freeze의 index/backend hash와 실제 GET hash가 일치한 뒤 full flow.
