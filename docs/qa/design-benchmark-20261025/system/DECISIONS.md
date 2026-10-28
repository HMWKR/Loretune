# Loretune 제작 디자인 시스템 · reference lock v2

기존 `reference-lock.md`의 무채색 브랜드를 확장한다. 목적은 광고 페이지 재현이 아니라 IP/인물/장소 일관성을 유지하는 음악영상 제작 작업대다. 비교대상 5개: Krea(시각 토큰), Clipchamp(미디어 편집 구조), ElevenLabs(검토/출력), Neural Frames·Tunee(직접 경쟁사의 진입/제작 개념). 새로운 에이전트에게 역할을 위임한 것이 아니라 참조별 설계 역할을 나눈 것이다.

## 근거 등급
M=현재 DOM computed style 실제 계측, R=Refero metadata, V=이번에 직접 본 이미지에서 관측한 구조, P=Loretune 제안값. R에 포함된 approximate 색상·크기·motion은 M이 아니다. 스크린샷에서 breakpoint/hover/animation/성공률을 추론하지 않는다. 경쟁사 로그인·계정 생성·업로드·생성 없음.

## 주/보조 참조와 결정
|참조|역할|채택|배제|적용|
|---|---|---|---|---|
|Krea style 3a63b3fa-dc79-4dc3-935e-3f8f4ab447a7 (R), 기존 Loretune (M)|주 시각 방향|near-black/coal/white CTA, 14/16/20 크기 위계, 8px controls|마케팅 hero, gradient, 영문 전용 폰트 강제|semantic surfaces/type/action|
|Clipchamp 839c1e07-b36f-42e5-9972-9e6160600c83 (R,V)|보조1 공간 구조|좌측 자산·중앙 media·하단 timeline, 선택과 미디어 맥락 동시 표시|브랜드 보라색·로고·확인 못한 drag motion 복제|scene workspace, takes, timeline|
|ElevenLabs 109cd2d1-a399-4ad9-aa54-04416cfd89d6 및 4a54… (R,V)|보조2 검토/출력|작업물 옆 검토, 출력 비용 설명과 실행 버튼 인접|붉은 transcript selection 색상을 오류 토큰으로 전용, serif 추정 복제|plan review, action quote/grant, comments|
|Neural Frames (M: signup only)|직접 경쟁 범위 확인|음악이 제작 진입점이라는 공개 제품 흐름|로그인4px radius/Geist를 내부 editor 토큰으로 일반화|음악→구간→계획 순서 점검|
|Tunee (M: public landing + V: auth)|직접 경쟁 범위 확인|대화와 작업별 모델 개념을 요구사항 대조|Poppins marketing type, 프로모션 보라/크레딧 장식|chat/image/video 분리 모델 요약|

Refero 이미지에서 Clipchamp preview와 timeline이 한 화면에 있고 ElevenLabs export popover가 작업물 가까이 있음은 직접 확인했다. metadata의 serif/색상 설명은 이미지와 일부 불일치하므로 정확 토큰으로 채택하지 않았다. Krea full style는 ../refero-0.json, flow는 ../refero-1.json, 이번 screen은 refero-screens.json.

## Loretune의 고유한 구조
- 대화는 의도 입력. 계획은 버전 있는 검토 객체. 장면은 media와 IP 개체 연결. 선택/승인/유료 실행은 서로 다른 상태다.
- media가 주 시각 자산이다. 앱 chrome에 장식 이미지나 gradient를 넣지 않는다. 빈 media는 정확한 다음 행동 안내, 실제 결과가 오면 contain으로 원본 비율 보존.
- 온톨로지 chip에는 개체명·승인 버전·변경 여부를 텍스트로 표시. 영상 성공을 뜻하는 녹색 check로 개체 선택을 표현하지 않는다.
- 대표 행동은 현재 단계에 하나. navigation selected는 dark fill+underline, 실행 CTA만 white fill. 경고 색은 검토 필요/비용 조건, 오류는 기존 salmon. 색만으로 상태 전달 금지.
- 비용 카드: 모델 release→입력/길이→견적/만료→이미 승인한 범위→실행 순. 수신 실패를 생성 실패와 섞지 않는다. backend state가 없으면 성공 UI를 꾸미지 않는다.

## 구현 경계
design-system.css는 `.lt-system` opt-in으로 기존 app에만 적용한다. integration-system.patch는 현재 소스를 기준으로 스타일 추가+body class+프로젝트/모드 toolbar wrapper만 변경. JS 이벤트/ID/데이터 의미 보존. 기존 index/backend 직접 수정하지 않았다. 상세 state component 표식은 후속 기능 구현 계약이며 CSS만으로 동작을 만든 것이 아니다.
