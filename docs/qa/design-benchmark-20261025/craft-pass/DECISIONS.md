# Craft pass · reference lock / tokens

목표: revision59의 구조를 보존하며 읽기 위계와 조작부 마감을 개선한다. 신규 기능·새 palette·유료 미디어·경쟁사 계정 작업은 범위 밖. 조사 확장 없이 기존 참조를 재사용한다.

주 참조: Krea Refero style `3a63b3fa-dc79-4dc3-935e-3f8f4ab447a7`의 coal canvas / white action / 14·16·20px 위계. 보조: Clipchamp screen `839c1e07-b36f-42e5-9972-9e6160600c83`의 미디어·타임라인 인접성, ElevenLabs `109cd2d1-a399-4ad9-aa54-04416cfd89d6`의 검토·출력 위계. Neural Frames 공식 Track/Storyboard 이미지는 짧은 맥락과 미디어 옆 작업 제어의 참고이며 직접 로그인 편집기 관찰이 아니다. 정확 타사 토큰을 측정했다고 주장하지 않는다.

|결정|근거/역할|후보 값(P)|
|---|---|---|
|canvas / review / input 분리|Krea R + 기존 브랜드|#101010 / #1b1b1b / #141414|
|본문·보조·제목|Krea R + 한국어 읽기|14px/1.6, 13px/1.55, 20px/1.4|
|구조선과 실제 입력선 분리|기존 semantic roles|#353535 구조, #707070 입력|
|white action 유지|실행·기록 CTA 전용|#f4f4f2 on #151515|
|선택 상태|탐색 선택≠작업 승인|중립 fill+흰 inset 표시, 텍스트 보존|
|작업 상태 chip|사용자 승인 구분|서버 결정 문자열 그대로, 색만으로 의미 전달하지 않음|
|작업 영수증·반복 설명 disclosure|ElevenLabs 검토 맥락/Refero craft|모델·$0·전송없음·연산비미계측·승인 상태는 항상 표시, 상세만 접힘|
|검토 패널 표면|NF 작업물 옆 제어 / 기존 구조|288px 유지, 내부16px, radius12px|
|브랜드 표식|Loretune 기존 wordmark|750 weight와 간격만 정리. 3선 표식은 메뉴 버튼으로 오인할 수 있어 후보 시각 검사 후 배제|
|mobile compact|현재 실제 기하/44px touch craft|같은 작업 탭, 중복 저장 설명만 disclosure, 44px target 유지|

간격: 4/8/12/16/24. control radius8, media/review12, chip6. 그림자는 dialog에만. 무장식 배경, 외부 font/icon 로딩 없음. 새 animation 없음. 기존 위험·오류 토큰은 유지하며 error는 disclosure 밖에서 바로 볼 수 있도록 자동 펼침.

토큰은 Loretune 제안(P)이다. 참조 R/V, 현재 M의 상세 출처는 ../system/DECISIONS.md와 ../structure/DECISIONS.md. 이번 산출물은 미통합 후보이며 후속 기능 회귀가 필요하다.
