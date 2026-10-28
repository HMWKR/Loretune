# 토큰 비교와 Loretune 의미 매핑

등급 M/R/V/P 정의는 DECISIONS.md. 값은 표본 화면의 값이며 제품 전체 토큰을 역설계한 것이 아니다. Neural Frames/Tunee editor는 인증 경계라 내부 token·state·responsive·motion 모두 미확인이다.

|범주|Krea (R)|Clipchamp (R,V)|ElevenLabs (R,V)|Neural Frames (M signup)|Tunee (M 공개 landing/V auth)|Loretune M → P|
|---|---|---|---|---|---|---|
|색상 역할|#000 canvas/#171717 surface/#262626 secondary/#fff action|light panels, purple selection (V); 구체 hex는 R 추정|white/gray, transcript와 track의 색 구분(V); palette metadata는 역할 불명|Google button rgb51,50,57/white; login text rgb221,104,95|landing text rgb26,26,26; auth white/black(V)|#101010/#171717/#222 유지; white CTA, selected #303030, error #ffb49d|
|type family|Suisse Intl, Inter 대체|Segoe UI(R)|Inter(R), 설명 중 serif는 이미지 근거 부족|GeistSans(M)|Poppins(M landing)|system-ui → 한국어 fallback 포함 system-ui 유지|
|type scale|12/14/16/20/24…|14 body,16–18 heading,12–13 timecode(R 추정)|14–16/16(R 추정)|button14/500/24.5; input16/400/23(M)|heading36/400/54 등(M landing), 내부 미확인|body14/400/21, title20/700/28 → body14/21, section16/24, title20/28, meta12/18|
|spacing/density|gap8,card20(R)|gutters16,padding12–16(R 추정)|padding16–20(R 추정)|Google pad10×8; input16.5×14(M)|44px circle control(M landing)|toolbar10×24, nav10×24 → 4/8/12/16/24/32 scale; chrome6–8×24|
|layout|centered marketing; editor 근거 아님|자산/preview/tools + bottom timeline(V)|script/preview/comments + timeline(V)|900px viewport signup button405w(M)|auth dialog 약560w(V), 내부 미확인|1280에서 main1100,board220 → main1280,board220,preview max720(P)|
|media ratio|product imagery 강조(R)|16:9 preview(V)|원본 ratio 선택, video+script(V)|portrait video(V)|auth media 없음; landing 영상|16:9/9:16+contain 유지|
|border/radius|8control,14large(R)|8panel(R 추정), thin dividers(V)|flat panels(V), exact 미확인|button radius4/border1/none shadow(M); input 자체 radius0, 외곽 wrapper 별개|circle9999/border1rgba0,0,0,.14(M landing)|8controls, cards6/8혼재 → 4chip/8control/12panel|
|shadow|subtle action/card(R)|subtle(R 추정)|popover 분리(V)|none buttons(M)|none sampled landing buttons(M)|none→dialog만 0 16 48 #0006(P)|
|button/input|white primary/charcoal secondary(R)|import/export 강조, adjacent controls(V)|export 비용 설명 옆 CTA(V)|disabled rgba white.3/.12(M)|auth email/social 분리(V)|primary와 navigation 둘 다white → primary white, navigation dark+underline; disabled opacity.45→명시text/border|
|dialog/tabs/cards|style component guidance(R)|툴별 패널(V), 동작 미검증|export popover(V)|auth page만|auth modal(V)|640dialog 유지, project/mode toolbar wrapper, plan 카드 버전/조건/승인 묶음|
|timeline|미확인|preview 바로 아래 tracks(V)|text/audio별 track(V)|미확인|미확인|기존 numeric timeline 유지, semantic timecode 제안; draggable 구현 주장 없음|
|loading/empty/error|미확인|흐름에 upload progress/empty canvas(R), 현재 이미지 state 아님|현재 이미지에서 미확인|disabled signup(M), error실행 안함|signup/login boundary(V)|empty/plan error 관측, pending/loading은 명시 component 계약|
|focus/selected|role rules(R)|selected media frame(V)|selected transcript(V)|focus 미실행|focus 미실행|2px white outline 유지; selected underline; 상태 text 필수|
|responsive|전체 breakpoint 미확인|미확인|미확인|900px 관측만|900px 관측만|기존700/1050/1000 규칙→overlay700/1100(P); 320/390/1280별 실화면 확인|
|motion/reduced|미확인|R motion 설명은 실제 검증 아님|정지 이미지로 판단 불가|250ms material easing(M CSS 선언), 실제/reduced미검증|200ms easing(M 일부 landing)|기본none→120ms color/border만(P), reduce에서는none|

## 의미 토큰 매핑

|token|값(P)|의미/사용처|금지|
|---|---|---|---|
|--lt-canvas/surface/surface-raised|#101010/#171717/#222|작업바탕/카드/보조조작|승인 상태를 표면색만으로 표시|
|--lt-media|#050505|원본 미디어 뒤|랜딩 장식|
|--lt-text/secondary/disabled|#f5f5f5/#b5b5b5/#999|주문장/근거·메타/사용불가|opacity로 모든 내부 요소까지 흐리기|
|--lt-line/control-border|#414141/#777|그룹 경계/입력 affordance|decorative line을 유일한 입력 경계로 사용|
|--lt-action/on-action|#f5f5f5/#101010|현재 단계 대표 행동|모든 navigation을 CTA처럼 강조|
|--lt-selected|#303030|현재 단계/선택 take|승인됨과 동의어 취급|
|--lt-danger|#ffb49d|실패/invalid 및 설명|정상 선택색|
|--lt-warning|#e6c58b|검토 필요/견적 만료 설명|브랜드 배경/장식; backend state 없는 경고|
|--lt-focus|#fff|2px outline+3px offset|focus 제거|
|--lt-meta/body/section/title|12/14/16/20 × text-scale|출처/본문/영역/단계|display hero형 과대 제목|
|--lt-radius-small/control/panel|4/8/12px|chip/입력·버튼/카드·dialog|모든 요소 pill|
|--lt-duration/ease|120ms/cubic-bezier(.2,0,0,1)|hover color/border|spinner로 진행률 추정, media autoplay 강제|

`semantic-tokens.json`은 CSS에서 추출한 현재 후보값이다. `contrast-check.json`은 지정한 텍스트/표면 조합의 수학적 대비이며 WCAG 전체 준수 판정이 아니다.

원본 위치: ../refero-0.json, refero-screens.json, neural-auth-computed.json, tunee-auth-computed.json, loretune-computed.json. tunee-auth-computed.json의 표본은 query 첫20개인 **landing 요소**이며 auth dialog의 정확 token으로 사용하지 않았다. neural-access.png는 최초 전환 중 빈 화면으로 수락하지 않았고 neural-auth-boundary.png가 최종 근거다.
